# Interaction and Diagrams

Use interaction as a comprehension tool.

## Useful interactions

- section-aware navigation
- filters for requirements, risks, owners, or severity
- current/proposed-state toggle
- stakeholder-view toggle
- expandable implementation details
- copy buttons for commands, schemas, or acceptance criteria
- synchronized hover/focus across a diagram and its legend
- lightweight editable fields when the artifact is explicitly a workbench
- print and compact-view controls

## Interaction constraints

- all controls must be keyboard reachable
- use real buttons and links
- expose state through text or ARIA, not color alone
- preserve useful content when scripts fail
- do not require hover
- avoid custom scrolling
- avoid auto-playing animation
- persist state only when it helps and does not expose sensitive data

## Inline SVG diagrams

Use SVG for:
- system context
- component relationships
- data flows
- sequences
- dependency maps
- capability maps
- timelines

Requirements:
- include a title and description
- use readable labels
- keep line crossings low
- use consistent arrow semantics
- provide a textual summary nearby
- scale through `viewBox`
- ensure focus/hover is supplementary, not required
- avoid rasterizing text

## Diagram selection

- boxes and arrows: architecture and flow
- sequence lanes: ordered interaction among actors
- swimlanes: ownership and handoff
- dependency graph: prerequisites and blockers
- state machine: valid states and transitions
- matrix: responsibility or coverage
- timeline: chronological milestones
- layered stack: abstraction or platform layers

## Avoid diagram theater

A diagram is not useful merely because it looks technical. It must answer a question that prose or a table answers less effectively.
