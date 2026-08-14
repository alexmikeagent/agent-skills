# UiPath Validation Contract

## Gates

| Gate | Status proves | Does not prove |
|---|---|---|
| L1 static | XML, expression heuristics, metadata, invoke contracts, policy, EOL | UiPath compilation or execution |
| L2 compile | Windows restore and `uip rpa build` | Business behavior |
| L3 execution | Selected test/workflow completed in Windows | Uncovered scenarios or UAT |
| UAT | Representative business acceptance | Scenarios outside the UAT set |

Allowed states are `passed`, `failed`, `blocked`, and `not_run`.

## Exit codes

| Code | Meaning |
|---:|---|
| 0 | Requested gates passed |
| 1 | Validation finding failed a gate |
| 2 | Tool, configuration, or transport error |
| 3 | Windows capability blocked |
| 4 | Unsafe execution refused |

`build-and-test` passes only when compile succeeds and at least one selected test runs and passes. Missing, malformed, wrong-job, or contract-invalid result JSON is a tool error (2), not a validation failure (1).

## Result interface

`assets/schemas/validation-result-v1.schema.json` is authoritative. Findings carry a stable code, severity, message, gate, file when known, activity IdRef when known, evidence, and remediation. Generated logs and results belong under the transient job root, never the UiPath source repository.
