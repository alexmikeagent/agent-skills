# Schema

`Schema` is the source of truth at untrusted edges. Decode unknown input; keep trusted domain logic narrow.

## Shape

```ts
import { Effect, Schema } from "effect"

export class CheckoutRequest extends Schema.Class<CheckoutRequest>("checkout/CheckoutRequest")({
  sku: Schema.NonEmptyString,
  quantity: Schema.Int,
  email: Schema.String
}) {}

export const decodeCheckoutRequest = Schema.decodeUnknownEffect(CheckoutRequest)

export class InvalidCheckoutRequest extends Schema.TaggedError<InvalidCheckoutRequest>()("InvalidCheckoutRequest", {
  message: Schema.String
}) {}

export const parseCheckoutRequest = Effect.fn("parseCheckoutRequest")((input: unknown) =>
  decodeCheckoutRequest(input).pipe(
    Effect.mapError((error) => new InvalidCheckoutRequest({ message: error.message }))
  )
)
```

Same type both ways: `Schema.Finite`, `Schema.Date`. Transforms: `FiniteFromString`, `DateFromString`. Filters via `.check(...)`. Structs are readonly.

Inside Effect code, use `decodeUnknownEffect`; use `decodeUnknownResult`, `decodeUnknownPromise`, or `decodeUnknownSync` only when that execution boundary calls for it. There is no plain v4 RC `Schema.decodeUnknown`. Use `Schema.TaggedStruct("Tag", fields)` when `_tag` is part of the contract instead of rebuilding it manually.

## Reach for Schema

- HTTP / RPC / SQL / AI structured output
- Config and persisted payloads
- Domain models that must not be constructed invalid (`Schema.Class`, `Model.Class`)

A local increment or an already-trusted in-process value does not need a schema. Cross-process JSON uses `Schema.encodeUnknownSync` / `decodeUnknownSync`. Branded ids use `Schema.make`.

## Traps

| Reach for | Instead of |
| --- | --- |
| `Schema.DateFromString` | `Schema.Date` for ISO strings |
| `Schema.Finite` | `Schema.Number` when you mean JSON numbers |
| `Schema.Union([A, B])` / `Schema.Literals(["draft", "paid"])` | variadic v3 constructors |
| `decodeUnknownEffect` / `decodeUnknownResult` | `validate*` / `decodeUnknownEither` |
| `Predicate.isString` | a hand-rolled `isString` |

If the installed package exposes `effect/schema` `Parser`, still prefer the `effect` barrel the nearby code already uses. Read `SCHEMA.md` in the package when the edge is a transform, not a struct.
