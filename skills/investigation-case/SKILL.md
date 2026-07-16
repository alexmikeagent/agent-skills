---
name: investigation-case
description: Build and maintain evidence-led investigative case files in Obsidian, including questions, hypotheses, entities, timelines, claims, contradictions, confidence, and verification gaps. Use for investigative or adversarial research where provenance and proof-versus-inference boundaries matter; do not use for ordinary topic research.
---

# Investigation Case

Create the case beneath `50 Investigations/<case>/` with `index.md`, `hot.md`,
`log.md`, and only the evidence directories the inquiry needs.

## Rules

- Record the exact question, allegation, or anomaly before analysis.
- Assign stable IDs to evidence, claims, entities, hypotheses, and timeline
  events when they will be cross-referenced.
- Keep original evidence immutable or clearly versioned. Store its source,
  capture time, hash when available, and chain-of-custody notes.
- Label every conclusion as proved, supported, plausible, contradicted,
  disproved, or unknown.
- Put corroborating and contradicting evidence side by side.
- Keep people and organizations as neutral entities; do not convert suspicion
  into fact.
- Append actions and state changes to `log.md`. Keep `hot.md` short enough for a
  fresh agent to load without the full case.
- Use JSON Canvas only when relationships or timelines become materially easier
  to inspect visually.

Stop rather than placing employer/client-confidential evidence in this personal
vault. Store only a sanitized reference when permitted.

