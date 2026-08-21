# Errors

Expected business failures live in `E`. Defects stay out of `E`. Recover only what this boundary can handle.

## Shape

```ts
import { Effect, Schema } from "effect"

export class PaymentDeclined extends Schema.TaggedError<PaymentDeclined>()("PaymentDeclined", {
  orderId: Schema.String,
  reason: Schema.String
}) {}

export class InsufficientInventory extends Schema.TaggedError<InsufficientInventory>()("InsufficientInventory", {
  sku: Schema.String
}) {}
```

Handle with `Effect.catchTag` / `Effect.catch`. `return yield*` on failure so TypeScript narrows.

```ts
export const chargeOrder = Effect.fn("chargeOrder")(function*(orderId: string) {
  const payments = yield* Payments
  return yield* payments.charge(orderId).pipe(
    Effect.catchTag("PaymentDeclined", (error) =>
      Effect.succeed({ _tag: "Unpaid" as const, reason: error.reason })
    )
  )
})
```

## Adapter conversion

Vendor and transport types end at the adapter. The domain sees `PaymentDeclined`, not Stripe. Prefer an exhaustive `switch (error._tag)` when several tags map to different domain errors.

```ts
const charge = Effect.fn("Payments.charge")(function*(orderId: string) {
  const stripe = yield* StripeClient
  return yield* stripe.charge(orderId).pipe(
    Effect.mapError((cause) => new PaymentDeclined({ orderId, reason: String(cause) }))
  )
})
```

Unexpected decode or driver failures that this service cannot explain become defects (`Effect.orDie`, `Effect.die`) so the interface stays domain-shaped.

Use `Effect.catchTags` for tag-directed recovery across a union. Use `Effect.mapError` for a pure one-to-one error conversion; a catch that only fails again hides that intent. `Data.TaggedError` remains valid for a local error that does not need a Schema contract.

## Channel

- `Effect.fail` / yieldable tagged errors → typed `E`
- `Effect.die`, thrown `sync` → defect
- `Effect.result` lifts typed `E` into `Result`
- `Effect.exit` preserves the full `Cause`

Current v4 RC uses `Schema.TaggedError`; `Schema.TaggedErrorClass` is not exported. Verify the installed constructor because RC surfaces move.
