# Machines

A machine exists when the domain has multiple valid states and illegal transitions. A single `Effect.fn` story is not a machine.

## Shape

Make states and events unrepresentable in the wrong combination. A pure table owns legal transitions. Effects that talk to the world stay in services the service calls before committing the next state.

```ts
import { Context, Effect, Layer, Ref, Schema } from "effect"

export type CheckoutState =
  | { readonly _tag: "Draft" }
  | { readonly _tag: "AwaitingPayment"; readonly orderId: string }
  | { readonly _tag: "Paid"; readonly orderId: string; readonly paymentId: string }
  | { readonly _tag: "Failed"; readonly orderId: string; readonly reason: string }

export type CheckoutEvent =
  | { readonly _tag: "Submit"; readonly sku: string; readonly quantity: number }
  | { readonly _tag: "PaymentSucceeded"; readonly paymentId: string }
  | { readonly _tag: "PaymentFailed"; readonly reason: string }

export class IllegalCheckoutTransition extends Schema.TaggedErrorClass<IllegalCheckoutTransition>()(
  "IllegalCheckoutTransition",
  {
    from: Schema.String,
    event: Schema.String
  }
) {}

const nextState = (
  state: CheckoutState,
  event: CheckoutEvent
): CheckoutState | IllegalCheckoutTransition => {
  switch (state._tag) {
    case "Draft":
      return new IllegalCheckoutTransition({ from: state._tag, event: event._tag })
    case "AwaitingPayment":
      if (event._tag === "PaymentSucceeded") {
        return { _tag: "Paid", orderId: state.orderId, paymentId: event.paymentId }
      }
      if (event._tag === "PaymentFailed") {
        return { _tag: "Failed", orderId: state.orderId, reason: event.reason }
      }
      return new IllegalCheckoutTransition({ from: state._tag, event: event._tag })
    default:
      return new IllegalCheckoutTransition({ from: state._tag, event: event._tag })
  }
}
```

## Holding state

In-process shared state is a `Ref` behind the service. Two cells that must commit together use `Effect.tx` / `TxRef`. Across machines, a Cluster `Entity`.

```ts
export class Checkout extends Context.Service<Checkout, {
  apply(event: CheckoutEvent): Effect.Effect<
    CheckoutState,
    IllegalCheckoutTransition | InsufficientInventory | PaymentDeclined
  >
}>()("checkout/Checkout") {
  static readonly layer = Layer.effect(
    Checkout,
    Effect.gen(function*() {
      const cell = yield* Ref.make<CheckoutState>({ _tag: "Draft" })
      const inventory = yield* Inventory
      const payments = yield* Payments

      const apply = Effect.fn("Checkout.apply")(function*(event: CheckoutEvent) {
        const current = yield* Ref.get(cell)
        if (current._tag === "Draft" && event._tag === "Submit") {
          const reservation = yield* inventory.reserve(event.sku, event.quantity)
          yield* payments.authorize(reservation.orderId)
          const next = { _tag: "AwaitingPayment" as const, orderId: reservation.orderId }
          yield* Ref.set(cell, next)
          return next
        }
        const next = nextState(current, event)
        if (next instanceof IllegalCheckoutTransition) {
          return yield* next
        }
        yield* Ref.set(cell, next)
        return next
      })

      return Checkout.of({ apply })
    })
  )
}
```

XState is out of scope unless the target repo already uses it.
