# Quality Gates

Run every gate before delivery.

## 1. Fidelity
- All material decisions, risks, dates, owners, requirements, and caveats are preserved.
- No facts, metrics, or commitments were invented.
- Inference is labeled.
- Contradictions and gaps remain visible.

## 2. Information architecture
- The first viewport explains purpose and current conclusion.
- The first viewport does not waste a large upper band on empty hero space. Check viewport-height minimums and bottom alignment at both short and tall desktop sizes.
- The hierarchy reflects meaning rather than the source file's formatting accidents.
- Important material is easy to find.
- Secondary detail does not overwhelm the main path.
- Long content has effective navigation.

## 3. Visual quality
- The artifact has a subject-specific visual thesis.
- Typography has a deliberate scale and readable measure.
- Color is restrained and semantic.
- Spacing and alignment create clear grouping.
- Cards, pills, gradients, shadows, and radii are justified.
- At least one memorable choice exists without harming usability.
- The result does not resemble generic AI-generated SaaS UI.

## 4. Interaction
- Every interaction reduces cognitive work.
- Controls work by keyboard.
- Focus is visible.
- Nothing critical depends on hover.
- Reduced-motion preferences are respected.
- Core content remains accessible without JavaScript where practical.

## 5. Accessibility
- Semantic landmarks are present.
- Heading levels are logical.
- Contrast is sufficient.
- Form controls have labels.
- SVGs have accessible names or nearby textual descriptions.
- Color is not the only carrier of meaning.
- Touch targets are usable.
- Long filenames, code identifiers, URLs, and machine labels wrap without escaping cards, columns, or callouts.
- SVG text remains legible over every fill color after the full CSS cascade is applied; explicitly test inverse labels on dark shapes.

## 6. Responsiveness
Check approximately:
- 360px
- 768px
- 1280px
- wide desktop

No horizontal scrolling except intentionally scrollable data tables or code.

- Grid and flex children use `min-width: 0` where long content could force overflow.
- Responsive SVGs fit their content column through `viewBox`; do not impose a forced `min-width` unless the diagram is intentionally scrollable and labeled as such.
- At 1024–1280px, a persistent sidebar must not starve the primary content or diagram. Make it collapsible when it materially reduces usable canvas, and verify both expanded and collapsed states.

## 7. Portability and security
- The HTML opens locally.
- Essential assets are inline.
- No untrusted script injection.
- Source text is escaped when inserted programmatically.
- External dependencies are absent or explicitly justified.
- No secrets, local paths, or private metadata leak into the file.

## 8. Print
- Page prints legibly.
- Navigation and interactive-only controls are hidden.
- Background-dependent text remains readable.
- Important sections are not clipped.
- URLs or source labels remain understandable.

## 9. Technical validation
- Valid document structure.
- No console errors.
- Anchor links work.
- Buttons and filters work.
- CSS variables are defined.
- No placeholder text remains.
- Title and metadata are meaningful.

## 10. Final editorial pass
- Remove repetition.
- Tighten labels.
- Replace vague headings.
- Put caveats beside claims.
- Verify terminology is consistent.
- Remove any visual element that does not earn its space.
