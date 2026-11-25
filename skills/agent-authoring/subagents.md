# Subagents

Read by `agent-authoring` when the task writes or changes a subagent, or delegates work to one.

## When to use one

A subagent runs the same model with a fresh context. It does not make an answer smarter. It helps in three cases only: (C4, P3)

- Noisy work whose result fits in a summary: exploring a repo, running a long test suite, web research.
- Truly independent work that can run in parallel.
- A fresh pair of eyes: a reviewer that did not see how the code was written. (P1)

Do the task in the main session when it already has the context, or when the task is small. A new subagent has to rebuild that context, which costs time and tokens.

## Rules

- **One writer at a time.** Every edit carries unstated decisions; two agents writing at once make conflicting ones. Subagents read in parallel; writing stays sequential, one task after another. Write in parallel only when the files and interfaces do not overlap and a shared check runs at the end. (C4)
- **Return a summary.** Ask for about 1,000-2,000 tokens with file:line references, not raw logs. (C4)
- **Least privilege.** List `tools` explicitly. A reviewer gets read-only tools (`Read, Grep, Glob`) and no Edit or Write. (P1)
- **Review against the spec.** Give a reviewer the diff and the spec or acceptance criteria, not the conversation. Ask it to report only correctness issues, with file:line, and to skip style. (P1)
- **Check the work, not the report.** A subagent's "done" is a claim. Before you accept it, read its diff and rerun the check yourself. (C1)
- **Short description.** Every description loads into every session. Say what the subagent does and when to delegate to it, in one or two sentences. Follow the repo's own limit if it has one.
- **Brief it fully.** The subagent knows only its prompt. Pass the goal, absolute paths, what is already ruled out, and the output shape.
- **Pick the model on purpose.** A cheaper model for search and mechanical steps; a stronger one for planning and review. Use `inherit` when unsure.
- Plugin subagents ignore `permissionMode`, `hooks`, and `mcpServers`. Put those in the plugin or project settings instead.

## Check

- Spawn it once on a real task and read what comes back: is it a summary, within length, with references?
- For a reviewer: plant a known bug and confirm it is reported. (C1)

## Skeleton

```markdown
---
name: <agent-name>
description: <Role> - <what it does>. Use <when to delegate>.
tools: Read, Grep, Glob
model: sonnet
---

You receive <inputs>. If an input is missing, say which and stop.

1. <Step>.
2. <Step>.

Do not edit files. Do not spawn subagents.

Return at most <n> lines: <output shape, with file:line>.
```
