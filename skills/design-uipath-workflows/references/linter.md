# Read-only UiPath style linter

`scripts/uipath_style_lint.py` performs dependency-free, read-only XML heuristics. It never edits XAML and is not UiPath Workflow Analyzer, Studio validation, compilation, execution, or UAT.

## Usage

From the skill directory:

```bash
python3 scripts/uipath_style_lint.py --project /path/to/project --scope all
python3 scripts/uipath_style_lint.py --project /path/to/project --scope changed
python3 scripts/uipath_style_lint.py --project /path/to/project --scope selected --files Components/Invision/Invision_Login.xaml
python3 scripts/uipath_style_lint.py --project /path/to/project --scope all --format json
```

Scopes:

- `selected` — only paths supplied with `--files`;
- `changed` — tracked working-tree/staged changes plus untracked XAML in the Git checkout;
- `all` — every project XAML outside common generated directories.

Exit codes:

- `0` — no unwaived errors; warnings may remain;
- `1` — one or more unwaived policy errors;
- `2` — usage, configuration, Git-discovery, or XML parse failure.

Text and JSON include errors, warnings, informational metrics, and active waivers. Use `--fail-on warning` when a consuming CI policy wants warnings to fail without changing their meaning.

## Project configuration

Place optional `.uipath-style.json` at the project root or pass `--config`:

```json
{
  "application_aliases": ["Invision", "Epic"],
  "abbreviations": {
    "Patient": "PAT",
    "Terminal": "TER"
  },
  "safe_value_classifications": {
    "safe": ["intTimeoutMS", "intRetryCount", "bnIsSimulation"],
    "sensitive": ["strPatientStatus", "strPatientAccountNumber"]
  },
  "loop_threshold": 10,
  "loop_progress_interval": 100,
  "protected_paths": [
    "Framework/*.xaml",
    "Legacy/Vendor/*.xaml"
  ],
  "waivers": [
    {
      "rule": "HOUSE-WF-006",
      "workflow": "Components/Legacy/ProLegacyExtract.xaml",
      "rationale": "Extraction would duplicate a tightly coupled vendor transaction.",
      "approver": "COE architecture",
      "expiration": "2026-12-31"
    }
  ]
}
```

Paths and workflow waiver patterns use forward-slash glob syntax. Configuration augments the built-in protected native REFramework paths. `TC_*.xaml` is excluded from v1.

Safe classifications are exact variable names or glob patterns. An explicit sensitive match wins. Without an approved safe classification, string, row/table, collection, object, path, selector, screen, payload, patient, account, claim, credential, and exception values are treated as sensitive. A small set of plainly technical counter, retry, timeout, elapsed-time, and simulation names is recognized as safe; configure ambiguous values explicitly.

Each waiver requires all five fields. Expired waivers do not suppress findings. Security findings, XML/config errors, the 10 MB support boundary, and UI Automation inside Parallel are not waivable.

## What it checks

The linter checks high-signal static evidence:

- filename grammar, complete length, case-insensitive collisions, and compact-name suggestions;
- root `DisplayName` and the required annotation sections;
- approximate activity count, file size, nesting, and nested If thresholds;
- unique `[Activity - action]` DisplayNames;
- Invoke Code/Invoke Method, GenericValue, argument budget, prefixes, name lengths, and duplicate variables;
- Start/End boundaries and straightforward Sequence action/log adjacency;
- Assign and Multiple Assign target names, dynamic approved values, sensitive interpolation, and multiline grouping;
- obvious assigned literals copied into the following log instead of reading an approved safe target dynamically;
- branch-entry logs, loop-adjacent logs, high-volume loop levels, and caller-side invoke logging;
- telemetry-shaped or disclosure-signaling log prose;
- ContinueOnError, empty Catch, Write Line, Delay-based UI synchronization, raw exception interpolation, and UI Automation inside Parallel.

Every workflow receives an informational metrics record.

## Heuristic limits

UiPath XAML serialization differs across Studio and activity versions. The linter deliberately avoids evaluating VB/C# expressions, resolving packages, proving selector quality, inferring every execution path, or deciding whether a business value is truly non-sensitive. Adjacency checks are strongest in ordered Sequences. Flowcharts, State Machines, custom activities, complex expressions, and hidden Studio metadata require human and Windows Studio review.

Treat a clean result as “no configured static finding detected,” never as proof that the workflow compiles or runs.
