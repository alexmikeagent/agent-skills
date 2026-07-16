# UiPath GenAI Activities

Use this reference when selecting or configuring UiPath-managed GenAI Activities. Recheck the live activity page before implementation because the catalog, models, fields, limits, and billing can change.

## Product boundary

UiPath GenAI Activities use UiPath-managed models through the AI Trust Layer and an Integration Service connection. The connection has no third-party subscription parameters, but it is still required for authenticated execution and governance. The service is cloud-backed; an on-premises robot can call it only through Automation Cloud.

Studio Desktop requires 2023.10 or newer. Unified Integration Service activities support Windows and Cross-platform projects, not Windows-Legacy. Confirm Automation Ops policy, tenant provisioning, connection permissions, regional feature availability, and Public Sector-specific minimum versions before authoring.

Official sources:

- [About the UiPath GenAI Activities package](https://docs.uipath.com/activities/other/latest/integration-service/uipath-uipath-airdk-about)
- [UiPath GenAI Activities connector](https://docs.uipath.com/integration-service/automation-cloud/latest/user-guide/uipath-uipath-airdk)
- [Current activity catalog](https://docs.uipath.com/activities/other/latest/integration-service/uipath-uipath-airdk-activities)
- [Working with UiPath GenAI activities](https://docs.uipath.com/activities/other/latest/integration-service/working-with-genai-activities)
- [GenAI Activities FAQ](https://docs.uipath.com/activities/other/latest/integration-service/genai-activities-frequently-asked-questions)
- [Supported models and data residency](https://docs.uipath.com/activities/other/latest/integration-service/uipath-uipath-airdk-supported-models)

The catalog verified on 2026-07-14 includes Content Generation, Update Context Grounding Index, Context Grounding Search, Get DeepRAG Analysis by ID, Summarize Text, PII Filtering, Translate, Detect Language, Rewrite, Generate Email, Categorize, Named Entity Recognition, Image Analysis, Detect Object, Signature Similarity, Sentiment Analysis, Reformat, Semantic Similarity, Image Comparison, Image Classification, Web Search, Web Summary, Web Reader, and the Index Completed trigger. Treat the live catalog as authoritative.

## Selection matrix

| Need | Prefer | Contract to validate |
|---|---|---|
| Custom generation, instructions, model choice, or grounded answer | Content Generation | generated text, citations/evidence, truncation, schema |
| Concise reduction | Summarize Text | length, preserved facts, omissions |
| Closed-set classification | Categorize | category allowlist, ambiguity/abstention |
| Entity extraction | Named Entity Recognition | entity types, spans/values, duplicates |
| Sensitive-data discovery/redaction | PII Filtering | categories, confidence threshold, residual leakage |
| Language identification | Detect Language | supported-language code and confidence |
| Controlled rewriting, email, translation, sentiment, image/object analysis, or signature comparison | matching task-specific activity | activity-specific typed output and boundary cases |
| Semantic retrieval without generation | Context Grounding Search | source, relevance, permissions, empty result |
| RAG answer | Content Generation with Context Grounding | citations, groundedness, unsupported-answer fallback |
| Index refresh | Update Context Grounding Index + completion event | ingestion status before query |

Choose the task-specific activity when the business task fits its typed fields. Its prompt/model combination may be intentionally managed and not selectable. Choose Content Generation only when the extra flexibility is required and covered by stronger tests.

## Content Generation pattern

1. Define a single business task, authoritative context, output schema, allowed values, and refusal/insufficient-evidence behavior.
2. Keep instructions static. Insert runtime data through explicit variables/arguments and delimit it as data.
3. Ask for the minimum output needed by the deterministic workflow.
4. When using Context Grounding, validate that the selected index is ingested and folder-authorized; require citations or proof of knowledge for consequential answers.
5. Parse the response into a typed internal contract and reject extra/missing fields, invalid enum values, unsupported claims, or missing evidence.

Official activity page: [Content Generation](https://docs.uipath.com/activities/other/latest/integration-service/uipath-uipath-airdk-content-generation).

Content Generation exposes connection, model, prompt, optional system prompt, PII options, Context Grounding mode, result count, maximum tokens, temperature, frequency/presence penalties, completion count, and stop sequences. The documented defaults include maximum tokens 1024, temperature 0, and one completion. Change temperature or nucleus sampling, not both, and keep the completion count at one unless alternatives have measured value.

For just-in-time file grounding, the documented field limit is 30 MB and UiPath recommends fewer than 50 pages because processing must fit the Integration Service timeout. Scanned-PDF images require OCR before grounding. Prompt plus completion must fit the selected model's context window.

## Structured task patterns

- **Categorize**: provide distinct, uniquely named categories with descriptions/attributes and optional content description; validate the single returned category against the allowlist. A poor content description can reduce accuracy.
- **Named Entity Recognition**: provide distinct entity names/descriptions and optional examples; deserialize the documented JSON-string entity list, then validate types and duplicates.
- **Summarize Text**: set source text, maximum word count, format, and language behavior; compare preserved facts and omissions against the source.
- **Context Grounding Search**: set shared folder, index, natural-language query, result count (documented default 3), and relevance threshold (documented default 0.75); consume citations and route an empty/low-relevance result explicitly.
- **Image Analysis**: provide one image resource or public URL plus a bounded prompt; verify the selected model's current image formats and size limits.
- **Web Search/Summary/Reader**: treat results as public web data and retain URLs/citations. UiPath warns Search and Summary may lag time-sensitive facts by days.

## PII Filtering pattern

PII Filtering accepts text, language, optional PII/PHI categories, and a minimum confidence score; it returns redacted text and a full analysis object. The documented default confidence threshold is 0.75 when the property is unset.

Use the redacted output as the downstream model input. Test known sensitive values, unsupported languages/categories, false negatives, and over-redaction. Treat filtering as one control in a data-minimization design, not proof that arbitrary content is safe.

Official activity page: [PII Filtering](https://docs.uipath.com/activities/other/latest/integration-service/uipath-uipath-airdk-pii-filtering).

## File and Context Grounding pattern

GenAI activities primarily accept text. Retrieve the source through a connector, storage bucket, queue, or local path appropriate to the runtime, then use a trusted extraction activity. For serverless robots, avoid local-path assumptions.

For just-in-time grounding: retrieve and upload the file, update the index, wait for the Index Completed event, verify success, then call Content Generation or the consuming process. In debug mode the persisted workflow may require manual resume.

## PII controls

Distinguish the PII Filtering activity from centrally configured AI Trust Layer in-flight masking. Filtering returns redacted content for the workflow to use. In-flight masking is a tenant control for supported activities, is disabled by default, and has entitlement/activity/rate-limit constraints. Verify current policy and supported-activity coverage rather than assuming either control applies to every model call.

Official source: [PII masking](https://docs.uipath.com/automation-cloud/automation-cloud/latest/admin-guide/pii-masking).

## Reliability and safety gates

- Test saved fixtures before paid live calls; include prompt injection strings inside dynamic data.
- Treat all generations as inferences. Use Action Center or another human-in-the-loop route for low-confidence or consequential output.
- Keep model availability and deprecation outside the business contract; model changes can alter outputs, so rerun the evaluation set after a model/package change.
- Log identifiers, counts, outcome codes, latency, and validation results. Keep prompts, raw source content, full generations, PII/PHI, and connection secrets out of logs.
- Review AI Trust Layer audit-log retention and prompt/output capture policy; disabling content capture improves minimization but removes that content from later audit review.
