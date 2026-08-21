# RPC

`effect/unstable/rpc`. Unstable — may break in minors. Schema-first RPCs shared by client and server.

## When

Typed request/response between processes, workers, or Cluster entities. HTTP JSON routes belong in [http.md](http.md). Distributed durable actors belong in [cluster.md](cluster.md).

## Shape

Define the contract once in a shareable module. Handlers and clients both import that module — never the handler file from a client. Authorize per method, not per socket. The session performs one attempt; retry lives in a supervisor. Map RPC `_tag`s to domain errors at that edge.

Give payload, success, and expected errors concrete Schemas. `Schema.Unknown` is an escape hatch, not a typed protocol.

```ts
import { Effect, Layer, Schema } from "effect"
import { Rpc, RpcGroup, RpcServer } from "effect/unstable/rpc"

export const ChargeOrder = Rpc.make("ChargeOrder", {
  payload: { orderId: Schema.String },
  success: Schema.Struct({ paymentId: Schema.String }),
  error: PaymentDeclined
})

export class CheckoutRpcs extends RpcGroup.make(ChargeOrder) {}

export const CheckoutRpcHandlers = CheckoutRpcs.toLayer(
  Effect.gen(function*() {
    const payments = yield* Payments
    return CheckoutRpcs.of({
      ChargeOrder: ({ orderId }) => payments.charge(orderId).pipe(
        Effect.map((paymentId) => ({ paymentId }))
      )
    })
  })
)

export const CheckoutRpcServer = RpcServer.layer(CheckoutRpcs).pipe(
  Layer.provide(CheckoutRpcHandlers)
)
```

Wire a matching `RpcClient` at the other edge. Verify constructors against the installed package — this surface moves.

Cluster entities reuse the same `Rpc.make` definitions as their protocol.
