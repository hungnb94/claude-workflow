---
name: issue-writing
description: Write, improve, or split Jira and GitHub issues (user story, feature, bug report, task, chore, spike) using best-practice rules and templates. Use when the user asks to write or review the text of an issue, ticket, bug report, or story. Do not use to create issues through an API or CLI, to do the work in an issue, to write a PRD, roadmap, sprint plan, or PR description. For commit messages, use atomic-commit.
---

# Issue Writing

This skill helps you draft the text of an issue. The user copies the text into Jira or GitHub. The skill does not create real issues.

Write in plain English. Use short sentences.

## When to use

- The user wants a new issue, ticket, bug report, or story.
- The user has a rough draft and wants it improved.
- The user has a big request that must be split into smaller issues.
- The user wants several issues written at once.

## When not to use

- Creating issues through an API, CLI, or MCP tool.
- Doing the work described in an issue.
- Writing a PRD, roadmap, or sprint plan.
- Writing a PR description.
- Writing a commit message (use `atomic-commit`).

## Supporting files

Find the folder of this skill with "Base directory for this skill". If it is not shown, search with Glob for `**/issue-writing/templates.md`.

- Read `templates.md` before you write. Read only the part for the chosen type.
- Read `references.md` only when the user asks where a rule comes from.
- If you cannot read `templates.md`, write the issue with the minimum fields in the table below, and tell the user.

## Workflow

### Step 1. Pick the issue type

| Type | Use when | Must have |
|---|---|---|
| Story | A user gets new value | Title, user story, context, acceptance criteria |
| Bug | Existing behavior is wrong | Title, environment, steps to reproduce, expected, actual, severity |
| Task / Chore | Technical or maintenance work with no new user behavior | Title, goal, what to do, done when |
| Spike | A question must be answered before work can be planned | Title, question, why it matters, timebox, output |

This table is the minimum. `templates.md` lists every Required field for each type.

If a request mixes a bug and a feature, write two issues.

### Step 2. Check the input

Look for missing information. Follow "Missing information" below. Ask first only if the gap blocks the issue.

### Step 3. Fill the template

Use the template in `templates.md`. Apply the writing rules. Use the format of the target platform (see "Jira vs GitHub").

### Step 4. Self-check and return

Run the final checklist. Return the issue in the output format. Put open questions in the issue's "Open questions" section.

## Writing rules

### Title

- For a story, task, or spike, start with a verb and name the object. Be specific and short.
- Keep it under about 70 characters. This is a rule of thumb, not a standard.
- Good: "Export invoices as CSV". Bad: "CSV stuff".
- Good: "Checkout button does nothing on Safari 17". Bad: "Fix bug".
- For a bug, state the symptom and where it happens. Do not guess the cause.

### Acceptance criteria

Acceptance criteria (AC) are checks that show the work is done. Each line must pass or fail.

- Default to a checklist. One check per line.
- For a user flow, use Given/When/Then. Given is the starting state. When is the action. Then is the result you can see.
- Write one behavior per scenario. Say what should happen, not which buttons to click.
- Do not use vague words such as "fast" or "user-friendly". Use a number, or write `TBD`.
- AC belong to one issue. The Definition of Done is shared by the whole team.

### Definition of Ready and Done

- Definition of Ready (DoR) means the issue is clear enough to start. It is a common practice. It is not part of the Scrum Guide.
- A short DoR check: the goal is clear, AC are written, dependencies are known, the issue is small enough, no blocking question is open.
- Definition of Done (DoD) is the quality bar the team agreed on. The Scrum Guide defines it.
- Use the team's DoD only. Do not invent one. If the team has none, do not add a DoD section.

### Size and splitting

Use INVEST to check size and quality. A good issue is:

- Independent: it can be built without waiting for others, when possible.
- Negotiable: details can be discussed.
- Valuable: it gives value to a user or the team.
- Estimable: the team can judge the effort.
- Small: it fits in a few days.
- Testable: AC can be checked.

An issue may be too big if it has more than about 8 AC lines, many "and" words in the title, or more than one user role.

Split by vertical slice, not by layer. Ways to split:

- By workflow step.
- By business rule.
- By data type.
- Happy path first, then edge cases.

Do not split into "frontend" and "backend" unless the team asks for it.

### Bug reports

- Put facts first. Put guesses in "Suspected cause" and label them as a guess.
- Give the shortest steps that show the bug.
- Keep expected and actual results apart.
- Give exact versions. Do not write "latest".
- Severity is the impact of the bug. Priority is the order of fixing. Use the team's scales. If there are none, suggest Critical, Major, Minor, Trivial for severity. This is a common convention.
- Write one bug per issue.
- Add what the reporter already tried, if known.

### Links and dependencies

- State parent or epic, blocked by, blocks, relates to, and duplicates when they apply.
- Use only real IDs that the user gave you. If a link applies but has no ID, describe the link and write `TBD`.
- If no link applies, drop the Dependencies section. Do not fill it with `TBD`.

### Labels and priority

- Use the labels and priority scale the team already has.
- Do not invent new labels without saying so.
- If you do not know, drop the field. These fields are Optional.

### Plain English

- Use short sentences. Use active voice. One idea per sentence.
- Explain a short form the first time you use it, for example "AC (acceptance criteria)".
- Avoid extra jargon.
- Write the issue in English unless the user asks for another language.

## Missing information

Never invent versions, numbers, names, dates, steps, error text, IDs, or URLs.

- Blocking gap: ask before you write. Ask at most 5 questions, in one message.
  - Story: who the user is and what outcome they want.
  - Bug: expected result, actual result, and one way to reproduce it or the error seen.
  - Task: the goal.
  - Spike: the question to answer.
- Non-blocking gap: write `TBD` in the field. Add a question to "Open questions".
- If the user says "just draft it", write the issue with `TBD` and do not ask more.

## Edge cases

### Vague input

Example: "login is broken". Say in one sentence what you understood. Ask the blocking questions. If the user does not want to answer, draft the issue with `TBD` fields and list your assumptions under "Assumptions".

### Input too big (epic)

Do not write one huge issue. Return:

- One short parent issue with the goal and the list of child issues.
- A list of child issues. For each, give a title, one sentence, the type, and the order or dependency.
- Full text for the first one or two children only.

Then ask if the user wants the rest written in full.

### Many issues at once

- Start with a summary table: number, type, title, depends on.
- Write each issue in full with its own template. Do not merge issues.
- Number them: Issue 1, Issue 2, and so on.
- Use "Issue 2" style references for dependencies when real IDs do not exist yet.
- Group open questions by issue.

### Improving an existing issue

Keep the original facts. Do not add new facts. Mark gaps with `TBD`. List the changes you made in a few lines.

## Jira vs GitHub

Use the platform the user names. If it is unknown, use plain Markdown and no platform-specific features.

| Topic | GitHub | Jira |
|---|---|---|
| Format | GitHub Flavored Markdown. Task lists use `- [ ]`. | The Jira Cloud editor converts Markdown as you type. `- [ ]` may not become a checkbox, so write checklist items as plain `-` bullets for Jira. Older Jira versions may differ, so ask if unsure. |
| Types | Labels. Issue types exist only if the organization turned them on. | Epic, Story, Task, Bug, Subtask by default. Admins can change them. Newer docs say "work item". |
| Templates | Markdown templates or YAML issue forms in `.github/ISSUE_TEMPLATE`. Forms can mark fields as required. | Fields are set by the Jira admin. |
| ID | `#123`, or `owner/repo#123` for another repository. | A key such as `PROJ-123`. |
| Closing | Put `Closes #123`, `Fixes #123`, or `Resolves #123` in a PR description. The issue closes when the PR merges into the default branch. | Depends on your Jira workflow and integrations. |
| Hierarchy and links | Sub-issues. Dependencies: blocked by and blocking. | Parent or epic. Link types such as blocks, is blocked by, relates to, duplicates. Admins can change them. |
| Other fields | Labels, assignees, milestone, projects. | Priority, components, fix version, labels, if your site uses them. |

If you are not sure how the user's site is set up, say so. Do not claim a field exists.

## Output format

For each issue, give:

- A line `Type: <type>`.
- A line `Title: <title>`.
- The body inside one fenced block marked `markdown`, so the user can copy it. Open the block with four backticks (````markdown) and close it with four backticks, so code blocks inside the body (logs, errors) do not end it early.

Open questions go in each issue's own "Open questions" section, not after all issues. After all issues, add "Assumptions" if there are any. Do not add long comments.

## Final checklist

Before you return the issue, check:

- [ ] The type is right.
- [ ] The title is specific. Story, task, and spike titles start with a verb. Bug titles name the symptom and where it happens.
- [ ] All Required fields are filled or marked `TBD`.
- [ ] AC pass or fail, and have no vague words.
- [ ] No fact is invented.
- [ ] Every `TBD` has an open question.
- [ ] The size passes INVEST. If not, split it.
- [ ] Links and dependencies that apply are stated, or marked `TBD` if the ID is unknown.
- [ ] Labels and priority follow the team's scheme, or are dropped.
- [ ] The language is plain, terms are explained, and the format fits the platform.

## Sources

The rules come from Atlassian, GitHub Docs, Agile Alliance (INVEST), Cucumber (Gherkin), the Scrum Guide, and Simon Tatham's bug report guide. See `references.md` for links.
