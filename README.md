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

`ops/second_brain.py` backs the local `sb-*`, `skills-*`, and `vault-health`
commands. The checked-in LaunchAgent runs a validated snapshot every 30 minutes
from an installed app under `~/Library/Application Support/Second Brain`, which
avoids macOS blocking an interpreter while it opens a script through a
`Documents` symlink. The Python entrypoints are sealed inside the signed app
bundle instead of being left as loose executable files; all data and canonical
source remain in the locations above.

The LaunchAgent starts the dedicated, ad-hoc-signed `Second Brain Snapshot.app`
wrapper built from `launchd/SecondBrainSnapshot.swift`. Only that wrapper needs
macOS Full Disk Access for unattended reads of the iCloud vault and the
`Documents` repositories; Python and the user's other apps do not.

Rebuild and stage the runtime with:

```sh
python3 ops/install_snapshot_runtime.py
```

After `Second Brain Snapshot.app` has Full Disk Access, load it with:

```sh
python3 ops/install_snapshot_runtime.py --load
```

The foreground `sb-snapshot` command does not need this background permission.
