---
name: design-uipath-workflows
description: Design, create, review, audit, refactor, or standardize custom UiPath Studio low-code XAML workflows using the global workflow naming, modularity, annotation, activity naming, PHI-safe action logging, variable and argument, error-handling, and UI Automation conventions. Use for production `.xaml` workflow style and static governance checks; do not use for coded workflows, generated artifacts, third-party packages, native REFramework restyling, or UiPath test-case design.
---

# Design UiPath Workflows

Apply a strict, readable house style without presenting house rules as UiPath product requirements. Keep every conclusion inside the validation layer actually proved.

## Choose the task

1. **Design** — propose workflow seams, names, contracts, annotations, and log placement before editing.
2. **Audit** — inspect requested files read-only and report `MUST`, `SHOULD`, and `WAIVER` findings.
3. **Implement** — edit only when the user explicitly authorizes implementation. Use `$uipath-rpa` for project-safe XAML changes and validation.
4. **Lint** — run `scripts/uipath_style_lint.py` for a repeatable read-only static check.

Do not infer edit permission from a request to explain, review, audit, diagnose, or design.

## Classify before applying rules

For every in-scope XAML, determine whether it is:

- a new or materially changed custom workflow — apply the full standard;
- untouched legacy custom code — report debt, but do not mass-remediate;
- a native REFramework workflow or contract — preserve its filename, path, public arguments, state-machine structure, and lifecycle behavior;
- a test workflow beginning with `TC_` — leave beside its target and exclude it from v1 governance;
- generated, third-party, or coded automation — exclude it.

Project-specific instructions override this global baseline when they are explicit. Never use an override to weaken a security requirement silently.

## Load only the needed references

- Read [references/style-guide.md](references/style-guide.md) for naming, annotations, modularity, activity names, variables, arguments, configuration, errors, and UI Automation.
- Read [references/logging-guide.md](references/logging-guide.md) whenever creating, reviewing, or changing logs.
- Read [references/linter.md](references/linter.md) before running or interpreting the bundled linter or authoring `.uipath-style.json`.
- Read [references/official-basis.md](references/official-basis.md) when attributing a rule, explaining why it exists, or resolving tension between UiPath guidance and house policy.

## Work in this order

1. Resolve the project root, requested scope, active XAML, invoke relationships, and any local instructions.
2. Protect native REFramework and excluded files before suggesting renames or edits.
3. Define one responsibility per custom workflow. Choose Sequence for linear work, Flowchart for decision-heavy work, and State Machine for lifecycle behavior.
4. Name the workflow, then set the custom root container `DisplayName` to the filename stem.
5. Write the required workflow annotation before composing the body.
6. Define a small, typed argument contract and narrowly scoped variables.
7. Lay out native UiPath activities, unique activity `DisplayName` values, action logs, branch logs, loop controls, and failure behavior.
8. Check selectors, postconditions, configuration boundaries, sensitive-data handling, and modularity.
9. If authorized to edit, preserve serialization, sidecars, dependencies, invoke contracts, line endings, and unrelated work with `$uipath-rpa`.
10. Run the linter on the narrowest useful scope, then perform the strongest available UiPath validation separately.

## Report findings honestly

Label each rule with both enforcement and origin:

- `MUST` — required by this house standard, a security boundary, or a documented support boundary.
- `SHOULD` — recommended; deviations need a concrete maintainability reason.
- `WAIVER` — an approved, scoped, time-bounded exception to a waivable rule.
- `UiPath` — official product behavior, support boundary, or configurable Analyzer guidance.
- `House` — organization-specific convention.
- `Security` — sensitive-data or credential boundary.

Do not call the bundled linter a compiler or Workflow Analyzer. Distinguish:

1. local XML/static heuristics;
2. supported Windows Studio validation and configured Workflow Analyzer;
3. Studio build;
4. Robot or test execution;
5. UAT or production-like acceptance.

## Completion criteria

A completed design or implementation has:

- a classified scope with protected files left intact;
- a name, root `DisplayName`, annotation, and single responsibility that meet the standard;
- unique contextual activity names and PHI-safe logs at every required action boundary;
- a deliberate, bounded argument contract and correctly prefixed variables;
- explicit synchronization, postconditions, error propagation, and configuration choices;
- linter results plus any documented waivers;
- a precise statement of which validation layers passed and which remain outstanding;
- no unrelated edits, commits, pushes, or claims of runtime proof.
