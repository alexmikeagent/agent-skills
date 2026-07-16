# Content Architecture

The transformation succeeds when structure reflects meaning.

## First-pass extraction

Capture:
- title and purpose
- intended audience
- primary thesis or outcome
- source sections
- decisions
- requirements and acceptance criteria
- metrics
- actors and ownership
- dates and milestones
- dependencies
- risks and mitigations
- assumptions
- open questions
- source citations or references

Do not summarize away exact details that support execution or accountability.

## Design the reading layers

### Layer 1: Orientation
Answer within the first viewport:
- What is this?
- Why does it matter?
- What is the current conclusion or status?
- What should the reader do?

### Layer 2: Navigation and scan
Expose the document's meaningful sections, not merely its original heading list.

### Layer 3: Core reasoning
Present claims, evidence, tradeoffs, requirements, and flows in the representation best suited to each.

### Layer 4: Operational detail
Preserve IDs, implementation notes, criteria, owners, dates, and source excerpts.

### Layer 5: Appendix
Place supplementary detail, glossary, raw references, and secondary history here.

## Re-representation choices

Use:
- prose for argument and nuance
- concise lists for discrete items
- definition lists for term-value relationships
- tables for exact multi-attribute comparison
- timelines for temporal sequence
- swimlanes for actor-based flow
- graphs for dependency or network relationships
- matrices for coverage and responsibility
- callouts for decisions, risks, and constraints
- accordions for secondary detail
- filters for large repeated item sets

Do not use:
- cards for every section
- charts without quantitative data
- timelines for unordered lists
- numbered steps when order is irrelevant
- accordions to hide weak organization

## Source fidelity

When synthesizing multiple documents:
- retain provenance where it matters
- flag contradictions
- show unresolved differences rather than averaging them away
- label inferred connections
- preserve the strongest original wording only when quotation is warranted
- never create missing dates, owners, metrics, or commitments

## Long-document navigation

For artifacts with more than roughly five major sections:
- provide a visible table of contents
- indicate current section
- support anchor links
- add “back to top” or equivalent context-preserving navigation
- enable browser search through real text, not canvas-rendered text

## Density management

Use hierarchy before hiding:
1. improve headings
2. group related content
3. align comparable items
4. reduce repetition
5. move secondary detail to disclosure
6. add filters only when volume requires them

## Traceability

For PRDs and technical documents, keep stable identifiers visible:
- requirement IDs
- decision IDs
- risk IDs
- component names
- milestone labels

Support deep links to important sections when practical.
