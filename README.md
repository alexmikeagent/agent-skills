# Agent Skills

Canonical, source-controlled global skills for this Mac.

- Runtime path: `~/.agents/skills`
- Canonical repository: this directory
- Obsidian view: generated one-way mirror in `Second Brain/90 Meta/Skills Mirror`

The `skills/` directory is the only skill source of truth. Changes made in the
Obsidian mirror are not promoted unless `skills-promote --apply` is used.
Codex may recreate a marker-backed `~/.codex/skills/.system` bundle for built-in
skills. It contains no user-installed skills; overlapping built-ins are disabled
in `~/.codex/config.toml`, leaving the reviewed `.agents` versions active.

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

`ops/second_brain.py` backs the local `sb-status`, `sb-refresh`, `skills-*`, and
`vault-health` commands. The Second Brain is not source-controlled and has no
background snapshot job. Run `sb-refresh` when you want to validate the vault,
regenerate the skills view, and update the read-only Google Drive mirror.
