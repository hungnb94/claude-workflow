# Issue Templates

Pick the template that matches the issue type. Fill every Required field. Drop Optional fields that have no data. Do not leave them empty.

If a Required field is unknown, write `TBD` and add a question to "Open questions".

Each template has two parts. The field table explains each field. The skeleton is the text to copy and fill.

## User Story / Feature

Use for new value for a user. The "As a, I want, so that" form is a recommendation. Two plain sentences with the same meaning are fine.

### Story fields

| Field | Need | How to fill | Example |
|---|---|---|---|
| Title | Required | Verb plus object. Name the outcome. | Export invoices as CSV |
| User story | Required | Say who, what, and why. | As an accountant, I want to export invoices as CSV, so that I can open them in a spreadsheet. |
| Context / Problem | Required | Explain the problem today in 1-3 sentences. | Accountants copy invoice data by hand. This takes hours each month. |
| In scope | Optional | List what this issue covers. | Export of the invoice list page |
| Out of scope | Optional | List what this issue does not cover. | PDF export |
| Acceptance criteria | Required | Write checks that pass or fail. Use a checklist, or Given/When/Then for flows. | The CSV has one row per invoice. |
| Design / links | Optional | Link mockups, docs, or related pages. | Link to the mockup |
| Dependencies | Optional | List parent, blocked by, and blocks. | Blocked by Issue 2 |
| Labels / Priority | Optional | Use the team's labels and scale. | Label: export |
| Open questions | Required if any `TBD` | Ask one question per unknown. | Which date format should the CSV use? |

### Story skeleton

```markdown
## User story
As a <role>, I want <goal>, so that <benefit>.

## Context / Problem
<What is wrong or missing today?>

## In scope
- <item>

## Out of scope
- <item>

## Acceptance criteria
- [ ] <A check that passes or fails>
- [ ] <Another check>

## Design / links
- <link>

## Dependencies
- Blocked by: <ID or TBD>
- Blocks: <ID or TBD>

## Labels / Priority
<team labels, priority>

## Open questions
- <question>
```

## Bug

Use when existing behavior is wrong. Write facts first. Put guesses in "Suspected cause".

### Bug fields

| Field | Need | How to fill | Example |
|---|---|---|---|
| Title | Required | Name the symptom and where it happens. Do not guess the cause. | Checkout button does nothing on Safari 17 |
| Summary | Required | Describe the problem in 1-2 sentences. | Clicking Pay on the checkout page has no effect on Safari. |
| Environment | Required | Give exact app version or commit, OS, browser or device, and account type. | Web app 4.12.0, macOS 14.5, Safari 17.5, free account |
| Steps to reproduce | Required | Number the shortest steps that show the bug. | 1. Add any item to the cart. 2. Open checkout. 3. Click Pay. |
| Expected result | Required | Say what should happen. | The payment form opens. |
| Actual result | Required | Say what happens. Quote error text exactly. | Nothing happens. No error is shown. |
| Frequency | Required | Use Always, Sometimes, or Once. Add the rate if known. | Always |
| Severity | Required | Rate the impact. Critical: no workaround, data loss, or outage. Major: main feature broken. Minor: small impact. Trivial: cosmetic. | Major |
| Priority | Optional | Say how soon to fix it. The team decides. | TBD |
| Evidence | Optional | Add logs, screenshots, or error text. Paste logs in a code block. | Console error: TypeError at checkout.js:88 |
| Regression | Optional | Name the last version that worked. | Worked in 4.11.2 |
| Workaround | Optional | Say how users can avoid the bug. | Use Chrome |
| Suspected cause | Optional | Write a guess and say it is a guess. | This is a guess: the new payment script may not support Safari. |
| Open questions | Required if any `TBD` | Ask one question per unknown. | Does it also fail on iOS Safari? |

### Bug skeleton

```markdown
## Summary
<1-2 sentences>

## Environment
- App version or commit: <exact value>
- OS: <value>
- Browser or device: <value>
- Account type: <value>

## Steps to reproduce
1. <step>
2. <step>
3. <step>

## Expected result
<what should happen>

## Actual result
<what happens>

## Frequency
<Always / Sometimes / Once>

## Severity
<Critical / Major / Minor / Trivial>

## Priority
<team scale or TBD>

## Evidence
<logs, screenshots, error text>

## Regression
<last version that worked>

## Workaround
<workaround>

## Suspected cause
This is a guess: <guess>

## Open questions
- <question>
```

## Task / Chore

Use for technical or maintenance work with no new user behavior.

### Task fields

| Field | Need | How to fill | Example |
|---|---|---|---|
| Title | Required | Verb plus object. | Upgrade Node.js from 18 to 22 in CI |
| Goal / Why | Required | Say why the work is needed. | Node 18 is no longer supported. |
| What to do | Required | List short steps or parts. | Change the CI image. Fix failing builds. |
| Done when | Required | Write checks that pass or fail. | All CI jobs pass on Node 22. |
| Out of scope | Optional | Name related work you will not do. | Upgrading dependencies |
| Dependencies | Optional | List parent, blocked by, and blocks. | Blocks Issue 3 |
| Risks / Notes | Optional | Note risks or hints. | Some native modules may need a rebuild. |
| Open questions | Required if any `TBD` | Ask one question per unknown. | Do we also upgrade local dev? |

### Task skeleton

```markdown
## Goal / Why
<why this work is needed>

## What to do
- <step>
- <step>

## Done when
- [ ] <A check that passes or fails>
- [ ] <Another check>

## Out of scope
- <item>

## Dependencies
- Blocked by: <ID or TBD>
- Blocks: <ID or TBD>

## Risks / Notes
- <note>

## Open questions
- <question>
```

## Spike / Research

Use when a question must be answered before work can be planned. A spike is time-boxed research. Its output is knowledge or a decision, not production code.

### Spike fields

| Field | Need | How to fill | Example |
|---|---|---|---|
| Title | Required | Start with Investigate, Decide, or Evaluate. | Decide between WebSockets and SSE for live updates |
| Question to answer | Required | Ask 1-3 specific questions. | Which option works with our load balancer? |
| Why it matters | Required | Name the decision or issue that is blocked. | We cannot plan the live updates story until we choose. |
| Timebox | Required | Set a hard time limit. | 2 days |
| Approach / options to check | Optional | List options or steps to try. | Build a small test with each option. |
| Output | Required | Say what you will deliver. A written recommendation or decision. A throwaway prototype is fine. | A one-page recommendation |
| Done when | Required | Write checks that pass or fail. | The recommendation is shared with the team. |
| Out of scope | Optional | Name what the spike will not do. | Production code |
| Follow-up | Optional | List issues to create after the spike. | Story: show live order status |
| Open questions | Required if any `TBD` | Ask one question per unknown. | Who approves the final choice? |

### Spike skeleton

```markdown
## Question to answer
- <specific question>

## Why it matters
<what decision or issue is blocked>

## Timebox
<for example: 2 days>

## Approach / options to check
- <option>

## Output
<recommendation, decision, or throwaway prototype>

## Done when
- [ ] <A check that passes or fails>

## Out of scope
- <item>

## Follow-up
- <issue to create later>

## Open questions
- <question>
```
