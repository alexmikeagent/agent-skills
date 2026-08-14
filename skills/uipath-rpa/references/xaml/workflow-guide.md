# XAML Workflow Guide

Discovery-first approach with iterative error-driven refinement for generating and editing XAML workflows. Always understand before acting, start simple, and validate continuously.

## Prefer the XAML Edit Fast Path first

For **routine edits on mature multi-workflow projects** (REFramework, COE performers, Assign/If/Log/invoke/Main-arg work), **stop here and use** [xaml-edit-fast-path.md](xaml-edit-fast-path.md) instead of the full discovery → CLI validate loop below. That guide encodes Studio-readable style, naming, logging, sidecar metadata, and the Mac static verification gate.

Continue with this document only for **greenfield** workflows, **unknown activities**, package discovery, Flowchart/StateMachine canvas work, or when the fast path explicitly defers.

## Core Principles

1. **Activity Docs Are the Source of Truth** — Installed packages may ship structured documentation at `{projectRoot}/.local/docs/packages/{PackageId}/`. When present, these docs contain source-accurate properties, types, defaults, enum values, conditional property groups, and working XAML examples. Always check for them first.
2. **Know Before You Write** — **NEVER** generate XAML blind. Understand the project structure, packages, expression language, and existing patterns. On mature projects, a sibling workflow is the style/serialization anchor.
3. **Use What You Know, Skip What You Don't Need** — If you already know the package ID and activity class name, go directly to its doc file. Be efficient: the discovery steps are a priority ladder, not a mandatory checklist. Card activities (`Assign`, `If`, `LogMessage`, …) do not need `activities find`.
4. **Start Minimal, Iterate to Correct** — Start one workflow at a time and break out logic into multiple files if needed. Build one activity at a time within each workflow. Write the smallest working XAML, then verify (see principle 5).
5. **Verify After Every Change (host-aware)** — On a **signed-in Windows UiPath host**: **MUST** validate with **both** `uip rpa validate` and `uip rpa build`. `validate` clean alone is not validated — it does not catch unknown member names or invalid enum values; `build` does. On the **user's Mac** (default for this skill install): **do not** run those CLI commands; use the static gate in [xaml-edit-fast-path.md §7](xaml-edit-fast-path.md) and state that Windows compile validation remains outstanding.
6. **Fix Errors by Category** — Triage in order: Package → Structure → Type → Activity Properties → Logic → Style/sidecar.
7. **Studio-readable style is part of correctness** — Expanded Assigns, sensitive-data-safe narrative logs, unique `WorkflowViewState.IdRef`, active entry-point metadata, and matching line endings.

---

## Core Workflow: Classify Request

| Request Type | Trigger Words | Action |
|--------------|---------------|--------|
| **FAST EDIT** | "fix", "add log", "rename", "wire invoke", "Main argument", "style", mature project polish | [xaml-edit-fast-path.md](xaml-edit-fast-path.md) |
| **CREATE** | "generate", "create", "make", "build", "new" (unknown activities) | Discovery → Generate |
| **EDIT** | "update", "change", "modify" with new activity types | Discovery → Edit |

If unclear which file to edit, **ask the user** rather than guessing.

---

## Phase 1: Discovery

**Goal:** Understand project context, leverage installed activity documentation, study existing patterns, identify reusable components, and discover activities before writing any XAML.

> **Batch discovery across activities.** When the workflow needs several activities, do NOT run the find → read-doc → `get-default-xaml` triple one activity at a time. Emit all `activities find` calls in parallel, then all `<Activity>.md` `Read`s in parallel, then all `get-default-xaml` calls in parallel (SKILL.md § Call Batching). Only the per-activity *authoring + validate* loop (Phase 2 / Phase 3) stays sequential — discovery fans out.

### Step 1.1: Project Structure

```
Glob: pattern="**/*.xaml" path="{projectRoot}"       → list all XAML workflow files
Read: file_path="{projectRoot}/project.json"          → read the project definition
```

Analyze:
- Where should new workflows be placed? (folder conventions)
- What naming pattern is used?
- What similar workflows already exist?
- VB or C# syntax? (check `expressionLanguage` in `project.json`)
- What packages are already installed?
- Are there existing connections, credentials, or objects to reuse?

### Step 1.2: Discover Activity Documentation (Primary Source)

**This is the most important discovery step. Read `<Activity>.md` BEFORE `activities get-default-xaml`, every time, even for activities that look simple.** Installed activity packages ship structured markdown at `{projectRoot}/.local/docs/packages/{PackageId}/activities/<Activity>.md`. The doc is the property surface; the CLI starter is not. `activities get-default-xaml` strips every property at its type default — for `NGetText` that means **all** output properties are absent from the starter, and authoring from the starter produces `NGetText.Value="..."` instead of `NGetText.Text="..."`. `validate` does not catch the wrong member name; only `build` does, after a wasted round-trip.

**Availability:** Docs exist only for **installed packages** and typically only for **newer package versions**. When the package is not installed, install it first. When docs are missing, update to the latest version, or fall back to `skills/uipath-rpa/references/activity-docs/<PackageId>/<closest-version>/`.

#### Filesystem Structure

```
{projectRoot}/.local/docs/packages/
+-- {PackageId}/
    +-- overview.md
    +-- activities/
    |   +-- {ActivitySimpleClassName}.md
    +-- coded/                             # Ignore for XAML workflows
```

#### Activity Doc Template

Every `activities/{ActivityName}.md` follows: Header → Metadata → Properties (Input, Output, Conditional groups, Common) → Valid Configurations → Enum Reference → XAML Examples → Notes.

#### Decision Table

| Situation | Action |
|-----------|--------|
| **Know package + activity name** | `Read: file_path="{projectRoot}/.local/docs/packages/{PackageId}/activities/{ActivityName}.md"` |
| **Know package, not activity** | `Read` the `overview.md`, then read the identified activity doc |
| **Don't know package** | `Glob` with `**/*.md` in `{projectRoot}/.local/docs/packages/`. `.local/` is gitignored — use `Glob` + `Read`, not `Grep` |
| **Docs exist but activity undocumented** | Use other docs as structural reference, fall back to `activities get-default-xaml` |
| **No docs for package** | Update the package first — this often adds docs. **Caution:** major version jumps (e.g., 23.x → 26.x) may deprecate activities — prefer minor/patch updates. If still no docs, fall back to Steps 1.4-1.7 |
| **Package not installed** | Install it first — both docs and `activities get-default-xaml` require it |
| **No `.local/docs/` at all** | Use fallback flow starting at Step 1.3 |

### Step 1.3: Search Current Project

Search existing workflows for reusable patterns and conventions.

```
Glob: pattern="**/*pattern*.xaml" path="{projectRoot}"
Grep: pattern="ActivityName|pattern" path="{projectRoot}"
Read: file_path="{projectRoot}/ExistingWorkflow.xaml"
```

- **Mature project**: Prioritize local patterns.
- **Greenfield project**: Skip this step.

### Step 1.4: Discover Activities (When Needed)

Use when you need to find which activity implements a user-described action:

```bash
uip rpa activities find --query "send mail" --limit 10 --output json```
```

- Results are **global** — not limited to installed packages
- If a useful activity is in an uninstalled package, install it immediately
- Tags can narrow results further

### Step 1.5: Disambiguate Approach and Provider

#### Approach-level (API vs UI Automation vs Connector)

- **Auto-select** when the user stated the approach or only one is viable
- **Prompt** when multiple approaches are viable and user hasn't indicated preference
- **Do NOT install packages until approach is confirmed**

#### Provider-level (within an approach)

**Auto-select** when: user specified provider, only one package matches, project already has the package installed, project defines a matching connection, or workflow already uses activities from one package.

**Prompt only as last resort** — present top 2-4 choices with recommendations.

### Step 1.6: Resolve Activity Properties (Fallback)

Use `uip rpa activities get-default-xaml` when activity docs are insufficient:

```bash
# Non-dynamic activity:
uip rpa activities get-default-xaml --activity-class-name "<FULLY_QUALIFIED_CLASS>" --output json
# Dynamic activity (connector-backed):
uip rpa activities get-default-xaml --activity-type-id "<TYPE_ID>" --connection-id "<CONN_ID>" --output json```

For JIT custom types: `Read: file_path="{projectRoot}/.project/JitCustomTypesSchema.json"`. See [jit-custom-types-schema.md](jit-custom-types-schema.md).

### Step 1.7: Search Examples Repository

Use when activity docs, `activities find`, and `activities get-default-xaml` don't provide enough context:

```bash
uip rpa workflow-examples list --tags web --limit 10 --output json
uip rpa workflow-examples get --key "<BLOB_PATH>"
```

**Complete tag list:** `adobe-sign`, `asana`, `box`, `concur`, `confluence`, `database`, `document-understanding`, `docusign`, `dropbox`, `email-generic`, `excel`, `excel-online`, `freshbooks`, `freshdesk`, `github`, `gmail`, `google-calendar`, `google-docs`, `google-drive`, `google-sheets`, `gsuite`, `hubspot`, `intacct`, `jira`, `mailchimp`, `marketo`, `microsoft-365`, `onedrive`, `outlook`, `outlook-calendar`, `pdf`, `powerpoint`, `productivity`, `quickbooks`, `salesforce`, `servicenow`, `sharepoint`, `shopify`, `slack`, `smartsheet`, `stripe`, `teams`, `testing`, `trello`, `web`, `webex`, `word`, `workday`, `zendesk`, `zoom`
```

### Step 1.8: Get Current Context (As Needed)

```
Read: file_path="{projectRoot}/project.json"
Glob: pattern="**/*" path="{projectRoot}/.objects/"
Bash: uip is connections list --output json
```

### Step 1.9: Discover Connector Capabilities (For IS/Connector Workflows)

For end-to-end authoring of `ConnectorActivity` XAML (connection + type ID + Configuration blob + FieldObjects), see **[../is-connector-xaml-guide.md](../is-connector-xaml-guide.md)** — worked example included. For the discovery commands only (list connectors, describe operation, manage connections), see [../connector-capabilities.md](../connector-capabilities.md).

**Path selection for calling connectors from XAML:**

| Option | When to use |
|--------|-------------|
| **IS generic `ConnectorActivity`** with a typed operation typeId (e.g. `37a305b2-...` for Slack "Send Message to Channel") | **Default choice** — schema-driven, hand-authorable with the CLI flow below. Works via `UiPath.IntegrationService.Activities`. |
| **IS generic `ConnectorActivity`** with `ConnectorHttpActivity` typeId (e.g. `...httpRequest...`) | Fallback for endpoints the connector hasn't modeled as a first-class operation. Field names are still connector-defined — not `method`/`path`/`body`. Read the schema. |
| **Per-product BAF activity package** (`UiPath.Slack.Activities`, `UiPath.Salesforce.Activities`, etc.) | Avoid for headless authoring. These wrap IS internally but use a more complex BAF XAML shape (`ScopeActivity` + dynamic child activity with `BusinessEntity`, `SelectedFields`, `PopulatedAPIParameters`). Same complexity, less mechanical. Skill users should default to the generic `ConnectorActivity` path unless the project already uses the BAF package. |

---

## Phase 2: Generate or Edit

### UI Automation — Target Configuration Gate (MANDATORY)

Before writing any XAML with UI activities: [ui-automation-guide.md](../ui-automation-guide.md) MUST be read IN FULL first. Every UI element target MUST be configured through the `uia-configure-target` skill flow — [uia-configure-target-workflows.md](../uia-configure-target-workflows.md) MUST be read IN FULL first.

**NEVER** manually call low-level `uip rpa uia` CLI commands outside of the skill flow.

### For CREATE Requests

**Strategy:** Generate minimal working version, one activity at a time, validate frequently.

Use the `Write` tool to create a new `.xaml` file. Refer to [xaml-basics-and-rules.md](xaml-basics-and-rules.md) for the complete XAML file anatomy template.

```
Write: file_path="{projectRoot}/Workflows/DescriptiveName.xaml"
       content=<valid XAML content>
```

**File path inference:** Use folder conventions from project structure, create descriptive filenames, ensure `.xaml` extension.

### For EDIT Requests

**Strategy:** Always read current content before editing.

```
Read: file_path="{projectRoot}/WorkflowToEdit.xaml"
Edit: file_path=... old_string=<exact text> new_string=<modified text>
```

**Critical:** `old_string` must match exactly and be unique. Include surrounding context if needed.

---

## Phase 3: Validate & Fix Loop

### Mac host (default for this skill)

Do **not** run `uip rpa validate` / `build` / analyzer. Use [xaml-edit-fast-path.md §7](xaml-edit-fast-path.md): `xmllint`, duplicate IdRef scan, collapsed-Assign grep, invoke-contract scan (normalize `/` and `\\`), `jq empty` on sidecars when Main args changed, CRLF-aware `git diff --check`. Report Windows compile validation as still required.

### Windows signed-in UiPath host

**MUST** repeat until 0-error state from **both** `validate` and `build`, or max 5 fix attempts. After 5 attempts, stop and present remaining errors to the user.

### Step 3.1: Check for Errors (Windows host only)

Run the applicable static and compile gates per iteration. Build catches member-name and enum-value mistakes that source validation can miss (e.g. `NGetText.Value` when the property is `Text`, `Operator="StartsWith"` when the enum has no such member). See [../validation-guide.md § Fix loop](../validation-guide.md#fix-loop) for the canonical loop.

```bash
uip rpa validate --file-path "Workflows/MyWorkflow.xaml" --output json
uip rpa build "<PROJECT_DIR>" --log-level Warn --output json
```

`--file-path` must be **relative to the project directory**. Use `--skip-validation` only for quick cached-error checks. Treat `validate` clean as half-done — `build` clean is the signal to exit the loop.

### Step 3.2: Categorize and Fix

**Fix order:** Package → Structure → Type → Activity Properties → Logic.

1. **Package Errors** — Install/update the package. After install, activity docs become available.
2. **Structural Errors** — Fix XML structure. Cross-check against [xaml-basics-and-rules.md](xaml-basics-and-rules.md).
3. **Type Errors** — Check activity doc for correct types and enum values. For JIT types: [jit-custom-types-schema.md](jit-custom-types-schema.md).
4. **Activity Properties Errors** — Read activity doc for properties, conditional groups, valid configurations. Fallback: `activities get-default-xaml`. Watch for OverloadGroup conflicts.
5. **Logic Errors** — Verify expression syntax matches project language. For UI automation: use `debug start`; [ui-automation-guide.md](../ui-automation-guide.md) MUST be read IN FULL first (see § Running UI Automation Workflows for the debug procedure).

**When stuck:** Defer to user for minor config details. If failing to resolve an activity, consider InvokeCode as a last resort.

For detailed procedures, see [../validation-guide.md](../validation-guide.md).

---

## Phase 4: Response

1. **File path** of created/edited workflow
2. **Brief description** of what the workflow does
3. **Key activities** and logic implemented
4. **Packages installed** (if any)
5. **Limitations** or notes
6. **Suggested next steps** (testing, parameterization)
7. **Encourage user to review and customize** (fill placeholders, set up connections)

---

## Anti-Patterns

- **NEVER** generate large, complex workflows in one go
- **NEVER** manually craft UI selectors outside of `uia-configure-target` skill flow
- **NEVER** assume a create/edit succeeded without verification (Windows: `validate` + `build`; Mac: static gate in [xaml-edit-fast-path.md §7](xaml-edit-fast-path.md))
- **NEVER** treat "no diagnostics found" from `validate` as final on a Windows host — run `build` next; member-name and enum-value errors hide behind a clean `validate`
- **NEVER** burn iterations rediscovering Mac Helm/platform blocks for `validate`/`build`
- **NEVER** stop the iteration loop before correctly rendering all activities
- **NEVER** guess properties, types, or configurations without checking docs
- **NEVER** ship compact one-line Assigns, missing Main sidecars, duplicate IdRefs, or PHI-heavy logs on mature projects
- **NEVER** run full activity discovery for card activities (`Assign` / `If` / `LogMessage` / …) when the fast path applies
- **NEVER** use incorrect keys with `uip rpa workflow-examples get` (always from list results)
- **NEVER** pass absolute paths to `--file-path` in `validate` (must be relative)
- **NEVER** ask user to choose provider without checking project signals first
- **NEVER** retry failing CLI commands in a loop without diagnosing root cause
- **NEVER** skip Phase 0 (Studio readiness)
- **NEVER** use connector activities without checking connection existence
- **NEVER** ignore activity doc conditional property groups (OverloadGroup conflicts cause validation errors)
- **NEVER** generate full XAML from scratch without using `activities get-default-xaml` as a starting point
