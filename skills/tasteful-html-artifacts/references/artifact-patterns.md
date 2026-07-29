# Artifact Patterns

Choose the pattern that best matches the reader's job. Patterns are starting
shapes, not templates: they do not prescribe a palette, type system, navigation
model, or component vocabulary. Combine at most two primary patterns unless the
material truly demands more. Define a custom composition when none fits.

## Contents

- Patterns 1–5: editorial brief through project command map
- Patterns 6–10: comparative lens through custom composition
- [Choose navigation independently](#choose-navigation-independently)
- [Define the fingerprint](#define-the-fingerprint)
- [Selection heuristic](#selection-heuristic)

## 1. Editorial brief

Use for executive summaries, research reports, strategy memos, and narrative PRDs.

Structure:
- strong thesis-led opening
- compact metadata or context rail
- narrative sections with pull findings
- evidence or source notes beside relevant claims
- decision and implication section near the end

Visual character:
- editorial typography
- controlled measure
- asymmetric details
- limited but meaningful emphasis

## 2. Decision cockpit

Use when the reader must approve, choose, prioritize, or resolve issues.

Structure:
- decision required
- recommendation
- options with explicit tradeoffs
- evidence and assumptions
- risks
- unresolved questions
- next action

Do not turn this into a generic KPI dashboard. Every visual element must help the decision.

## 3. Specification atlas

Use for long PRDs, platform specs, policy documents, or multi-module plans.

Structure:
- visible table of contents; make it persistent only when repeated lookup
  justifies the lost canvas
- overview map
- sections by capability or domain
- requirement IDs and acceptance criteria
- cross-links among dependencies
- status or confidence labels with a legend
- appendices in collapsible sections

## 4. Architecture field guide

Use for system design, automation architecture, infrastructure, and integration documents.

Structure:
- system context
- component map
- request or data-flow sequence
- component responsibility sheets
- interface contracts
- failure modes
- security and observability
- migration or rollout

Prefer inline SVG for diagrams. Provide a textual equivalent.

## 5. Project command map

Use for delivery plans and cross-functional programs.

Structure:
- outcome and scope
- workstream lanes
- milestone horizon
- dependency map
- ownership
- risk register
- decisions calendar
- immediate next actions

Avoid Gantt charts unless dates and dependencies are sufficiently precise.

## 6. Comparative lens

Use for option evaluation, vendor selection, technical alternatives, or before-and-after analysis.

Structure:
- evaluation criteria
- side-by-side comparison
- meaningful differences
- tradeoff matrix
- recommendation by scenario
- disqualifiers and unknowns

Use synchronized highlighting or filters only when the comparison is large.

## 7. Review workbench

Use for code review, design critique, document review, or audit findings.

Structure:
- review summary
- issue severity and category filters
- annotated excerpts
- rationale
- suggested resolution
- affected areas
- verification checklist

Keep evidence adjacent to each finding.

## 8. Living design reference

Use for design systems, UI inventories, visual language, and reusable patterns.

Structure:
- principles
- tokens
- typography
- components
- states
- examples and counterexamples
- accessibility notes
- usage guidance

The reference itself should embody the system.

## 9. Guided explainer

Use for onboarding, technical concepts, process education, and complex workflows.

Structure:
- orienting mental model
- staged explanation
- diagrams or simulations
- examples
- misconceptions
- practical checklist
- glossary

Interaction can reveal layers, but core understanding must not require clicking everything.

## 10. Custom composition

Use when the source has a distinctive shape that the named patterns would
flatten: an investigative case file, annotated transcript, operational runbook,
visual essay, evidence wall, or another purpose-built form.

Before building, state the custom composition internally in one sentence:

> A [reader job] organized as [dominant spatial model], with [navigation model]
> and [one memorable mechanism].

Borrow individual techniques from the named patterns, but keep one dominant
reading path. Custom means source-shaped, not unstructured.

## Choose navigation independently

Navigation follows lookup behavior, not the chosen pattern's name:

- **No persistent navigation:** short or strongly linear artifacts with roughly
  five or fewer major sections.
- **Inline contents or top index:** medium documents read mostly front to back.
- **Sticky section bar:** a small set of peer sections where quick switching
  matters and labels remain short.
- **Side rail:** lookup-heavy references, atlases, or cross-linked documents
  with enough sections to justify constant orientation. Verify it at
  1024–1280px and make it collapsible when it materially narrows the content.
- **View switcher or filters:** repeated structured items where changing the
  visible slice is the reader's actual task.

Choose a sidebar only under the side-rail criteria above; use the lighter
navigation models for the other reading paths.

## Define the fingerprint

After choosing a pattern, make contextual choices on these independent axes:

- composition and section rhythm
- navigation model
- typography roles and contrast
- palette temperature, lightness, and chroma
- surface treatment and density
- diagram or evidence language
- interaction and motion

If related artifacts from this project or session are visible, compare their
fingerprints. A different reader job should normally change at least two axes;
continuity inside a shared design system is a valid reason not to.

## Selection heuristic

Ask which cognitive task dominates:
- reading and synthesis → editorial brief
- choosing → decision cockpit or comparative lens
- lookup and traceability → specification atlas
- relationship and flow → architecture field guide
- coordination → project command map
- inspection and remediation → review workbench
- reuse and consistency → living design reference
- learning → guided explainer
- none fits without distortion → custom composition
