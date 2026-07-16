---
name: research-ingest
description: Preserve AI-assisted, web, document, or code research in the Second Brain with durable sources, evidence, claims, confidence, contradictions, and context. Use when research findings or source material must remain recoverable across future agent sessions; do not use for a quick unsourced capture or an adversarial investigation case.
---

# Research Ingest

Store the packet beneath `40 Research/<topic>/` and reusable source records
beneath `60 Sources/`.

## Packet contract

```text
index.md
hot.md
log.md
Sources/
Evidence/
Claims/
Entities/
Hypotheses/
Timeline/
Outputs/
```

Create only directories the work needs.

## Workflow

1. State the research question and intended audience in `index.md`.
2. Preserve each source's URL, author, publication date, access date, capture
   method, verification state, and limitations. Do not silently rewrite a raw
   capture.
3. Separate source fact, observation, inference, recommendation, and open
   question.
4. Link evidence to the claim it supports or challenges. Record contradicting
   evidence beside supporting evidence.
5. Set `confidence` to `low`, `medium`, or `high` and explain why. Set
   `verified: true` only after direct corroboration.
6. Keep `hot.md` bounded to the context a new agent needs now. Append material
   work to `log.md` with a timestamp.
7. Save polished output under `Outputs/<slug>/index.md`. Use `mdx-publish` only
   when a restricted MDX/static HTML presentation is explicitly useful.

Never treat generated prose as a source. Cite the underlying evidence.

