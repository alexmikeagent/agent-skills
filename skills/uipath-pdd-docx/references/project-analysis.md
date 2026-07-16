# Project Analysis

## Goal

Use this checklist to extract support-ready documentation facts from a UiPath project without inventing behavior.

## Minimum repo scan

Inspect these areas first:

- `Main.xaml`
- `Framework/`
- `Components/`
- `Other/`
- `Data/Config.xlsx`
- any lookup workbook paths, asset keys, queue names, or mail workflows found during the scan

Use `rg` to locate:

- `Add Queue Item`
- `Get Transaction Item`
- `Get Queue Items`
- `STATUS`
- `Config(`
- asset names
- credential names
- `Send Outlook Mail`, `Office365`, or custom email workflows

## Evidence to capture

Capture concrete facts for documentation tables:

- process inputs and arguments
- queue names and queue item payload fields
- config keys and required assets
- external systems touched by the bot
- lookup files and workbook dependencies
- transaction filters and retry rules
- success and failure status values
- generated reports, attachments, and email recipients

## Dispatcher-specific questions

- How is source data obtained: export, query, manual workbook, queue, API?
- What filtering, sorting, limiting, or enrichment occurs before queuing?
- How are duplicates prevented?
- Which fields are encrypted or normalized before handoff?
- What row-level status is written back?
- What is the contract handed to the performer?

## Performer-specific questions

- What systems are driven after queue pickup?
- Which fields from the queue are consumed?
- What business outcome is completed by the performer?
- What artifacts are produced: screenshots, uploaded files, notes, final status?
- What exceptions are handled per transaction versus process-level?

## Shared PDD questions

Before writing shared headings, ask:

- Is this claim true for dispatcher only, performer only, or both?
- Will the later performer pass need to add rows under the same section?
- Should this row be worded as component-owned instead of whole-process?

If the answer is unclear, document it as:

- `Dispatcher implementation currently shows ...`
- `Performer behavior not yet analyzed`
- `Assumption pending performer repo review`

## Assumptions and open points

Always call out:

- missing repos or missing component coverage
- runtime behavior that appears to live in Orchestrator rather than code
- config-key naming mismatches
- workbook template assumptions
- selector/UI dependencies likely to change

## Final quality check

Before producing final markdown or DOCX content, confirm:

- every step is repo-backed or clearly labeled as inference
- exception names match actual failure points where possible
- support dependencies are explicit
- component boundaries are visible
