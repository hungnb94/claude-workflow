# Templates

Fill these in at Step 6. The criteria below are the only scoring criteria. Change a criterion here, not in `SKILL.md`.

## Criteria

Score each option 1-5 per criterion. 5 is always the best end.

1. Fit with current architecture and conventions
2. Testability
3. Effort and complexity (5 = least)
4. Extensibility without over-engineering
5. Risk and migration cost (5 = lowest)
6. Performance and operations

## Output

Write in the user's language. Keep technical terms in English. Use these parts in this order.

### 1. Context

Two or three lines: the task, the detected platform, the architecture you found, and any project convention that shaped the options.

### 2. Assumptions

Only if the user said to just go. One bullet per assumption.

### 3. The 10 options

Always 10 rows. One or two lines per row.

| # | Option (main pattern) | Investment | Verdict | Reason |
|---|---|---|---|---|
| 1 | Name (pattern) | Low / Mid / High | Kept / Dropped / Merged into #n | Why, tied to this project |

Exactly 3 rows are `Kept`, one per investment level. Use `Merged into #n` only when a row shares the main pattern of an earlier row #n.

### 4. Scores

Only the 3 kept options. One row per criterion, in the order of the Criteria list. Do not add a sum row.

| Criterion | A (Minimal) | B (Balanced) | C (Durable) |
|---|---|---|---|
| Fit with current architecture and conventions | 1-5 | 1-5 | 1-5 |

### 5. The 3 options in detail

Repeat this block for A, B and C.

```markdown
#### Option A - <name> (<main pattern>)

**Trade-off:** <only if it goes against the current architecture: which convention it breaks>

- How it works: 3-5 sentences.
- Layers/files: a short tree.
- Skeleton: at most about 20 lines in the project language. Mark `// pseudo` if you are unsure of an API.
- Pros:
- Cons:
- When to choose:
- Effort: S | M | L
```

### 6. Recommendation

```markdown
**Recommendation:** Option <X>, because <reason tied to this project>.

Which option do you choose? After that I can implement it, or you can hand it to `/feature-workflow`.
```
