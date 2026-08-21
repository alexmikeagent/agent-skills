# Atom

`effect/unstable/reactivity` plus `@effect/atom-react` / `atom-solid` / `atom-vue`. Unstable — may break in minors.

## When

Frontend state that must subscribe, cache, or run Effects in the UI. Server programs do not need Atom. Replacing TanStack Query / Zustand is the usual cut.

## Shape

Atoms are the subscription seam. Define shared atoms at module scope so render cycles do not recreate their identity. Put connection, RPC, and domain atoms in a client-runtime package. Apps only supply the platform layer. Components subscribe and send — they do not construct transports or clients.

```ts
import { Atom } from "effect/unstable/reactivity"

export const skuAtom = Atom.make("")
export const quantityAtom = Atom.make(1)

export const checkoutDraftAtom = Atom.make((get) => ({
  sku: get(skuAtom),
  quantity: get(quantityAtom)
}))
```

An Effect-backed atom is `Atom.make(effect)` and surfaces `AsyncResult`. Per-id work is a family. Decode UI input with Schema before it crosses into checkout services.

Use `Atom.keepAlive(atom)` only when state must remain mounted with zero subscribers. Register external listeners and subscriptions with `get.addFinalizer(...)`. Render Effect-backed atoms with `AsyncResult.builder` or its match helpers; core `Result` has no `builder` in current v4 RC.

Provide the same application Layer the server uses, via the framework binding's runtime helper. Do not construct services inside components.

Verify `Atom.make`, family, and `AsyncResult` helpers against the installed `effect/unstable/reactivity` and the matching `@effect/atom-*` package. Website coverage is thin; source wins.
