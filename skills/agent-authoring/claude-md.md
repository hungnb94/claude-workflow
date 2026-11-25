# CLAUDE.md and AGENTS.md

Read by `agent-authoring` when the task writes or changes CLAUDE.md or AGENTS.md.

## What goes in

These files load into every session, so every line costs attention on every task. Write a map, not a manual. (P5)

Keep only what the agent cannot read from the code:

- The commands that check work: test, typecheck, lint, build. (C1)
- Code that misleads: a name that means something else here, a file that must not be edited by hand.
- Decisions that live outside the repo: why a library was picked, a team rule.
- A mistake the user had to correct twice. (C2)

Leave out:

- Architecture overviews and folder trees. The agent reads the repo itself.
- Style rules a formatter or linter already enforces.
- Long how-tos. Put them in a skill or a doc and link to it, so they load only when needed.

## Rules

- Keep the file under 200 lines. When it grows, move task-specific parts into skills. (P5)
- Add a line only after the same correction happened twice. Write that line from the real mistake. (C2)
- Write plain sentences. If the agent still ignores a line, shorten the file first; if the rule has no exceptions, make it a hook (`hooks.md`). Do not add IMPORTANT or capitals. (P2)
- Delete lines the agent follows without being told, and lines about code that no longer exists.
- Rules that apply to one part of the repo go in `.claude/rules/*.md` with `paths` frontmatter, so they load only when the agent works on those files. `@path` imports still load at launch and do not save context.
- AGENTS.md is read by other coding agents too. Claude Code reads it only when no CLAUDE.md exists. To share rules across tools, keep them in AGENTS.md and put `@AGENTS.md` in CLAUDE.md, instead of copying the text.

## Check

- `wc -l CLAUDE.md` is under the limit above.
- Every new line traces to a mistake or a command; say which one in the PR or reply.
