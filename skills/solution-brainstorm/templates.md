# Templates

Fill these in at Step 6. The counts and criteria below are the only ones. Change a count or a criterion here, not in `SKILL.md`.

## Counts

- Options: 15
- Kept: 6

Sort the kept options by investment and label them A, B, C and so on. A is the cheapest Low option, the last one is the most durable High option, and at least one kept option is Mid. If no fitting option exists for a level, keep the closest one and say why in its Reason cell.

## Criteria

Score each option 1-5 per criterion. 5 is always the best end.

1. Fit with current architecture and conventions
2. Testability
3. Effort and complexity (5 = least)
4. Extensibility without over-engineering
5. Risk and migration cost (5 = lowest)
6. Performance and operations
7. Maintainability (SRP, cohesion, coupling): 5 = every touched class and function keeps one reason to change and uses the narrowest owner

## Output

Write in the user's language. Keep technical terms in English. Use these parts in this order.

### 1. Context

Two or three lines: the task, the detected platform, the architecture you found, and any project convention that shaped the options. Then one bullet per SRP hit and per owner scope dependency from Step 1, if any.

### 2. Assumptions

Only if the user said to just go. One bullet per assumption.

### 3. All options

Always one row per option, as many rows as **Options** in Counts. One or two lines per row.

| # | Option (main pattern) | Investment | Verdict | Reason |
|---|---|---|---|---|
| 1 | Name (pattern) | Low / Mid / High | Kept / Dropped / Merged into #n | Why, tied to this project |

As many rows as **Kept** in Counts are `Kept`, following the investment rule in Counts. Use `Merged into #n` only when a row shares the main pattern of an earlier row #n.

### 4. Scores

Only the kept options, one column each in label order. The table below shows one column per kept option; keep its column count equal to **Kept**. One row per criterion, in the order of the Criteria list, then a bold Total row. Total is the plain sum of the option's scores, out of 35 (5 x 7 criteria). All criteria weigh the same.

| Criterion | A (Low) | B | C | D | E | F (High) |
|---|---|---|---|---|---|---|
| Fit with current architecture and conventions | 1-5 | 1-5 | 1-5 | 1-5 | 1-5 | 1-5 |
| (one row for each remaining criterion) | 1-5 | 1-5 | 1-5 | 1-5 | 1-5 | 1-5 |
| **Total (/35)** | **sum** | **sum** | **sum** | **sum** | **sum** | **sum** |

### 5. Kept options in detail

Repeat this block for each kept option, in label order.

```markdown
#### Option <label> - <name> (<main pattern>, <Low / Mid / High>)

**Trade-off:** <only if it goes against the current architecture: which convention it breaks>

- How it works: 3-5 sentences.
- Layers/files: a short tree.
- Skeleton: at most about 20 lines in the project language. No comments (`comment-policy.md`); mark `// pseudo` if you are unsure of an API.
- Pros:
- Cons:
- When to choose:
- Legacy technique & tests (only when Step 1 found an untested legacy target or the SRP check fired): technique and rung from `legacy-techniques.md`; new-code tests written first (TDD) covering happy/edge/error; call-site characterization test, or the untested debt; why a cheaper rung is not enough (`Lý do bậc rẻ hơn không đủ`) if it climbs.
- Effort: S | M | L
```

### 6. Recommendation

```markdown
**Recommendation:** Option <X>, because <reason tied to this project>.

<only if X does not have the highest Total: why it still wins over the higher-scoring option>

<only if the SRP check fired: Follow-up refactors, one line per responsibility left in the target (file:line, technique); they can become tickets with `/issue-writing`>

Which option do you choose? After that I can implement it, or you can hand it to `/feature-workflow`.
```
