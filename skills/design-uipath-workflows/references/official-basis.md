# Official basis and house-policy boundary

Research was checked against first-party UiPath documentation on 2026-08-12. HHS is used only for the narrow de-identification boundary. Product versions and Analyzer defaults can change; verify the installed Studio and activity versions when the distinction matters.

## Supported by official UiPath guidance

- Give workflows, activities, arguments, and variables meaningful names; except for `Main`, workflow names should contain a verb. [Workflow Design](https://docs.uipath.com/studio/standalone/latest/user-guide/workflow-design)
- Split projects into smaller workflows, prefer Sequence for linear behavior, use Flowchart for decision-rich logic, and separate business logic from UI components. [Project Organization](https://docs.uipath.com/studio/standalone/2025.10/user-guide/project-organization)
- Keep workflow files below 5 MB; files above 10 MB are unsupported. [Project Organization](https://docs.uipath.com/studio/standalone/2025.10/user-guide/project-organization)
- Default Analyzer guidance includes 20 arguments, 30-character variable and argument names, avoiding more than three nested If activities, and review at seven nested activities. These rules and severities are configurable. [High Arguments Count](https://docs.uipath.com/studio/docs/st-dbp-002), [Variable Length Exceeded](https://docs.uipath.com/studio/standalone/latest/user-guide/st-nmg-008), [Argument Length Exceeded](https://docs.uipath.com/studio/standalone/latest/user-guide/ST-NMG-016), [Nested If Clauses](https://docs.uipath.com/studio/standalone/2025.10/user-guide/st-mrd-007), [Deeply Nested Activities](https://docs.uipath.com/studio/standalone/latest/user-guide/st-mrd-009)
- Use narrowly scoped variables, avoid duplicate names, and use direction-prefixed arguments. [Managing Variables](https://docs.uipath.com/studio/standalone/latest/user-guide/managing-variables), [Managing Arguments](https://docs.uipath.com/studio/standalone/latest/user-guide/managing-arguments)
- Use useful logs without sensitive data; Private does not protect values explicitly placed in Log Message. [Minimum Log Messages](https://docs.uipath.com/studio/standalone/latest/user-guide/st-usg-020), [Protecting Sensitive Information](https://docs.uipath.com/studio/standalone/latest/user-guide/protecting-sensitive-information)
- Handle predictable exceptions contextually, do not leave Catch blocks empty, and propagate what cannot be resolved locally. [Project Organization](https://docs.uipath.com/studio/standalone/2025.10/user-guide/project-organization), [Empty Catch Block](https://docs.uipath.com/studio/standalone/2022.4/user-guide/st-dbp-003)
- Use durable selectors and state checks; UI Automation inside Parallel is unsupported. [UI Automation](https://docs.uipath.com/studio/standalone/latest/user-guide/ui-automation)
- Workflow Analyzer is static and configurable; it does not prove runtime behavior. [About Workflow Analyzer](https://docs.uipath.com/studio/standalone/latest/user-guide/about-workflow-analyzer)

## House rules, not UiPath product limits

The following are intentionally stricter organization governance:

- the complete 40-character XAML filename limit;
- application and lifecycle prefix grammar;
- exact root `DisplayName` equality;
- the mandatory ten-section annotation;
- the 50/55 activity review thresholds;
- exact `[Activity name] - [action]` DisplayNames;
- the default ban on Invoke Code and Invoke Method;
- one custom log after every action;
- exact Start and End message patterns;
- the variable type-prefix table and 10-argument preferred budget.

Do not attribute these to UiPath. UiPath provides Invoke Code and Invoke Method as supported activities and does not publish a universal filename or activity-count limit. Its logging rule asks for a reasonable number of helpful messages, not one after every activity.

## Sensitive-data basis

UiPath says not to log sensitive data and warns that Verbose/Trace output can expose values. HHS explains that data is de-identified only when it does not identify an individual and there is no reasonable basis to believe it can do so. Listed identifiers include names, patient-related dates, contact information, medical-record, health-plan, account and license numbers, URLs, IP addresses, biometrics, images, and other identifying codes. A derivative or re-identification code can remain PHI. [HHS de-identification guidance](https://www.hhs.gov/hipaa/for-professionals/special-topics/de-identification/index.html)

Therefore the house logging policy is fail-closed: variable names may be logged, but patient-derived or unclassified values are not interpolated. This is an engineering control, not legal advice.

## Validation ladder

Report each layer separately:

1. **Local static inspection** — XML, naming, adjacency, contracts, and heuristic style checks.
2. **Windows Studio validation and configured Workflow Analyzer** — serialization, expressions, imports, and installed rules.
3. **Studio build** — compilation for the installed dependency set.
4. **Robot/test execution** — behavior for exercised scenarios and environment.
5. **UAT or production-like acceptance** — business outcome, real applications, selectors, assets, queues, recovery, and operational controls.

Never turn a lower layer into a claim about a higher one.
