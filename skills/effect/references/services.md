# Services and layers

Structure behaviour as services. The id is package path plus file path. The live layer lives on the class.

V4 uses `Context.Service`, not v3 `Effect.Service`. Generated `.Default` layers and service `dependencies` options are gone; construct `Layer.effect` explicitly and satisfy its requirements with `Layer.provide` / `Layer.provideMerge`.

## Shape

```ts
import { Context, Effect, Layer } from "effect"
import { InsufficientInventory } from "./errors.ts"

export class Inventory extends Context.Service<Inventory, {
  reserve(sku: string, quantity: number): Effect.Effect<{ readonly orderId: string }, InsufficientInventory>
}>()("checkout/inventory/Inventory") {
  static readonly layer = Layer.effect(
    Inventory,
    Effect.gen(function*() {
      const stock = yield* StockStore

      const reserve = Effect.fn("Inventory.reserve")(function*(sku: string, quantity: number) {
        const available = yield* stock.available(sku)
        if (available < quantity) {
          return yield* new InsufficientInventory({ sku })
        }
        return yield* stock.reserve(sku, quantity)
      })

      return Inventory.of({ reserve })
    })
  )
}
```

The class may be a tag only, with `make` and `layer` beside it — t3code's usual cut. Acquire where work happens (`const inventory = yield* Inventory`). Prefer `yield*` over `.use` in generators.

Request- or instance-scoped values are `Context.Reference`, not a global. Config-backed services parse `Config.all` in `layer` and take a `Layer.succeed` in tests.

## Compose at the edge

Build focused layers, then `Layer.provide` / `Layer.provideMerge`. Expose `layer` and `layerTest`. Provide once from `main`, `Layer.launch`, or `ManagedRuntime`.

```ts
const CheckoutLive = Checkout.layer.pipe(
  Layer.provide(Inventory.layer),
  Layer.provide(Payments.layer)
)
```

Memoization across `provide` is a safety net. Composition is the design.

## Layout

Follow the target tree. Colocate service, layer, and errors. Greenfield default is one capability file or feature folder. Monorepo: domain and protocol inward; adapters and the composition root outward. A `services/` + `layers/` + `errors/` dump is the wrong cut.

## Test

Prove through the service interface. `layerWithoutDependencies` plus a test adapter, or `layerTest` with `Ref` state. Mocking internals is the last resort.
