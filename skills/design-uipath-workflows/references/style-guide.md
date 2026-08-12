# UiPath workflow design style guide

This document is the enforceable global baseline for custom UiPath Studio low-code XAML. Rule labels distinguish official UiPath guidance from stricter house policy. Test-case workflow design is outside v1.

## 1. Scope and enforcement

| Level | Meaning |
|---|---|
| `MUST` | Required unless the rule explicitly permits a recorded waiver. |
| `SHOULD` | Default choice; deviate only for a stated maintainability or product reason. |
| `WAIVER` | Approved exception naming the rule, workflow, rationale, approver, and expiration. |

Apply the full standard to new and materially modified custom workflows. For untouched legacy workflows, report debt and propose a bounded migration; do not restyle an entire project opportunistically.

Protect native REFramework filenames, locations, public arguments, state transitions, invoke paths, and lifecycle behavior. New custom components called by REFramework follow this guide. Do not reorganize or govern `TC_*.xaml` test workflows in v1.

## 2. Workflow names and folders

### 2.1 General rules

- **MUST · House:** Count the entire filename, including `.xaml`; it must be 40 characters or fewer.
- **MUST · House:** Use UpperCamelCase words. Do not add spaces or hyphens.
- **MUST · House:** Use a verb-led action so the name points to what the workflow does.
- **MUST · House:** Check names case-insensitively for collisions.
- **MUST · House:** Never append meaningless suffixes such as `1`, `2`, or `New` to resolve a collision.
- **MUST · House:** For a custom Sequence, Flowchart, or State Machine root, set `DisplayName` exactly to the filename stem.
- **MUST · House:** Preserve native REFramework names such as `Main.xaml`, `GetTransactionData.xaml`, and other template contracts.

### 2.2 Application workflows

Use `[Application]_[Verb][Object].xaml` with exactly one structural underscore.

Examples:

- `Invision_Login.xaml`
- `Invision_SearchPatient.xaml`
- `Invision_AddComment.xaml`

The application segment identifies the system. The action segment is a compact verb-object pointer.

### 2.3 Non-application workflows

Use one controlled lifecycle prefix followed immediately by an UpperCamelCase pointer. Do not use an underscore.

| Prefix | Use | Example |
|---|---|---|
| `Init` | Initialization-stage work | `InitPatientSearch.xaml` |
| `Pro` | Transaction or process-stage work | `ProPatientAcctVeri.xaml` |
| `End` | End, close, or cleanup-stage work | `EndCloseApplications.xaml` |
| `Util` | Reusable technical utility | `UtilMoveFile.xaml` |

Use `Util`, never `Shared`. A utility must be independent of a specific application and lifecycle stage and must perform one reusable technical responsibility.

### 2.4 Shortening strategy

When a proposed filename exceeds 40 characters, shorten it automatically rather than abandoning the grammar:

1. Preserve the application segment or lifecycle prefix.
2. Remove filler words such as `The`, `A`, `To`, `For`, `Of`, `And`, `With`, and `From`.
3. Prefer readable compact forms first: `Account` → `Acct`, `Verification` → `Veri`, `Configuration` → `Config`.
4. If still too long, use recognizable pointer abbreviations: `Patient` → `PAT`, `Terminal` → `TER`, `Transaction` → `TXN`, `Configuration` → `CFG`.
5. Stop as soon as the complete filename is 40 characters or fewer.
6. Recheck case-insensitive collisions and report every abbreviation with its expansion.

Grammar is less important than an unambiguous pointer after shortening. Do not blindly truncate a word or invoke target.

Recommended folders for new projects are:

```text
Framework/
Components/Invision/
Components/Initialization/
Components/Process/
Components/Utility/
```

Preserve an established project layout unless reorganization is explicitly in scope. Do not create a `Tests/` folder for existing `TC_` files.

## 3. Required workflow annotation

**MUST · House:** Every governed workflow root has one concise annotation with these headings in this order. Use `None` instead of leaving a section blank.

```text
Purpose:
Runs in:
Inputs:
Outputs:
Side effects:
Assumptions:
Expectations:
Static values:
Failure behavior:
Sensitive data:
```

Write short, operational statements:

- `Purpose` — one sentence describing the single responsibility.
- `Runs in` — application and lifecycle context.
- `Inputs` and `Outputs` — argument names and meanings, never real values.
- `Side effects` — UI, file, queue, database, email, or other external mutations.
- `Assumptions` — entry conditions the workflow relies on but does not establish.
- `Expectations` — observable successful post-state.
- `Static values` — behavior-affecting literals, commands, coordinates, timeouts, and defaults with their meanings. Exclude Studio layout metadata. For credentials, name only the secure source.
- `Failure behavior` — local recovery, translation, cleanup, and propagation owner.
- `Sensitive data` — categories and handling restrictions, never actual data.

## 4. Responsibility, size, and control flow

- **MUST · House:** A workflow performs one cohesive responsibility.
- **SHOULD · UiPath:** Prefer Sequence for linear work, Flowchart for decision-rich work, and State Machine for lifecycle behavior.
- **SHOULD · UiPath:** Extract repeated logic and separate UI interaction from process-dependent business logic.
- **SHOULD · House:** At 51–55 activities, stop for a modularity review. Above 55 activities requires a waiver and a documented reason extraction would make the design worse.
- **SHOULD · UiPath:** Review at seven nested activities and avoid more than three nested `If` activities.
- **MUST · UiPath support boundary:** Keep a workflow below 10 MB. **SHOULD · UiPath:** keep it below 5 MB.
- **MUST · House:** Prefer native, visually inspectable activities. `Invoke Code` and `Invoke Method` require a waiver proving no reasonable native activity or readable expression solution exists; isolate, annotate, and test the exception.
- **SHOULD · House:** Group 2–10 closely related assignments in `Multiple Assign`. Split larger or semantically mixed groups.
- **MUST · House:** `Invoke Workflow File` is allowed for modularity. Do not add a caller-side completion log immediately after it; the child owns its Start and End logs. A parent End boundary is still required when the invoke is the parent's final action. The layer that catches, retries, or translates a failure owns the failure log.

Activity counts are a house design heuristic, not a UiPath runtime limit. Count visible activity elements consistently and review responsibility and nesting, not the number alone.

## 5. Activity display names

**MUST · House:** Give every user-authored visible activity and active container a unique `DisplayName`:

```text
[Canonical activity name] - [specific action]
```

Retain the activity name and describe the concrete action. Keep the description short and specific. Do not number generic duplicates.

Examples:

- `Log Message - Assigned value to strSampleVariable`
- `Send Control Key - Submit patient search`
- `If - Patient information screen loaded`
- `Multiple Assign - Initialize terminal settings`
- `Use Application Browser - Open Invision patient search`

The custom root is the exception: its `DisplayName` equals the workflow stem. Studio-generated structural labels and protected native REFramework content are exempt.

## 6. Variables and arguments

### 6.1 Prefixes

| Type | Prefix | Example |
|---|---|---|
| String | `str` | `strPatientStatus` |
| Integer | `int` | `intRetryCount` |
| Boolean | `bn` | `bnIsSimulation` |
| DataTable | `dt_` | `dt_Transactions` |
| DataRow | `dr` | `drCurrentTransaction` |
| Dictionary | `dict` | `dictConfig` |
| List | `lst` | `lstResults` |
| Decimal | `dec` | `decBalance` |
| Exception | `ex` | `exCaughtException` |
| Terminal connection | `tc` | `tcInvision` |

Arguments add the direction before the type prefix:

- `in_strPatientAccountNumber`
- `out_bnPatientFound`
- `io_dt_TransactionData`
- `io_tcInvision`

### 6.2 Contract rules

- **MUST · House:** Use strongly typed values; do not use `GenericValue` for governed contracts.
- **MUST · UiPath/House:** Declare and map every runtime dependency an invoked workflow uses. A child cannot rely on a caller variable merely being in scope; pass an active terminal connection as a typed `io_tc...` argument when the child interacts with that session.
- **MUST · House:** Use positive Boolean names and avoid generic names such as `value`, `data`, `item`, and `result`.
- **MUST · House:** Keep variables in the narrowest practical scope; do not shadow or duplicate names.
- **SHOULD · UiPath Analyzer default:** Keep variable and argument names to 30 characters or fewer.
- **SHOULD · House:** Use `InOut` only for genuine shared state.
- **SHOULD · UiPath:** Give input arguments safe defaults only when that improves isolated execution without embedding environment or sensitive data.

Count all argument directions together:

- 0–10: acceptable;
- 11–20: interface review warning;
- above 20: error unless waived.

Do not hide an oversized contract inside the entire Config dictionary, an unrelated DataTable or Dictionary, `Object`, or `GenericValue`. A cohesive typed object is appropriate only when it represents a genuine domain contract.

## 7. Configuration and static values

- Put environment-sensitive or operator-tunable values in Config or Orchestrator Assets.
- Put credentials and secrets only in approved secure stores.
- Stable application commands such as `"01"`, terminal transaction codes, and screen coordinates may remain static when the annotation states their meaning.
- Extract repeated literals into one named value.
- Never embed patient data, credentials, environment paths, or production endpoints as static values.

## 8. Error handling

- **MUST:** Leave `ContinueOnError` false unless the behavior is explicitly justified and verified.
- **MUST:** Do not leave Catch blocks empty or swallow exceptions.
- Catch locally only to recover, translate, clean up, or add safe context. Otherwise propagate to the owning REFramework or process handler.
- Use a Business Rule Exception only for a non-retryable business condition, not a technical failure.
- Make retries bounded and configuration-driven.
- Log immediately before `Throw`, `Rethrow`, `Break`, `Continue`, or termination because a following activity is unreachable.
- Do not interpolate raw exception messages or objects into custom logs when they may contain sensitive data.
- The layer that handles, translates, or retries logs once. Do not duplicate the same failure at every propagation layer.

## 9. UI Automation

- Prefer stable selectors and Object Repository descriptors. Remove volatile attributes and avoid `idx` except when demonstrably stable.
- Use application/browser containers and reusable UI components to centralize selectors.
- Check the expected application state before interaction and verify the postcondition after a consequential action.
- Do not use `Delay` as the primary synchronization mechanism; use state checks and bounded timeouts.
- Do not place UI Automation inside `Parallel`; UiPath documents that combination as unsupported.
- Use image automation only when stronger element identification is unavailable and false-positive risk is tested.

## 10. Review checklist

Before handoff, confirm:

- filename, folder, root `DisplayName`, and annotation;
- one responsibility, activity count, nesting, and workflow size;
- unique activity names and native-first design;
- one contextual log at every required action boundary using the logging guide;
- small typed interface, prefixes, scope, and safe defaults;
- configuration, static-value, credential, and PHI boundaries;
- selectors, synchronization, postconditions, retries, and exception ownership;
- read-only linter results, recorded waivers, and validation-layer limits.
