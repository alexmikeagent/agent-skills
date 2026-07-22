---
name: uipath-rpa
description: "Create, edit, debug, and validate UiPath RPA projects and workflows. Use for XAML or coded workflows, REFramework performers, behavior-preserving workflow refactors, UiPath tests, project.json and sidecars, Studio build errors, UI automation, Integration Service, and deployment."
---

# UiPath RPA

Use the installed packages, Studio-generated XAML, and a working sibling workflow as the serialization truth. Make the smallest coherent change that preserves the requested business behavior.

## 1. Establish the project contract

1. Resolve the project from the nearest `project.json`; read its framework, expression language, dependencies, entry points, and test registrations.
2. Run `python3 <skill-dir>/scripts/uipath_tool.py inspect --project <project> --format text`.
3. Open a nearby working workflow as the style anchor for namespaces, Assign shape, arguments, ViewState, logs, and line endings.
4. For a behavior-sensitive refactor, read [behavior-preserving-refactors.md](references/xaml/behavior-preserving-refactors.md) and record the boundary before editing.

Completion criterion: the affected call graph, public arguments, expected outcomes, style anchor, and required validation gates are known.

Never change `targetFramework` or `expressionLanguage` in an existing project. Check package usages before changing dependencies.

## 2. Read only the active branch

| Work | Required reference |
|---|---|
| Routine mature-XAML edit | [xaml-edit-fast-path.md](references/xaml/xaml-edit-fast-path.md) |
| Behavior-preserving split or test replacement | [behavior-preserving-refactors.md](references/xaml/behavior-preserving-refactors.md) |
| Build, run, or gate interpretation | [validation-guide.md](references/validation-guide.md) |
| Local Parallels Windows validation | [parallels-windows-bridge.md](references/parallels-windows-bridge.md) |
| XAML test case | [testing-guide.md](references/testing-guide.md) |
| New XAML, Flowchart, or StateMachine | [workflow-guide.md](references/xaml/workflow-guide.md) |
| Coded workflow | [operations-guide.md](references/coded/operations-guide.md) and [coding-guidelines.md](references/coded/coding-guidelines.md) |
| UI automation | [ui-automation-guide.md](references/ui-automation-guide.md) and installed package docs |
| DataTable, LINQ, Regex, collections, or JSON | [data-manipulation-guide.md](references/data-manipulation-guide.md) |
| Integration Service | [is-connector-xaml-guide.md](references/is-connector-xaml-guide.md) |

Read the selected reference in full. Use [reference-map.md](references/reference-map.md) only when the correct branch is unclear.

## 3. Implement a coherent slice

- Preserve the sibling anchor's XAML form; do not regenerate an unaffected workflow.
- Prefer native UiPath activities and explicit typed Assigns for business logic.
- Give containers and actions business-readable `DisplayName` values.
- Add PHI-safe start/end and narrative decision logs; use counts, flags, and reason codes rather than raw transaction data.
- Keep every `WorkflowViewState.IdRef` unique.
- Keep entry-point XAML, sidecars, and `entry-points.json` synchronized.
- Verify every invoke target and direct argument binding.
- Confirm unfamiliar activity tags against installed package documentation or a sibling usage.

For test replacement, add and register the replacement before deleting the superseded test. Preserve old tests until the replacement passes the gates required by the change.

Before any test deletion, run the affected L1 scope with `--require-registered-tests`. `META003` is otherwise a warning for legacy compatibility; this flag makes an unregistered `TC_*.xaml` an error.

Completion criterion: one reviewable slice is implemented, all affected contracts remain intentional, and replacement coverage exists before removals.

## 4. Run explicit validation gates

Run the static gate on the touched scope:

```bash
python3 <skill-dir>/scripts/uipath_tool.py audit \
  --project <project> --scope changed --policy baseline
```

Choose the policy deliberately:

- Use `baseline` for diagnosis, contract repair, routine orchestration changes, and mixed workflow scopes.
- Use `native-business-rules` for production rule workflows that must prohibit Invoke Code and Invoke Method, require boundary/storytelling logs, and use Studio-readable Assign serialization. Scope it to rule workflows; its leaf rule intentionally rejects Invoke Workflow File.

Use `normalize-eol --check` before any explicit `--write` repair. If `inspect` reports a parse finding, stop at L1 diagnosis; do not proceed to Windows validation until the XAML parses.

On this Mac, L1 proves structure and contracts only. When Windows proof is required, run:

```bash
python3 <skill-dir>/scripts/uipath_tool.py windows preflight --vm "Windows 11"
python3 <skill-dir>/scripts/uipath_tool.py windows validate \
  --project <project> --vm "Windows 11" --mode build-and-test --tests changed
```

Treat the gates separately:

- **L1 static:** XML, expressions, metadata, invoke contracts, style policy, and line endings.
- **L2 compile:** Windows dependency restore and UiPath build.
- **L3 execution:** selected Windows test or workflow execution.
- **UAT:** representative business validation outside the technical gates.

Completion criterion: every required gate passed, or its exact blocked state and evidence are recorded. Never promote L1 into a compile or runtime claim.

## 5. Deliver evidence

- State the L1, L2, L3, and UAT status independently.
- List changed workflows, project metadata, tests, and sidecars.
- Report remaining warnings and concrete blockers.
- For behavior-sensitive work, name the parity cases and unchanged output/status/exception boundaries.
- Do not call the automation deployment-ready until Windows compilation, appropriate execution, and required UAT pass.
