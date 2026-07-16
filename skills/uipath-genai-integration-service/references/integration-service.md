# Integration Service

Use this reference for connector activities, connector HTTP calls, triggers, connection governance, and hybrid GenAI/API workflows.

## Architecture

Prefer Integration Service over UI automation when a supported API operation exists. Treat connector, connection, activity/trigger, folder binding, and runtime identity as separate parts of the contract.

Integration Service activities are delivered through `UiPath.IntegrationService.Activities`. The live connector schema and generated activity configuration are authoritative; connector catalogs and schemas can change independently of the workflow source.

Design within current platform limits: the official activities page documents a 90-second connector activity/trigger timeout and an 8 MB JSON response-processing limit. Filter and paginate upstream; use file/resource handling rather than forcing large files through JSON.

Official sources:

- [Integration Service introduction](https://docs.uipath.com/integration-service/automation-cloud/latest/user-guide/introduction)
- [Connectors](https://docs.uipath.com/integration-service/automation-cloud/latest/user-guide/connectors)
- [Connections](https://docs.uipath.com/integration-service/automation-cloud/latest/user-guide/connections)
- [Connections troubleshooting](https://docs.uipath.com/integration-service/automation-cloud/latest/user-guide/connections-troubleshooting)
- [Integration Service licensing overview](https://docs.uipath.com/integration-service/automation-cloud/latest/user-guide/integration-service-licensing-overview)

## Build path

Invoke `uipath-rpa` and read its full matching reference:

- XAML connector activity: `references/is-connector-xaml-guide.md`
- coded workflow connector: `references/coded/integration-service-guide.md`
- environment/build validation: `references/validation-guide.md`

In a signed-in supported environment, discover the connector key, connection ID, activity type, resource/object, operation, field schema, reference fields, and generated default XAML. Preserve opaque configuration blobs and every generated field object. Use exact schema field names and generated output types.

For a connection, verify:

- tenant and folder placement;
- robot/user access to the same folder and Connections permission;
- service account versus personal account ownership;
- minimum OAuth scopes and credential-asset/vault use;
- connection health, token refresh, firewall/Relay path, and non-production equivalent;
- deployment binding and post-deployment authentication responsibility.

Connection management is moving into Orchestrator during 2026, so verify the current tenant UI and documentation instead of assuming the older Integration Service Connections tab is present.

## Hybrid AI/API order

For a workflow that reads external data, calls GenAI, then writes back:

1. retrieve the minimum required fields;
2. redact/minimize sensitive content;
3. run the GenAI inference;
4. parse and validate the output;
5. route uncertain/consequential cases to review;
6. check idempotency/current external state;
7. execute the external write once;
8. verify the write result and record a PHI-safe audit event.

Use a dead-letter/retry path for transient connector faults. Re-authentication, missing permission, schema-breaking changes, and validation failures are terminal configuration/business routes rather than blind retries.

## Consumption boundary

The current licensing overview defines one Integration Activity as a connector interaction, connector HTTP request, or trigger and maps it to API calls under Flex or Platform Units under Unified Pricing. GenAI and ScreenPlay have their own product-specific meters. Do not sum meters as if they stack unless current UiPath documentation or the customer's contract confirms that behavior. Read [pricing-governance.md](pricing-governance.md).
