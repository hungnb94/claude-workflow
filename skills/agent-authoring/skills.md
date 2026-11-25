# Skills

Read by `agent-authoring` when the task writes or changes a skill.

## Contents

- Before you write
- Folder and files
- Frontmatter
- Description
- Body
- Discipline skills
- Check
- Skeleton

## Before you write

- Do the task once with the agent, without a skill. Note what you had to repeat or correct. That list is the skill. Do not ask the agent to invent a skill from nothing. (C2)
- A constraint a regex, a schema, or a script can check is not a skill. Make it a hook or a CI check (`hooks.md`). (P2)
- Check whether an existing skill already covers it. Extend that one instead of adding a near copy.

## Folder and files

- One folder per skill: `SKILL.md` plus reference files next to it. In a project the folder is `.claude/skills/<name>/`; in a plugin it is `skills/<name>/`. Follow the layout the repo already uses.
- Name the folder in lowercase with hyphens. Use the naming pattern of the skills already in the repo.
- Link every reference file straight from `SKILL.md`, and say when to read it. Never chain references (`SKILL.md` -> `a.md` -> `b.md`): the agent often reads only part of a nested file. (P5)
- Keep numbers, thresholds, and templates in one reference file, so a change happens in one place.
- Say whether a script is to be run or to be read. Refer to files next to the skill with `${CLAUDE_SKILL_DIR}`, or in a plugin with `${CLAUDE_PLUGIN_ROOT}`.

## Frontmatter

| Field | Use it when |
|---|---|
| `name` | Always. Same as the folder name. |
| `description` | Always. See below. |
| `disable-model-invocation: true` | The skill has side effects (deploy, release, push, posting) or is costly (starts a long workflow or many subagents). Then only the user starts it with `/name`. |
| `user-invocable: false` | The skill is background knowledge that only the model should load. |
| `argument-hint` | The skill takes arguments. Shown in the `/` menu. |
| `allowed-tools` | The skill always needs a few tools and prompting for them adds nothing. Keep the list short. |
| `context: fork` | The skill does noisy work whose result can be a short summary. Not for skills that must see the conversation. |

Unknown fields are ignored without an error, so spell field names exactly. Outside Claude Code (Skills API, claude.ai) only `name`, `description`, `license`, `compatibility`, `metadata`, and `allowed-tools` are allowed.

## Description

The description sits in the system prompt of every session. It is the only text the agent reads to choose a skill. (P6)

- Say what the skill does and when to use it: "Use when ...". Add the words users actually type, in every language they use.
- Add "Do not use ..." for the nearest wrong matches.
- Write in the third person.
- Do not list the steps. When the description summarizes the workflow, the agent follows the summary and skips the body.
- Stay well under the 1,536-character listing limit; aim for under 1,024.

## Body

- Keep `SKILL.md` under 500 lines. Move details into reference files, and give a reference file over 100 lines a contents list at the top. (P5)
- Write plain, short sentences. Explain why when a rule is not obvious; do not shout. (P2)
- Say what to do when input is missing: ask, do not guess. With `$ARGUMENTS`, check for an empty value first.
- Say what the skill must not do (edit files, push, post) when the user could expect it.
- End with what to report to the user.

## Discipline skills

A skill that must hold under pressure (write the test first, verify before saying done):

- Pressure-test it: give the agent a reason to skip the rule ("10 minutes to the demo") and run several times without and with the skill. (C2)
- Add a table of excuses the agent gave and the answer to each, taken from the real runs. Only add it when the runs show the agent breaking the rule. (P4)

## Check

- Write at least 3 test scenarios, each with binary expected behaviors (pass/fail per item, no 1-5 score). Run them without the skill first, then with it. Keep only text that raises the pass count. (C2, L1)
- Run them in a fresh session or subagent, not in the session that wrote the skill.
- Run the repo's own checks (in a plugin: `claude plugin validate`).
- `wc -l SKILL.md` is under the limit.

Scenario shape:

```json
{
  "query": "Write a skill that summarizes merged PRs into a changelog",
  "expected_behavior": [
    "Asks for or records a real failure before writing SKILL.md",
    "Description names triggers only and does not list steps",
    "Every reference file is linked from SKILL.md"
  ]
}
```

## Skeleton

```markdown
---
name: <skill-name>
description: <What it does>. Use when <triggers and user phrases>. Do not use for <nearest wrong matches>.
---

# <Title>

<One or two sentences: the goal.>

## When to read the other files

- `<file>.md`: <when>.

## Workflow

### Step 1. <Get the input>

If `$ARGUMENTS` is empty, ask the user. Do not guess.

### Step 2. <...>

## Report

<What to tell the user, including what was not checked.>
```
