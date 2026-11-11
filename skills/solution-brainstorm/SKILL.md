---
name: solution-brainstorm
disable-model-invocation: true
description: Brainstorm solutions for a coding task. Reads the codebase, detects the platform and architecture, lists 15 options, narrows them to 6 (sorted from Low to High investment) with a fixed scoring table and a total per option, then recommends one and asks the user to choose. Runs only when the user types /solution-brainstorm. Do not use to write implementation code, review code, or edit files.
---

# Solution Brainstorm

Think through a coding task before any code is written. Produce many options, keep the best few (counts in `templates.md`), recommend one, and stop to ask the user.

The output follows the user's language. Keep technical terms in English.

Read-only: do not edit files, and do not write implementation code. Run in one pass without subagents. Do not start any other workflow; only suggest one in the last message.

## Source priority

When sources disagree, the higher one wins:

1. Project conventions: CLAUDE.md, AGENTS.md, docs/adr, and the existing code layout.
2. The matched section in `platforms.md` (next to this file).
3. General best practice.

An option that goes against source 1 is still allowed. Label it **Trade-off** and name the convention it breaks.

## Workflow

### Step 0. Get the task

If `$ARGUMENTS` is empty or only spaces, ask the user what to solve. Do not guess a task.

### Step 1. Survey and detect

- Read the build files, the package or folder layout, CLAUDE.md, AGENTS.md, and docs/adr.
- Read `platforms.md`. A section matches when at least one signal on its **Detect** line is present.
  - Several match: use the one with the most distinctive signals (a section's Detect line may say it wins over another). Keep the others as secondary context.
  - None match: tell the user and use general best practice.
- If the chosen section has a **Standards** line, follow it and Read that file. Use only its architecture, pattern, and migration rules; ignore rules about how another workflow runs (slices, delegation, commits). If it cannot be read, say so and continue.
- Mark the target as untested legacy when no test covers it or it cannot be instantiated in a test. Then Read `legacy-techniques.md` (next to this file; if missing, Glob `**/solution-brainstorm/legacy-techniques.md`). If it cannot be read, say so and continue. Use `Mũ: feature` techniques only when the task adds behavior; for a pure refactor use only `Mũ: chung` techniques (Two Hats).

### Step 2. Check for outdated tech

Compare the project with the **Outdated signals** line of the section and with the migration rules in the linked Standards file, if any.

- Signal found: list what you found (file and line). Add one question to Step 3: migrate as part of this task, or keep the current tech?
- A convention in source 1 that already decides it counts as the answer. Do not ask.
- No signal found: continue.

### Step 3. Clarify

Ask everything in one message, then wait: the migration question from Step 2 (if any) plus only what blocks option design, at most 5 questions in total. If nothing blocks, ask none and continue. If the user says to just go, write an **Assumptions** list (including the migration choice you assumed) and continue.

### Step 4. Diverge

Read `templates.md` (next to this file). Always write as many options as **Options** in its Counts. No shortcut for easy tasks. Aim for a different main pattern in each row. If an idea turns out to share the main pattern of an earlier row, keep it as its own row and mark it `Merged into #n`, where #n is that earlier row. The row count never changes.

### Step 5. Converge

Judge every option against the criteria in `templates.md` and give each a verdict. Keep as many as **Kept** in its Counts. The kept options differ in main pattern and follow the investment rule in Counts. Score only the kept options, 1-5 per criterion. Add up each option's scores into the Total row described in `templates.md`. Recheck each sum before writing it.

Untested legacy: A uses the cheapest sufficient rung of the catalog's cost ladder. Any later option that climbs a rung states why the cheaper rung is not enough (`Lý do bậc rẻ hơn không đủ`).

### Step 6. Write and stop

Read `comment-policy.md` (next to this file). Fill in the `templates.md` output. Use the project language for skeletons. Keep each skeleton short and follow the comment policy: no comments except `// pseudo` when you are unsure of an API.

End with the recommendation and ask the user which option to choose. Then stop. Offer to implement it or to hand it to `/feature-workflow`, but do neither on your own.

If the user later asks you to implement the chosen option in this session, write the code by `comment-policy.md`.
