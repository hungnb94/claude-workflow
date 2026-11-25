# Standards lookup

Read by `solution-brainstorm` (Step 1) and `feature-workflow` (B1). This is the only place that says how to
turn `platforms.md` into the standards a task follows. Change the procedure here, not in a caller.

1. Read `platforms.md` (next to this file). A section matches when at least one signal on its **Detect**
   line is present.
   - Several match: the primary section is the one with the most distinctive signals (a section's Detect
     line may say it wins over another). Keep the others as secondary context only.
   - None match: there are no platform standards. Say so and use project conventions and general best
     practice.
2. The primary section has a **Standards** line naming a skill (`skill <name>`): find its `SKILL.md` in
   this order:
   1. `../<name>/SKILL.md` next to the folder of this file.
   2. Glob `**/<name>/SKILL.md`.
   3. Still missing: tell the user, and use the primary section itself as the standards.

   Read that `SKILL.md`, then only the reference files its table names for this task.
3. The primary section has no **Standards** line: the standards are that section of `platforms.md`.
4. Record:
   - Platform: the primary section's heading.
   - Standards: absolute paths of the files you read. For a section of `platforms.md`, write its path and
     the heading, like `/abs/path/platforms.md` `## iOS`. With no platform standards, write `không có`.
   - Priority when they disagree: project conventions (CLAUDE.md, AGENTS.md, docs/adr, the existing code
     layout) > the standards > general best practice.
