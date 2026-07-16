---
name: mdx-publish
description: Create and validate portable rich-document bundles containing canonical Obsidian Markdown, restricted MDX, and self-contained static HTML. Use when the user explicitly requests MDX, reusable document components, a rich HTML-like report, or an Obsidian-friendly artifact bundle; do not use for normal notes, forward implementation plans, or Git diff recaps.
---

# MDX Publish

Keep Markdown canonical and create this bundle:

```text
<slug>/
  index.md
  presentation.mdx
  artifact.html
  assets/
```

## Workflow

1. Finish `index.md` first. Preserve evidence, decisions, caveats, identifiers,
   and source links.
2. Author `presentation.mdx` with Markdown plus only the components documented
   in `references/components.md`.
3. Do not use imports, exports, expressions, event handlers, scripts, iframes,
   remote runtime assets, or undeclared components.
4. Validate and build:

```sh
npm run check -- <bundle-directory>
npm run build -- <bundle-directory>
```

5. Confirm `artifact.html` is responsive, printable, keyboard-readable,
   self-contained, and still useful without JavaScript. The renderer emits no
   client JavaScript.

Never render downloaded or third-party MDX. Preserve it as text or convert it
to reviewed Markdown first. Use `tasteful-html-artifacts` instead when the
document needs a bespoke reading interface beyond the restricted component set.

