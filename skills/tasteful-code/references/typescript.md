# Tasteful TypeScript

Use inference for local implementation detail. Add named types where they communicate a boundary, invariant, or reusable domain concept. Avoid `any`, broad assertions, and non-null assertions that silence a real modeling or validation problem.

## Model alternatives honestly

Use a discriminated union when a value has materially different valid states. It keeps each branch safe and makes the state machine visible.

```ts
type Payment =
  | { readonly status: "pending" }
  | { readonly status: "settled"; readonly settledAt: Date }
  | { readonly status: "rejected"; readonly rejectionReason: string }

const describePayment = (payment: Payment): string => {
  switch (payment.status) {
    case "pending":
      return "Payment is pending"
    case "settled":
      return `Payment settled on ${payment.settledAt.toISOString()}`
    case "rejected":
      return `Payment was rejected: ${payment.rejectionReason}`
  }
}
```

Do not model this as one object with dependent optional properties such as `settledAt?` and `rejectionReason?`; that permits invalid combinations and pushes checks onto every consumer.

## Make call sites explain decisions

Prefer a domain-shaped input to positional booleans or generic configuration that hides the intent.

```ts
scheduleInvoiceReminder({ invoiceId, sendAt })
// Not: scheduleReminder(invoiceId, true)
```

Use the narrowest useful exported API. Extract a helper only if it gives a coherent concept, enforces an invariant, or serves a real shared use.

Sources: [TypeScript narrowing](https://www.typescriptlang.org/docs/handbook/2/narrowing.html) and [function design](https://www.typescriptlang.org/docs/handbook/2/functions.html).
