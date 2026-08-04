# XAML Edit Fast Path

**Use this file for routine create/edit work on existing mature XAML projects** (REFramework, multi-workflow processes, COE-style performers). Goal: make correct, Studio-readable changes in **one pass** — not many validate/fix loops.

Read this whole file before editing. For greenfield activity discovery, Flowchart/StateMachine canvas work, or UIA target capture, use the broader guides after this path.

---

## 0. Decision: is this a fast-path edit?

| Request | Fast path? | Why |
|---------|------------|-----|
| Add/change Assigns, Ifs, logs, args, vars in existing Sequence workflows | **Yes** | Style + contracts dominate |
| Wire `InvokeWorkflowFile`, map args, add Main job inputs | **Yes** | Sidecar + IdRef + invoke contracts |
| Fix naming/logging/style after a prior edit | **Yes** | Local serialization anchor |
| New project / unknown activity packages / UIA capture | **No** | Use full discovery + Rule 21 / UIA guides |
| Flowchart / StateMachine / ProcessDiagram layout | **No** | Canvas layout rules required |

---

## 1. 60-second project anchor (do this once per session)

1. Find `{projectRoot}/project.json` → note `expressionLanguage`, `targetFramework`, entry points.
2. List nearby workflows with the same folder conventions (`Framework/`, `Components/`, `init*`, `br*`, `ai*`, etc.).
3. **Open one Studio-readable sibling workflow** that already looks correct in Designer. That file is the **serialization/style anchor** for:
   - Assign shape (expanded vs compact; generic `Assign<T>` vs untyped tag)
   - LogMessage shape (attribute form vs property-element form)
   - Argument/variable naming prefixes
   - Whether `sap2010:WorkflowViewState.IdRef` and `HintSize` are present
   - Line endings (CRLF vs LF) of the file you will edit
4. On the user's Mac, **do not** run `uip rpa validate` / `build` / `run` / analyzer (see SKILL.md **Host Reality**). Plan the static gate in §7 instead.

Do **not** invent a new house style. Match the anchor.

---

## 2. Authoring order (minimize iterations)

Work in this order; do not jump to bulk rewrites:

1. **Contracts first** — arguments, variables, invoke maps, Main sidecar JSON
2. **Control flow skeleton** — Sequences / If / TryCatch with real `DisplayName`s
3. **Assign-heavy logic** — one Assign per target, expanded form
4. **Storytelling logs** — branch/decision/outcome logs (PHI-safe)
5. **Analyzer-safe identifiers** — arguments and variables must be 30 characters or fewer by default. Retain direction/type prefixes, shorten the descriptive portion, and update every caller and sidecar when renaming.
6. **Expression contracts** — when an expression uses `scg:List(...)`, `List(Of T)`, or LINQ `.ToList()`, copy `System.Collections.Generic` into `TextExpression.NamespacesForImplementation` and the `System.Collections`, `System.Core`, and `System.ObjectModel` assembly references from the Studio-readable anchor. `xmlns:scg` alone does not import `List` into the VB expression compiler.
7. **IdRef uniqueness** — every new activity gets a unique `WorkflowViewState.IdRef`
8. **Static gate** — §7 checks on touched files only
9. Report: Mac static checks passed; Windows Studio compile still required

Prefer **targeted edits** over regenerating whole workflows. Do not re-indent or reserialize the entire file.

---

## 3. Code style (Studio-readable XAML)

### 3.1 Assigns — Studio-readable (this is where "looks odd in Studio" comes from)

**Read the full guide:** [assign-studio-style.md](assign-studio-style.md) — wrong/right XAML from real fix threads (`brCheckComponentSumEvidence`, `Assign - Create dt_InputData`).

**Required shape** (property elements on their own lines; **no** `x:TypeArguments` on the `<Assign` tag in mature projects):

```xml
<Assign DisplayName="Assign - Initialize captured comments" sap2010:WorkflowViewState.IdRef="Assign_InitCapturedComments_1">
  <Assign.To>
    <OutArgument x:TypeArguments="x:String">[out_strCapturedComments]</OutArgument>
  </Assign.To>
  <Assign.Value>
    <InArgument x:TypeArguments="x:String">[""]</InArgument>
  </Assign.Value>
</Assign>
```

**Janky patterns users called out — never ship:**

```xml
<!-- 1) collapsed one-line To/Value -->
<Assign.To><OutArgument x:TypeArguments="x:Object">[out_dict("Key")]</OutArgument></Assign.To>
<!-- 2) generic type on Assign tag in a Studio-style project -->
<Assign x:TypeArguments="x:Object" DisplayName="Assign - Runtime flag">...</Assign>
```

Rules:

| Rule | Detail |
|------|--------|
| Expanded form | Never commit one-line `<Assign.To><OutArgument ... /></Assign.To>` or single-line full Assigns |
| Local typing style | Mature anchors omit `x:TypeArguments` on `<Assign>` and type only `InArgument`/`OutArgument` — **match that**. Do not mix generic Assign tags into those projects |
| Expression form | Usually bracket shorthand `[var]` / `[expr]`. Use `VisualBasicReference`/`VisualBasicValue` only if the anchor does |
| One target | One Assign → one left-hand side |
| DisplayName | `Assign - <specific target/result>` — not `Assign`, `Assign - Value`, or `CORRECT Assign …` leftovers |
| Prefer Assign-heavy | For parsing, flags, mapping, regex, and small transforms: use Assign + If. **Avoid `Invoke Code` / `Invoke Method`** unless the user explicitly approves or there is no practical XAML alternative |

### 3.2 Logs — storytelling, PHI-minimized

Preferred mature-project form (attribute style, common in REFramework/COE performers):

```xml
<ui:LogMessage DisplayName="Log Message - AI eligibility evaluated"
               sap2010:WorkflowViewState.IdRef="LogMessage_AIEligibility_1"
               Level="Info"
               Message="[&quot;AI eligibility evaluated | Eligible=&quot; + boolAIEligible.ToString + &quot; | Reason=&quot; + strAIEligibilityReason]" />
```

If the anchor expands `LogMessage.Message` as a property element, match that instead.

**What to log (narrative path):**

- Workflow / component start with purpose (not empty "started")
- Important inputs/config **summaries** (counts, flags, model version — not raw secrets)
- Branch selected / rule outcome / fallback chosen
- External side effects (file written, queue item added, portal submit attempted)
- Validation success/failure **reason codes**
- Final mapped status / bill action / exception path

**What never to log:**

- Raw GenAI prompts or full model responses
- Patient names, MRNs, account numbers, full comments
- Queue reference IDs, tokens, cookies, connection strings
- Full file contents

Log **counts, booleans, reason codes, hashes, capped lengths, cache hit/miss, sanitized paths**.

| Level | When |
|-------|------|
| `Info` | Normal narrative progress |
| `Warn` | Recoverable fallback / degraded path / retry |
| `Error` | About to throw or map to system-exception path |

Workflow-emitted `Error` logs are **observability**, not the CLI success verdict (SKILL Common Rule 8a).

### 3.3 Naming

Match the project. Common mature patterns:

| Kind | Pattern | Examples |
|------|---------|----------|
| Workflow files | verb/domain prefixes | `initMergeOutputReports`, `brApplyRules`, `aiInitializeRuntime`, `proFlushOutputReport` |
| Arguments | `in_` / `out_` / `io_` + type hint | `in_bnEnableAIWork`, `out_strStatusMessage`, `io_tcTerminalConnection` |
| Locals | type prefix | `strPatientNo`, `boolAIEligible`, `dtCapturedComments`, `dictAIRuntimeContext`, `intLastFlushRow` |
| Booleans | `bn` / `bool` | `in_bnGenerateReport`, `boolShouldThrowBRE` |
| DisplayNames | business language | `Map AI technical failure`, `Use deterministic fallback` — not bare `Then`/`Else` when you author the container |

### 3.4 Containers

- Every `If.Then` / `If.Else` / loop body / TryCatch branch wraps children in `<Sequence>` (even one child).
- Expand one-line `If.Else` / bare bodies to match Studio-readable anchors.
- Do not strip existing `ViewState` / `HintSize` on nodes you are not changing.
- New activities: add a **unique** `sap2010:WorkflowViewState.IdRef` following the file's pattern (`Assign_12`, `LogMessage_AICacheMiss_1`, etc.).

### 3.5 Line endings

Match the file you edit. Many Windows Studio projects use **CRLF**. After patching:

- If the file was CRLF, normalize back to CRLF.
- For `git diff --check` noise on CRLF XAML, use:  
  `git -c core.whitespace=cr-at-eol diff --check -- <files>`  
  Do not rewrite a whole workflow just to silence CRLF scanners.

---

## 4. Main arguments and sidecar metadata (Studio will "repair" you if you skip this)

When you add/rename/remove an argument on the **process entry point** (`Main.xaml` or the active entry workflow):

1. Update the XAML `<x:Members>` (+ root default via `this:Class.arg` if needed).
2. Update **`Main.xaml.json`** (or `<Entry>.xaml.json`) `Arguments[]` entry (`Name`, `DisplayName`, `IsPrincipal`, etc.).
3. Update **`entry-points.json`** input schema/default for that argument.
4. Keep `entry-points.json` aligned to **active** entry points only — remove stale component paths Studio no longer publishes as entries.

XML-only edits that skip sidecars are a top cause of "opens in Studio and auto-fixes half the repo."

Component workflows under `Components/` usually **do not** need `.xaml.json` sidecars unless they are published entry points.

---

## 5. InvokeWorkflowFile contracts

Before finishing any invoke change:

1. Target path exists (normalize `/` and `\\` — both are valid).
2. Every `In`/`Out`/`InOut` argument on the callee is mapped or intentionally defaulted.
3. Caller variable types match callee argument types.
4. If a tiny helper only exists to hold Assign-heavy logic and runtime treats the invoke as fragile, **inline** it into the caller (prefer fewer invoke boundaries for trivial helpers).

---

## 6. Studio-compatible activity skeletons (when adding new activities outside Studio)

Copy structure from a sibling usage in the same project when possible. Known repair patterns Studio has applied in this environment:

- New workflow files may need additional assembly references Studio emits (e.g. `System.Linq.Expressions`, `System.ComponentModel.TypeConverter`, project `GlobalVariables*` reference). Prefer cloning the reference set from a sibling component over inventing a minimal set.
- Modern Excel `ExcelProcessScopeX` often needs explicit null defaults Studio serializes:  
  `DisplayAlerts`, `ExistingProcessAction`, `FileConflictResolution`, `LaunchMethod`, `LaunchTimeout`, `MacroSettings`, `ProcessMode` as `{x:Null}` when unused.
- Preserve explicit Sequence wrappers and container indentation around `TryCatch` / `If` — bare bodies validate but render poorly and get reserialized.

---

## 7. Static verification gate (Mac default)

Run the collocated validator on touched files after the edit pass. Do not recreate this gate as ad hoc shell snippets.

```bash
python3 <skill-dir>/scripts/uipath_tool.py audit \
  --project <project> --scope changed --policy baseline
```

For native business-rule cleanup, replace `baseline` with `native-business-rules` and limit the scope to the intended leaf workflows. Run `normalize-eol --check` before any explicit EOL repair.

**Pass criteria:** L1 is `passed`; every warning has been reviewed; invoke contracts, metadata, expression hazards, line endings, and the selected policy are clean for the intended scope.

**Always state:** L1 is static evidence. Use the Parallels Windows bridge from [validation-guide.md](../validation-guide.md) for L2 compile and L3 execution evidence.

---

## 8. Symptom → fix (from real fix threads)

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Studio auto-rewrites many XAMLs after open | Missing sidecar args, stale entry-points, incomplete references, missing Excel null defaults | Update `Main.xaml.json` + `entry-points.json`; clone sibling references; match Studio activity skeletons |
| Designer hard to review / "ugly" Assigns | Compact one-line Assigns or mixed generic/non-generic style | Expand Assigns; match anchor typing style |
| First-pass logic works but looks wrong | One-line `If.Else`, missing Sequence wraps, vague DisplayNames | Expand containers; business DisplayNames |
| `uip rpa validate` → Helm signed-in user | Mac host limitation | Stop retrying; use §7 static gate |
| `uip rpa build` → Windows projects on Linux | Windows-target project on Mac | Same — static gate + defer compile to Windows |
| `git diff --check` red on every XAML line | CRLF treated as trailing whitespace | `core.whitespace=cr-at-eol`; do not mass-convert blindly |
| Runtime missing new Main input | Updated XAML only | Add to `Main.xaml.json` + `entry-points.json` |
| Invoke target "missing" in scanner | Path slash mismatch | Normalize `/` and `\\` |
| Silent wrong parser offsets / rules | Copied sibling offsets without fixture check | Verify against sample inputs before hardcoding |
| PHI leak in Orchestrator logs | Logged raw comments/prompts/IDs | Counts + reason codes only |
| Agent loops on activity docs for simple If/Assign | Treated every edit as greenfield discovery | Stay on this fast path; use common-activity-card |
| `BC30451: 'Regex' is not declared` | Assembly reference exists but VB namespace import does not | Fully qualify `System.Text.RegularExpressions.Regex` or add the VB import; do not create a Data Manager variable |
| `BC30198: ')' expected` on XML-valid XAML | Fluent VB chain was split after a trailing `.` | Keep the chain on one physical line or split it across typed Assign activities |

---

## 9. Done checklist (copy into your mental model)

- [ ] Style matched to a real sibling anchor (Assign, logs, names, IdRef pattern)
- [ ] Assign-heavy logic; no unsolicited Invoke Code
- [ ] Storytelling, PHI-safe logs with correct levels
- [ ] Container bodies wrapped in Sequence; no compact style drift
- [ ] Unique IdRefs on new activities
- [ ] Main/entry sidecars updated if arguments changed
- [ ] Argument names are at most 30 characters (`ST-NMG-016`)
- [ ] Variable names are at most 30 characters (`ST-NMG-008`)
- [ ] Invoke contracts verified (`/` + `\\`)
- [ ] Line endings match the file
- [ ] §7 static gate green on touched files
- [ ] User told Windows compile validation still required (Mac)

When this checklist is green, stop. Do not open the full validation-guide loop or re-run blocked CLI commands.
