---
name: agent-authoring
description: Best practices for working with AI coding agents and for writing the files that steer them - Claude Code skills, hooks, slash commands, subagents, and CLAUDE.md or AGENTS.md. Use when the user asks to create, edit, or review one of these, to make an agent follow a rule, or to set up an agent task that runs unattended. Do not use for ordinary feature code or to write a research report.
---

# Agent Authoring

Write the files that steer a coding agent, and hand work to an agent, the way proven practitioners do. Each rule names its principle (C1, P2, and so on); `references.md` lists the principles and their sources.

The output follows the user's language. Keep technical terms in English.

Project rules win. When CLAUDE.md, AGENTS.md, docs/adr, or the existing artifacts in the repo disagree with this skill, follow the project and say which rule you followed.

## Read only what you need

Read every file whose row matches the task, and only those. All files sit next to this one.

| The task writes or changes | Read |
|---|---|
| A skill (`SKILL.md` and its folder) | `skills.md` |
| A hook, a deny rule, or a check that blocks the agent | `hooks.md` |
| A slash command | `commands.md` |
| A subagent, or a task that delegates to one | `subagents.md` |
| CLAUDE.md or AGENTS.md | `claude-md.md` |
| Nothing above, or the user asks why a rule exists | `references.md` |

## Rules for every artifact

1. **Start from a real failure.** Name what the agent got wrong without the artifact: a real run, or a correction the user had to give twice. If nobody can name one, say so and ask before you write. A rule written from imagination costs context on every task and can make the agent overdo it. (C2)
2. **Pick the weakest tool that holds the rule.** A rule with exceptions or judgment goes in words, in CLAUDE.md or a skill. A rule with zero exceptions that a machine can check goes in a hook, a deny rule, or CI. Do not add IMPORTANT, MUST, or capitals to make words stronger; move the rule to a hook instead. (P2)
3. **Write the smallest text that fixes the failure.** Use plain sentences. Leave out what the agent can read from the repo. (P5)
4. **Give a pass/fail check and run it before you say done.** For example: validate the JSON, feed the hook script a sample input, run `claude plugin validate`, or run the repo's tests. Run it again after your last change and read the exit code; an earlier run, a clean lint, or "should pass" does not count. Done means the check is green, not that the file looks right. (C1)
5. **Test with a fresh agent.** Run the failing case from rule 1 again in a clean session or subagent that has the new artifact, and compare. If you did not run it, say so in your reply. (C2)

## Working with an agent on a task

- **Plan when it is unclear.** A vague or multi-file task gets a plan first; each step names its check, and the user approves the plan before code. A small, clear task with a test goes straight to code. (C3)
- **Reset after two failed corrections.** When the same fix failed twice, start a fresh session with a prompt that includes what you learned. Do not try a third time in the same conversation. (C3)
- **Stop at the first cheating sign.** A deleted or loosened assertion, a skipped test, a feature nobody asked for, or a loop on the same error. Review every change to a test file on its own. (P4)
- **Start with one agent.** Add subagents or a multi-step workflow only when a measure (evals, time, bugs found) shows it helps. (P3)
- **No check, no unattended run.** Before a run without a human, answer five questions: what done is, how it is checked, what it may touch, what stops it (turn or budget limit), and who approves the merge. (C1)

## Before you finish

Tell the user, in a few lines: the failure the artifact fixes, the check you ran and its result, and what you did not test.
