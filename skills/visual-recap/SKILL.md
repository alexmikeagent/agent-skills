---
name: visual-recap
description: Turn a substantial PR, branch, commit, or scoped git diff into an evidence-grounded Obsidian-friendly Markdown, restricted MDX, and static HTML recap. Use after implementation when reviewers need the outcome, file footprint, architecture or contract changes, focused excerpts, verification, and risks at a higher level than the raw diff; skip small obvious changes and forward plans.
---

# Visual Recap

Build the recap from the actual change, not from intent or memory. Produce:

```text
recaps/<slug>/
  index.md
  presentation.mdx
  artifact.html
  assets/
```

`index.md` is the durable source of truth. The other files are generated review
surfaces that remain local, portable, and free of hosted dependencies.

## Workflow

1. Establish the exact comparison point and exclude unrelated dirty work.
   Inspect the diff, status, changed-file list, commit messages, tests, and the
   load-bearing changed source.
2. Inventory meaningful surfaces: user-visible states, routes, data models,
   APIs, workflows, configuration, tests, migrations, and operational changes.
3. Write a concise `index.md` containing:
   - outcome and why it matters
   - scope and comparison point
   - before/after behavior
   - changed file tree grouped by responsibility
   - important schema, API, or workflow changes
   - 3–8 focused implementation excerpts or explanations
   - validation actually run and its results
   - compatibility, security, rollout, and unresolved risks
4. Write `presentation.mdx` from the same evidence. Use `Comparison`, `Flow`,
   `FileTree`, `CodeWalkthrough`, `DataModel`, `ApiEndpoint`, `EvidenceTable`,
   and `Disclosure` selectively.
5. Read `~/.agents/skills/mdx-publish/references/components.md`, then run:

```sh
npm --prefix ~/.agents/skills/mdx-publish run check -- "$PWD/recaps/<slug>"
npm --prefix ~/.agents/skills/mdx-publish run build -- "$PWD/recaps/<slug>"
```

6. Inspect `artifact.html` locally at desktop and narrow width. Confirm the
   recap matches the current diff and does not expose secrets or sensitive
   source material.

Use `tasteful-html-artifacts` if an exact UI before/after or interactive review
surface is essential. Label reconstructed UI as inference unless it was captured
from the running product.

## Quality bar

- Cite file paths, symbols, tests, and commits precisely.
- Distinguish verified behavior, interpretation, and remaining risk.
- Show the shape of the change; do not dump an entire diff into the artifact.
- Do not claim a test passed unless its command and result were observed.
- Keep the recap standalone and useful after the branch or chat disappears.
