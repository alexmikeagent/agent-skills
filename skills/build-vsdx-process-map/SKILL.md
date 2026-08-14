---
name: build-vsdx-process-map
description: Trace, create, revise, compare, and validate editable VSDX process maps with VSDX Guard. Use when Codex needs to turn source code or operating evidence into a Visio process map, build or improve a swimlane diagram, learn from a user-edited VSDX, or prove spacing, page-fit, rendering, semantic-ID, and connector fidelity.
---

# Build VSDX Process Maps

**Trace before drawing.** Treat the diagram as a compact evidence model, not an
illustration assembled from plausible labels.

## 1. Orient

Read the applicable workspace instructions. Resolve:

- the source of process truth;
- whether the map is as-implemented, current-state, or proposed;
- the reference and user-edited VSDX files;
- the required output location and external-write boundary;
- the installed `vsdx` path, version, revision, dirty flag, and binary hash.

Read [references/vsdx-guard.md](references/vsdx-guard.md) before invoking the
tool. Finish when the scope, evidence set, output contract, and exact tool build
are recorded.

## 2. Trace the process

Traverse reachable behavior end to end. Use the appropriate domain skill when
the source needs specialized interpretation. Build a ledger with one row per
drawn node or edge:

`map id | label | actor/lane | source evidence | condition/outcome | confidence`

Separate active behavior from dead code, disabled branches, examples, and
future intent. Mark external steps and unsupported inferences visibly. Finish
when every proposed node and edge has evidence or an explicit unresolved
assumption.

## 3. Learn the visual grammar

For each reference or user-edited VSDX:

1. Run `vsdx inspect`.
2. Open it individually with `vsdx view --no-open`.
3. Render each page for controlled full-sheet and focused review.
4. When a baseline and edited file exist, run:

```sh
python3 scripts/vsdx_map_tools.py compare BASELINE.vsdx EDITED.vsdx \
  --format markdown
```

Classify each delta as copy, geometry, lane ownership, routing, style,
connector semantics, or package side effect. Read
[references/process-map-design.md](references/process-map-design.md) for the
decision rules. Finish when intentional conventions and mechanical side
effects are separated.

## 4. Set the layout contract

Choose lane order, ownership, primary reading direction, exception/status
placement, shape vocabulary, palette, spacing thresholds, page bounds, and
connector tracks before generating.

Use explicit user direction first, then intentional user edits, named
references, project conventions, and finally the house style in the design
reference. Treat a lane reassignment as a semantic change. Finish when the
layout contract contains numeric padding and gap targets and every branch has a
planned route.

## 5. Generate save-as candidates

Author or update a Diagram Spec and create a new candidate:

```sh
vsdx create --spec MAP.spec.json --output MAP.candidate-01.vsdx
```

Carry intentional edits back into the spec instead of promoting a
Visio-resaved file as the source of truth. Preserve stable semantic IDs. Create
each iteration under a new name. Finish when the candidate represents the
complete evidence ledger and can be regenerated from the spec.

## 6. Inspect and refine

Run the audit after every material layout change:

```sh
python3 scripts/vsdx_map_tools.py audit MAP.candidate-01.vsdx \
  --format markdown
```

Review the full page and focused crops. Correct the spec when the audit or
visual review finds crowded peers, asymmetric rows, weak lane-edge clearance,
line/box intersections, ambiguous labels, page bloat, misplaced color, lost
semantic IDs, unsupported geometry, or connector failures. Finish when the
audit passes and the rendered reading order is unambiguous at fit-to-page
scale.

## 7. Prove the artifact

Read [references/validation-gates.md](references/validation-gates.md) and apply
every gate relevant to the requested claim. Regenerate twice and compare
hashes. Treat authenticated Visio upload as an external write and obtain
authorization before performing an artifact-specific web gate.

Finish when source fidelity, package integrity, visual layout, connector
structure, render output, and determinism are proven, and any environment-only
gate is labeled separately.

## 8. Deliver

Place final deliverables according to workspace rules. Prefer this set:

- final `.vsdx`;
- canonical `.spec.json`;
- `.svg` and reader-sized `.png`;
- audit JSON;
- validation receipt with tool provenance and evidence boundaries.

Link the final VSDX first. State what was proven, what remains external, and
which file is canonical. Finish when the files exist at the reported paths and
the handoff does not overstate Visio or runtime proof.
