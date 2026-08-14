---
name: uipath-rpa
description: "Inspect, change, debug, and validate UiPath project artifacts: XAML or coded workflows, project.json and entry-point metadata, REFramework contracts, UI Automation serialization, and UiPath-specific build or test failures. Use when work must preserve UiPath project contracts or report L1/L2/L3/UAT evidence; compose with specialist UiPath skills for GenAI, Integration Service, and PDD work."
---

# UiPath RPA

Follow one spine: **authority -> contract -> branch -> slice -> gates -> evidence**. Installed packages, live project metadata, Studio-generated artifacts, and a loading sibling workflow outrank remembered syntax.

## 1. Fix the authority and contract

1. Record the authorized mode: diagnosis/review, plan-only, implementation, or delivery. Diagnosis/review and plan-only do not authorize implementation. Side-effecting execution, publish, and deploy require explicit approval.
2. Resolve the exact nested repository and nearest `project.json`. Record the requested process, project root, entry point, branch/commit when Git-backed, destination, and source evidence. Abort on a Dispatcher/Performer, current/archive, or project/output identity mismatch.
3. Run:

   ```bash
   python3 <skill-dir>/scripts/uipath_tool.py inspect --project <project> --format text
   ```

4. Read `targetFramework`, `expressionLanguage`, installed dependencies, active entry points, test registrations, and the affected reachable call graph. Open a loading sibling workflow as the serialization anchor.
5. Separate facts from decisions. Discover project/tool/host facts; ask before changing behavior, framework/language, public contracts, dependencies, side effects, acceptance gates, or test coverage.
6. For a runtime failure, invoke `$diagnosing-bugs`. Correlate same-run logs, report/output rows, screenshots or video, transaction identity, timestamps, and the active XAML. Mark later screenshots as later-state evidence, not decision-time proof.

Completion criterion: the mode, identities, authority sources, affected call graph, public arguments, behavior boundary, serialization anchor, and required gates are recorded with no conflict.

## 2. Select only the branches the task needs

| Condition | Owner / reference |
|---|---|
| Routine edit to mature XAML | [XAML edit fast path](references/xaml/xaml-edit-fast-path.md) |
| Behavior-preserving refactor or test replacement | [Behavior-preserving refactors](references/xaml/behavior-preserving-refactors.md) |
| New XAML, Flowchart, or StateMachine | [Workflow guide](references/xaml/workflow-guide.md) |
| REFramework lifecycle, retry, queue, or `Config.xlsx` contract | [REFramework guide](references/reframework-guide.md) |
| XAML test case or variations | [Testing guide](references/testing-guide.md); add `$tdd` when red/green sequencing is requested |
| Coded workflow | [Operations guide](references/coded/operations-guide.md) and [coding guidelines](references/coded/coding-guidelines.md); add `$tasteful-code` for a substantial implementation |
| UI Automation | [UI Automation guide](references/ui-automation-guide.md) plus the installed package's co-versioned docs |
| Build, run, or validation claim | [Validation guide](references/validation-guide.md); use the [Parallels bridge](references/parallels-windows-bridge.md) only when its preconditions hold |
| GenAI, ScreenPlay, AI Trust Layer, connector selection, connection governance, or consumption | Invoke `$uipath-genai-integration-service`; use [connector XAML serialization](references/is-connector-xaml-guide.md) only for the project-side artifact, then return here for gates |
| PDD or support documentation | Invoke `$uipath-pdd-docx` |
| Fixed-point implementation review | Invoke `$code-review`, then use the [UiPath review ledger](references/review-guide.md) |

Read each selected reference in full. Compound tasks may select multiple rows; every task dimension must have one owner. Exact activity members, flags, commands, and generated filenames come from the installed package docs or live `--help`, never the closest cached version.

Completion criterion: every task dimension maps to one owner and direct reference; no branch is loaded merely because it is adjacent.

## 3. Implement one coherent slice

- Preserve unrelated files, existing public arguments, resolver precedence, outputs, exceptions, REFramework lifecycle placement, and the sibling anchor's XAML form.
- Prefer native activities for business rules; keep decisions, external actions, retries, and postconditions visibly separate.
- Give containers and actions business-readable `DisplayName` values. Log boundaries plus consequential decisions, external actions, retries, and outcomes; omit routine chatter and sensitive values such as PHI, PII, secrets, raw prompts, or full transaction content.
- Keep each `WorkflowViewState.IdRef` unique. Validate unfamiliar activity types, members, attached properties, and attributes against the installed package and a loading sibling; scan the complete touched cohort for the same defect class.
- Treat entry-point metadata as a discovered project contract. Update XAML, `project.json`, sidecars, and `entry-points.json` only where those surfaces are active; do not create or restore an optional metadata file solely by convention.
- Verify every invoke target and direct binding. Preserve replacement coverage until the replacement is registered and passes the gates required by the change.

Completion criterion: the diff contains only the intended slice; every contract delta is explicit and authorized; replacements exist before removals; no sibling path retains the same discovered defect.

## 4. Close the tight gate loop

Run the cheapest gate that can disprove the slice, fix one evidenced cause, then rerun the full required gate:

```bash
python3 <skill-dir>/scripts/uipath_tool.py audit \
  --project <project> --scope changed --policy baseline
```

Use `native-business-rules` only for selected leaf rule workflows whose stated policy matches the project. Run `normalize-eol --check` before an explicit `--write` repair. The local audit is XAML-focused heuristic evidence; read [validation-guide.md](references/validation-guide.md) for its exact implemented boundary and for the live target/host capability matrix.

Report gates independently:

- **L1 static:** selected source and heuristic contract checks.
- **L2 compile:** supported-host dependency restore and UiPath build.
- **L3 execution:** selected harmless test or explicitly authorized workflow execution.
- **UAT:** representative business acceptance.

Completion criterion: every required layer is `passed`, `failed`, `blocked`, or `not_run` with evidence. A lower layer never proves a higher one.

## 5. Deliver the evidence ledger

List changed workflows, metadata, tests, configuration/data contracts, and sidecars; give the four gate states; name parity cases, unresolved warnings, and residual risks. Deployment-ready requires the agreed L2, L3, and UAT evidence, not a clean L1 report.
