# Templates

Fill these in at Step 6. The counts and criteria below are the only ones. Change a count or a criterion here, not in `SKILL.md`.

## Counts

- Options: 18
- Kept: 9
- Detailed: 3
- Min per level: 2

Sort the kept options by investment and label them A, B, C and so on. A is the cheapest Low option and the last one is the most durable High option. Keep at least **Min per level** options at each of Low, Mid and High. If a level has fewer fitting options than **Min per level**, fill it with the closest ones and say why in each one's Reason cell.

Pick as many kept options as **Detailed**, highest Total first; on a tie, the lower investment goes first, then the earlier label. The recommended option is always picked: if the rule leaves it out, it takes the place of the last one picked. Only the picked options get the full block in part 5.

## Criteria

Score each option 1-5 per criterion. 5 is always the best end.

1. Fit with current architecture and conventions
2. Testability
3. Effort and complexity (5 = least)
4. Extensibility without over-engineering
5. Risk and migration cost (5 = lowest)
6. Performance and operations
7. Maintainability (SRP, cohesion, coupling): 5 = every touched class and function keeps one reason to change and uses the narrowest owner

## Option card

Generators write each option in this shape and the judge reads it. Each field is one line; How it works is at most 3 sentences. Equal-length cards keep a long card from winning on length alone.

```markdown
#### <n>. <Name> (<main pattern>)

- Investment: Low / Mid / High
- How it works: <at most 3 sentences, tied to files or conventions in this codebase>
- Breaks convention: <the project convention it goes against, or none>
- Knowledge: <the source the idea comes from: a path or a URL>
```

## Judge rubric

What 5 and 1 mean for each criterion. Score in between by how close the card is to each end.

- **Fit**: 5 = follows every convention in the brief; 1 = breaks a project convention without a stated reason.
- **Testability**: 5 = the new behavior is testable with the current test setup; 1 = needs a large new harness first.
- **Effort**: 5 = a few files in one module; 1 = many modules or a data migration.
- **Extensibility**: 5 = the next similar change adds code without editing this one, and nothing is built for needs that do not exist yet; 1 = every similar change edits it again, or it adds layers nothing uses.
- **Risk**: 5 = easy to revert, no change to data or a public API; 1 = a one-way change to data or a public API.
- **Performance and operations**: 5 = no new runtime cost and nothing new to run; 1 = a measurable cost on a hot path, or new infrastructure to operate.
- **Maintainability**: 5 = every touched class and function keeps one reason to change and uses the narrowest owner; 1 = adds a responsibility to a class that already mixes them.

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

| Criterion | A (Low) | B | C | D | E | F | G | H | I (High) |
|---|---|---|---|---|---|---|---|---|---|
| Fit with current architecture and conventions | 1-5 | 1-5 | 1-5 | 1-5 | 1-5 | 1-5 | 1-5 | 1-5 | 1-5 |
| (one row for each remaining criterion) | 1-5 | 1-5 | 1-5 | 1-5 | 1-5 | 1-5 | 1-5 | 1-5 | 1-5 |
| **Total (/35)** | **sum** | **sum** | **sum** | **sum** | **sum** | **sum** | **sum** | **sum** | **sum** |

### 5. Kept options in detail

Repeat this block for each option picked by **Detailed** in Counts, in label order.

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

Then put every other kept option into one table, one row each, in label order. One line per cell. When the full block would have a **Trade-off** line, start the How it works cell with `Trade-off: <convention it breaks>`. When the full block would have a Legacy technique & tests line, name the technique and rung in the How it works cell, plus `Lý do bậc rẻ hơn không đủ` if it climbs.

| Label | Option (main pattern) | Investment | How it works | When to choose | Effort |
|---|---|---|---|---|---|
| <label> | Name (pattern) | Low / Mid / High | One sentence | One phrase | S / M / L |

### 6. Recommendation

```markdown
**Recommendation:** Option <X>, because <reason tied to this project>.

<only if X does not have the highest Total: why it still wins over the higher-scoring option>

<only if the SRP check fired: Follow-up refactors, one line per responsibility left in the target (file:line, technique); they can become tickets with `/issue-writing`>

Which option do you choose? After that I can implement it, or you can hand it to `/feature-workflow`.
```
