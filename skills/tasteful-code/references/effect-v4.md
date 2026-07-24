# Tasteful Effect v4

Effect v4 is evolving. Treat this reference as design guidance, not a frozen API recipe. Inspect the installed package, source, and nearby code before selecting exact imports or constructors.

## Keep the effect type intentional

Make success, expected failure, and required services part of the design. Use small named domain errors for expected business failures. Convert transport or vendor errors at the adapter boundary; do not leak them as the domain contract. Recover only errors that the boundary can actually handle.

## Let the program read in order

Use `Effect.gen` when sequential dependencies and intermediate names clarify the work. Keep each generator short enough to tell one story. Extract a named domain operation when it becomes a second story.

```ts
const reserveInventory = (order: Order) =>
  Effect.gen(function*() {
    const inventory = yield* Inventory
    const available = yield* inventory.available(order.sku)

    if (available < order.quantity) {
      return yield* Effect.fail(new InsufficientInventory({ sku: order.sku }))
    }

    return yield* inventory.reserve(order.sku, order.quantity)
  })
```

This is an illustrative shape. Verify the installed v4 tag, service, error, and constructor APIs.

## Compose dependencies at the edge

Depend on narrow service capabilities. Acquire services where work is performed, but assemble live and test layers at composition boundaries. Make resource lifetime explicit and prefer test layers or focused fakes over mocking arbitrary internals.

Start with sequential code. Add concurrency only after independence, ordering, cancellation, resource lifetime, and failure behavior are all clear.

Sources: [Effect v4 development repository](https://github.com/Effect-TS/effect-smol), [Effect documentation](https://effect.website/), and [Effect v4 language service](https://github.com/Effect-TS/tsgo).
