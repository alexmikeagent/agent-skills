# Artifact Patterns

Choose the pattern that best matches the document's job. Combine at most two primary patterns unless the material truly demands more.

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
- persistent table of contents
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
