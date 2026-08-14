# Taste

Habits from [t3code](https://github.com/pingdotgg/t3code) and [OpenCode](https://github.com/anomalyco/opencode). Follow the target repo when it already decided. These are the defaults when it has not.

## Imports

Match nearby files. t3code uses namespace imports so `@effect/tsgo` can see every module:

```ts
import * as Context from "effect/Context"
import * as Effect from "effect/Effect"
import * as Layer from "effect/Layer"
import * as Schema from "effect/Schema"
```

OpenCode and `LLMS.md` often use the `effect` barrel. Do not convert a barrel repo to namespaces, or the reverse, as a drive-by.

## Contract module

RPC payloads, domain schemas, and tagged errors that cross a process live in a shareable module (`packages/contracts`). Server and client import that module. A client never imports a handler file.

## Service as a tag

The class is the key. `make` + `layer` sit beside it. Methods stay `Effect<A, E, never>`.

```ts
export class RpcSessionFactory extends Context.Service<
  RpcSessionFactory,
  {
    readonly connect: (
      connection: PreparedConnection
    ) => Effect.Effect<RpcSession, ConnectionAttemptError, Scope.Scope>
  }
>()("@acme/client-runtime/rpc/RpcSessionFactory") {}

export const layer = Layer.effect(RpcSessionFactory, make)
```

Id is package path plus file path. One domain namespace (`Interface`, `Service`, `layer`) in one file unless a cycle forces a split.

## Map `_tag` at the edge

Transport and vendor errors become domain errors in one exhaustive switch. The rest of the program never sees `RpcClientError`.

```ts
function mapSessionRpcError(error: InitialConfigError): ConnectionAttemptError {
  switch (error._tag) {
    case "EnvironmentAuthorizationError":
      return new ConnectionBlockedError({ reason: "permission", detail: error.message })
    case "RpcClientError":
      return new ConnectionTransientError({ reason: "transport", detail: error.message })
  }
}
```

## One attempt, then a supervisor

A session or adapter performs one attempt. Retry, backoff, and offline policy live in a supervisor one layer out. t3code's RPC session does not retry; the connection supervisor does.

## Thin edges

HTTP / RPC handlers: decode, read request context, call a service, map errors. React / Atom: subscribe and send events. Components do not construct transports, retry loops, or RPC clients.

## Re-enter Effect

JS, plugin, and callback boundaries capture the current `Context.Reference`s (instance, workspace, request) and re-enter through a runtime helper. New ambient globals are the wrong cut.

## Time, JSON, IDs

`Clock.currentTimeMillis` / `DateTime.now` — tests freeze `TestClock`. `Schema.encodeUnknownSync` / `decodeUnknownSync` at JSON edges. Branded ids through `Schema.make`, not `makeUnsafe`.

## Config

Env and flags are `Config` fields on a `Context.Service`. Production layer reads `Config.all`. Tests provide `Layer.succeed` with a parsed value.

## Workers

Follow-up work that must stay ordered is a queue plus a drain the test can await. Production behavior does not wait on test-only receipt buses.
