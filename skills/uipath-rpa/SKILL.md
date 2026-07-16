---
name: uipath-rpa
description: "Create, edit, debug, and validate UiPath RPA projects and workflows, including .xaml and .cs coded workflows, REFramework performers, UI automation, Object Repository selectors, test cases, integration-service connectors, and deployment. Use whenever a request concerns UiPath project.json, XAML, coded workflows, Studio validation/build errors, UI scraping/automation, Orchestrator packages, or UiPath tests."
---

# UiPath RPA

Use the project’s installed packages, Studio-generated XAML, and a working sibling workflow as the source of truth. Prefer the smallest Studio-readable change that meets the requested business behavior.

## 1. Establish the execution context

1. Resolve `PROJECT_DIR` from the named project or nearest `project.json`.
2. Read `project.json`: `targetFramework`, `expressionLanguage`, dependencies, entry points, and project type.
3. Inspect a nearby working workflow before serializing a new or edited XAML file. It is the style and serialization anchor.
4. Check whether `.claude/rules/project-context.md` exists. If its recorded file/dependency counts are materially stale, refresh project context before a broad change; do not create or overwrite user-owned context files for a narrow repair.

Never change `targetFramework` or `expressionLanguage` in an existing project. Do not add or remove a package before checking `project.json` and usages across the project.

## 2. Choose the correct path

| Work | Read before acting |
|---|---|
| Routine edit of a mature XAML workflow | [xaml/xaml-edit-fast-path.md](references/xaml/xaml-edit-fast-path.md) |
| New XAML, unknown activity, Flowchart, or StateMachine | [xaml/workflow-guide.md](references/xaml/workflow-guide.md) and [xaml/xaml-basics-and-rules.md](references/xaml/xaml-basics-and-rules.md) |
| XAML type, namespace, reference, or Designer error | [xaml/common-pitfalls.md](references/xaml/common-pitfalls.md) and the matching sibling workflow |
| Coded workflow or C# source | [coded/operations-guide.md](references/coded/operations-guide.md) and [coded/coding-guidelines.md](references/coded/coding-guidelines.md) |
| UI automation / scraping | [ui-automation-guide.md](references/ui-automation-guide.md) |
| XAML test case | [testing-guide.md](references/testing-guide.md) |
| DataTable, LINQ, Regex, collections, JSON, or conversion | [data-manipulation-guide.md](references/data-manipulation-guide.md) |
| Integration Service connector | [is-connector-xaml-guide.md](references/is-connector-xaml-guide.md) or [coded/integration-service-guide.md](references/coded/integration-service-guide.md) |
| Build, validation, run, or debugging | [validation-guide.md](references/validation-guide.md) and [debugging.md](references/debugging.md) |
| Package, project initialization, or Studio environment | [environment-setup.md](references/environment-setup.md) |
| Publish a process or library | [publishing-guide.md](references/publishing-guide.md) or [library-authoring-guide.md](references/library-authoring-guide.md) |

Read each selected reference in full. Do not apply the full greenfield activity-discovery flow to routine Sequence/Assign/If/LogMessage work; use the XAML fast path instead.

## 3. Host-aware validation

### Mac-hosted editing

Do not run `uip rpa analyzer-rules list`, `validate`, `build`, `run`, `debug start`, `studio start`, `activities get-default-xaml`, or UIA capture commands unless a signed-in Windows UiPath environment is explicitly available to this task. On this Mac they are commonly non-actionable (`Helm requires a signed-in user` or Windows-project-on-Linux failures).

Use the static gate from [xaml/xaml-edit-fast-path.md](references/xaml/xaml-edit-fast-path.md): XML parse, duplicate IdRef scan, sidecar and invoke-contract checks, reference/import checks, local-style checks, and CRLF-aware `git diff --check`. State that Windows Studio/Robot compile and run validation remains required before deployment.

### Signed-in Windows UiPath environment

For an authoring session, run enabled analyzer rules once before editing. After each touched workflow, run per-file validation. Before declaring compile verification, run a project build after all files validate. `validate` alone does not catch every member/property or JIT expression error. Treat the outer command result (or `HasErrors`), not a workflow-emitted log level, as the command success verdict.

## 4. XAML rules that prevent Studio repairs and compile errors

- Match the sibling anchor’s namespaces, assembly references, root `x:Class`, argument/variable syntax, Activity serialization, line endings, ViewState, and naming style.
- Keep mature workflows Assign-heavy: one expanded Assign per target, explicit typed `InArgument` / `OutArgument`, unique `WorkflowViewState.IdRef`, and `Sequence` wrappers for every container branch/body.
- Write PHI-minimized logs: workflow start and end, key counts/flags/reason codes, branch outcome, fallback, and mapped result. Never log patient identifiers, raw comments, credentials, tokens, prompts, or full model responses.
- For `scg:List(...)`, `List(Of T)`, or LINQ `.ToList()` in a Visual Basic expression, add `System.Collections.Generic` to `TextExpression.NamespacesForImplementation` and copy compatible `System.Collections`, `System.Core`, and `System.ObjectModel` assembly references from the anchor. `xmlns:scg` only supports the XAML type declaration; it does not make `List` visible to the VB compiler.
- Treat VB expression compilation as a separate gate from XML parsing. Run `scripts/check_vb_xaml_expressions.py` on touched VB XAML files. It catches unbalanced parentheses, Studio-unsafe fluent chains split after `.`, and `Regex` calls that lack a VB namespace import.
- Prefer `System.Text.RegularExpressions.Regex` in small or legacy expressions. An assembly reference alone does not declare the short `Regex` name; without the corresponding `TextExpression.NamespacesForImplementation` import, Studio reports `BC30451` and may misleadingly suggest creating a variable in Data Manager.
- Do not split a fluent VB chain at a trailing period. Studio can report `BC30198: ')' expected` even when the XML and a superficial parenthesis count are clean. Keep the chain on one physical line or split intermediate results into typed Assign activities.
- For a new activity outside the common built-ins, read the installed package docs under `.local/docs/packages/<PackageId>/` before generating its tag or properties. Do not infer an activity class name from its Studio display label.
- When editing `Main.xaml` or another active entry point’s arguments, update the XAML, matching `.xaml.json`, and `entry-points.json` together. Components normally need no sidecar unless published as entry points.
- Before changing an `InvokeWorkflowFile`, confirm target existence, argument direction/type compatibility, and intentional defaults.

## 5. Coded workflow rules

- Use `CodedWorkflow` plus `[Workflow]` or `[TestCase]` only for executable coded workflows and tests; keep reusable source files plain C#.
- Use one workflow/test class per file, an `Execute` entry method, and the sanitized project-name namespace.
- Add required packages to `project.json` before using their services. Register test cases in `designOptions.fileInfoCollection`; update process entry points only when the project type requires them.

## 6. UI automation boundary

Use UiPath UI Automation and Object Repository targets for visible desktop/browser interaction. Read [ui-automation-guide.md](references/ui-automation-guide.md) before any UIA work and capture selectors through the documented UiPath indication/configuration flow; never hand-write selectors or substitute Playwright, Selenium, raw DOM scripting, PowerShell, or HTTP form posts.

If live target capture is unavailable, use real UIA activities with explicit `TODO Indicate` markers—never log-only interaction stubs.

## 7. Delivery checklist

- Verify the requested business behavior and affected workflow contracts.
- Run the validation appropriate to the active host and report its actual scope.
- List touched workflow/project files and note any sidecar, dependency, or entry-point update.
- Do not call the automation verified or deployment-ready until Windows Studio/Robot compilation and the appropriate run/test have passed.
- When a plan governs the work, re-read it before reporting and identify any unchecked item and its concrete blocker.
