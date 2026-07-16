---
name: skills-repo-maintenance
description: Maintain the canonical global skills repository, verify that ~/.agents/skills is the only user-authored runtime source, generate its one-way Obsidian mirror, audit skill metadata and tool dependencies, and explicitly promote reviewed mirror edits. Use for global skill installation, migration, deduplication, mirroring, promotion, or drift repair.
---

# Skills Repository Maintenance

The canonical repository is
`/Users/aman-mac-work/Documents/PERSONAL/Projects/agent-skills`; the runtime path
is `~/.agents/skills`. Existing `.agents` content wins any merge collision.

Use the bundled Python tool:

```sh
python3 scripts/skills_tool.py doctor
python3 scripts/skills_tool.py mirror
python3 scripts/skills_tool.py promote <mirror-relative-path>
python3 scripts/skills_tool.py promote --apply <mirror-relative-path>
```

`promote` is a dry-run unless `--apply` is present. Never install into or
recreate `~/.codex/skills`. Codex may materialize its own marker-backed
`.codex/skills/.system` bundle; it is not a user skill repository, and duplicate
system skills must be disabled in `~/.codex/config.toml` so the reviewed
`.agents` copies win. Stage third-party skills outside the canonical tree, read
them completely, retain their license/provenance, remove irrelevant or
missing-tool branches, validate, then add them intentionally.
