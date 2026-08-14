# HTTP

`effect/unstable/http` and `effect/unstable/httpapi`. Unstable — may break in minors. Read installed source / `LLMS.md` before copying constructors.

## When

- Outbound calls: wrap `HttpClient` in a domain service. Decode bodies with `Schema`. Map failures to a domain tagged error.
- Inbound APIs: schema-first `HttpApi`. Keep the Api definition in a shareable module so clients do not import handlers. Handlers decode, read request context, call a service, and map errors.

## Client shape

```ts
import { Context, Effect, Layer, Schema } from "effect"
import { FetchHttpClient, HttpClient, HttpClientRequest, HttpClientResponse } from "effect/unstable/http"

export class PaymentsUnavailable extends Schema.TaggedErrorClass<PaymentsUnavailable>()("PaymentsUnavailable", {
  cause: Schema.Defect()
}) {}

export class Payments extends Context.Service<Payments, {
  authorize(orderId: string): Effect.Effect<void, PaymentsUnavailable>
}>()("checkout/payments/Payments") {
  static readonly layer = Layer.effect(
    Payments,
    Effect.gen(function*() {
      const client = (yield* HttpClient.HttpClient).pipe(
        HttpClient.mapRequest(HttpClientRequest.prependUrl("https://payments.example")),
        HttpClient.filterStatusOk
      )

      const authorize = Effect.fn("Payments.authorize")(function*(orderId: string) {
        yield* client.post("/authorize", { urlParams: { orderId } }).pipe(
          Effect.flatMap(HttpClientResponse.schemaBodyJson(Schema.Struct({ ok: Schema.Boolean }))),
          Effect.mapError((cause) => new PaymentsUnavailable({ cause }))
        )
      })

      return Payments.of({ authorize })
    })
  ).pipe(Layer.provide(FetchHttpClient.layer))
}
```

## Server

Define `HttpApi` separately from handlers. Implement with `HttpApiBuilder`. Serve with `HttpRouter.serve` + platform server, or `HttpRouter.toWebHandler` in serverless. Generate the client with `HttpApiClient`. Test handlers with `HttpApiTest` — no real port.

Entry: `Layer.launch(HttpServerLayer)` + `NodeRuntime.runMain`.
