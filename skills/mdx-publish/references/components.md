# Restricted MDX component reference

Use quoted string props and bare `open` only. JavaScript expressions, imports,
exports, inline styles, event handlers, and undeclared components are rejected.
Ordinary Markdown remains valid inside every container component.

## Narrative components

```mdx
<Callout tone="info" title="Why this matters">
The conclusion, caveat, or decision.
</Callout>

<Steps>
  <Step title="Capture">Write the durable note first.</Step>
  <Step title="Present">Add the rich MDX layer.</Step>
</Steps>

<Timeline>
  <Event date="2026-07-15" title="Decision recorded">The evidence.</Event>
</Timeline>

<Disclosure title="Method details" open>
Optional depth for interested readers.
</Disclosure>
```

Callout tones are `info`, `warning`, and `danger`.

## Comparison and metrics

```mdx
<MetricGrid>
  <Metric label="Sources" value="14">Twelve primary, two secondary.</Metric>
  <Metric label="Confidence" value="High" />
</MetricGrid>

<Comparison>
  <Option name="Approach A" status="recommended">Strengths and tradeoffs.</Option>
  <Option name="Approach B" status="alternative">Strengths and tradeoffs.</Option>
</Comparison>
```

## Technical material

```mdx
<FileTree>
project/
  src/
  tests/
</FileTree>

<CodeWalkthrough title="Request path">
Explain the important lines around an ordinary fenced code block.
</CodeWalkthrough>

<ApiEndpoint method="POST" path="/v1/items">
Contract, examples, and failure behavior.
</ApiEndpoint>

<DataModel name="ResearchPacket">
A Markdown table describing fields and invariants.
</DataModel>
```

## Evidence and flows

```mdx
<EvidenceTable>

| Claim | Evidence | Confidence |
| --- | --- | --- |
| Example | [Primary source](https://example.com) | High |

</EvidenceTable>

<Flow>
  <Node title="Capture" kind="input">Raw note or source.</Node>
  <Edge from="Capture" to="Synthesis" label="normalize" />
  <Node title="Synthesis" kind="process">Durable context.</Node>
</Flow>
```

## Safe HTML subset

The publisher accepts common reading-oriented HTML tags such as headings,
paragraphs, links, lists, tables, `details`, `figure`, code, and local raster
images. Images must be PNG, JPEG, GIF, or WebP inside the bundle; they are
embedded into `artifact.html`. Remote hyperlinks are allowed, but remote
runtime assets are not.
