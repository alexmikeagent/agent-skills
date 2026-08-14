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

## Matt Pocock skills

- Source: [mattpocock/skills](https://github.com/mattpocock/skills)
- Tag: `v1.2.3`
- Peeled commit: `6acc160e4e0cd062dbbbd7a1b26ae92855edf07e`
- Imported promoted engineering skills: `ask-matt`, `code-review`,
  `codebase-design`, `diagnosing-bugs`, `domain-modeling`, `grill-with-docs`,
  `implement`, `improve-codebase-architecture`, `prototype`, `research`,
  `resolving-merge-conflicts`, `setup-matt-pocock-skills`, `tdd`, `to-spec`,
  `to-tickets`, `triage`, `wayfinder`, and `wizard`
- Imported promoted productivity skills: `grill-me`, `grilling`, `handoff`,
  `teach`, `to-questionnaire`, `wait-what`, and `writing-for-agents`
- Local changes within imported packages: none. Each imported package is kept
  byte-for-byte identical to its directory at the pinned upstream revision.
- License: MIT

MIT License

Copyright (c) 2026 Matt Pocock

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

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
