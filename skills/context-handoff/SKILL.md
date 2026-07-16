---
name: context-handoff
description: Preserve the exact state of substantial AI or development work so a future agent can continue without reconstructing the conversation. Use when ending, pausing, switching agents, compacting context, recording a major milestone, or when the user says to remember or hand off ongoing work; do not use as a generic research note.
---

# Context Handoff

Use `70 AI Sessions/YYYY/MM/<timestamp>-<slug>/index.md` for session-level
records. For ongoing projects, also update the project's `hot.md` and append to
`log.md`.

## Required handoff

Capture:

1. concrete goal and success criteria
2. current state and work completed
3. decisions already made and rejected alternatives
4. evidence, source locations, and important file paths
5. commands or tests that were actually run and their results
6. artifacts produced
7. unresolved questions, risks, and blockers
8. exact next action
9. agent/model/provider and task identifier when known
10. repository, branch, commit, and working directory when relevant

Prefer durable facts over a conversational summary. Quote exact error text or
commands only when the exact form matters. Mark memory-derived or inferred
details explicitly. Never store credentials or confidential work content.

