# Hooks

Read by `agent-authoring` when the task writes or changes a hook, a deny rule, or another check that blocks the agent.

## Contents

- When a hook is the right tool
- Pick the event
- Exit codes and output
- Rules
- Check
- Skeleton

## When a hook is the right tool

A hook runs every time, whatever the model thinks. Words in CLAUDE.md or a skill are advice the model may decide does not apply. (P2)

- Use a hook for a rule with zero exceptions that a script can check: "do not edit `migrations/`", "typecheck must pass before stopping".
- Use a hook when the agent ignored a plainly written rule.
- A fixed list of forbidden commands or paths fits a `permissions.deny` rule in settings, with no script at all.
- A rule that needs judgment stays in words.
- Keep the set small. Dozens of hooks usually means preferences are being enforced as rules.

## Pick the event

| Goal | Event |
|---|---|
| Block or allow a tool call before it runs | `PreToolUse`, with a `matcher` on the tool name |
| React after a tool ran (format, lint, add context) | `PostToolUse` |
| Keep the agent working until a check is green | `Stop` (or `SubagentStop` for subagents) |
| Add context to, or block, a user prompt | `UserPromptSubmit` |
| Load context when a session starts | `SessionStart` |

There are many more events; read <https://code.claude.com/docs/en/hooks> before using one not listed here.

## Exit codes and output

- Exit 0: success. Stdout that is one JSON object is read as a decision; for `UserPromptSubmit` and `SessionStart`, plain stdout is added as context.
- Exit 2: blocking error. Stderr is the reason. `PreToolUse` blocks the call; `Stop` keeps the agent working; `PostToolUse` only shows stderr to the agent, since the tool already ran.
- Any other code: non-blocking. The action goes on and the transcript shows a hook error.
- To deny from `PreToolUse` with JSON: `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "..."}}`.
- To add context without blocking: `hookSpecificOutput.additionalContext`.
- A `Stop` hook must read `stop_hook_active` from its input and exit 0 when it is `true`, or the agent can loop.

## Rules

- Match as narrowly as you can: a `matcher` for the tool, and an early exit 0 in the script when the file path does not apply.
- A plugin hook runs in every repo that installs the plugin. Exit 0 quietly when the repo or file is not one the hook is for.
- Keep it fast and set a `timeout`. A hook on every Edit runs hundreds of times a session.
- Write the reason so the agent can fix the problem: which rule, which file, which command to run.
- Read the input from stdin as JSON. Quote every variable. Never `eval` input.
- Put the logic in a script file, not inline in JSON, so it can be tested. In a plugin, call it through `${CLAUDE_PLUGIN_ROOT}`; in a project, through `$CLAUDE_PROJECT_DIR`.
- Follow the hook layout the repo already has (`hooks/hooks.json` in a plugin, `.claude/settings.json` in a project).

## Check

- Feed the script sample stdin JSON for a case it must block and a case it must allow, and check the exit code and output. Add these as tests when the repo has a test suite. (C1)
- Validate the JSON config.
- Trigger the hook once in a real session and confirm the agent sees the reason.

## Skeleton

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [{ "type": "command", "command": "sh \"${CLAUDE_PLUGIN_ROOT}/hooks/guard.sh\"", "timeout": 10 }]
      }
    ]
  }
}
```

```sh
#!/bin/sh
input=$(cat)
path=$(printf '%s' "$input" | sed -n 's/.*"file_path" *: *"\([^"]*\)".*/\1/p')
case "$path" in
  */migrations/*) echo "migrations/ is generated. Create a new migration with the project's tool." >&2; exit 2 ;;
esac
exit 0
```
