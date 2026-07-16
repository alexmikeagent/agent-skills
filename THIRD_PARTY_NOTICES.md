# Third-party notices

This repository contains adapted instructions and pinned runtime dependencies.
The local modifications are documented in Git history.

## Obsidian skills

- Source: [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills)
- Revision: `a1dc48e68138490d522c04cbf5822214c6eb1202`
- Imported: `obsidian-markdown`, `obsidian-bases`, and `json-canvas`
- License: MIT
- Local changes: removed plugin-dependent map and diagram branches, added
  local agent metadata, and kept only native Obsidian functionality used by
  this vault.

## Visual plan and recap concepts

- Source consulted: [BuilderIO/skills](https://github.com/BuilderIO/skills)
- Revision: `d1344bc088f850f829d9bcf4170516bb670a438f`
- Context consulted: [Introducing /visual-plan](https://youtu.be/NE0aBuQF0HA)
  and [Builder.io's visual planning write-up](https://www.builder.io/blog/claude-code-plan)
- License: MIT
- Local changes: replaced hosted services, authentication, connectors, and
  remote preview tooling with canonical Markdown, restricted MDX, and a local
  static renderer. No upstream executable code is retained.

## MDX publishing runtime

The `mdx-publish` skill pins these npm packages in `package-lock.json`:

- `@mdx-js/mdx` 3.1.1 — MIT
- `react` 19.2.7 — MIT
- `react-dom` 19.2.7 — MIT
- `remark-frontmatter` 5.0.0 — MIT
- `remark-gfm` 4.0.1 — MIT
- `unist-util-visit` 5.1.0 — MIT

Their transitive license notices remain available in their npm package
metadata and upstream repositories.
