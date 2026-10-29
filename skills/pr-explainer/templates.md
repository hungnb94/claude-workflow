# PR Explainer Templates

Fill the facts table first. Both versions use only the facts in the table. Write `Not confirmed` in any cell you cannot support with evidence. In Vietnamese, write "Chưa xác định".

## Facts table

| Field | Need | How to fill |
|---|---|---|
| PR type | Required | Bug fix, or Change (feature, refactor, performance, docs, chore, revert). |
| Problem | Required | Bug: the symptom users see. Change: what was missing or hard. |
| Root cause (bug) or Reason for change (non-bug) | Required | Mark `Verified` with evidence (file, function, commit, log, test) or `Not confirmed`. |
| Contributing factors | Optional | Conditions that made the cause matter. |
| Fix or What changed | Required | Main files and functions. |
| Why this approach | Optional | Other options that were rejected, if known. Else `Not confirmed`. |
| Impact | Required | Who or what is affected, scope, severity. Only from data. |
| Risks and limits | Optional | What the change does not cover. |
| How it was verified | Required | Tests added or run, manual checks. Else `Not confirmed`. |
| Sources used | Required | PR number, linked issue, commits. |

Skeleton:

```markdown
| Field | Value |
|---|---|
| PR type | |
| Problem | |
| Root cause | Verified: ... (evidence) / Not confirmed |
| Contributing factors | |
| Fix | |
| Why this approach | |
| Impact | |
| Risks and limits | |
| How it was verified | |
| Sources used | |
```

## Metaphor version

Use 100 to 200 words, about one minute of reading. Use one everyday metaphor from start to end. Open with the conclusion. Say the "why it matters" part in plain business words, not only inside the metaphor. The heading language follows the output language.

### Metaphor version skeleton

````markdown
<One sentence in the metaphor: the problem is fixed.>

**What went wrong:** <what happened, in the metaphor>

**Why it matters:** <what users or the business saw or lost, in plain words>

**How we fixed it:** <the fix, in the metaphor>

**Where the comparison stops:** <one sentence on what the metaphor does not cover>

<Optional: one sentence inviting questions, if still under 200 words.>
````

## Metaphor mapping check

Fill this table before you write. Keep it short.

| Metaphor part | Real part | Accurate (scope, severity, cause)? |
|---|---|---|
| | | |

Ask three questions.

- Does every main part of the bug and the fix have a match?
- Does the metaphor make the scope or severity look bigger or smaller than it is?
- Does it suggest a cause that differs from the facts table?

If any answer is a problem, change the metaphor or fix the sentence.

## Technical version

Cite real files, functions, and commits. Explain the mechanism: what triggers the bug and why the old code was wrong. Keep verified facts apart from guesses.

### Technical version skeleton

````markdown
**Summary:** <1-2 specific sentences: the bug and the fix. It must stand alone.>

**Root cause:** <mechanism, with `path/file.ext`, `functionName`, commit hash. Add contributing factors.>

**Fix and why this approach:** <what changed, and why. Other options if known.>

**Impact and risks:** <who is affected, scope, limits, risks>

**How it was verified:** <tests added or run, commands, results>

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

For a refactor, write "no behavior change expected" only when the diff or tests show it.

## Example

Illustrative only. All names are made up.

Facts table:

| Field | Value |
|---|---|
| PR type | Bug fix |
| Problem | Reloading the cart page applied the coupon discount twice. |
| Root cause | Verified: `applyCoupon` in `cart/pricing.js` ran on each page load and added to the saved total. |
| Fix | `applyCoupon` now computes the total from the base price each time. |
| Impact | Customers with a coupon saw a price that was too low. Scope not measured. |
| How it was verified | Verified: new test `reload keeps discount single` passes. |

Plain-language version (metaphor):

````markdown
The double-discount problem is fixed.

**What went wrong:** Think of a cashier who scans a discount voucher. If you walked away and came back, the cashier scanned the same voucher again and took off the discount a second time.

**Why it matters:** Customers who reloaded the cart page saw a price lower than the real price. That is lost revenue, and it could confuse people at checkout.

**How we fixed it:** Now the cashier starts from the shelf price every time and applies the voucher once.

**Where the comparison stops:** A real cashier remembers the voucher. Our system did not, and the cause was a calculation step, not a person.
````

Technical version:

````markdown
**Summary:** Fix the coupon discount being applied twice when the cart page reloads.

**Root cause:** `applyCoupon` in `cart/pricing.js` added the discount to the saved total on every page load instead of the base price.

**Fix and why this approach:** `applyCoupon` now computes the total from the base price each time. This makes the result the same on every reload.

**Impact and risks:** Customers with a coupon saw a lower price. The number of affected orders is not measured.

**How it was verified:** New test `reload keeps discount single` passes.

**Verified:**

- Root cause in `applyCoupon` (code read).
- New test passes.

**Not confirmed:**

- How many orders were affected.
````

Mapping check:

| Metaphor part | Real part | Accurate? |
|---|---|---|
| Cashier scans voucher again | Discount added again on reload | Yes, same cause |
| Price lower than shelf price | Total too low | Yes, same severity |
| Start from shelf price | Compute from base price | Yes |

In Vietnamese, pick a metaphor from everyday Vietnamese life. Do not translate the English one word for word.
