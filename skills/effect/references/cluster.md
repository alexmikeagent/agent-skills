# Cluster

`effect/unstable/cluster`. Unstable — may break in minors. Distributed entities: one address, message protocol, passivation.

## When

State must live in one place across processes — a checkout session, a counter, a workflow inbox. In-process `Ref` is enough for a single runtime. `@effect/experimental/Machine` is gone.

## Shape

```ts
import { Effect, Layer, Ref, Schema } from "effect"
import { Entity, TestRunner } from "effect/unstable/cluster"
import { Rpc } from "effect/unstable/rpc"

const Apply = Rpc.make("Apply", {
  payload: {
    event: Schema.Union([
      Schema.Struct({ _tag: Schema.Literals(["Submit"]), sku: Schema.String, quantity: Schema.Int }),
      Schema.Struct({ _tag: Schema.Literals(["PaymentSucceeded"]), paymentId: Schema.String })
    ])
  },
  success: Schema.Struct({ _tag: Schema.String })
})

export const CheckoutEntity = Entity.make("Checkout", [Apply])

export const CheckoutEntityLayer = CheckoutEntity.toLayer(
  Effect.gen(function*() {
    const cell = yield* Ref.make<{ _tag: string }>({ _tag: "Draft" })
    return CheckoutEntity.of({
      Apply: ({ payload }) =>
        Ref.updateAndGet(cell, (current) =>
          current._tag === "Draft" && payload.event._tag === "Submit"
            ? { _tag: "AwaitingPayment" }
            : current
        )
    })
  }),
  { maxIdleTime: "5 minutes" }
)
```

Clients: `yield* CheckoutEntity.client`, then `clientFor(orderId)`. Messages are volatile unless annotated persisted. Handlers on one entity run sequentially unless a handler is `Rpc.fork`.

Persistence annotations still require a real message-storage layer. Use `Rpc.fork` only when overlapping handlers preserve the entity's invariants.

## Run

- Production: platform cluster layer (`NodeClusterSocket.layer` or HTTP equivalent) + entity layers + `Layer.launch`
- Tests / local: `TestRunner.layer` — no network, in-memory storage

Read installed `LLMS.md` cluster section and the entity module before choosing storage or sharding options.
