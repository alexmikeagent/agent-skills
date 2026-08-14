---
name: effect
description: Effect v4 design and implementation. Use when writing Effect.ts, Context.Service, Layer, Schema, tagged errors, Effect.gen, Effect.fn, or effect/unstable HTTP, SQL, RPC, Cluster, AI, or Atom.
---

# Effect

Inspect installed `effect`, then design and implement. `/implement` and `/tasteful-code` own the work loop. This skill owns Effect shape. For seam/adapter language, `/codebase-design`.

APIs come from the installed package and its `LLMS.md` / `AGENTS.md`. Shapes here are illustrative — verify constructors against the installed major.

## 1. Inspect

Read the installed `effect` version, nearby imports, and the local tree. Name the import style (barrel vs `import * as Effect from "effect/Effect"`), the error constructor, and where contracts live.

**Complete when:** the major is named, and those three house facts are named. If the major is 3, stop; these constructors are v4.

## 2. Name the contract

State success `A`, expected errors `E`, and required services `R` in one sentence. Expected failures are named domain errors. Construction dependencies belong in Layers, not in method `R`.

**Complete when:** `A`, `E`, and `R` can be said without pointing at a vendor type.

## 3. Design

- Narrow `Context.Service`. Methods are `Effect<A, E, never>`.
- Convert transport and vendor errors at the adapter.
- `Schema` at untrusted edges.
- A machine only when illegal transitions exist.
- Follow the target tree. Colocate service, `static readonly layer`, and tagged errors. The service id is package path plus file path. One composition root at the app edge.

**Complete when:** every new service has a named capability and a single place its live layer will be provided.

## 4. Implement

Match the repo's import style. Write named work with `Effect.fn("Service.method")` and a short `gen` when names clarify the story. `return yield*` on failure. Compose layers, then provide once. Start sequential. Time through `Clock` / `DateTime`. JSON through `Schema`. IDs through branded `make`. Use `Predicate` instead of hand-rolled type guards. Handlers and UI stay thin — decode, call a service, map `_tag`. Re-enter Effect at JS/callback edges through a captured runtime, not a global. Process entry is `NodeRuntime.runMain`, `BunRuntime.runMain`, `Layer.launch`, or `ManagedRuntime`.

**Complete when:** the program type shows the intended `A`, `E`, and `R`.

## 5. Prove

Test through the service interface or a test layer. Prefer `@effect/vitest` when the repo has it. Run `@effect/tsgo` diagnostics when they are installed.

**Complete when:** a test would fail if the contract broke.

## Traps → v4

| Reach for | Instead of |
| --- | --- |
| `Context.Service` + `static readonly layer` | `Context.Tag`, `Effect.Service`, `.Default` |
| `Effect.catch` / `catchCause` / `catchDefect` | `catchAll` / `catchAllCause` / `catchAllDefect` |
| `Result` | `Either` |
| `Effect.forkChild` / `forkDetach` | `Effect.fork` / `forkDaemon` |
| `Ref.get` / `Deferred.await` / `Fiber.join` | yielding `Ref` / `Deferred` / `Fiber` |
| `Schema.DateFromString` / `Schema.Finite` | `Schema.Date` for ISO strings / `Schema.Number` for JSON |
| `Effect.fn("name")` | `const f = () => Effect.gen(...)` |
| One composed `Effect.provide` | Many `provide` calls as architecture |

## Open a reference

Open only the branch the task hits. Unstable modules may still break in minors.

- How t3code / OpenCode write Effect: [references/taste.md](references/taste.md)
- Errors, fail vs die, adapter conversion: [references/errors.md](references/errors.md)
- Services and layers: [references/services.md](references/services.md)
- Schema at edges: [references/schema.md](references/schema.md)
- Explicit machines: [references/machines.md](references/machines.md)
- HTTP client or HttpApi: [references/http.md](references/http.md)
- SQL and `Model.Class`: [references/sql.md](references/sql.md)
- RPC contracts: [references/rpc.md](references/rpc.md)
- Distributed entities: [references/cluster.md](references/cluster.md)
- Language models: [references/ai.md](references/ai.md)
- Frontend atoms: [references/atom.md](references/atom.md)
