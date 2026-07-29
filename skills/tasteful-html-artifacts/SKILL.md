---
name: tasteful-html-artifacts
description: Transform substantial written material into source-faithful, self-contained HTML reading interfaces. Use for PRDs and specifications, architecture documents, project plans, research, reviews or audits, and status or executive reports when visual hierarchy, diagrams, navigation, comparison, or lightweight interaction would improve comprehension; also use when the user asks for a polished HTML report, document microsite, project portal, or HTML instead of Markdown.
---

# Tasteful HTML Artifacts

Build a source-faithful reading interface with a subject-specific
**fingerprint**. Treat the source as material to clarify, not prose to decorate.
The pattern, navigation, palette, typography, density, and interaction must
answer the brief. Quality gates are a usability floor, not a house style.

## Decision policy

- The user's pinned aesthetic, brand system, supplied assets, and source truth
  outrank this skill's defaults.
- Infer ordinary design choices and commit without asking the user to art-direct
  every token. Ask only when a choice changes meaning, scope, or brand identity.
- Vary by context, not novelty. Different subjects or reader jobs should produce
  different fingerprints; related artifacts inside one design system may share
  a visual language deliberately.
- Protect the committed concept during QA. Repair fidelity, hierarchy,
  accessibility, responsiveness, and finish without sanding every artifact into
  the same safe layout.

## Workflow: diverge, commit, converge

1. **Map the source.** Inspect every supplied source before choosing a form.
   Build an internal ledger of the thesis, audience, facts, identifiers,
   decisions, requirements, owners, dates, risks, caveats, evidence, open
   questions, contradictions, and gaps. Complete when every material item has a
   planned destination or an explicit reason to omit it.

2. **Diverge on form.** Read
   [`references/artifact-patterns.md`](references/artifact-patterns.md) and
   [`references/design-taste.md`](references/design-taste.md). Generate two or
   three materially different directions internally. Vary at least three
   fingerprint axes: composition, navigation, typography, palette,
   surface/density, diagram language, or interaction. Complete when the
   candidates differ structurally, not merely by color.

3. **Commit to one brief.** Choose the direction that best serves the audience
   and primary reader job. Silently record: subject, audience, job, pattern,
   visual thesis, fingerprint, aesthetic risk, and restraint. Complete when one
   sentence connects the subject to the form and every high-salience design
   choice has a content, brand, or use-context rationale.

4. **Architect the reading path.** For long or complex material, read
   [`references/content-architecture.md`](references/content-architecture.md).
   Decide what the first viewport answers, the section order, the best
   representation for each block, the navigation model, and what may be
   disclosed progressively. A side rail earns its place only when persistent
   lookup or cross-reference value outweighs the canvas it consumes. Complete
   when every major block improves orientation, reasoning, traceability, or
   action, and critical decisions and risks remain visible.

5. **Build the portable artifact.** Default to one HTML file with inline CSS and
   only useful vanilla JavaScript. Use
   [`assets/starter.html`](assets/starter.html) only for portability and
   accessibility scaffolding; replace its composition, tokens, and content.
   When controls, diagrams, timelines, or editable views reduce cognitive work,
   read
   [`references/interaction-and-diagrams.md`](references/interaction-and-diagrams.md).
   Complete when the file opens locally, the core reading path survives with
   JavaScript disabled, and all controls use semantic elements.

6. **Reconcile fidelity.** Compare the built artifact with the source ledger.
   Locate every material fact, decision, risk, requirement, caveat, and source
   reference in the artifact. Complete when nothing material is lost, invented,
   or silently reclassified, and synthesis or inference is labeled at the point
   where it appears.

7. **Converge with bounded QA.** Only after the creative direction is
   implemented, read
   [`references/quality-gates.md`](references/quality-gates.md) and run
   `scripts/validate_artifact.py`. Inspect desktop, mobile, keyboard, no-script,
   and print behavior in one batched pass; fix all observed defects together,
   then run one confirmation pass. Complete when the validator has no errors,
   every warning is fixed or explicitly justified, and every applicable quality
   gate passes with the real content.

8. **Deliver.** Provide the HTML file, name the chosen concept and the most
   important transformations, report validation performed, and disclose any
   remaining limitation. Complete when the user can open the file directly and
   understand what was preserved, transformed, and verified.

## Output contract

The artifact must:

- open locally in a modern browser without a build step
- preserve exact source identifiers, dates, owners, acceptance criteria, and
  citations where they matter
- distinguish source fact, interpretation, recommendation, and unresolved
  question
- use semantic HTML, keyboard-operable controls, visible focus, and useful
  no-script content
- respond from narrow mobile widths through wide desktop, respect
  `prefers-reduced-motion`, and print legibly
- use a small semantic token system for color, type, spacing, shape, and motion
- keep essential assets inline and include external dependencies only when the
  task benefits, the user permits them, and the artifact remains shareable
- exclude secrets, private metadata, unresolved local paths, and unsafe source
  injection

## Transformation invariants

- Preserve nuance before compressing. Keep caveats beside the claims they
  qualify.
- Use prose for argument, tables for exact comparison, and diagrams for
  relationships, flow, sequence, ownership, or boundaries.
- Let proximity and hierarchy group content before adding containers.
- Keep secondary detail discoverable through progressive disclosure; keep
  decisions, critical risks, and required actions in the primary path.
- Represent gaps honestly with unknowns, questions, or empty states instead of
  fabricated metrics, dates, owners, testimonials, or commitments.
- Make one area memorable and keep the rest disciplined.

When goals conflict, prioritize truth, comprehension, and usability while
preserving the chosen visual thesis.
