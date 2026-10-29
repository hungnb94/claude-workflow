# PR Explainer Templates

Fill the facts table first. Both versions use only the facts in the table. Write `Not confirmed` in any cell you cannot support with evidence.

## Facts table

| Field | Need | How to fill |
|---|---|---|
| PR type | Required | Bug fix, or Change (feature, refactor, performance, docs, chore, revert). |
| Problem | Required | Bug: the symptom users see. Change: what was missing or hard. |
| Root cause (bug) or Reason for change (non-bug) | Required | Mark `Verified` with evidence (file, function, commit, log, test) or `Not confirmed`. |
| Contributing factors | Optional | Conditions that made the cause matter. |
| Broken invariant | Optional | The rule the code must always keep, if one was broken. Write it as a rule. Leave out if none. |
| Fix or What changed | Required | Main files and functions. If there is a broken invariant, the fix restores it. |
| Safety nets | Optional | Extra guards (null check, try/catch, skip). Label "Safety net, not the fix". Leave out if none. |
| Why this approach | Optional | Other options that were rejected, if known. Else `Not confirmed`. |
| Impact | Required | Who or what is affected, scope, severity. Only from data. |
| Risks and limits | Optional | What the change does not cover. |
| How it was verified | Required | Only checks that actually ran: what, how it was run, result. Else `Not confirmed`. |
| Suggested checks for QA | Optional | User actions that go through the changed code path. From the code, not guesses. Leave out if no user-facing path changed. |
| Sources used | Required | PR number, linked issue, commits. |

Skeleton:

```markdown
| Field | Value |
|---|---|
| PR type | |
| Problem | |
| Root cause | Verified: ... (evidence) / Not confirmed |
| Contributing factors | |
| Broken invariant | The rule, if any |
| Fix | |
| Safety nets | Safety net, not the fix: ... |
| Why this approach | |
| Impact | |
| Risks and limits | |
| How it was verified | Only what ran: what, how, result / Not confirmed |
| Suggested checks for QA | |
| Sources used | |
```

## Metaphor version

Use 100 to 200 words, about one minute of reading. Use one everyday metaphor from start to end. Open with the conclusion. Say the "why it matters" part in plain business words, not only inside the metaphor. Headings are always in English. Keep the metaphor in every part, not only at the end.

### Metaphor version skeleton

````markdown
<One sentence: the conclusion, in the metaphor. What users saw is fixed.>

**What went wrong:** <what happened, in the metaphor>

**Why it matters:** <what users or the business saw or lost, in plain words>

**How we fixed it:** <the fix, in the metaphor>

**Where the comparison stops:** <one sentence on what the metaphor does not cover>

<Optional: one sentence inviting questions, if still under 200 words.>
````

## Metaphor mapping check

Fill this table before you write. Keep it short.

| Metaphor part | Real part | Accurate (scope, severity, cause, who acts on what and when)? |
|---|---|---|
| | | |

Ask four questions.

- Does every main part of the bug and the fix have a match?
- Does the metaphor make the scope or severity look bigger or smaller than it is?
- Does it suggest a cause that differs from the facts table?
- Does the metaphor have the same causal structure: who acts on what, and in what order? For a timing bug: who reads, who writes, and when?

If any answer is a problem, change the metaphor or fix the sentence.

Counter-example: a double bank withdrawal (two people take money from one account at once) is the wrong key for a bug where one side reads while the other side is halfway through writing. In the withdrawal, both sides write. Pick a metaphor where one side reads (or copies) while the other side rewrites.

## Technical version

Cite real files, functions, and commits. Explain the mechanism: what triggers the bug and why the old code was wrong. Keep verified facts apart from guesses. Open with the conclusion. Say why before what.

### Technical version skeleton

````markdown
**Summary:** <1-2 specific sentences: the conclusion, the bug and the fix. It must stand alone.>

**Root cause:** <start with the broken rule, if any. Then the mechanism, with `path/file.ext`, `functionName`, commit hash. Add contributing factors.>

**Fix and why this approach:** <how the fix restores the rule, and why. Other options if known.>

**Safety net, not the fix:** <optional: extra guards. Leave out if none.>

**Impact and risks:** <who is affected, scope, limits, risks>

**How it was verified:** <only checks that ran: what, how, result. Else Not confirmed.>

**Suggested checks for QA:** <optional: leave out if no user-facing path changed>

1. <user action that goes through the changed code path>

**Verified:**

- <fact and evidence>

**Not confirmed:**

- <guess or open point, labeled "Hypothesis" if it has partial evidence>
````

## Non-bug changes

Use the same skeletons. Change the headings.

| Bug heading | Non-bug heading |
|---|---|
| What went wrong | What was missing or hard |
| Root cause | Why this change |
| How we fixed it | What we changed |

Leave out Broken invariant and Safety net if there are none. For a refactor, write "no behavior change expected" only when the diff or tests show it.

## Example

Illustrative only. All file names, function names, PR and issue numbers are made up.

Facts table:

| Field | Value |
|---|---|
| PR type | Bug fix |
| Problem | The app sometimes closed (crashed) while the watchlist refreshed prices. |
| Root cause | Verified (code read): `WatchlistSyncWorker.buildPayload()` loops over the live watchlist on a background thread. At the same time `WatchlistViewModel.onPricesUpdated()` clears and refills that list on the main thread. The loop sees a half-rebuilt list and throws `ConcurrentModificationException`. |
| Contributing factors | Price updates got more frequent, so the overlap happened more often. Not confirmed (no data). |
| Broken invariant | Only the main thread reads or changes the live watchlist. Other threads read a copy. |
| Fix | At the end of each update, on the main thread, `onPricesUpdated()` publishes a read-only snapshot (`toList()`). The worker reads only the snapshot. |
| Why this approach | The snapshot is taken on the main thread between updates, so it is never half-built. Copying on the background thread was rejected: the copy itself would loop over the live list mid-update. A lock was rejected: it could block the main thread. |
| Safety nets | The worker catches the exception, logs it, and skips that sync round. Safety net, not the fix. |
| Impact | Users saw the app close during a refresh and had to reopen it. The saved watchlist did not change (the worker only reads). Number of affected users: Not confirmed. |
| Risks and limits | The snapshot is up to one update old when the worker reads it. |
| How it was verified | Not confirmed. This is an illustrative example; no test was run. |
| Suggested checks for QA | 1. Open a watchlist with 20+ symbols and pull to refresh several times quickly. 2. Add and remove a symbol while prices refresh. 3. Leave the app in the background longer than one sync interval, then reopen it. The app stays open and the list is correct. |
| Sources used | PR #456, issue #450 (made up). |

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

Causal structure: one side reads while the other side writes. Same as the bug. A double bank withdrawal would be wrong here: both sides write.
