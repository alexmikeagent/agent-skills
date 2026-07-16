# Agent Skills

Canonical, source-controlled global skills for this Mac.

- Runtime path: `~/.agents/skills`
- Canonical repository: this directory
- Obsidian view: generated one-way mirror in `Second Brain/90 Meta/Skills Mirror`

The `skills/` directory is the only skill source of truth. Changes made in the
Obsidian mirror are not promoted unless `skills-promote --apply` is used.

## Operating commands

```sh
skills-doctor
skills-mirror
skills-promote path/to/file
skills-promote --apply path/to/file
vault-health
```

The MDX renderer lives entirely under `skills/mdx-publish`; its dependencies
are pinned by `package-lock.json` and audited in `tooling-lock.json`. Third-party
sources and local adaptations are recorded in `THIRD_PARTY_NOTICES.md`.

`ops/second_brain.py` backs the local `sb-*`, `skills-*`, and `vault-health`
commands. The checked-in LaunchAgent runs a validated snapshot every 30 minutes.
