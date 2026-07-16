# ScreenPlay

Use this reference whenever ScreenPlay is proposed, configured, edited, tested, or costed.

## Boundary and prerequisites

ScreenPlay is an agentic UI Automation activity, not a UiPath GenAI connector activity. The documented activity type is `UiPath.Semantic.Activities.NUITask`, and it must be placed inside Use Application/Browser. Studio Desktop setup requires a cloud connection and UI Automation package 2025.10.20 or newer; UiPath recommends Studio 2025.10 or newer for the richer prompt editor.

Generate the exact XAML from the project's installed UI Automation package or a working sibling. Do not infer the serialized tag/properties from the display label alone.

Official sources:

- [ScreenPlay activity](https://docs.uipath.com/activities/other/latest/ui-automation/screenplay)
- [Installing ScreenPlay](https://docs.uipath.com/agents/automation-cloud/latest/user-guide-screenplay/installing-screenplay)
- [ScreenPlay overview](https://docs.uipath.com/agents/automation-cloud/latest/user-guide-screenplay/overview)
- [Best practices](https://docs.uipath.com/agents/automation-cloud/latest/user-guide-screenplay/best-practices)
- [Variable Security](https://docs.uipath.com/agents/automation-cloud/latest/user-guide-screenplay/screenplay-variable-security)
- [Running and inspecting execution results](https://docs.uipath.com/agents/automation-cloud/latest/user-guide-screenplay/running-and-inspecting-the-execution-results)
- [ScreenPlay licensing](https://docs.uipath.com/agents/automation-cloud/latest/user-guide-screenplay/licensing)

## Controlled-agency design

Use ScreenPlay at high-friction UI seams: brittle selectors, dynamic/virtualized controls, semantic choices, changing layouts, or image-based interfaces. Keep stable navigation, API calls, business rules, and irreversible actions deterministic.

Prefer several granular ScreenPlay activities. Each task should normally cover one or two actions and only a few relevant UI elements; UiPath's current best-practice page describes two or three naturally related steps as the upper shape for a granular activity. Bound the containing workflow before and after the activity with deterministic state checks.

## Task contract

Write the Task as:

1. current application/screen and narrow goal;
2. allowed actions and relevant UI cues;
3. dynamic variables as data;
4. explicit success condition visible in the UI;
5. stop/escalate condition when the expected state is absent or ambiguous.

Keep Variable Security enabled in production so variable values remain untrusted literal data. Disable it only in controlled debugging after inspecting a suspected false positive, then restore it before delivery.

Set Max number of steps to the smallest value that covers the task. Choose a basic model for simple browser tasks and a standard model only when the measured failure rate justifies its cost/capability. Test DOM mode for the target; disable Use DOM when available only when DOM-based targeting demonstrably causes incorrect coordinates.

## Failure and side-effect boundary

- Set Continue on error to false unless the surrounding workflow explicitly inspects and routes the failed state.
- Verify the postcondition after ScreenPlay returns; completion of the activity is not proof that the intended business action occurred.
- ScreenPlay has no documented business-data output analogous to GenAI generated text; treat changed UI state as its result and verify that state deterministically.
- Put confirmation/submit/payment/destructive actions behind a deterministic check or human approval.
- Design retries around observed UI state so a partial first attempt cannot duplicate the side effect.

## Trace-based validation

Run in Debug on a supported environment and inspect the HTML execution trace. Check prompt interpretation, screenshots/targets, each reasoning/action iteration, errors/fallbacks, duration, tokens, and total UI actions. Configure job trace attachment according to the sensitivity and audit requirement; traces can contain prompts, screenshots, reasoning, and application data.

Build a small evaluation set covering normal layout, changed layout, missing controls, ambiguous matches, slow load, unexpected modal, malicious variable content, partial completion, and retry. Record task success, false action rate, UI-action count, latency, and model tier.

## Cost lever

ScreenPlay is metered by runs, with one run covering a band of up to five UI actions. Granular tasks improve accuracy but can create more activity boundaries; optimize the measured total UI actions and model tier, not merely the number of ScreenPlay activities. Read [pricing-governance.md](pricing-governance.md) and verify current entitlement/overage rules before scale testing.
