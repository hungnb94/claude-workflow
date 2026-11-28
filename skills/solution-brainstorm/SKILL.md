---
name: solution-brainstorm
description: Brainstorm solutions for a coding task. Reads the codebase, detects the platform and architecture, lists 18 options from generator subagents that each read a different knowledge lens, narrows them to 9 (sorted from Low to High investment), has a blind judge subagent score them on a fixed table, details the top 3, then recommends one and asks the user to choose. Use when the user explicitly asks for options, approaches, or trade-offs before coding, such as "what are the ways to", "how should I solve", "compare approaches", or "brainstorm solutions". Do not use for plain implement, fix, or review requests, or to write implementation code or edit files.
---

# Solution Brainstorm

Think through a coding task before any code is written. Produce many options, keep the best few (counts in `templates.md`), recommend one, and stop to ask the user.

The output follows the user's language. Keep technical terms in English.

Read-only: do not edit files, and do not write implementation code. Use subagents only in Steps 4 and 5, and never `subagent_type: "fork"`: a fork inherits your context, so the lenses stop differing and the judge stops being blind. Do not start any other workflow; only suggest one in the last message.

## Source priority

When sources disagree, the higher one wins:

1. Project conventions: CLAUDE.md, AGENTS.md, docs/adr, and the existing code layout.
2. The platform standards found at Step 1.
3. General best practice.

An option that goes against source 1 is still allowed. Label it **Trade-off** and name the convention it breaks.

## Workflow

### Step 0. Get the task

The task is `$ARGUMENTS`. A caller that invokes this skill on its own, the model or another skill, passes a one-line task summary as the argument. If `$ARGUMENTS` is empty or only spaces, ask the user what to solve. Do not guess a task.

When the argument contains the line `CALLER: feature-workflow`, the calling workflow has already agreed the requirements with the user and picks the option itself. Then Read the requirements file the argument names, skip Step 3 and the question at the end of Step 6, and write an **Assumptions** list (including the migration choice from Step 2, if any). The requirements file and the Assumptions take the place of the Step 3 answers in `BRIEF`.

### Step 1. Survey and detect

- Read the build files, the package or folder layout, CLAUDE.md, AGENTS.md, and docs/adr.
- Follow `standards-lookup.md` (next to this file; if missing, Glob `**/solution-brainstorm/standards-lookup.md`) to pick the platform section in `platforms.md` and read its standards. When a caller is set (Step 0) and the requirements file already records the platform and standards, use those standards instead of looking them up again, but still read that platform's section in `platforms.md` for Step 2's **Outdated signals**. Write the platform and the absolute paths of its standards in your Context notes, so they reach `BRIEF`. Use only the architecture, pattern, and migration rules of the standards; ignore rules about how another workflow runs (slices, delegation, commits).
- Mark the target as untested legacy when no test covers it or it cannot be instantiated in a test. Then Read `legacy-techniques.md` (next to this file; if missing, Glob `**/solution-brainstorm/legacy-techniques.md`). If it cannot be read, say so and continue. Use `Mũ: feature` techniques only when the task adds behavior; for a pure refactor use only `Mũ: chung` techniques (Two Hats).
- Apply the SRP check (`## Kiểm tra SRP` in `legacy-techniques.md`) to every class and function the task changes, tested or not. Note each hit (file:line, test net or not) in Context.
- Apply the owner scope check (`## Kiểm tra phạm vi owner` in `legacy-techniques.md`) to every lifecycle, listener, or scope dependency the task adds or rebinds. Note its owners (narrow to wide, with cause) in Context.

### Step 2. Check for outdated tech

Compare the project with the **Outdated signals** line of the section and with the migration rules in the standards from Step 1, if any.

- Signal found: list what you found (file and line). Add one question to Step 3: migrate as part of this task, or keep the current tech?
- A convention in source 1 that already decides it counts as the answer. Do not ask.
- No signal found: continue.

### Step 3. Clarify

Ask everything in one message, then wait: the migration question from Step 2 (if any) plus only what blocks option design, at most 5 questions in total. If nothing blocks, or a caller is set (Step 0), ask none and continue. If the user says to just go, write an **Assumptions** list (including the migration choice you assumed) and continue.

### Step 4. Diverge

Read `templates.md` and `lenses.md` (both next to this file). Pick as many lenses as **Generators** in Counts, in the pick order of `lenses.md`. In one message, spawn one `sb-1-generator` per lens so none sees another's output. Pass only `BRIEF` (the task, your Context notes, and the Step 3 answers or Assumptions), `LENS`, the absolute paths `LENS_CATALOG` and `TEMPLATES`, and `OPTION_COUNT` (**Options per generator** in Counts). If a generator fails or returns too few cards, write its missing rows yourself through the same lens and say so in Context.

Merge the cards into part 3 in lens order. Always write as many options as **Options** in its Counts. No shortcut for easy tasks. A row that shares the main pattern of an earlier row #n stays as its own row, marked `Merged into #n`; the row count never changes.

### Step 5. Converge

Judge every option against the criteria in `templates.md` and give each a verdict. Keep as many as **Kept** in its Counts. The kept options differ in main pattern and follow the investment rule in Counts.

Score the kept options with the blind judge:

1. Use each option's card in the `## Option card` shape of `templates.md` (the generator's, or yours for a row you wrote), without its Knowledge line, which would reveal the lens. Put any Trade-off, `nợ SRP`, or `Lý do scope rộng hơn` from its Reason cell into Breaks convention. Relabel the cards `O1`, `O2`, and so on in a shuffled order.
2. In one message, spawn as many `sb-2-judge` as **Judge agents** in Counts. Give each `ORDERS`: as many reading orders of the labels as **Judge orderings** in Counts. The second order reverses the first; any later order is a new shuffle. Also pass `BRIEF`, `TEMPLATES`, `CARDS`, and `SHORTLIST` (**Detailed** in Counts).
3. Map the labels back and average each score over every ordering of every judge. Add up each option's scores into the Total row described in `templates.md`. Recheck each sum before writing it. Keep any shortlist disagreement between orderings or close call for the Recommendation. If a judge returns fewer tables than the orders in its `ORDERS`, or two identical tables, or every judge fails, say so in Context and score each ordering that has no table yourself.

Untested legacy: A uses the cheapest sufficient rung of the catalog's cost ladder. Any later option that climbs a rung states why the cheaper rung is not enough (`Lý do bậc rẻ hơn không đủ`).

SRP check fired: drop any option that puts a new responsibility into the target. A follows the check's cheapest reaction; an in-place option names its `nợ SRP` in its Reason cell and scores lower on criterion 7.

Owner scope check fired: drop any option that reaches its owner through a wider object. A wider-owner option writes `Lý do scope rộng hơn` in its Reason cell.

### Step 6. Write and stop

Read `comment-policy.md` (next to this file). Fill in the `templates.md` output. Use the project language for skeletons. Keep each skeleton short and follow the comment policy: no comments except `// pseudo` when you are unsure of an API.

End with the recommendation and ask the user which option to choose. Then stop. Offer to implement it or to hand it to `/feature-workflow`, but do neither on your own.

When a caller is set (Step 0), leave out the closing question and the offer, and hand control back to the caller after the recommendation.

If the user later asks you to implement the chosen option in this session, write the code by `comment-policy.md`.
