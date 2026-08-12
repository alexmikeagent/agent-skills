# UiPath action logging guide

This is a strict house contract. UiPath recommends useful non-sensitive logging; it does not require one custom log after every action. Apply this policy without leaking PHI or flooding production logs.

## 1. Workflow boundaries

Every governed workflow starts and ends with these Info logs.

For `Invision_Patient_Search_Terminal.xaml`:

```text
DisplayName: Log Message - Start process
Message:     "Start: Invision_Patient_Search_Terminal | Process to search the patient in Invision terminal"

DisplayName: Log Message - End process
Message:     "End: Invision_Patient_Search_Terminal | Process to search the patient in Invision terminal"
```

The Start log is the first executable activity. The End log records successful completion only and is the last activity on the successful path. Never emit a misleading End after a failed action. A locally handled failure uses a concise, sanitized `Failed:` log; an unhandled failure propagates to its owner.

Keep the purpose clause short and direct. The pipe is reserved for the boundary delimiter.

## 2. One contextual log per action

**MUST · House:** Put one contextual log immediately after every executable leaf action.

Exceptions:

- `Log Message` itself;
- `Invoke Workflow File`, because the invoked workflow owns Start and End;
- passive structural containers such as Sequence, Flowchart, Try Catch, Catch/Finally, annotations, and comments;
- `Throw`, `Rethrow`, `Break`, `Continue`, and termination, whose contextual log goes immediately before the action;
- decisions, whose selected-result log is the first activity inside each branch;
- loops, which also need a loop Start and End log plus the contained action logs.

Do not add a generic “workflow completed” log after `Invoke Workflow File`. A parent's own End boundary remains required when the invoke is its last action.

For a consequential irreversible mutation, use two phases when an attempted action and a verified result are materially different:

1. `Attempt:` immediately before the mutation;
2. `Completed:` after its postcondition is verified.

Both messages remain contextual and PHI-safe.

## 3. Natural-language message rules

Write logs as short, natural operational sentences. Name the exact variable whenever an action reads, assigns, or modifies it.

Good:

```vb
"Assigned the terminal timeout intTimeoutMS to " + intTimeoutMS.ToString + " milliseconds."
"Read the patient status into strPatientStatus."
"Entered the patient account number from strPatientAccountNumber in Invision."
"Submitted the patient search in Invision."
"Waited " + intRetryDelayMS.ToString + " milliseconds before retrying the Invision patient search."
"Saved the output report using strOutputPath."
```

Do not write telemetry-shaped prose:

```text
Assigned: intRetryLimit | Source=Config | Value omitted
PHI=NotLogged
{"action":"assigned","variable":"intRetryLimit"}
```

Avoid `Assigned:`, `Source=`, `Value=`, JSON/YAML fields, unnecessary pipes, or padding such as “The value was intentionally omitted from the log.” Never say a value is hidden, omitted, redacted, or PHI. Just state the safe action.

## 4. Dynamic safe values and sensitive values

When an approved non-sensitive scalar improves debugging, concatenate the runtime variable. Never statically repeat the expected value.

Correct:

```vb
"Assigned the terminal timeout intTimeoutMS to " + intTimeoutMS.ToString + " milliseconds."
```

Incorrect:

```vb
"Assigned the terminal timeout intTimeoutMS to 30000 milliseconds."
"Assigned the retry count intRetryCount to 0."
"Assigned the simulation setting bnIsSimulation to False."
```

This applies even when the workflow just assigned a known constant such as `0`, `25`, `True`, or `False`. The log must read the post-assignment variable dynamically. If the variable is sensitive or unclassified, do not state either its assigned constant or its runtime value.

Candidates for approved dynamic logging include technical Booleans, counters, retry numbers, elapsed time, non-sensitive enums/status values, and approved technical settings. Approval depends on meaning, not only type.

Treat values as sensitive by default when they involve patients, accounts, claims, invoices, medical records, health plans, names, contact details, dates linked to an individual, screen text, screenshots, payloads, paths, URLs, selectors, exception text, credentials, DataRows, DataTables, collections, or objects.

For a sensitive target, put the exact variable name in the sentence but do not reference its runtime value:

```vb
"Assigned the patient account number to strPatientAccountNumber."
```

Do not hash, truncate, abbreviate, or relabel patient-derived data and assume it is safe. A technical correlation ID is loggable only when it is independently generated, cannot identify or re-identify a patient, and is approved for the log audience.

## 5. Assign and Multiple Assign

After one Assign, the next activity is one Log Message that:

- describes the assignment naturally;
- includes the exact target variable name;
- dynamically references an approved safe value; or
- names a sensitive/unclassified variable without referencing its value.

After a Multiple Assign, use one immediately following multiline Log Message. Include one sentence per assignment in assignment order and one sentence per line. Each target is named on exactly one line; approved safe values remain dynamic on that same line.

Example:

```vb
"Assigned the retry limit intRetryLimit to " + intRetryLimit.ToString + "." + Environment.NewLine +
"Assigned the terminal timeout intTimeoutMS to " + intTimeoutMS.ToString + " milliseconds." + Environment.NewLine +
"Assigned the simulation setting bnIsSimulation to " + bnIsSimulation.ToString + "." + Environment.NewLine +
"Assigned the workflow name to strWorkflowName." + Environment.NewLine +
"Assigned the patient account number to strPatientAccountNumber." + Environment.NewLine +
"Assigned the candidate counter intCandidateCount to " + intCandidateCount.ToString + "." + Environment.NewLine +
"Assigned the simulation setting bnIsSimulation to " + bnIsSimulation.ToString + "."
```

The safe values are evaluated from their variables at runtime. The string and patient values are not interpolated.

## 6. Decisions and loops

For If, Switch, or Flow Decision, the first activity in each branch logs the selected result. Do not log the condition value if it is sensitive.

Loops retain physical action-log pairing while changing log level to control volume:

| Situation | Level and behavior |
|---|---|
| Known 10 iterations or fewer | Contained action logs at Info. |
| More than 10 or unbounded | Routine contained action logs at Trace. |
| External mutation or important decision | Info even in a large loop. |
| Retry or recoverable condition | Warn. |
| Locally handled terminal failure | Error. |
| Whole-job termination at the owning layer | Fatal. |

Also add:

- an Info loop Start log before entry;
- an Info loop End log after completion;
- an Info progress summary every 100 iterations for a long-running loop, unless project configuration sets another threshold;
- only PHI-safe aggregate counts and approved technical correlation.

Never log every field, row, cell, screen value, or selector to prove progress. The action logs remain next to their actions; Trace suppresses routine production noise when the deployed logging level is Info.

## 7. Levels and exception ownership

| Level | Use |
|---|---|
| Trace | Routine actions inside large or unbounded loops. |
| Info | Workflow Start/End, normal actions, decisions, handoffs, consequential mutations, and loop summaries. |
| Warn | Bounded retries, recoverable conditions, and expected business exceptions. |
| Error | A terminal failure handled at the current layer. |
| Fatal | The owning layer terminates the whole job. |

Log a failure at the layer that handles, translates, or retries it. If it is merely propagated to REFramework, let the framework owner log it. Sanitize every explicit message; marking an activity Private does not sanitize a custom Log Message expression.

## 8. Logging review checklist

- Start first and successful End last, with exact boundary DisplayNames.
- One immediate action log, except for the explicit structural and control-flow cases.
- Unique `Log Message - [specific action]` DisplayNames.
- Natural, short sentences with exact variable names.
- Approved safe values dynamically concatenated from the runtime variable.
- Sensitive and unclassified values never interpolated.
- Multiple Assign sentences separated by real newline expressions.
- Branch result logged first inside every branch.
- Loop volume controlled by level and progress summaries.
- No caller completion log after Invoke Workflow File.
- No duplicate failure logging or raw exception content.
