# Validation gates

Apply the gates needed for the requested claim and report each result
separately.

## Source fidelity

- Every node and edge resolves to the evidence ledger.
- Decision labels match actual conditions.
- Exceptions, retries, batching, cleanup, and external steps are represented
  at the correct scope.
- As-implemented and proposed behavior are visibly distinct.

## Package and schema

- `vsdx validate` returns `valid: true`.
- ZIP CRC testing reports no corrupt member.
- Expected pages, lanes, nodes, and connectors are present.
- Semantic IDs are unique and complete.
- Baseline-to-edit connector topology is unchanged unless the user intended a
  process-flow change.
- Added package parts, masters, and relationships are explained.
- Repeated generation from the same spec is byte-identical or every
  nondeterministic part is explained.

## Connector integrity

- Every process connector has exactly two `Connect` rows.
- Both coordinates of each endpoint use a coherent point formula.
- Connector direction and arrowheads match the intended flow.
- Reconnected or Visio-created connectors retain two endpoints after save and
  reopen when an artifact-specific browser gate is authorized.

## Visual layout

- Node overlaps: zero.
- Lane-edge padding and adjacent-peer gaps meet the map's numeric contract.
- Row alignment and gap spread are deliberate.
- Dense routes do not cross unrelated nodes or obscure labels.
- Page bounds fit the visible content; invisible or rotated backgrounds do not
  create large blank regions.
- Render warnings are resolved or documented shape by shape.
- Color remains within the approved palette and lane scope.

## Visual review

- Review the complete sheet at fit-to-page scale.
- Review dense exception, retry, completion, and loop regions separately.
- Compare the final render with named references and intentional user edits.
- Confirm that reader-facing titles omit internal build metadata.

## Visio and runtime boundaries

Use precise claims:

- **Structurally validated**: package, formulas, and local render passed.
- **Build browser-gated**: the exact VSDX Guard build passed an authenticated
  representative Visio interaction gate.
- **Artifact browser-gated**: this exact VSDX passed open, edit, move, resize,
  reconnect, save, download, and reopen checks.
- **Runtime validated**: the represented automation or system executed in its
  required environment.

One claim does not imply another.

## Delivery receipt

Record:

- source revision and scope;
- VSDX Guard path, version, revision, dirty flag, and binary hash;
- final artifact path, byte size, and SHA-256;
- page/node/connector counts;
- spacing and page-utilization measurements;
- package, render, connector, and determinism results;
- browser and runtime evidence boundaries.
