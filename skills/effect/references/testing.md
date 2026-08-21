# Testing

Prove through the service interface or a test layer. Prefer `@effect/vitest` when the repo has it. Run `@effect/tsgo` diagnostics when they are installed.

## Shape

```ts
import { describe, expect } from "vitest"
import { it } from "@effect/vitest"
import { Effect, Layer } from "effect"

describe("Checkout", () => {
  it.effect("reserves stock", () =>
    Effect.gen(function*() {
      const checkout = yield* Checkout
      const state = yield* checkout.apply({ _tag: "Submit", sku: "sku-1", quantity: 1 })
      expect(state._tag).toBe("AwaitingPayment")
    }).pipe(Effect.provide(Checkout.layerTest))
  )
})
```

## Layers per test

Default to a fresh layer inside each `it.effect` so state never leaks. Use `it.layer(Layer)` only when an expensive resource must be shared across the suite — it constructs once and tears down after all tests.

```ts
it.layer(Checkout.layerTest)("Checkout", (it) => {
  it.effect("...", () => ...)
})
```

## Test layers

Expose `layerTest` beside `layer`: same constructor, test adapters for outbound services (`Layer.succeed` for parsed config, in-memory `Ref` stores for repositories). Mocking internals is the last resort.

## Time

Freeze time with `TestClock` when behaviour depends on it. `TestClock.adjust` advances; the code under test sees `DateTime.now` move without real waiting.

## What proves the contract

A test fails if the contract broke: wrong `E` surfaces as a failed assertion on the error tag, missing service requirement fails typecheck before run, illegal transition returns `IllegalCheckoutTransition`. Assert on tags and types, not messages.
