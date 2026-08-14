# UiPath Validation Guide

Use the collocated validator so every run applies the same checks and reports the same gate vocabulary.

## L1: static gate

Run after each coherent XAML slice:

```bash
python3 <skill-dir>/scripts/uipath_tool.py audit \
  --project <project> \
  --scope changed \
  --policy baseline
```

Use `--scope staged` for a pre-commit check and `--scope all` for a project audit. Pass explicit files with `--files`. Use `--format json` or `--json-out <path>` when another tool will consume the result.

An empty workflow scope fails with `SCP001`; use explicit `--files` after intermediate commits instead of accepting a vacuous pass. Before deleting superseded tests, add `--require-registered-tests` so each unregistered `TC_*.xaml` is an error rather than a legacy warning.

The static gate currently checks:

- XAML plus `project.json`, sidecar, and optional `entry-points.json` parsing;
- unique `WorkflowViewState.IdRef` values;
- selected Visual Basic expression hazards when `expressionLanguage` is Visual Basic;
- invoke targets and direct argument name/direction/type contracts;
- equivalent CLR/XAML type aliases;
- entry-point file existence, orphan sidecars, and test registration existence/IDs;
- line endings and CRLF-aware Git whitespace;
- selected policy rules;
- activity serialization that is new to the project.

L1 is XAML-focused heuristic evidence. It does not prove complete argument parity across every metadata representation, compile coded workflows, or execute a project.

## Policy selection

Use `baseline` for diagnosis, orchestration, contract repair, and mixed workflow scopes. Use `native-business-rules` only for leaf production rule workflows; it forbids Invoke Code, Invoke Method, and Invoke Workflow File, requires start/end logs, checks Studio-readable Assign serialization, and warns when log expressions contain configured sensitive-data tokens. Token scanning is a review prompt, not proof that logging is safe.

Apply the strict profile to the intended business-rule files, not an entire legacy project whose unrelated workflows follow different conventions.

## Line-ending repair

Check first:

```bash
python3 <skill-dir>/scripts/uipath_tool.py normalize-eol \
  --project <project> --scope changed --check
```

Use `--write` only when the identified files should be repaired. The tool infers the expected style from Git HEAD, then siblings, then CRLF; reparses XML after writing. It never normalizes an unselected workflow.

## L2 and L3: live capability matrix

Resolve proof by `targetFramework`, requested verb, installed `uip --version`/`--help`, Studio requirements, and runner architecture. Portable projects may support build/analyze on macOS or Linux; Windows projects need a supported Windows toolchain for Windows compile/runtime claims; `run-file` is Windows/Studio-dependent. Report the environment actually used.

When the local Parallels bridge is the selected supported runner, discover its VM name from `UIPATH_PARALLELS_VM` or pass it explicitly:

Run the preflight once per Windows environment or after a toolchain change:

```bash
python3 <skill-dir>/scripts/uipath_tool.py windows preflight --vm "Windows 11"
```

Build only:

```bash
python3 <skill-dir>/scripts/uipath_tool.py windows validate \
  --project <project> --vm "Windows 11" --mode build
```

Build and run changed registered tests:

```bash
python3 <skill-dir>/scripts/uipath_tool.py windows validate \
  --project <project> --vm "Windows 11" \
  --mode build-and-test --tests changed
```

Use `--tests all` for the full registered suite or `--tests paths --test-path <relative.xaml>` for explicit tests. The Windows runner restores dependencies, builds through `uip rpa build`, then uses `uip rpa run-file` for selected test workflows.

`build-and-test` requires at least one selected test to run and pass. An empty selection leaves L3 `not_run` and returns exit 1; it is not successful execution proof.

The bridge's `run-workflow` mode is a side-effecting escape hatch, not a validation default. Use it only after the user authorizes the exact entry point, input, target environment/folder, transaction scope, and replay boundary. The current bridge accepts only a coarse `--allow-side-effects` flag; if those details cannot be bounded outside the tool, leave L3 blocked and run a harmless registered test instead.

```bash
python3 <skill-dir>/scripts/uipath_tool.py windows validate \
  --project <project> --vm "Windows 11" \
  --mode run-workflow --allow-side-effects
```

Never add `--allow-side-effects` merely to overcome a blocked test. Confirm the intended systems and transaction scope first.

## Fix loop

1. Read the first failing gate and its findings.
2. Fix one evidenced root cause.
3. Re-run the cheapest gate that can disprove the fix.
4. Re-run the full required gate before delivery.
5. Stop retrying when the result is `blocked`; resolve the named capability or report it.

Keep unrelated cleanup outside the validation fix.

## Result interpretation

| Gate | Passed means |
|---|---|
| L1 static | The selected source and structural checks passed |
| L2 compile | Windows restore and UiPath build passed |
| L3 execution | The selected tests or workflow completed successfully |
| UAT | The representative business scenarios were accepted |

Use [validation-contract.md](validation-contract.md) for exit codes and the versioned JSON interface. Do not call a project deployment-ready until the required L2, L3, and UAT evidence exists.
