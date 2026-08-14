# Parallels Windows Validation Bridge

## Preconditions

- Parallels Desktop and `prlctl` are installed.
- The named Windows VM is running.
- The Windows guest is x64. UiPath Studio does not support Windows ARM.
- Parallels Tools and `\\Mac\Home` sharing work.
- The current Windows user can run guest commands.
- UiPath CLI, Studio, required runtime, packages, and licensing are available to that user.

Run `scripts/uipath_tool.py windows preflight --vm <name>` before the first validation session. A missing capability returns gate state `blocked` and exit code 3.

The standalone UiPath CLI supports ARM64, but Studio-backed build and `run-file` proof still require a supported x64 Windows Studio environment. An Apple Silicon Parallels ARM guest can validate transport only; it cannot supply L2 or L3. Confirm the current boundary in the official [UiPath Studio hardware and software requirements](https://docs.uipath.com/studio/standalone/latest/user-guide/hardware-and-software-requirements).

## Job flow

The Mac adapter transports tracked files plus nonignored untracked project-source files through `\\Mac\Home`. It fails closed on tracked files in excluded cache/output paths, credential-like filenames, symlinks, oversized files, and untracked non-source files. The Windows runner verifies the SHA-256 manifest after copying. Treat the share as transport, not isolation. Do not use it for a project whose tracked files contain secrets, PHI/PII-bearing inputs, or other data that the Windows guest is not authorized to receive.

The Windows runner copies that snapshot into `%LOCALAPPDATA%\CodexUiPathBridge\jobs\<job-id>`, restores dependencies, builds, optionally runs selected tests, and copies the result bundle back to `~/.codex/uipath-rpa/jobs/<job-id>/results`.

Host and Windows project snapshots are removed after passed, failed, or blocked runs unless `--keep-job` is explicit. Result evidence remains on the host. No password is passed to `prlctl`; the adapter uses the current guest user.

## Execution safety

`build` and `build-and-test` are the normal modes. Prefer a harmless registered test for L3. `run-workflow` requires `--allow-side-effects`, but that flag is only a coarse technical gate: obtain authorization for the exact entry point, input, target environment/folder, transaction scope, and replay boundary first. The bridge never publishes a package or starts an Orchestrator job.

## Troubleshooting order

1. Read the preflight checks.
2. Confirm the VM is running and the current Windows desktop session is signed in.
3. Confirm `uip --version` and Studio discovery in the guest.
4. Read restore, build, and test logs from the result bundle.
5. Use `--keep-job` only when local Windows inspection is required.
