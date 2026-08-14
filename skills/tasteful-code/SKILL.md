---
name: tasteful-code
description: Tasteful code for implementations, refactors, and reviews. Use when a user asks for readable, maintainable, idiomatic, proportionate, or less over-engineered code; load the TypeScript appendix only for TypeScript type or API work.
---

# Tasteful Code

Use **proportionate** as the governing test: make the smallest design that clearly expresses the domain, its contract, and its important constraints. Optimize for a capable maintainer reading without the author's context.

## 1. Orient

Read the target code, its callers, nearby tests, and project instructions before editing. Identify the behavior, module boundary, invariants, failure paths, local conventions, and smallest relevant validation command.

**Complete when:** state the intended design in one sentence and can name the behavior that will prove it.

## 2. Shape the change

Implement one coherent change.

- Express domain decisions directly and keep normal control flow visible.
- Choose names for domain concepts, operations, and propositions; reuse the codebase's vocabulary.
- Make meaningful alternatives, required data, ownership, side effects, and expected failures explicit in the type or API contract.
- Keep validation and I/O at boundaries; keep trusted domain logic narrow.
- Extract only a concept, invariant, or present variation point that deserves an independent name.
- Follow the repository's architecture and ecosystem conventions.

**Complete when:** every new abstraction has a purpose a reader can name without opening its implementation.

## 3. Prove the contract

Add or update the smallest test that demonstrates the changed observable behavior. Include a meaningful boundary or expected-failure case when the change creates one. Apply the formatter and relevant static checks.

**Complete when:** the test would fail for a credible regression, and validation is passing or any unavailable check is explicitly reported.

## 4. Review for proportion

Read the diff as a context-poor reviewer. Confirm each question has a satisfactory answer:

- Is this the smallest coherent diff for the stated problem?
- Can a reader identify the purpose, invariant, happy path, state changes, failure path, and resource ownership?
- Do names and types communicate the domain and make important invalid states hard to represent?
- Are mutation, I/O, ordering, retries, material cost, and errors predictable to callers?
- Does each comment preserve rationale, a constraint, or a surprising contract that code alone cannot convey?
- Does the diff keep behavior changes, refactors, and mechanical formatting easy to distinguish?

**Complete when:** every modified line contributes to behavior, an explicit contract, or necessary clarity.

## Contextual judgment

Defer function size, file size, line length, return count, DRY, dependency injection, functional versus object-oriented design, comment density, and formatting to the local codebase. Favor local clarity over pattern compliance. Surface genuine architectural choices for a user decision rather than imposing a personal preference.

## Language appendices

- For TypeScript types, unions, or API design, read [references/typescript.md](references/typescript.md).
- For Effect.ts, load `/effect`.

## Review-only requests

Report material findings only. Tie every finding to correctness, comprehension, maintainability, or an observable contract. A locally clear and consistent choice needs no stylistic correction.
