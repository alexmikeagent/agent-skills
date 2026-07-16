---
name: vault-health
description: Audit the Second Brain for required structure, invalid JSON Canvas files, missing or forbidden sensitivity metadata, likely secrets, oversized files, unsafe MDX, external HTML assets, and portability hazards. Use before Git snapshots, Drive mirroring, publishing, or when the vault appears inconsistent.
---

# Vault Health

Run the bundled standard-library Python validator:

```sh
python3 scripts/vault_health.py
```

Pass `--vault <path>` only for a different vault. Use `--json` for structured
output.

Treat any error as blocking for Git and Google Drive. Warnings require review
but do not block. Never weaken the secret, sensitivity, MDX, or file-size gates
to make a snapshot pass; repair or remove the offending content.

