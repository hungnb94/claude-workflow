---
name: solution-brainstorm
disable-model-invocation: true
description: Brainstorm solutions for a coding task. Reads the codebase, detects the platform and architecture, lists 10 options, narrows them to 3 (Minimal, Balanced, Durable) with a fixed scoring table, then recommends one and asks the user to choose. Runs only when the user types /solution-brainstorm. Do not use to write implementation code, review code, or edit files.
---

# Solution Brainstorm

Think through a coding task before any code is written. Produce 10 options, keep the best 3, recommend one, and stop to ask the user.

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
- Read `platforms.md`. Pick every section whose **Detect** line matches what you found.
  - Several match: use the most specific one (most distinctive signals). Keep the others as secondary context.
  - None match: tell the user and use general best practice.
- If the chosen section has a **Standards** line, follow it and Read that file. If it cannot be read, say so and continue.

### Step 2. Check for outdated tech

Compare the project with the **Outdated signals** line of the section, or with the migration rules in the linked Standards file.

- Signal found: list what you found (file and line). Ask once: migrate as part of this task, or keep the current tech? Wait for the answer.
- A convention in source 1 that already decides it counts as the answer. Do not ask again.
- No signal found: continue.

### Step 3. Clarify

Ask only what blocks option design, at most 5 questions. If the task is clear, ask none. If the user says to just go, write an **Assumptions** list and continue.

### Step 4. Diverge: 10 options

Always write exactly 10 options. No shortcut for easy tasks. Each option differs from the others in its main pattern. The table always has 10 rows; an idea that shares a pattern with another stays as its own row marked `Merged into #n`.

### Step 5. Converge: best 3

Score the options on the criteria in `templates.md`. Keep 3 that differ in main pattern and span the investment levels: A Minimal, B Balanced, C Durable. Scores are 1-5 per criterion. Do not add them up.

### Step 6. Write and stop

Read `templates.md` (next to this file) and fill it in. Use the project language for skeletons. Keep each skeleton short; mark `// pseudo` when you are unsure of an API.

End with the recommendation and ask the user which option to choose. Then stop. Offer to implement it or to hand it to `/feature-workflow`, but do neither on your own.
