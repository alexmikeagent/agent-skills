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

The Mac adapter creates a snapshot from tracked and nonignored project files, excludes `.git`, caches, packages, and logs, and writes a SHA-256 manifest. The Windows runner copies the snapshot from `\\Mac\Home` into `%LOCALAPPDATA%\CodexUiPathBridge\jobs\<job-id>`, restores dependencies, builds, optionally runs selected tests, and copies the result bundle back to `~/.codex/uipath-rpa/jobs/<job-id>/results`.

Successful jobs remove the project snapshot. Windows job folders are removed unless `--keep-job` is explicit. No password is passed to `prlctl`; the adapter uses the current guest user.

## Execution safety

`build` and `build-and-test` are the normal modes. `run-workflow` requires `--allow-side-effects`; without it the adapter refuses execution with exit code 4. The bridge never publishes a package or starts an Orchestrator job.

## Troubleshooting order

1. Read the preflight checks.
2. Confirm the VM is running and the current Windows desktop session is signed in.
3. Confirm `uip --version` and Studio discovery in the guest.
4. Read restore, build, and test logs from the result bundle.
5. Use `--keep-job` only when local Windows inspection is required.
