---
name: uipath-pdd-docx
description: Analyze UiPath RPA projects, extract implemented dispatcher or performer behavior, draft support-ready PDD markdown, and insert the content into Word DOCX templates with clean formatting. Use when documenting UiPath automations, filling PDD TO-BE sections, updating shared dispatcher/performer process documents, or rebuilding poorly formatted DOCX sections from repo evidence.
---

# UiPath PDD DOCX

## Overview

Use this skill when the user wants reusable documentation output from a UiPath project, especially:

- a PDD section drafted from actual implemented workflows
- dispatcher-only or performer-only documentation extracted from a REFramework repo
- a shared PDD where dispatcher and performer content must coexist without incorrect scope claims
- markdown content inserted into a `.docx` with Word-native headings, tables, notes, and diagrams

This skill is for evidence-based documentation. Document what the repo implements now, label assumptions, and keep unsupported claims out of the final document.

## Workflow

### 1. Set the document boundary first

Before drafting anything, determine whether the target document is:

- dispatcher only
- performer only
- a shared dispatcher and performer PDD

If it is shared, write component-specific content without turning shared headings into global claims. Prefer wording like:

- `The rows below document dispatcher-owned scope only within the shared PDD.`
- `The exception entries below are limited to dispatcher behavior and should be supplemented later with performer exceptions.`

Avoid wording like:

- `This is out of scope for RPA`
- `The process does not perform portal entry`

unless you have confirmed that statement for the full combined automation.

### 2. Analyze the UiPath project from local evidence

Start from the repo. Do not begin by paraphrasing the business objective.

Inspect, at minimum:

- `Main.xaml`
- `Framework/*.xaml`
- `Components/**/*.xaml`
- `Other/**/*.xaml`
- `Data/Config.xlsx` and any referenced assets or lookup files
- project arguments, config keys, queue names, folder paths, credentials, secrets, email flows

For REFramework projects, confirm:

- init path behavior
- source data ingestion path
- transaction-build logic
- queue behavior
- exception boundaries
- report outputs
- cleanup logic

Use `rg` first to find:

- workflow names
- queue usage
- `Add Queue Item`
- `Get Queue Items`
- `STATUS`
- email workflows
- config keys
- credential or asset names

If the user asks for best-practice guidance, browse official UiPath documentation and prefer UiPath primary sources.

Detailed inspection guidance lives in [project-analysis.md](references/project-analysis.md).

### 3. Draft markdown to match the target PDD structure

Draft into markdown first unless the user explicitly wants direct DOCX edits with no intermediate artifact.

Rules:

- match the document's existing section numbering and headings
- describe implemented behavior, not intended behavior, unless clearly labeled as assumption or open point
- surface operational dependencies for support: config, queues, assets, mailboxes, lookup files, external apps
- separate dispatcher and performer ownership when the repo is only one side of the process
- call out assumptions and unresolved points explicitly

Good output patterns:

- short intro note stating component scope
- process map plus support interpretation
- workflow-to-action table
- queue payload or handoff contract table
- component-specific in-scope and out-of-scope rows
- known business and application exception tables
- reporting artifacts table

### 4. Insert the content into DOCX carefully

When editing Word documents:

- preserve the template's native heading styles and numbering
- do not hardcode heading numbers if the template already numbers headings
- rebuild target sections between heading anchors instead of appending ad hoc paragraphs
- use Word-native tables with fixed widths, padding, repeated header rows, and top-aligned cells
- use note paragraphs to mark dispatcher-only or performer-only content in shared sections
- use code-style formatting sparingly inside tables; monospace text makes narrow tables unreadable

For process maps:

- Word does not render Mermaid natively
- generate an image or replace the diagram with a readable textual flow
- if one image becomes too dense at page width, split it into multiple diagrams
- verify the image visually before finalizing

Detailed insertion and formatting guidance lives in [docx-insertion.md](references/docx-insertion.md).

### 5. Validate before handing off

Always verify:

- each documented step maps to a real workflow or config key
- dispatcher-only content is not presented as whole-process truth in a shared PDD
- performer-only claims are not inferred from dispatcher code
- table headers fit the page width and are readable
- process-map images are legible at the inserted size
- section boundaries in the `.docx` are still correct after insertion

If possible, create a backup of the original `.docx` before rewriting the section.

## Shared PDD Strategy

When the final PDD is shared across dispatcher and performer, treat these sections as potentially shared and component-mixed:

- process map
- in scope
- out of scope
- exceptions handling
- reporting
- assumptions or observations

Recommended pattern:

1. add dispatcher content with a scope note
2. leave room for performer content under the same heading
3. phrase rows and notes as component-owned entries
4. avoid absolute language unless confirmed for both components

If needed, add explicit labels in row text such as `Dispatcher:` and `Performer:`.

## Resources

- [project-analysis.md](references/project-analysis.md): checklist for extracting facts from UiPath repos
- [docx-insertion.md](references/docx-insertion.md): DOCX replacement, formatting, and validation rules
- [docx_section_rebuilder.py](scripts/docx_section_rebuilder.py): reusable starter module for replacing DOCX sections, formatting tables, and inserting notes/images
