# Templates

Read at Steps 4-6 and by the brainstorm subagents. The counts and criteria below are the only ones. Change a count or a criterion here, not in `SKILL.md`.

## Counts

- Options: 18
- Kept: 9
- Detailed: 3
- Min per level: 2
- Generators: 2
- Options per generator: 9
- Judge passes: 2

**Generators** times **Options per generator** equals **Options**: each generator fills its share of the rows. Each judge pass reads the kept options in a different order.

Sort the kept options by investment and label them A, B, C and so on. A is the cheapest Low option and the last one is the most durable High option. Keep at least **Min per level** options at each of Low, Mid and High. If a level has fewer fitting options than **Min per level**, fill it with the closest ones and say why in each one's Reason cell.

Rank the kept options by averaged judge Total, highest first; on a tie, the lower investment goes first, then the earlier label. The first **Detailed** of them are the top options, marked `⭐ top 1`, `⭐ top 2` and so on in rank order. The recommended option is always a top option: if the rank leaves it out, it takes the last top place and its marker. Top options get the full block in part 5; every other kept option gets the short block. The marker never changes the label order of parts 4 and 5.

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

Two or three lines: the task, the detected platform and the paths of its standards, the architecture you found, and any project convention that shaped the options. Then one line naming the lenses the generators used, and any generator or judge pass that failed and what you did instead. Then one bullet per SRP hit and per owner scope dependency from Step 1, if any.

### 2. Assumptions

Only if the user said to just go, or a caller is set. One bullet per assumption.

### 3. All options

Always one row per option, as many rows as **Options** in Counts. One or two lines per row. Rows follow the generators in lens order. Put the whole part inside `<details>` with the summary `All <Options> options`, and leave a blank line after the summary so the table renders.

| # | Option (main pattern) | Lens | Investment | Verdict | Reason |
|---|---|---|---|---|---|
| 1 | Name (pattern) | conventions | Low / Mid / High | Kept / Dropped / Merged into #n | Why, tied to this project |

As many rows as **Kept** in Counts are `Kept`, following the investment rule in Counts. Use `Merged into #n` only when a row shares the main pattern of an earlier row #n.

### 4. Kept options

Only the kept options, one row each in label order. Put each top option's marker from Counts after its label, like `C ⭐ top 1`. One sentence per How it works cell and one phrase per When to choose cell. Total is the option's Total from the score table below.

| Label | Option (main pattern) | Investment | How it works | When to choose | Total |
|---|---|---|---|---|---|
| <label> | Name (pattern) | Low / Mid / High | One sentence | One phrase | <Total>/35 |

Right below that table, put the scores by criterion inside `<details>` with the summary `Scores by criterion`, and leave a blank line after the summary so the table renders. One column per kept option in label order; keep its column count equal to **Kept**. One row per criterion, in the order of the Criteria list, then a bold Total row. Each score is the judge's score averaged over the **Judge passes**. Total is the plain sum of the option's scores, out of 35 (5 x 7 criteria). All criteria weigh the same.

| Criterion | A (Low) | B | C | D | E | F | G | H | I (High) |
|---|---|---|---|---|---|---|---|---|---|
| Fit with current architecture and conventions | 1-5 | 1-5 | 1-5 | 1-5 | 1-5 | 1-5 | 1-5 | 1-5 | 1-5 |
| (one row for each remaining criterion) | 1-5 | 1-5 | 1-5 | 1-5 | 1-5 | 1-5 | 1-5 | 1-5 | 1-5 |
| **Total (/35)** | **sum** | **sum** | **sum** | **sum** | **sum** | **sum** | **sum** | **sum** | **sum** |

### 5. Kept options in detail

One block per kept option, in label order. Every heading ends with the option's Total in parentheses, so the reader never scrolls back to the scores. A top option (Counts) uses the full block, with its marker after the label; every other kept option uses the short block.

Full block, for a top option:

```markdown
#### Option <label> <⭐ top n> - <name> (<main pattern>, <Low / Mid / High>) (<Total>/35)

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

Short block, for every other kept option:

```markdown
#### Option <label> - <name> (<main pattern>, <Low / Mid / High>) (<Total>/35)

**Trade-off:** <only if it goes against the current architecture: which convention it breaks>

- How it works: 1-2 sentences.
- Pros: one line.
- Cons: one line.
- When to choose:
- Legacy technique (only when the full block would have a Legacy technique & tests line): technique and rung, plus `Lý do bậc rẻ hơn không đủ` if it climbs.
- Effort: S | M | L
```

### 6. Recommendation

```markdown
**Recommendation:** Option <X> (<Total>/35), because <reason tied to this project>.

<only if X does not have the highest Total: why it still wins over the higher-scoring option>

<only if the judge passes shortlisted different options or reported close calls: which options, and the one question that would separate them>

<only if the SRP check fired: Follow-up refactors, one line per responsibility left in the target (file:line, technique); they can become tickets with `/issue-writing`>

Which option do you choose? After that I can implement it, or you can hand it to `/feature-workflow`.
```

Leave out the closing question when a caller is set (`SKILL.md` Step 0).
