#!/usr/bin/env node

import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

import { evaluate } from "@mdx-js/mdx";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import * as jsxRuntime from "react/jsx-runtime";
import remarkFrontmatter from "remark-frontmatter";
import remarkGfm from "remark-gfm";
import { visit } from "unist-util-visit";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const THEME = path.resolve(HERE, "../assets/theme.css");
const MAX_ASSET_BYTES = 8 * 1024 * 1024;

const COMPONENT_NAMES = new Set([
  "Callout",
  "MetricGrid",
  "Metric",
  "Comparison",
  "Option",
  "Steps",
  "Step",
  "Timeline",
  "Event",
  "EvidenceTable",
  "FileTree",
  "CodeWalkthrough",
  "ApiEndpoint",
  "DataModel",
  "Flow",
  "Node",
  "Edge",
  "Disclosure",
]);

const HTML_TAGS = new Set([
  "a", "abbr", "b", "blockquote", "br", "cite", "code", "dd", "del",
  "details", "div", "dl", "dt", "em", "figcaption", "figure", "h1",
  "h2", "h3", "h4", "h5", "h6", "hr", "i", "img", "kbd", "li",
  "mark", "ol", "p", "pre", "q", "s", "small", "span", "strong",
  "sub", "summary", "sup", "table", "tbody", "td", "tfoot", "th",
  "thead", "tr", "u", "ul",
]);

const BOOLEAN_ATTRIBUTES = new Set(["open"]);
const STRING_ATTRIBUTES = new Set([
  "alt", "aria-label", "className", "href", "id", "role", "src", "title",
  "type", "label", "value", "name", "method", "path", "status", "tone",
  "verb", "endpoint", "from", "to", "kind", "date", "number", "caption",
]);

const MIME_TYPES = new Map([
  [".gif", "image/gif"],
  [".jpeg", "image/jpeg"],
  [".jpg", "image/jpeg"],
  [".png", "image/png"],
  [".webp", "image/webp"],
]);

function usage() {
  console.error("Usage: npm run <check|build> -- <bundle-directory>");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function stripCode(text) {
  return text
    .replace(/```[\s\S]*?```/g, "")
    .replace(/~~~[\s\S]*?~~~/g, "")
    .replace(/`[^`\n]*`/g, "");
}

function parseFrontmatter(text) {
  if (!text.startsWith("---\n")) return {};
  const end = text.indexOf("\n---", 4);
  if (end < 0) return {};
  const data = {};
  for (const line of text.slice(4, end).split("\n")) {
    const match = line.match(/^([A-Za-z0-9_-]+):\s*(.*?)\s*$/);
    if (match) data[match[1]] = match[2].replace(/^['"]|['"]$/g, "");
  }
  return data;
}

function validateAttributes(raw, tag, errors) {
  let rest = raw.replace(/^\s+|\s+$/g, "");
  if (rest.endsWith("/")) rest = rest.slice(0, -1).trim();
  while (rest) {
    const match = rest.match(/^([A-Za-z_:][A-Za-z0-9_.:-]*)(?:\s*=\s*("[^"]*"|'[^']*'))?(?:\s+|$)/);
    if (!match) {
      errors.push(`Unsupported or unquoted attribute syntax on <${tag}>: ${rest}`);
      return;
    }
    const name = match[1];
    const lower = name.toLowerCase();
    const hasValue = Boolean(match[2]);
    if (lower.startsWith("on") || lower === "style" || lower === "dangerouslysetinnerhtml") {
      errors.push(`Forbidden attribute ${name} on <${tag}>`);
    } else if (name.startsWith("aria-") || name.startsWith("data-")) {
      if (!hasValue) errors.push(`Attribute ${name} on <${tag}> requires a quoted string`);
    } else if (hasValue && !STRING_ATTRIBUTES.has(name)) {
      errors.push(`Undeclared string attribute ${name} on <${tag}>`);
    } else if (!hasValue && !BOOLEAN_ATTRIBUTES.has(name)) {
      errors.push(`Undeclared boolean attribute ${name} on <${tag}>`);
    }
    if (hasValue) {
      const value = match[2].slice(1, -1);
      if ((lower === "src" || lower === "poster") && /^(?:https?:)?\/\//i.test(value)) {
        errors.push(`Remote runtime asset is forbidden on <${tag}>`);
      }
      if (lower === "href" && /^(?:javascript|data):/i.test(value)) {
        errors.push(`Unsafe link scheme is forbidden on <${tag}>`);
      }
    }
    rest = rest.slice(match[0].length).trimStart();
  }
}

function validateSource(text, file) {
  const errors = [];
  const body = stripCode(text);
  const checks = [
    [/^\s*(?:import|export)\s/m, "imports and exports are forbidden"],
    [/[{}]/, "JavaScript expressions are forbidden"],
    [/<\s*(?:script|iframe|object|embed|style|form|input|button|video|audio)\b/i, "executable, interactive, or embedded HTML is forbidden"],
    [/\bdangerouslySetInnerHTML\b/i, "dangerouslySetInnerHTML is forbidden"],
    [/\bon[A-Za-z]+\s*=/i, "event-handler attributes are forbidden"],
  ];
  for (const [pattern, message] of checks) {
    if (pattern.test(body)) errors.push(message);
  }

  for (const match of body.matchAll(/<\/?([A-Za-z][A-Za-z0-9.]*)\b([^<>]*?)>/g)) {
    const [, tag, rawAttributes] = match;
    if (tag.includes(".")) {
      errors.push(`Member-expression component <${tag}> is forbidden`);
      continue;
    }
    if (/^[A-Z]/.test(tag)) {
      if (!COMPONENT_NAMES.has(tag)) errors.push(`Undeclared component <${tag}>`);
    } else if (!HTML_TAGS.has(tag)) {
      errors.push(`Undeclared HTML element <${tag}>`);
    }
    if (!match[0].startsWith("</")) validateAttributes(rawAttributes, tag, errors);
  }

  if (errors.length) {
    throw new Error(`${file}:\n- ${[...new Set(errors)].join("\n- ")}`);
  }
}

function element(tag, className, props, extra = {}) {
  const { children, ...rest } = props;
  return React.createElement(tag, { ...rest, ...extra, className }, children);
}

const components = {
  Callout: (props) => element("aside", `callout tone-${props.tone || "info"}`, props, { role: "note" }),
  MetricGrid: (props) => element("section", "metric-grid", props),
  Metric: ({ label, value, children }) => React.createElement(
    "article", { className: "metric" },
    React.createElement("span", { className: "metric-label" }, label),
    React.createElement("strong", { className: "metric-value" }, value),
    children ? React.createElement("div", { className: "metric-detail" }, children) : null,
  ),
  Comparison: (props) => element("section", "comparison", props),
  Option: ({ name, status, children }) => React.createElement(
    "article", { className: "option" },
    React.createElement("header", null, React.createElement("h3", null, name), status ? React.createElement("span", { className: "badge" }, status) : null),
    children,
  ),
  Steps: (props) => element("ol", "steps", props),
  Step: ({ title, children }) => React.createElement("li", { className: "step" }, React.createElement("strong", null, title), children),
  Timeline: (props) => element("section", "timeline", props),
  Event: ({ date, title, children }) => React.createElement("article", { className: "event" }, React.createElement("time", null, date), React.createElement("h3", null, title), children),
  EvidenceTable: (props) => element("section", "evidence-table", props),
  FileTree: (props) => element("pre", "file-tree", props),
  CodeWalkthrough: ({ title, children }) => React.createElement("section", { className: "code-walkthrough" }, title ? React.createElement("h3", null, title) : null, children),
  ApiEndpoint: ({ method, path: endpointPath, children }) => React.createElement("section", { className: "api-endpoint" }, React.createElement("header", null, React.createElement("span", { className: "method" }, method), React.createElement("code", null, endpointPath)), children),
  DataModel: ({ name, children }) => React.createElement("section", { className: "data-model" }, React.createElement("h3", null, name), children),
  Flow: (props) => element("section", "flow", props),
  Node: ({ title, kind, children }) => React.createElement("article", { className: `flow-node kind-${kind || "default"}` }, React.createElement("h3", null, title), children),
  Edge: ({ from, to, label }) => React.createElement("div", { className: "flow-edge", "aria-label": `${from} to ${to}` }, React.createElement("span", null, `${from} → ${to}`), label ? React.createElement("small", null, label) : null),
  Disclosure: ({ title, open, children }) => React.createElement("details", { className: "disclosure", open }, React.createElement("summary", null, title), children),
};

function headingsPlugin() {
  return (tree) => {
    visit(tree, "heading", (node) => {
      // Rendering adds stable ids later. This visit intentionally exercises the
      // pinned AST dependency and keeps heading processing in one pipeline.
      node.data ||= {};
    });
  };
}

function plainText(html) {
  return html.replace(/<[^>]+>/g, " ").replace(/&[A-Za-z0-9#]+;/g, " ").replace(/\s+/g, " ").trim();
}

function slug(value) {
  return value.toLowerCase().normalize("NFKD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "section";
}

function addHeadingIds(html) {
  const counts = new Map();
  const headings = [];
  const output = html.replace(/<h([1-3])([^>]*)>([\s\S]*?)<\/h\1>/g, (full, level, attrs, content) => {
    const label = plainText(content);
    const base = slug(label);
    const count = (counts.get(base) || 0) + 1;
    counts.set(base, count);
    const id = count === 1 ? base : `${base}-${count}`;
    headings.push({ level: Number(level), label, id });
    const cleanAttrs = attrs.replace(/\s+id=(?:"[^"]*"|'[^']*')/g, "");
    return `<h${level}${cleanAttrs} id="${id}">${content}</h${level}>`;
  });
  return { html: output, headings };
}

function tocMarkup(headings) {
  const useful = headings.filter((heading) => heading.level === 2 || heading.level === 3);
  if (!useful.length) return "";
  return `<nav class="toc" aria-label="On this page"><strong>On this page</strong><ol>${useful.map((heading) => `<li class="toc-level-${heading.level}"><a href="#${heading.id}">${escapeHtml(heading.label)}</a></li>`).join("")}</ol></nav>`;
}

async function inlineAssets(html, bundle) {
  const root = path.resolve(bundle);
  const matches = [...html.matchAll(/<img\b([^>]*?)\bsrc="([^"]+)"([^>]*)>/gi)];
  let output = html;
  for (const match of matches) {
    const src = match[2];
    if (/^(?:data:|https?:|\/\/)/i.test(src)) {
      if (!src.startsWith("data:")) throw new Error(`Remote image is forbidden: ${src}`);
      continue;
    }
    const asset = path.resolve(root, src);
    if (asset !== root && !asset.startsWith(`${root}${path.sep}`)) throw new Error(`Image path escapes bundle: ${src}`);
    const extension = path.extname(asset).toLowerCase();
    const mime = MIME_TYPES.get(extension);
    if (!mime) throw new Error(`Unsupported image type for self-contained HTML: ${src}`);
    const stat = await fs.stat(asset);
    if (stat.size > MAX_ASSET_BYTES) throw new Error(`Image exceeds 8 MB: ${src}`);
    const encoded = (await fs.readFile(asset)).toString("base64");
    output = output.replace(match[0], `<img${match[1]}src="data:${mime};base64,${encoded}"${match[3]}>`);
  }
  return output;
}

async function checkBundle(bundle) {
  const indexPath = path.join(bundle, "index.md");
  const presentationPath = path.join(bundle, "presentation.mdx");
  const index = await fs.readFile(indexPath, "utf8");
  if (!index.trim()) throw new Error(`${indexPath} is empty`);
  let sourcePath = indexPath;
  let source = index;
  try {
    source = await fs.readFile(presentationPath, "utf8");
    sourcePath = presentationPath;
  } catch (error) {
    if (error.code !== "ENOENT") throw error;
  }
  validateSource(source, sourcePath);
  return { index, source, sourcePath };
}

async function render(bundle) {
  const { index, source, sourcePath } = await checkBundle(bundle);
  const evaluated = await evaluate(source, {
    ...jsxRuntime,
    baseUrl: new URL(`file://${sourcePath}`),
    remarkPlugins: [remarkFrontmatter, remarkGfm, headingsPlugin],
  });
  const content = renderToStaticMarkup(React.createElement(evaluated.default, { components }));
  const withAssets = await inlineAssets(content, bundle);
  const { html, headings } = addHeadingIds(withAssets);
  const metadata = { ...parseFrontmatter(index), ...parseFrontmatter(source) };
  const title = metadata.title || headings.find((heading) => heading.level === 1)?.label || path.basename(bundle);
  const description = metadata.description || `Static document: ${title}`;
  const css = await fs.readFile(THEME, "utf8");
  const document = `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="${escapeHtml(description)}">
  <title>${escapeHtml(title)}</title>
  <style>${css}</style>
</head>
<body>
  <a class="skip-link" href="#content">Skip to content</a>
  <div class="page-shell">
    ${tocMarkup(headings)}
    <main id="content" class="document">${html}</main>
  </div>
</body>
</html>
`;
  const outputPath = path.join(bundle, "artifact.html");
  await fs.writeFile(outputPath, document, "utf8");
  return outputPath;
}

const [command, rawBundle] = process.argv.slice(2);
if (!command || !rawBundle || !new Set(["check", "build"]).has(command)) {
  usage();
  process.exit(2);
}

const bundle = path.resolve(rawBundle);
try {
  if (command === "check") {
    const { sourcePath } = await checkBundle(bundle);
    console.log(`[OK] Restricted MDX passed: ${sourcePath}`);
  } else {
    console.log(`[OK] Static HTML written: ${await render(bundle)}`);
  }
} catch (error) {
  console.error(`[ERROR] ${error.message}`);
  process.exit(1);
}
