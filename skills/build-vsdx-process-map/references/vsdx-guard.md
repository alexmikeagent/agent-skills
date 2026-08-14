# VSDX Guard

## Resolve the exact build

Use the live binary, not recalled repository state:

```sh
command -v vsdx
vsdx version
go version -m "$(command -v vsdx)"
shasum -a 256 "$(command -v vsdx)"
vsdx schema diagram-spec-v1 >/dev/null
```

Record the embedded VCS revision and `vcs.modified` value. When the binary or
schema has drifted, re-check current help and repository evidence before using
old commands or claims.

## Command roles

```sh
vsdx create --spec MAP.spec.json --output NEW.vsdx
vsdx validate MAP.vsdx
vsdx inspect MAP.vsdx
vsdx render --page PAGE_ID --output PAGE.svg MAP.vsdx
vsdx view --no-open MAP.vsdx
```

`create`, `apply`, and `swimlane add` are save-as operations. Give each output a
new path. The viewer is read-only, binds to `127.0.0.1`, and remains running
while the page is open; run it in a long-lived terminal session. Use `render`
for noninteractive QA and durable previews.

## Semantic IDs

VSDX Guard stores stable IDs in `User.VSDXGuardID.Value`. Use prefixes such as:

- `page:`
- `lane:<lane>:band` and `lane:<lane>:label`
- `node:`
- `edge:`

Preserve IDs across spec revisions. A connector recreated manually in Visio
can remain glued while losing its ID, so check identity and glue separately.

## Connector proof

For a generated dynamic connector, require:

- one one-dimensional connector shape;
- exactly two page-level `Connect` rows;
- paired `BeginX`/`BeginY` and `EndX`/`EndY` point formulas;
- formulas targeting the intended connection points;
- destination-only arrow styling when that is the map convention.

VSDX XML connection rows are zero-based while ShapeSheet formula names are
one-based. Keep XML row indices, `Connections.Xn/Yn`, `FromPart`/`ToPart`,
triggers, and both coordinate axes coherent. Generated-fixture tests alone do
not prove that a moved shape stays glued in Visio.

## Edit round trips

Treat a user-edited VSDX as review evidence:

1. Compare it with the generated baseline.
2. Identify intentional copy, geometry, ownership, and routing changes.
3. Update the canonical Diagram Spec.
4. Regenerate a fresh VSDX with stable IDs and clean page bounds.

Use `plan set-cell` and `apply` for targeted save-as changes when they preserve
the spec contract. Keep raw OOXML inspection for diagnosis and proof.

## Visio evidence boundary

A build-level authenticated product gate proves that the generator has passed
representative browser interactions. It does not prove that a new project
artifact was opened, edited, saved, and reloaded. Label these separately:

- local structural proof;
- build-level Visio product gate;
- artifact-specific Visio web proof.

Obtain approval before uploading a project artifact to Microsoft or another
external service.
