# Slash commands

Read by `agent-authoring` when the task writes or changes a slash command.

## Command or skill

Custom commands have been merged into skills. `.claude/commands/<name>.md` still works and gives `/<name>`, but new work should be a skill (`skills.md`):

- A skill folder can hold reference files and scripts; a command file cannot.
- When a skill and a command share a name, the skill wins.

Keep a command file only when the repo already uses `.claude/commands/` and the prompt fits in one short file. To grow one, move it to `.claude/skills/<name>/SKILL.md`.

## Rules

- A command that only the user should start (deploy, release, a long workflow) is a skill with `disable-model-invocation: true`. (P6)
- Take input with `$ARGUMENTS`, or `$0`, `$1` for positions. Add `argument-hint` so the `/` menu shows what to pass.
- If the input is empty, ask the user. Do not guess.
- Write the prompt the way you would brief a colleague: the goal, the check that says it is done, and what not to touch. (C1)
- Command files take the same frontmatter as skills, except `name`: the file name is the command name, and a subfolder adds a prefix (`frontend/component.md` gives `/frontend:component`).

## Check

- Run the command once with a real argument and once with none.
- Confirm it shows up in the `/` menu with the hint.

## Skeleton

```markdown
---
description: <What it does>. Use when <trigger>.
argument-hint: <arg>
disable-model-invocation: true
---

If `$ARGUMENTS` is empty, ask for <arg> and stop.

<Goal in one sentence, using $ARGUMENTS.>
Done when `<check command>` passes. Do not change <what to leave alone>.
```
