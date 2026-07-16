# Pricing and governance

Use this reference before design-time live calls, load tests, runtime rollout, or any claim about AI Units, Agent Units, Platform Units, API calls, ScreenPlay runs, or Context Grounding charges.

## Verification rule

Pricing is drift-prone. Recheck the official product page, licensing-plan framework, tenant Consumables dashboard, purchased entitlements, and contract on the day of the estimate. Record the verification date and do not convert units to currency unless the customer's actual commercial rate is known.

The public pages below were checked on 2026-07-14. They are evidence, not a permanent rate card.

## Public meters observed on 2026-07-14

| Branch | Flex | Unified Pricing | Counting boundary |
|---|---:|---:|---|
| UiPath GenAI Activity | 1 AI Unit per execution | 0.2 Platform Units per execution | design-time and runtime execution; documented as independent of token size |
| ScreenPlay standard tier overage | 1 Agent Unit per run | 0.20 Platform Units per run | one run covers 1–5 UI actions |
| ScreenPlay basic tier overage | 0.25 Agent Units per run | 0.05 Platform Units per run | one run covers 1–5 UI actions |
| Ordinary Integration Activity | 5 API calls per activity | 0.2 Platform Units per activity | connector operation, connector HTTP request, or trigger |

Sources:

- [UiPath GenAI Activities package licensing](https://docs.uipath.com/activities/other/latest/integration-service/uipath-uipath-airdk-about)
- [GenAI Activities FAQ](https://docs.uipath.com/activities/other/latest/integration-service/genai-activities-frequently-asked-questions)
- [ScreenPlay licensing](https://docs.uipath.com/agents/automation-cloud/latest/user-guide-screenplay/licensing)
- [Integration Service licensing overview](https://docs.uipath.com/integration-service/automation-cloud/latest/user-guide/integration-service-licensing-overview)
- [Unit-consumption dashboard](https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/about-licensing-units-resource-management-dashboard)
- [Tenant consumption enforcement](https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/about-tenant-consumption-enforcement)

The current GenAI package/FAQ pages say Context Grounding requests are not charged separately from a GenAI execution, while the current AI Center Platform Units table lists 0.2 without Context Grounding and 0.4 with Context Grounding. Treat this as a documentation conflict: show both sources, verify the tenant's applicable plan/contract, and avoid presenting either as settled until reconciled.

Conflicting source: [AI Center Platform Units](https://docs.uipath.com/ai-center/automation-cloud/latest/user-guide/platform-units).

## Estimation model

Estimate each branch independently:

```text
GenAI executions = business items x AI calls per item x (1 + retry rate)
ScreenPlay runs = ceiling(total ScreenPlay UI actions / 5)
Integration activities = connector operations + connector HTTP calls + metered triggers
```

Then calculate low/base/high scenarios. Include development/debug executions, evaluation cases, scheduled reprocessing, manual reruns, retries, fallback calls, and duplicated side effects prevented by idempotency. Report unit totals separately when the plan uses different unit types.

## Cost controls

- Apply deterministic eligibility and deduplication before the paid activity.
- Use one task-specific GenAI activity instead of multiple chained calls when it preserves the contract; each execution is a meter event.
- Shorter prompts can improve latency, context fit, and quality, but current UiPath-managed GenAI charging is flat per execution; token reduction alone does not lower that activity's documented unit charge.
- Cache immutable inference results using an input/prompt/model-contract hash when policy permits.
- Use saved responses and mocks for parsing, routing, UI plumbing, and negative tests; reserve live calls for behavior evaluation.
- Cap retries and distinguish transient transport faults from invalid output.
- Use smaller/basic ScreenPlay models for measured simple tasks and bound Max number of steps.
- Keep ScreenPlay tasks granular enough to succeed, then measure total UI actions; boundaries alone do not determine billed runs.
- Batch only when the activity supports it and one failed item cannot invalidate or duplicate the whole side effect.
- Add a feature flag/kill switch, per-run counters, volume thresholds, and alerts at expected consumption milestones.
- Review tenant allocations and overconsumption behavior. Current UiPath documentation says tenant-level enforcement is not yet implemented for GenAI Activities, so a tenant allocation may not be a hard stop.
- Expect reporting lag and aggregation. The GenAI package page says consumption can take up to 12 hours to appear; the unit dashboard notes Integration Service reporting may appear in 2-Platform-Unit increments.
- Evaluate ScreenPlay BYOM against provider charges, support, regional availability, and operational ownership. Current UiPath docs say BYOM avoids ScreenPlay run consumption but still requires the ScreenPlay add-on entitlement.

## Decision record

Every production design should state:

- license plan and entitlement source;
- verified rate pages and date;
- volume, calls/actions per item, retry assumptions, and scenarios;
- whether bundled entitlements or overage meters apply;
- unresolved documentation/contract conflicts;
- monitoring owner, alert threshold, and kill-switch owner;
- measured accuracy/latency/unit trade-off that justifies the selected activity or model tier.
