# UiPath Code Mode Playbook

## Ask-mode handoff

Before a substantial edit, produce a compact change charter:

```text
Goal
Affected workflow boundary
Behavior that must not change
Approved workflow decomposition
Style anchors
Tests to add before removal
Required validation gates
Known environmental limitations
```

The handoff is complete when another agent can implement without choosing new business behavior or workflow boundaries.

## Code-mode loop

1. Resolve the nearest `project.json` and run `scripts/uipath_tool.py inspect`.
2. Read the affected workflows, their callers, their callees, and one style anchor.
3. Implement one coherent slice—normally one contract or one business responsibility.
4. Run `audit --scope changed` after the slice.
5. Fix errors from evidence; do not bundle unrelated cleanup.
6. Run the Windows gate when the required claim exceeds L1.
7. Repeat until the charter is satisfied.

## Stop conditions

Pause implementation when:

- the business outcome is ambiguous;
- an external workflow contract must change without approval;
- a new activity has no trusted serialization example or package documentation;
- required Windows tooling or licensing is blocked;
- a replacement test cannot characterize the old behavior;
- production execution would cause an unapproved side effect.

## Evidence handoff

Return the changed files, test cases, four gate statuses, unresolved findings, and the exact command evidence. Do not use “validated” without naming the gate.
