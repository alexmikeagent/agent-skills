---
name: tasteful-html-artifacts
description: Transform PRDs, Markdown, project plans, architecture documents, research, reviews, status reports, and other substantial written material into distinctive, polished, self-contained HTML artifacts. Use whenever a document would benefit from visual hierarchy, spatial layout, diagrams, navigation, comparison views, progressive disclosure, lightweight interaction, or a purpose-built reading interface rather than plain Markdown. Also use when the user asks for a beautiful HTML report, interactive spec, visual plan, executive brief, project portal, document microsite, or “HTML instead of Markdown.”
---

# Tasteful HTML Artifacts

Create a purpose-built reading interface, not a decorated Markdown dump.

## Operating principle

Treat the source document as raw material. Preserve its meaning, evidence, decisions, uncertainty, and actionable details while redesigning how a human understands and navigates it.

The output should feel authored for this exact subject. Avoid generic dashboard styling, arbitrary cards, purple gradients, excessive pills, uniform rounded rectangles, and ornamental metrics.

## Workflow

1. Inspect all source material before choosing a layout.
2. Identify:
   - audience
   - artifact's single primary job
   - content type and hierarchy
   - decisions, risks, dependencies, evidence, and open questions
   - what benefits from spatial or interactive representation
3. Choose an artifact pattern from `references/artifact-patterns.md`.
4. Choose one explicit visual direction using `references/design-taste.md`.
5. Build an information architecture using `references/content-architecture.md`.
6. Implement a self-contained HTML file.
7. Run the checks in `references/quality-gates.md`.
8. Use `scripts/validate_artifact.py` when available.
9. Deliver the HTML file and briefly state the chosen concept.

## Read references selectively

- Read `references/artifact-patterns.md` when selecting the overall interface.
- Read `references/design-taste.md` before making visual choices.
- Read `references/content-architecture.md` for long or complex documents.
- Read `references/interaction-and-diagrams.md` when interaction, SVG, timelines, dependency maps, or editable controls would improve comprehension.
- Read `references/quality-gates.md` before finalizing every artifact.

## Output contract

Default to one portable `.html` file with CSS and, only when useful, small
vanilla JavaScript inline. Use only locally installed tools. Do not add a build
step or third-party runtime dependency unless the user explicitly asks for it.

The file must:
- work by opening it locally in a modern browser
- remain useful with JavaScript disabled whenever practical
- preserve source fidelity and clearly label inference or synthesis
- be responsive from narrow mobile widths through desktop
- support keyboard navigation and visible focus
- respect `prefers-reduced-motion`
- print cleanly
- use semantic HTML
- include no external dependency unless the task specifically benefits and the user permits it

## Design brief

Before coding, silently commit to:
- **Subject:** the concrete thing this artifact is about
- **Audience:** the person making or validating decisions
- **Job:** the one thing the artifact must make easier
- **Visual thesis:** a one-sentence design concept rooted in the subject
- **Aesthetic risk:** one deliberate, defensible choice
- **Restraint:** one common visual device you will intentionally avoid

Do not expose this planning unless useful to the user.

## Content transformation rules

- Do not force every paragraph into a card.
- Convert structure only when the representation improves understanding.
- Use tables for exact comparison, not as default layout.
- Use diagrams for relationships, flow, sequence, ownership, or system boundaries.
- Use callouts only for genuinely high-salience material.
- Keep important caveats near the claim they qualify.
- Preserve identifiers, acceptance criteria, dates, owners, and source references exactly.
- Distinguish source facts, interpretation, recommendation, and unresolved questions.
- Prefer progressive disclosure for secondary detail, never for critical risks or decisions.
- When the source is incomplete, design around the gaps instead of inventing content.

## Visual rules

- Typography should carry hierarchy and personality.
- Use a restrained type scale and line length suitable for reading.
- Derive colors and motifs from the subject, organization, or content semantics.
- Structural devices must encode meaning.
- Whitespace should clarify grouping, not merely make the page look expensive.
- Do not create a large empty first-screen band with viewport-height heroes or bottom-aligned content; the thesis and primary decision should begin promptly.
- Long filenames, workflow identifiers, URLs, and inline code must wrap inside their container. Give grid and flex children `min-width: 0` where needed.
- Use borders, shadows, radii, and gradients sparingly and consistently.
- Choose a small token system and use it throughout.
- Make one area memorable; keep the rest disciplined.
- Never use visual novelty at the expense of scanability.

## Interaction rules

Add interaction only when it reduces cognitive work:
- filtering a requirements matrix
- switching stakeholder views
- expanding implementation detail
- highlighting dependencies
- toggling current versus proposed state
- copying structured snippets
- navigating long material
- annotating or editing a small purpose-built subset

Avoid interaction that merely animates or hides content.

For long desktop documents, make a persistent sidebar collapsible when it materially compresses the reading or diagram area. The control must be a labeled button, expose expanded state with ARIA, remain keyboard-operable, and leave a visible way to reopen the navigation.

## Common artifact modes

### PRD or product specification
Prioritize problem framing, users, scope boundaries, requirements, flows, success metrics, dependencies, risks, decisions, and unresolved questions.

### Architecture or technical design
Prioritize system boundaries, component responsibilities, data flow, interfaces, constraints, tradeoffs, failure modes, rollout, observability, and security.

### Project plan
Prioritize outcomes, workstreams, milestones, owners, dependencies, critical path, risks, and decision points.

### Research synthesis
Prioritize thesis, evidence quality, findings, tensions, confidence, implications, and sources.

### Status or executive update
Prioritize current state, movement since last update, decisions needed, risks, asks, and next milestones.

## Anti-patterns

Reject and revise artifacts that:
- resemble a generic SaaS dashboard without a reason
- repeat the source document in a single centered column with cosmetic CSS
- contain many same-sized cards with no hierarchy
- use fake statistics or invented data for visual balance
- hide essential information behind hover
- use tiny text, weak contrast, or excessive animation
- include decorative charts whose encoding does not match the data
- depend on a CDN for basic rendering
- optimize screenshots while harming actual reading
- lose content or nuance during transformation

## Completion standard

A finished artifact should let a reader:
1. understand the document's thesis within seconds
2. locate decisions, risks, and open questions quickly
3. inspect supporting detail without losing context
4. distinguish fact from interpretation
5. navigate comfortably on desktop and mobile
6. print or share the file without repair

When these goals conflict, prioritize truth, comprehension, and usability over visual spectacle.
