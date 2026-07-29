# Convergence Quality Gates

Run these gates after the creative direction is implemented. They protect
truth, comprehension, and usability; they do not prescribe a palette, layout,
or house style. Preserve the committed visual thesis while repairing defects.

## Contents

- [Bounded inspection protocol](#bounded-inspection-protocol)
- Gates 1–3: source reconciliation, critique, and orientation
- Gates 4–6: visual craft, accessibility, and responsive structure
- Gates 7–10: portability, print, technical validation, and editorial finish

## Bounded inspection protocol

1. Render one batched evidence pass with the real content at:
   - 320px
   - 375px
   - 768px
   - 1280 × 800px
   - 1600px or the widest supported desktop
   - print preview or PDF
2. In the same pass, test keyboard navigation, core controls, anchor links,
   browser console, and the useful no-script state.
3. Record defects across the whole artifact before editing. Triage in this
   order: fidelity, blocked reading or interaction, accessibility, responsive
   structure, hierarchy, visual finish.
4. Fix the observed set in one batch, then run one confirmation pass. Continue
   only for a remaining gate failure, not open-ended polishing.

## 1. Source reconciliation

- Every material decision, requirement, risk, date, owner, identifier, caveat,
  and citation from the source ledger is present or explicitly omitted with a
  reason.
- Facts, interpretation, recommendations, and unresolved questions are visibly
  distinct.
- Inference is labeled beside the inferred claim.
- Contradictions and gaps remain visible.
- Quantitative claims, testimonials, commitments, and status values come from
  supplied evidence; illustrative values are labeled as such.

## 2. Pre-emit critique

Score the rendered artifact from 1–5 on each axis. Any score below 3 triggers a
revision before the remaining gates.

| Axis | Question |
| --- | --- |
| Thesis | Does the form take a clear position on what matters? |
| Hierarchy | Can the reader identify primary, secondary, and tertiary material within seconds? |
| Specificity | Does the artifact look and behave as though it belongs to this subject and reader job? |
| Coherence | Do composition, type, palette, surface, diagrams, and motion belong to one visual world? |
| Restraint | Does every high-salience device earn its space? |
| Finish | Are wrapping, alignment, contrast, states, focus, and details resolved? |

Keep the score in work notes unless sharing it helps the user. It is a revision
trigger, not decoration for the artifact.

## 3. Orientation and information architecture

- The first viewport answers: what is this, why does it matter, what is the
  current conclusion or state, and what should the reader do?
- At 1280 × 800px, the opening reads as a complete composition rather than an
  oversized headline or empty hero cut off by the fold.
- The hierarchy reflects meaning instead of the source file's formatting
  accidents.
- The squint test reveals the primary element, secondary element, and major
  groups in the intended order.
- Critical decisions, risks, and actions remain on the primary path.
- Secondary detail is discoverable without overwhelming the main path.
- Navigation matches lookup behavior. A side rail, when present, provides
  repeated orientation or cross-reference value that an inline index would not.

## 4. Visual craft

- The fingerprint is traceable to the source, brand, audience, or use setting.
- The result is structurally distinct from unrelated adjacent artifacts unless
  continuity is intentional.
- Typography has clear roles, a comfortable 45–75ch prose measure, and an
  ordinary body floor of 1rem/16px.
- Actual long headings, identifiers, URLs, and dense rows wrap without
  collision or clipping.
- Color tokens have explicit jobs. Body text meets at least 4.5:1 contrast;
  large text, icons, and focus indicators meet at least 3:1 against their
  computed backgrounds.
- Color is not the only carrier of status or meaning.
- Proximity establishes grouping before borders or cards.
- Tight and generous spacing create deliberate rhythm rather than one repeated
  interval.
- Equivalent items look equivalent; priority changes have a visible reason.
- Border, shadow, radius, gradient, texture, and accent footprint are coherent
  with the chosen visual thesis.
- Imagery, diagrams, and motifs carry evidence, explanation, orientation, or
  identity rather than filling space.

## 5. Interaction and accessibility

- Semantic landmarks are present and heading levels are logical.
- A keyboard user can reach every control in a sensible order and always see
  focus.
- Controls have accessible names and expose state through text or ARIA.
- Nothing critical depends on hover.
- Interactive states cover the states the artifact can actually enter:
  default, hover, focus, active, disabled, loading, empty, error, or success as
  applicable.
- Touch targets remain usable at narrow widths.
- SVGs have an accessible name or are explicitly decorative, and a textual
  equivalent is nearby for substantive diagrams.
- Motion is purposeful, interruptible where needed, and covered by
  `prefers-reduced-motion`.
- Core content remains useful when JavaScript fails or is disabled.

## 6. Responsive structure

- No unintended horizontal document scrolling occurs from 320px through wide
  desktop. Deliberately scrollable tables or code regions are labeled and
  contained.
- Grid and flex children use `min-width: 0` where long content could force
  overflow.
- Image-bearing fractional grid tracks use `minmax(0, 1fr)` where intrinsic
  width could escape the viewport.
- Display headings, identifiers, URLs, and code use an appropriate last-resort
  wrap strategy.
- Responsive SVGs use `viewBox` and fit their content column unless an
  intentional, labeled pan/scroll treatment is part of the concept.
- DOM order, visual order, and keyboard order remain coherent when columns
  collapse or reorder.
- At 1024–1280px, persistent navigation does not starve the reading or diagram
  canvas. Verify expanded and collapsed states when a collapsible rail exists.
- Sticky elements account for other sticky headers and never overlap content.

## 7. Portability and security

- The HTML opens locally without a build step.
- Essential assets are inline; every external dependency is authorized and
  justified.
- Source text inserted through JavaScript is escaped or assigned with safe text
  APIs.
- Links that open a new browsing context use safe `rel` values.
- No secret, credential, private metadata, unresolved local path, or internal
  environment detail appears in the file.
- CSS custom properties used without fallbacks are defined.

## 8. Print

- Navigation and interactive-only controls are hidden or simplified.
- Text remains readable without background fills.
- Important sections, diagrams, tables, and callouts are not clipped.
- Page breaks avoid separating a heading from the content it introduces where
  practical.
- URLs, citations, and source labels remain understandable on paper.

## 9. Technical validation

- `scripts/validate_artifact.py` reports no errors.
- Every validator warning is fixed or explicitly justified.
- The document has a meaningful title, language, viewport, one main landmark,
  and a logical heading outline.
- IDs are unique; internal links and ARIA references resolve.
- Buttons, filters, toggles, copy actions, and disclosures work.
- The browser console has no errors.
- No placeholder or template text remains.

## 10. Final editorial pass

- Remove repeated claims and decorative labels.
- Tighten vague headings and control labels.
- Place caveats beside the claims they qualify.
- Verify terminology, capitalization, identifiers, and date formatting.
- Remove every visual or interactive element that does not earn its space.

The artifact is complete when every applicable gate passes and the confirmation
pass finds no unaccounted defect.
