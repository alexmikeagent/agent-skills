# AI

`effect/unstable/ai` plus a provider (`@effect/ai-openai`, `@effect/ai-anthropic`, …). Unstable — may break in minors. Bedrock and Google providers were removed.

## When

Text, schema-validated objects, or streams from a language model. Keep `LanguageModel` behind a domain service so providers stay a Layer concern.

## Shape

```ts
import { OpenAiClient, OpenAiLanguageModel } from "@effect/ai-openai"
import { Config, Context, Effect, Layer, Schema } from "effect"
import { AiError, LanguageModel } from "effect/unstable/ai"
import { FetchHttpClient } from "effect/unstable/http"

export class FraudReview extends Schema.Class<FraudReview>("checkout/FraudReview")({
  risk: Schema.Literals(["low", "high"]),
  reason: Schema.NonEmptyString
}) {}

export class ReviewFailed extends Schema.TaggedErrorClass<ReviewFailed>()("ReviewFailed", {
  reason: AiError.AiErrorReason
}) {}

export class FraudAnalyst extends Context.Service<FraudAnalyst, {
  review(notes: string): Effect.Effect<FraudReview, ReviewFailed>
}>()("checkout/ai/FraudAnalyst") {
  static readonly layer = Layer.effect(
    FraudAnalyst,
    Effect.gen(function*() {
      const model = yield* OpenAiLanguageModel.model("gpt-4.1").captureRequirements

      const review = Effect.fn("FraudAnalyst.review")(
        function*(notes: string) {
          const lm = yield* LanguageModel.LanguageModel
          const response = yield* lm.generateObject({
            objectName: "fraud_review",
            prompt: notes,
            schema: FraudReview
          })
          return response.value
        },
        Effect.provide(model),
        Effect.mapError((error: AiError.AiError) => new ReviewFailed({ reason: error.reason }))
      )

      return FraudAnalyst.of({ review })
    })
  ).pipe(
    Layer.provide(
      OpenAiClient.layerConfig({ apiKey: Config.redacted("OPENAI_API_KEY") }).pipe(
        Layer.provide(FetchHttpClient.layer)
      )
    )
  )
}
```

Tools: define with Schema, group into a toolkit, pass to `generateText`. Multi-provider fallback is `ExecutionPlan`, not a home-rolled retry loop. Verify model names and `captureRequirements` against the installed provider package.
