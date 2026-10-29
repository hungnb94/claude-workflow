# PR Explainer Templates

## Facts table

Fill it first. Both versions use only these facts. Leave out optional rows that do not apply.

```markdown
| Field | Value |
|---|---|
| PR type | Bug fix, or Change (feature, refactor, performance, docs, chore, revert) |
| Problem | Bug: the symptom users see. Change: what was missing or hard. |
| Root cause / Reason for change | Verified: ... (file, function, commit, log, test) / Not confirmed |
| Contributing factors | Optional: conditions that made the cause matter |
| Broken invariant | Optional: the rule the code must always keep, written as a rule |
| Fix / What changed | Main files and functions; how it restores the invariant |
| Safety nets | Optional: Safety net, not the fix: ... |
| Why this approach | Rejected options, if known / Not confirmed |
| Impact | Who or what is affected, scope, severity. Only from data. |
| Risks and limits | Optional: what the change does not cover |
| How it was verified | Only checks that ran: what, how, result / Not confirmed |
| Suggested checks for QA | Optional: user actions through the changed code path |
| Sources used | PR number, linked issue, commits |
```

## Metaphor version skeleton

````markdown
<One sentence: the conclusion, in the metaphor. What users saw is fixed.>

**What went wrong:** <what happened, in the metaphor>

**Why it matters:** <what users or the business saw or lost, in plain words>

**How we fixed it:** <the fix, in the metaphor>

**Where the comparison stops:** <one sentence on what the metaphor does not cover>
````

## Metaphor mapping check

| Metaphor part | Real part | Accurate? |
|---|---|---|
| | | |

Change the metaphor or the sentence if any answer is a problem:

- Does every main part of the bug and the fix have a match?
- Does it make scope or severity look bigger or smaller?
- Does it suggest a different cause than the facts table?
- Does it have the same causal structure: who acts on what, and in what order?

Counter-example: a double bank withdrawal (both sides write) is the wrong metaphor for a bug where one side reads while the other is halfway through writing.

## Technical version skeleton

````markdown
**Summary:** <1-2 sentences that stand alone: the bug and the fix>

**Root cause:** <the broken rule, if any. Then the mechanism, with `path/file.ext`, `functionName`, commit. Contributing factors.>

**Fix and why this approach:** <how the fix restores the rule, and why. Rejected options if known.>

**Safety net, not the fix:** <optional>

**Impact and risks:** <who is affected, scope, limits, risks>

**How it was verified:** <only checks that ran: what, how, result. Else Not confirmed.>

**Suggested checks for QA:** <optional>

1. <user action through the changed code path>

**Verified:**

- <fact and evidence>

**Not confirmed:**

- <open point, or "Hypothesis" with partial evidence>
````

## Non-bug changes

Use the same skeletons with these headings: "What went wrong" becomes "What was missing or hard", "Root cause" becomes "Why this change", "How we fixed it" becomes "What we changed".

## Example

Illustrative only. All file names, function names, PR and issue numbers are made up.

Plain-language version (metaphor). For PM, QA, and business readers.

````markdown
The cafe no longer closes for a moment when the specials board is updated.

**What went wrong:** One staff member wipes and rewrites the board. A helper copies the board onto the printed menu. Sometimes the helper copied while the board was half wiped. The copy made no sense, so the helper stopped and the cafe shut for a moment.

**Why it matters:** Some users saw the app close while their watchlist refreshed, and they had to reopen it. Their saved list was not changed.

**How we fixed it:** When the staff member finishes each rewrite, they take a photo of the board. The helper now copies only from the photo, never from the board while it is being rewritten.

**Where the comparison stops:** There are no people here. Two parts of the app ran at the same time, and nobody made a mistake. The "photo" is a copy the app takes in a split second.
````

Technical version. For reviewers.

````markdown
**Summary:** Fixes a crash during watchlist price refresh by giving the background sync a read-only snapshot taken on the main thread.

**Root cause:** The rule "only the main thread reads or changes the live watchlist" was broken. `WatchlistSyncWorker.buildPayload()` looped over the live list on a background thread while `WatchlistViewModel.onPricesUpdated()` cleared and refilled it on the main thread. The loop saw a half-rebuilt list and threw `ConcurrentModificationException`. More frequent price updates may have made the overlap more likely (Not confirmed).

**Fix and why this approach:** `onPricesUpdated()` now publishes a read-only snapshot (`toList()`) on the main thread at the end of each update, and the worker reads only that snapshot. This restores the rule. The snapshot is never half-built because it is taken between updates. Copying on the background thread was rejected because the copy would loop over the live list mid-update. A lock was rejected because it could block the main thread.

**Safety net, not the fix:** The worker catches the exception, logs it, and skips that sync round.

**Impact and risks:** Users saw the app close during a refresh and had to reopen it. The saved watchlist did not change. The snapshot can be up to one update old when the worker reads it.

**How it was verified:** Not confirmed. This is an illustrative example; no test was run.

**Suggested checks for QA:**

1. Open a watchlist with 20+ symbols and pull to refresh several times quickly.
2. Add and remove a symbol while prices refresh.
3. Leave the app in the background longer than one sync interval, then reopen it. The app stays open and the list is correct.

**Verified:**

- Root cause in `buildPayload()` and `onPricesUpdated()` (code read).
- The saved watchlist is unchanged, because the worker only reads (code read).

**Not confirmed:**

- Number of affected users.
- Whether more frequent price updates made the crash worse.
- Test results.
````

Mapping check:

| Metaphor part | Real part | Accurate? |
|---|---|---|
| Staff member rewriting the board | Main thread clearing and refilling the list | Yes, the writer |
| Helper copying the board | Background worker looping over the list | Yes, the reader, at the same time |
| Copy of a half-wiped board makes no sense, helper stops | Loop sees half-rebuilt list, exception, app closes | Yes, same cause and severity (closes, no data lost) |
| Photo taken right after each rewrite | Snapshot made on the main thread between updates | Yes |
| Helper copies only the photo | Worker reads only the snapshot | Yes, restores the rule |
