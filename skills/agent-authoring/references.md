# References

Read by `agent-authoring` when no other file matches the task, or when the user asks why a rule exists. The principles were distilled on 2026-11-23 from 6 practitioners of 6 different schools; the Support column counts how many of them back each one. The field changes fast; review these rules about every 6 months.

## Principles

| ID | Principle | Support |
|---|---|---|
| C1 | Give the agent a pass/fail check it can run. Done is a green check, not the agent's word | Consensus, 6/6 |
| C2 | Write a rule or skill only after you saw the agent fail without it (baseline first) | Consensus, 4/6 |
| C3 | Split planning from execution for vague or multi-step tasks; reset after two failed corrections | Consensus, 4/6 |
| C4 | Use subagents for noisy reading or truly independent work; one writer at a time; subagents return a summary | Consensus, 4/6 |
| P1 | Review with a clean-context agent that checks the diff against the spec | Partial, 3/6 |
| P2 | Enforce zero-exception rules with a machine (hook, deny rule, CI), not stronger words | Partial, 3/6 |
| P3 | Start with the simplest setup (one agent); add complexity only when a measure shows a gain | Partial, 3/6 |
| P4 | Watch for cheating (deleted tests, scope creep, fix loops) and stop at the first sign | Partial, 3/6 |
| P5 | Files that load every session stay short: a map, not a manual; details load on demand | Partial, 2/6 |
| P6 | A skill description says only when to use it, in the third person, without the steps | Partial, 2/6 |
| L1 | Grade agent output with binary pass/fail criteria per failure type | Lone view, 1/6 |

## Sources

1. Anthropic - Best practices for Claude Code (2026-11). <https://code.claude.com/docs/en/best-practices>
2. Anthropic - Skill authoring best practices (2026-11). <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices>
3. Anthropic Applied AI - Effective context engineering for AI agents (2025-09-29). <https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents>
4. Boris Cherny - Claude Code tips thread (2026-01-02). <https://x.com/bcherny/status/2007179861115511237>
5. Jesse Vincent - superpowers, `writing-skills` and `test-driven-development` (2026). <https://github.com/obra/superpowers>
6. Kent Beck - Augmented Coding: Beyond the Vibes (2025-06-25). <https://newsletter.kentbeck.com/p/augmented-coding-beyond-the-vibes>
7. Mitchell Hashimoto - My AI Adoption Journey (2026-02-05). <https://mitchellh.com/writing/my-ai-adoption-journey>
8. Walden Yan - Multi-Agents: What's Actually Working (2026-04-22). <https://cognition.com/blog/multi-agents-working>
9. Hamel Husain - Evals Skills for Coding Agents (2026-03-03). <https://hamelhusain.substack.com/p/evals-skills-for-coding-agents>
10. Anthropic - Claude Code docs for skills, hooks, slash commands, and subagents. <https://code.claude.com/docs/en/skills>, <https://code.claude.com/docs/en/hooks>, <https://code.claude.com/docs/en/sub-agents>
