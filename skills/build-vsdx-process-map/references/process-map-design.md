# Process-map design

## Evidence and scope

- Label the map as as-implemented, current-state, or proposed.
- Draw reachable behavior. Put unsupported intent in notes or a separate
  future-state map.
- Keep one evidence-led label per node. Use implementation vocabulary only
  when it helps the reader.
- Mark external actors and steps rather than implying that the mapped system
  performs them.

## Reference and edit deltas

Inspect references one at a time. When a user supplies an edited VSDX, compare
it with the baseline and sort the changes:

| Delta | Default treatment |
|---|---|
| Copy | Preserve when it remains source-accurate. |
| Geometry | Learn the spacing, alignment, and visual hierarchy. |
| Lane ownership | Flag as a semantic decision before regenerating. |
| Routing | Preserve the intent; rebuild it from stable connectors. |
| Style | Prefer intentional visible changes over package normalization. |
| Connector semantics | Restore stable IDs and two-ended glue. |
| Package side effect | Exclude it from the canonical spec. |

Examples of package side effects include a rotated invisible background,
unexpected page expansion, style-cell normalization, lost semantic IDs, and
new geometry rows that create render warnings.

## Lanes and shapes

- Order lanes by ownership and the dominant reading sequence.
- Place an outcome/status lane last for RPA maps when it clarifies completion
  and exception handling.
- Keep actions in the owning actor's lane. If readability calls for an
  exception chain in one lane, make the ownership tradeoff explicit.
- Use a small vocabulary: terminator, process, decision, data, and status
  outcome.
- Align peer shapes by center or edge. Size boxes to content without allowing
  one long box to dominate a row.

## House style

When the user or a named reference does not specify a palette:

- use white fills, black borders, black text, and black connectors;
- reserve pale green `#e2f0d9` for success/completion;
- reserve pale red `#f4cccc` for exception/stopped outcomes;
- keep colored outcomes in the status/outcome lane;
- keep build hashes and tool versions in the validation receipt, not the
  reader-facing subtitle.

## Spacing and symmetry

Set numeric thresholds for each map rather than relying on visual intuition.
Useful starting points for a large landscape swimlane map are:

- horizontal lane-edge padding: `0.60 in`;
- vertical lane-edge padding: `0.40 in`;
- horizontal gap between adjacent peers: `0.60 in`;
- vertical gap between stacked peers: `0.80 in`.

Treat these as starting values, not universal constants. Preserve a visible
gap at both ends of every lane. For three or more peers in a row, compare edge
gaps as well as centers; investigate a gap spread greater than `0.50 in`.
A regular column rhythm is useful, but content and branch clarity take
precedence over forcing every node onto the grid.

## Routing

- Give the main path the straightest track.
- Route exception arrows toward the outcome lane with short, distinct tracks.
- Separate success, business-exception, system-exception, retry, and return
  routes when a shared segment would blur meaning.
- Attach labels to an unambiguous segment and keep them off lane borders.
- Use explicit orthogonal waypoints where automatic routing crosses nodes or
  unrelated connectors.
- Review the entire loop after moving one node; local alignment can hide a
  distant collision.

## Reader review

Review at fit-to-page scale first, then inspect dense regions. A map is ready
when the reader can identify the start, primary path, decisions, exceptions,
completion, and lane ownership without tracing a line twice.
