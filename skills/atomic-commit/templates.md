# Atomic Commit - Templates

## Commit message template

```text
<type>[(<scope>)]: <subject>

<body: explain what changed and why, wrapped at 72 characters>
```

Rules:

- The header is the whole first line, including the `type(scope):` prefix. Aim for 50 characters or less. 72 is the hard limit.
- Use the imperative mood: "add", not "added" or "adds". The header should complete: "If applied, this commit will ...".
- Start the subject with a lowercase letter after the colon. Conventional Commits replaces the Beams capital-letter rule here.
- Do not end the subject with a period.
- Put one blank line between the header and the body.
- Wrap body lines at 72 characters. Explain what and why, not how.
- Skip the body when the change is obvious from the header.
- The scope is optional. Use a short noun such as a folder or module name.
- Footers and trailers are out of scope. Add them only if the user asks.

## Types

Use only these 11 types. They are the common Conventional Commits types, and the ones the claude-workflow PR title check accepts. If the target repo has its own type list, use that list instead.

| Type | Use when | Example header |
|---|---|---|
| feat | A new feature for the user | `feat: add CSV export to reports` |
| fix | A bug fix | `fix: stop crash on empty cart` |
| docs | Documentation only | `docs: explain the setup steps` |
| style | Formatting only, no change in meaning | `style: format files with prettier` |
| refactor | Code change that is not a fix or a feature | `refactor: extract price calculation` |
| perf | A change that makes code faster | `perf: cache the user lookup` |
| test | Add or fix tests only | `test: cover the empty cart case` |
| build | Build system or dependencies | `build: bump gradle to 8.5` |
| ci | CI configuration | `ci: run lint on pull requests` |
| chore | Other upkeep that touches no source or tests | `chore: ignore local env files` |
| revert | Undo an earlier commit | `revert: add CSV export to reports` |

For `revert`, use the header of the undone commit after `revert:`.

## Commit plan template

```text
Commit plan (3 commits)

1. refactor: rename total to orderTotal
   Files: src/cart.ts
   Why together: pure rename, no behavior change

2. fix: stop crash on empty cart
   Files: src/cart.ts (hunks: lines 40-58), src/cart.test.ts
   Why together: the fix and its test

3. docs: note the empty cart rule
   Files: README.md
   Why together: docs only

Already staged: commit 1 is the part you staged. I kept it as is.

Excluded (not committed)
- Possible secrets: .env.local
- Build or workflow artifacts: .workflows/, dist/

Merged on purpose
- src/cart.ts lines 12-30: the rename and the fix touch the same lines, so they stay in commit 2.

Questions
- None.

Reply 'ok' to commit, or tell me what to change.
```

Rules:

- Leave out a section when it has nothing to say, except "Excluded" when something was excluded.
- Number the commits in the order they will be created.
- Name hunks by line range in the new file when a file is split.

## Good and bad examples

### Headers

| Header | Verdict | Why |
|---|---|---|
| `fix: stop crash on empty cart` | Good | Imperative, short, one change |
| `feat(export): add CSV export` | Good | Optional scope, imperative |
| `fix: stopped crash on empty cart.` | Bad | Past tense and a final period |
| `feat: add export and fix login bug` | Bad | Two changes, needs "and" |
| `update: change stuff` | Bad | Type is not in the list, vague |
| `fix: Stop crash on empty cart` | Bad | Capital letter after the colon |
| `fix: handle the case where the shopping cart is empty when the user opens checkout` | Bad | Over 72 characters |
| `chore: fix stuff` | Bad | Vague, wrong type |

### A full message

```text
fix: stop crash on empty cart

Checkout read the first item without checking the list length. An
empty cart threw an index error and ended the session.

Return early with a zero total when the cart has no items.
```

### Splitting one working tree

The working tree has a variable rename, a bug fix, and the test for the fix.

Good, two commits:

```text
1. refactor: rename total to orderTotal
2. fix: stop crash on empty cart       (includes the test)
```

Bad, one commit:

```text
1. fix: rename total and stop crash on empty cart
```

The bad commit cannot be reverted without losing the rename, and the header needs "and".

## Final report template

```text
Created 3 commits:
- a1b2c3d refactor: rename total to orderTotal
- d4e5f6a fix: stop crash on empty cart
- 0b1c2d3 docs: note the empty cart rule

Not committed
- .env.local (possible secret)
- .workflows/ (workflow artifact)

Left in the working tree: nothing else.

Nothing was pushed.
```
