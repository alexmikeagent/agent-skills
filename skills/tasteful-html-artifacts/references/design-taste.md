# Design Taste

Taste comes from contextual judgment, a clear point of view, and disciplined
editing. Set the direction before applying the craft floor. The brief wins:
quality rules may repair a concept, but they should not choose one by habit.

## Contents

- [Diverge before committing](#diverge-before-committing)
- [Commit a fingerprint](#commit-a-fingerprint)
- [Use contextual evidence](#use-contextual-evidence)
- [Palette as a contextual system](#palette-as-a-contextual-system)
- [Typography carries the voice](#typography-carries-the-voice)
- [Layout expresses priority](#layout-expresses-priority)
- [Imagery, diagrams, and motifs](#imagery-diagrams-and-motifs)
- [Motion and interaction](#motion-and-interaction)
- [Aesthetic risk and restraint](#aesthetic-risk-and-restraint)
- [Contextual variation check](#contextual-variation-check)

## Diverge before committing

Generate two or three directions internally before writing markup. Make them
materially different on at least three axes:

- composition and section rhythm
- navigation model
- typography roles
- palette temperature, lightness, and chroma
- density and surface treatment
- diagram, evidence, or imagery language
- interaction and motion

A palette swap is not a new direction. One candidate may use a named artifact
pattern, another may combine two, and another may be custom. Choose the
direction whose form best explains the source and supports the primary reader
job.

When an established brand or design system exists, diverge inside its
constraints: change composition, density, evidence treatment, or interaction
without inventing a second identity.

## Commit a fingerprint

Write one internal sentence that links the subject to the form:

> A [subject] artifact for [audience], shaped as [composition] so they can
> [reader job], using [visual language] to make [specific relationship] clear.

Then commit the fingerprint:

| Axis | Decision |
| --- | --- |
| Composition | dominant reading path, section rhythm, wide versus narrow moments |
| Navigation | none, inline index, top bar, side rail, filters, or another source-shaped model |
| Typography | role contrast, families, measure, density, and numerical/code treatment |
| Palette | canvas band, temperature, chroma, accent role, and semantic colors |
| Surface | flat, ruled, layered, tactile, archival, instrument-like, or another justified treatment |
| Visual language | diagrams, marginalia, annotations, imagery, rules, or subject motifs |
| Motion | none, one authored moment, or a small set of comprehension-driven transitions |

The fingerprint is coherent when the choices feel like one world rather than a
collection of fashionable parts.

## Use contextual evidence

Choose in this order:

1. explicit user direction and existing brand or design tokens
2. supplied assets, source material, and organization conventions
3. the subject's real materials, language, data, and operating environment
4. the reader's setting, task, urgency, and expected density
5. autonomous judgment when the earlier signals leave an axis open

Resolve open axes through informed design judgment. Reserve questions for
choices that change meaning, scope, or brand identity. State the final concept
at handoff so the choice remains easy to redirect.

## Palette as a contextual system

Treat every palette family as available. Warm paper, cool white, monochrome,
dark, saturated, muted, and restrained gradients can all be right when the
subject and use setting earn them.

Before choosing values, decide:

- **Canvas band:** light, mid-tone, dark, or mixed by section
- **Temperature:** warm, neutral, cool, or intentionally split
- **Chroma:** quiet, moderate, or vivid
- **Accent job:** action, status, evidence, annotation, or focal punctuation
- **Semantic set:** success, warning, danger, information, and unknown

Sample at least one palette outside the first habitual choice when no brand
palette is binding. Select by fit, not novelty. Large gradients, broad accent
fields, and tinted surfaces need a structural or semantic job; accent is
punctuation unless the color field itself is the concept.

Declare a small semantic token system. Verify text, icon, rule, focus, and
status contrast against their computed surfaces. Pair color with text, shape,
position, or pattern whenever it carries meaning.

## Typography carries the voice

- Define roles before sizes: display, section, body, label, metadata, data, and
  code only when each role is needed.
- Use the fewest families that make the hierarchy unmistakable. A single
  well-tuned family or a deliberate pairing can both be right.
- Prefer local or system fonts for portable artifacts. Use an external or
  embedded face only when the brief and delivery constraints justify it.
- Keep ordinary body text at least 1rem/16px and long-form measure around
  45–75 characters.
- Tune line height to the face, measure, language, contrast, and density.
- Reserve monospace for code, identifiers, measurements, or machine-oriented
  labels.
- Test the actual longest headings, identifiers, URLs, and localized-looking
  strings at every relevant width.

Hierarchy should remain obvious when the words are unreadable: scale, weight,
space, and tone must establish roles before the copy does.

## Layout expresses priority

- Establish one dominant reading path.
- Group by proximity before adding a container.
- Create rhythm through contrast between tight related groups and generous
  separation between distinct ideas.
- Let symmetry communicate stability and comparison; let asymmetry communicate
  hierarchy, sequence, or editorial energy.
- Give equivalent items equivalent treatment. Change span, weight, or placement
  when content or priority changes.
- Use section labels only when they encode taxonomy, status, sequence, or
  provenance. Let headings carry hierarchy otherwise.
- Use cards for self-contained or comparable units, not as a wrapper for every
  paragraph.
- Choose one elevation channel for a surface: border, shadow, or color
  separation. Layer channels only when actual depth or overlay state requires
  it.
- Let whitespace clarify relationships rather than repeat one padding value
  everywhere.

Apply the squint test: with detail blurred, the primary element, secondary
element, and major groups should still appear in the intended order.

## Imagery, diagrams, and motifs

Prefer real source imagery, diagrams derived from actual relationships, and
small motifs tied to the subject. A visual earns its place by carrying evidence,
orientation, explanation, or identity.

Use real screenshots in a `<figure>` when the interface itself is evidence.
Present code or commands directly when they are the evidence. Hand-built fake
browser, phone, terminal, or IDE chrome creates a second interface that the
reader must decode and should be replaced with the real capture or omitted.

Keep one visual language across diagrams: consistent line weight, arrow
semantics, label placement, and color roles. Provide a textual equivalent.

## Motion and interaction

Use interaction to reduce cognitive work and motion to explain change. One
authored moment is stronger than repeated entrance effects. Keep the useful
default state visible, make controls work without hover, and provide a
reduced-motion path that preserves the information.

## Aesthetic risk and restraint

Take one controlled risk: an unusual but readable composition, a
subject-specific navigation model, a distinctive diagram language, a strong
type treatment, a carefully bounded color field, or a small purpose-built
tool. Pair it with one explicit restraint so the risk remains legible.

## Contextual variation check

Before convergence, ask:

- Could this exact fingerprint fit an unrelated subject with only the nouns
  changed?
- Which choices came from the source, brand, reader job, or use setting?
- Did a sidebar, beige canvas, giant headline, card grid, or familiar type
  pairing appear because it fits, or because it was available?
- If adjacent artifacts are visible, what remains consistent by design and what
  changes because the job changed?
- Is the memorable choice still useful in grayscale, without motion, and at a
  narrow width?

If the first answer is yes or the third has no contextual rationale, revisit the
direction before polishing it.
