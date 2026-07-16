# Assign Activities That Look Correct in UiPath Studio

**Purpose:** Stop agent-authored Assigns from rendering as "odd" / janky cards in Studio Designer while still being XML-valid.

This guide is grounded in real COE-53 fix threads where the user said Assigns "look odd" in Studio and pointed at a known-good workflow (`brCheckComponentSumEvidence`), and an earlier thread that mandated converting every Assign to the expanded form exemplified by `Assign - Create dt_InputData`.

Read this **before** writing or bulk-editing any Assign activity.

---

## Why Studio looks janky

Studio Designer serializes Assigns as **multi-line property elements** with typing on `InArgument` / `OutArgument`, not as compact one-liners or generic activity tags. Agents often emit XML that **validates and runs** but:

1. Collapses `<Assign.To>` / `<Assign.Value>` onto a single line
2. Puts `x:TypeArguments` on the `<Assign>` activity tag itself (`Assign`1` generic form)
3. Mixes both styles in one workflow
4. Uses vague `DisplayName`s (`Assign`, `Assign - Value`)

Result in Designer: cramped, hard-to-inspect Assign cards, inconsistent property panes, and follow-up "redo all assigns" passes.

XML validity ≠ Designer readability.

---

## Canonical good form (use this)

Taken from Studio-readable project style (`brCheckComponentSumEvidence`, `Assign - Create dt_InputData`, mature REFramework components):

```xml
<Assign DisplayName="Assign - Create dt_InputData"
        sap2010:WorkflowViewState.IdRef="Assign_CreateInputData_1">
  <Assign.To>
    <OutArgument x:TypeArguments="sd:DataTable">[dt_InputData]</OutArgument>
  </Assign.To>
  <Assign.Value>
    <InArgument x:TypeArguments="sd:DataTable">[New DataTable("InputData")]</InArgument>
  </Assign.Value>
</Assign>
```

String example:

```xml
<Assign DisplayName="Assign - Component evidence"
        sap2010:WorkflowViewState.IdRef="Assign_ComponentEvidence_1">
  <Assign.To>
    <OutArgument x:TypeArguments="x:String">[strComponentEvidence]</OutArgument>
  </Assign.To>
  <Assign.Value>
    <InArgument x:TypeArguments="x:String">[If(in_dtCommentEvents Is Nothing, String.Empty, "...")]</InArgument>
  </Assign.Value>
</Assign>
```

Dictionary indexer example:

```xml
<Assign DisplayName="Assign - Runtime enabled flag"
        sap2010:WorkflowViewState.IdRef="Assign_RuntimeEnabled_1">
  <Assign.To>
    <OutArgument x:TypeArguments="x:Object">[out_dictAIRuntimeContext("Enabled")]</OutArgument>
  </Assign.To>
  <Assign.Value>
    <InArgument x:TypeArguments="x:Object">[boolAIEnabled]</InArgument>
  </Assign.Value>
</Assign>
```

### Required shape checklist

| Requirement | Detail |
|-------------|--------|
| Tag | `<Assign ...>` **without** `x:TypeArguments` on the activity tag (mature / Studio-emitted local style) |
| Structure | Multi-line: `Assign` → `Assign.To` → `OutArgument` → `Assign.Value` → `InArgument` |
| Typing | `x:TypeArguments` lives on **`OutArgument` and `InArgument` only** |
| Expression form | Match the sibling anchor: usually VB bracket shorthand `[expr]` (not nested `VisualBasicReference` / `VisualBasicValue` unless the anchor uses those) |
| DisplayName | `Assign - <specific target/result>` — e.g. `Assign - Create dt_InputData`, `Assign - Component evidence` |
| One target | Exactly one left-hand side per Assign |
| IdRef | Unique `sap2010:WorkflowViewState.IdRef` when the file uses IdRefs |
| No duplicates | Do not leave a second "example" / placeholder Assign after converting style |

---

## Forbidden / janky forms (what made Studio look odd)

### 1. Collapsed one-line To/Value (most common agent failure)

```xml
<!-- BAD — XML-valid, looks odd in Studio -->
<Assign x:TypeArguments="x:Object" DisplayName="Assign - Runtime confidence threshold">
  <Assign.To><OutArgument x:TypeArguments="x:Object">[out_dictAIRuntimeContext("ConfidenceThreshold")]</OutArgument></Assign.To>
  <Assign.Value><InArgument x:TypeArguments="x:Object">[dblConfidenceThreshold]</InArgument></Assign.Value>
</Assign>
```

### 2. Generic type on the Assign activity tag (mixed with local style)

```xml
<!-- BAD in mature COE / Studio-emitted projects -->
<Assign x:TypeArguments="x:String" DisplayName="Assign - Status">
  ...
</Assign>
```

Local good files use **zero** `x:TypeArguments` on the `<Assign` tag and still type the arguments.

### 3. Fully single-line Assign

```xml
<!-- BAD -->
<Assign DisplayName="Assign - X"><Assign.To><OutArgument x:TypeArguments="x:String">[strX]</OutArgument></Assign.To><Assign.Value><InArgument x:TypeArguments="x:String">[""]</InArgument></Assign.Value></Assign>
```

### 4. Attribute-style To/Value (not Studio shape)

```xml
<!-- BAD — do not invent -->
<Assign To="[strX]" Value="[0]" DisplayName="Assign - X" />
```

### 5. Vague names / leftover example copies

```xml
<!-- BAD -->
<Assign DisplayName="Assign">...</Assign>
<Assign DisplayName="Assign - Value">...</Assign>
<Assign DisplayName="CORRECT Assign - Create dt_InputData">...</Assign>  <!-- example marker left in file -->
```

---

## Before/after (mechanical conversion)

**Before (janky):**
```xml
<Assign x:TypeArguments="x:Object" DisplayName="Assign - Runtime enabled flag">
  <Assign.To><OutArgument x:TypeArguments="x:Object">[out_dictAIRuntimeContext("Enabled")]</OutArgument></Assign.To>
  <Assign.Value><InArgument x:TypeArguments="x:Object">[boolAIEnabled]</InArgument></Assign.Value>
</Assign>
```

**After (Studio-readable local style):**
```xml
<Assign DisplayName="Assign - Runtime enabled flag"
        sap2010:WorkflowViewState.IdRef="Assign_RuntimeEnabled_1">
  <Assign.To>
    <OutArgument x:TypeArguments="x:Object">[out_dictAIRuntimeContext("Enabled")]</OutArgument>
  </Assign.To>
  <Assign.Value>
    <InArgument x:TypeArguments="x:Object">[boolAIEnabled]</InArgument>
  </Assign.Value>
</Assign>
```

Conversion rules used in the fix threads:

1. Remove `x:TypeArguments="..."` from the `<Assign` opening tag
2. Expand every `<Assign.To><...></Assign.To>` onto multiple indented lines
3. Expand every `<Assign.Value><...></Assign.Value>` the same way
4. Keep typed `OutArgument` / `InArgument` and the `[expr]` bodies
5. Ensure `DisplayName="Assign - <specific>"`
6. Add/keep unique IdRef if the file uses them
7. Expand one-line `If.Else` / bare container bodies in the same pass (they cause the same "odd in Designer" complaint)

---

## Anchor-first rule (do not invent a house style)

Before writing Assigns in a mature project:

1. Open a sibling Studio-readable workflow (user may name one — e.g. `brCheckComponentSumEvidence.xaml`)
2. Copy **that** Assign serialization (tag attributes, indentation, bracket vs VBReference, IdRef pattern)
3. Only fall back to this guide's canonical form when no anchor exists

**Greenfield exception:** Some greenfield / skill-card samples use `<Assign x:TypeArguments="T">` for early type checking. That is acceptable **only** when the whole new project consistently uses generic Assigns. Once a project already has Studio-emitted non-generic Assigns, **never** mix generic tags into it — that mix is exactly what looked odd in Studio.

---

## Style verification (mandatory after Assign edits)

Run on touched files. Fail the task if any match remains (unless the project-wide anchor truly is compact — rare).

```bash
# Collapsed To/Value (janky)
rg -n '<Assign\.To><|<Assign\.Value><|</Assign\.To><Assign\.Value>|</Assign\.Value></Assign>' <files>

# Generic type on Assign activity tag (local-style drift in mature projects)
rg -n '<Assign[^>]*x:TypeArguments' <files>

# Vague / example DisplayNames
rg -n 'DisplayName="Assign"|DisplayName="Assign - Value"|CORRECT Assign' <files>

# One-line If.Else often co-travels with compact Assigns
rg -n '<If\.Else><[^[:space:]/S]' <files>
```

Also:

- `xmllint --noout` on touched XAML
- Duplicate `WorkflowViewState.IdRef` scan
- Prefer targeted structural edits over naive whole-file regex conversion (large XAML is irregular; batch regex has broken nesting before)

**Pass criteria used in successful fix threads:** zero compact Assigns, zero generic Assign tags (when anchor has none), zero one-line `If.Else`, XML clean.

---

## Related authoring rules

- Prefer **Assign-heavy** logic; avoid `Invoke Code` / `Invoke Method` unless explicitly approved
- One Assign → one assignment; chain multiple Assigns instead of cramming multi-target logic
- Pair Assign blocks with storytelling `Log Message` activities (PHI-safe) — see [xaml-edit-fast-path.md](xaml-edit-fast-path.md)
- Do not "preserve" a janky Assign just because it was agent-generated earlier; convert it when editing the same feature

---

## Symptom → fix

| User / Studio symptom | Cause | Fix |
|-----------------------|-------|-----|
| "Assigns look odd in Studio" | Collapsed To/Value and/or `x:TypeArguments` on Assign tag | Convert to multi-line local form; match named example workflow |
| "Use CORRECT Assign - Create dt_InputData" | Compact or inconsistent Assigns | Expand all Assigns; remove the example/duplicate Assign |
| "Don't mess up the assign activities" | Refactoring Assign structure while changing schema | Change values/names only; keep expanded shape |
| Designer hard to review after agent PR | Mixed generic + non-generic Assigns | Normalize whole feature to one style (local anchor wins) |
| Batch convert broke XML | Naive regex on irregular XAML | Targeted edits + `xmllint` after each batch |

---

## Done checklist for any Assign-touching change

- [ ] Sibling style anchor inspected (or this guide used for greenfield)
- [ ] No `x:TypeArguments` on `<Assign` tags when local style omits them
- [ ] Every Assign uses multi-line `Assign.To` / `Assign.Value`
- [ ] Typed `OutArgument` / `InArgument` with matching types
- [ ] `DisplayName="Assign - <specific target>"`
- [ ] Unique IdRefs; no `CORRECT Assign` leftovers
- [ ] Style greps clean
- [ ] `xmllint` clean
