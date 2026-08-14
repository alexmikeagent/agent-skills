# Behavior-Preserving XAML Refactors

## Freeze the boundary

Record before editing:

- workflow arguments, directions, and types;
- callers and invoke bindings;
- output/status/reason-code values;
- exception types and messages that callers consume;
- evaluation order and resolver precedence;
- report field order and downstream side effects.

Use `scripts/uipath_tool.py inspect` for the structural map. Characterization tests remain the source of truth for behavior.

## Split by responsibility

Create a workflow boundary when a block has a distinct business purpose, inputs/outputs that can be named clearly, and focused tests. Do not split solely to reduce line count. Keep leaf business rules free of orchestration when the project convention places orchestration in the caller.

## Simplify without hiding behavior

Inventory outputs and side effects before reducing activities. Remove only proven redundant work. Use Multi Assign for cohesive initialization or defaults when the Studio/package anchor supports it; keep decisions, external actions, retries, and postconditions visibly separate. The parity suite must show that the same inputs still reach the same externally visible results.

Treat REFramework state placement as part of the contract. Before moving work across states, prove equivalent initialization frequency, transaction scope, retry and exception routing, cleanup, and application lifetime against the active template.

## Replacement sequence

1. Add characterization cases for success, every primary failure reason, boundaries, and exceptions.
2. Add and register replacement tests while the old implementation remains available. Run L1 with `--require-registered-tests` before any deletion.
3. Add the new leaf workflow and pass L1.
4. Rewire one caller and pass L1 again.
5. Pass L2 and the selected L3 suite.
6. Delete the superseded workflow or tests only after replacement coverage passes.
7. Rerun L1, L2, and the selected L3 suite on the post-deletion tree.
8. Run representative UAT before deployment.

## Native business-rule shape

Use Assign, Multi Assign for cohesive defaults, If, loops, Break, Continue, Add Data Column, Add Data Row, and other native activities. Use sensitive-data-safe boundary logs plus meaningful decision, side-effect, retry, and outcome logs; avoid narrating routine initialization. Preserve exact decision precedence and transaction disposition.

## Parity evidence

Behavior parity requires assertions over externally visible results, not only successful execution. Compare exact reason codes, status text, report values and order, exception boundary, and REFramework transaction outcome. L1 static success is never runtime parity.
