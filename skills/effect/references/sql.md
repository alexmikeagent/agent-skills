# SQL

`effect/unstable/sql` plus a driver (`@effect/sql-pg`, `@effect/sql-sqlite-node`, …). Unstable — may break in minors.

## When

Persist domain records. The rest of the app depends on a repository service, not `SqlClient`.

## Shape

`Model.Class` is the source of truth for DB and JSON variants. `SqlModel.makeRepository` covers insert / update / findById. Extra queries use `sql` + `SqlSchema`. Domain misses (`OrderNotFound`) stay in `E`. Driver and decode failures that this service cannot explain become defects.

```ts
import { Context, Effect, Layer, Schema } from "effect"
import { Model } from "effect/unstable/schema"
import { SqlClient, SqlModel } from "effect/unstable/sql"

export const OrderId = Schema.String.pipe(Schema.brand("OrderId"))
export type OrderId = typeof OrderId.Type

export class Order extends Model.Class<Order>("Order")({
  id: Model.UuidV4Insert(OrderId),
  sku: Schema.NonEmptyString,
  quantity: Schema.Int,
  createdAt: Model.DateTimeInsert
}) {}

export class OrderNotFound extends Schema.TaggedErrorClass<OrderNotFound>()("OrderNotFound", {
  id: OrderId
}) {}

export class Orders extends Context.Service<Orders, {
  insert(sku: string, quantity: number): Effect.Effect<Order>
  findById(id: OrderId): Effect.Effect<Order, OrderNotFound>
}>()("checkout/orders/Orders") {
  static readonly layer = Layer.effect(
    Orders,
    Effect.gen(function*() {
      const repo = yield* SqlModel.makeRepository(Order, {
        tableName: "orders",
        spanPrefix: "Orders",
        idColumn: "id"
      })

      const insert = Effect.fn("Orders.insert")((sku: string, quantity: number) =>
        Order.insert.makeEffect({ sku, quantity }).pipe(Effect.flatMap(repo.insert), Effect.orDie)
      )

      const findById = Effect.fn("Orders.findById")((id: OrderId) =>
        repo.findById(id).pipe(
          Effect.catchTags({
            NoSuchElementError: () => new OrderNotFound({ id }),
            SchemaError: Effect.die,
            SqlError: Effect.die
          })
        )
      )

      return Orders.of({ insert, findById })
    })
  )
}
```

Provide the driver + migrator under `Orders.layer`. Swap Postgres / SQLite by swapping that driver layer only.

Migrations are ordered effects. Prefer files on disk over an inline record in production.
