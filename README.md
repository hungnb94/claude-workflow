# Claude Workflow

[![CI](https://github.com/hungnb94/claude-workflow/actions/workflows/ci.yml/badge.svg)](https://github.com/hungnb94/claude-workflow/actions/workflows/ci.yml)

Structured agent workflows for feature development in Claude Code, plus best-practice issue writing, two-version PR explanations, atomic commits, solution brainstorming, Jira lookup, distilling proven expertise on any topic, authoring agent skills, hooks, and commands, a learning coach that teaches a concept until you can explain it back, and grounded answers from your documents that label each point as answered, uncertain, or unknown.

## Overview

Claude Workflow packages one structured 4-step feature workflow with a fresh implementer subagent per batch of steps and an independent reviewer subagent, two platform standards skills it applies on its own (Android and KMP), plus nine lightweight skills (issue writing, PR explainer, atomic commit, solution brainstorm, Jira lookup, distill expertise, agent authoring, learning coach, and grounded answer), into an official Claude Code Plugin:

1. **Feature Workflow** (`/feature-workflow`) - A 4-step workflow for one story or feature, run by the main session. B1 interviews you until the requirements are agreed, grilling-style, with each question written for a reader who knows little about the code (context, choices, impact against current behavior, and a recommendation). Each question offers 3-4 choices spread along one axis the decision turns on (scope, completeness, or failure behavior), from the smallest change through the one that follows the detected standards to the most durable, instead of two near-identical variants; it offers only two when only two exist and says why. It writes each acceptance criterion (AC) as a row of a table with its check (a command, a script compared against a baseline, or a person following a script), the environment it runs in, the evidence file it will produce, and who grades it (the machine, a `verify` read of the evidence, or a human sign-off); an AC with an empty cell, or with words like "same" or "looks right" and no way to measure them, is rewritten before B1 is done. B2 calls Solution Brainstorm in caller mode. B3 picks the top-scoring option whose extensibility and maintainability scores are both at least 4, then codes it in small steps: by default the whole step table goes to one fresh `fw-3-implement` subagent, which codes the rows in order, runs the checks, and commits each row when green. Large work, with parts that share no files or more context than one agent can read, splits into at most 3 batches that run one after another, never in parallel, and the batch count and reason are written down. The main session records each row from the agent's status line and reads the whole diff once all rows are done; B3 does not run the evidence check. Wide searches go to `Explore` and long command output is cut to its summary, so the main session stays a small scheduler. B4 has the read-only `fw-4-review` subagent check the diff against the requirements and the detected platform standards only, including new functions or classes that duplicate code already in the repo, then hands every Blocker, Major, and small Minor finding of that round to one fresh `fw-3-implement`, one commit per finding, with at most 2 review rounds; there is no separate Minor pass. Each step writes one file to `.workflows/<slug>/`, and the next step starts only when it can read that file. State lives in those files, not in the chat: step 3 keeps a step table and a list of out-of-scope work found on the way, updated after each commit, and step 4 records each fix as it lands, so you can open a fresh session and run `/feature-workflow <slug>` to resume from the first unfinished step. Once, after step 4 and before the final report, a fresh `fw-3-evidence` subagent reruns every build and test command, checks each AC and saves fresh evidence for it in `.workflows/<slug>/evidence/`, and the main session records in the latest review file each command, exit code, summary line from the output, `HEAD`, and each AC's status (pass, fail, waiting for sign-off, or not checked with a reason); a pass that points to no file in that folder counts as not checked. A red run or a failed AC is never reported as done: it goes back to one fresh `fw-3-implement` and then a fresh `fw-3-evidence`, at most 2 times, before the workflow stops and tells you; when the evidence fixes added commits, one fresh `fw-4-review` reviews just those commits, and a Blocker or Major there stops the workflow without another fix round; an AC still not checked or waiting for sign-off turns the final report into "waiting for checks on N ACs" with the list and reasons, and neither a clean lint nor the reviewer's run counts. Commits stay local; nothing is pushed.
2. **Android Standards** (`/android-standards`) - Android/Kotlin coding standards: Coroutines, Flow, SOLID, Clean Architecture, MVVM, Hilt, Compose state, and testing, led by mandatory scope rules (migrate only when logic changes substantially, in its own commit; behavior tests; no single-consumer abstractions). Java→Kotlin migration rules sit in `migration.md`, read only when a task touches Java. Feature Workflow and Solution Brainstorm load it when `platforms.md` detects an Android project, and the model can also invoke it whenever you write or review Android code. Written in Vietnamese.
3. **KMP Standards** (`/kmp-standards`) - Kotlin Multiplatform coding standards: shared code and source set organization, expect/actual, Gradle multiplatform, cross-target coroutines/Flow, and Android/iOS/JVM/Native performance. Feature Workflow and Solution Brainstorm load it when `platforms.md` detects a Kotlin Multiplatform project, and the model can also invoke it whenever you write or review KMP code. Written in Vietnamese.
4. **Issue Writing** (`/issue-writing`) - A lightweight, single-pass skill (no subagents) that drafts Jira or GitHub issues from plain-English templates: User Story/Feature, Bug, Task/Chore, and Spike. It applies title, acceptance criteria (checklist or Given/When/Then), INVEST sizing, and bug-report rules, and marks missing data as TBD with open questions instead of guessing. The model can also invoke it automatically. Written in English, unlike the other skills.
5. **PR Explainer** (`/pr-explainer`) - A lightweight, single-pass skill (no subagents) that explains one pull request in two versions built from the same facts table: a short plain-language version with one everyday metaphor for PMs, QA, and business readers, and a technical version with the verified root cause, the fix and why, impact, and only the checks that actually ran, plus suggested checks for QA. It reads the PR with `gh` when available, marks unknown causes as not confirmed instead of guessing, and only drafts text; it posts a comment only when you ask. Written in English, and the output is always in English.
6. **Atomic Commit** (`/atomic-commit`) - A lightweight, single-pass skill (no subagents) that splits uncommitted changes into atomic commits. It reads staged, unstaged, and untracked changes, groups them into one logical change per commit, shows a commit plan, and waits for your approval unless you say to commit now. Messages follow Conventional Commits (the 11 types the PR title check accepts) and the Chris Beams rules. It can split a file by hunk with `git apply --cached`, never uses `git add -A` or `--no-verify`, excludes secrets and `.workflows/`, and never pushes or opens a PR. The model can also invoke it automatically. Written in English. Inside a workflow with its own commit rules, the workflow wins.
7. **Solution Brainstorm** (`/solution-brainstorm`) - A skill that thinks through a coding task before any code is written. It reads the codebase, detects the platform and architecture, and asks whether to migrate outdated tech. Two read-only `sb-1-generator` subagents, each reading a different knowledge lens from `lenses.md`, propose options in parallel; it lists 18 options in one table and narrows them to 9 (sorted from Low to High investment; each level keeps at least 2 options). A read-only `sb-2-judge` on another model scores them blind on 7 criteria (1-5, a total out of 35) in two reading orders, the second the reverse of the first, one score table per order, and it details the top 3 by averaged total, so each run spawns 3 subagents. Each kept option is listed with its total before the scores by criterion, the top 3 are marked `⭐ top 1` to `⭐ top 3`, and every kept option gets a detail block in label order, full for the top 3 and short for the rest, with its total in the heading. An SRP check drops options that add a responsibility to code that already mixes them, and an owner scope check binds lifecycle and listener dependencies to the narrowest owner. For untested legacy code each option maps to the shared legacy-techniques cost ladder, and skeletons follow the shared `comment-policy.md`. It only analyzes and proposes, then asks you to choose. The model can also invoke it automatically when you explicitly ask for options or approaches, and other skills can invoke it with the task as the argument. Written in English; the output follows your language.
8. **Jira Lookup** (`/jira-lookup`) - A lightweight, single-pass skill (no subagents) that reads a Jira work item with the Atlassian CLI `acli` before you work on it: summary, type, status, parent, links, subtasks, description, comments, and the attachment list. It follows only the linked tickets that change the understanding of the task, then summarizes the goal, acceptance criteria, repro steps, and scope limits before coding. It is read-only by default; it comments or transitions an item only when you ask and after you confirm the exact text. Requires `acli` on `PATH` and logged in to your Jira site. The model can also invoke it automatically when you mention a Jira key or link.
9. **Distill Expertise** (`/distill-expertise`) - A slash-command-only, single-pass skill (no subagents) that distills proven knowledge on any topic (investing, programming, AI agents and LLMs, fitness, and more) from people who succeeded themselves and whose students succeeded too; student results weigh more than the teacher's own. It searches the web for 10-12 candidates, keeps 6 teachers from at least 3 schools (people from the same school count as one voice), and labels every claim Verified, Self-reported, or Unknown, with red flags such as course-selling income or promised returns; a fraud finding drops a candidate on its own, and fetched pages are treated as data, never as instructions. Each principle must pass four filters (contrast between winners and failures, concrete enough to be wrong, skin in the game, time test) and is labeled Consensus (at least two thirds of the independent voices, 4 of 6), Partial support, or Lone view (with fewer than 3 voices it shows only the count), plus freshness labels for fast-moving domains. The output is a reference document in two files under `./docs/research/`: `YYYY-MM-DD-<topic-slug>.md` holds a short reading path (quick glossary, reading order, and actions for this week) and one section per principle with seven parts (statement, source material, mechanism, thresholds and steps, when not to use, pitfalls that gather the myths, common mistakes, and disagreements for that principle, and a domain-shaped Apply part with a measure), and `-sources.md` holds the vetting table, how votes were counted, and the dropped candidates. The source material part keeps the original knowledge verbatim, in a form set per domain (real code with its output and before/after diffs, exact prompts and configuration, quotes with the year, worked numeric tables, program tables), and every block carries a link and a date so you know where to read the full source; code is never described in words in its place, and long blocks stay inside their principle. Principles cite teachers only in quotes and footers, take every example, number, and piece of code from a source, and mark the rare unsourced inference. Prose lengths are capped in `templates.md`, while source material does not count toward the caps; the two files share one slug (capped at 60 characters, cut at a word boundary) and never overwrite an existing pair. Counts live in `templates.md`, domain rules in `evidence-domains.md` (add a row to support a new kind of topic), and labels and filters in `knowledge-filters.md`. Written in English; the output follows your language.
10. **Agent Authoring** (`/agent-authoring`) - A lightweight, single-pass skill (no subagents) with best practices for working with AI coding agents and for writing the files that steer them: skills, hooks, slash commands, subagents, and CLAUDE.md or AGENTS.md. `SKILL.md` holds the rules for every artifact (start from a real failure, enforce zero-exception rules with a hook instead of stronger words, rerun a pass/fail check after the last change and read its exit code before saying done, test with a fresh agent) and for handing work to an agent (plan when unclear, keep the context small by handing noisy reading to subagents and moving to a fresh session that reads a progress file, keep work state in files instead of the chat, reset after two failed corrections, stop at the first cheating sign, no unattended run without a check). A routing table then sends the agent to one reference file per artifact type (`skills.md`, `hooks.md`, `commands.md`, `subagents.md`, `claude-md.md`), so it reads only what the task needs, and `subagents.md` asks you to read a subagent's diff and rerun its check instead of trusting its report; `references.md` lists the principles and their public sources. The model invokes it automatically whenever you create, edit, or review one of these artifacts, and Solution Brainstorm reads it as the standards for tasks that touch them. Written in English; the output follows your language.
11. **Learning Coach** (`/learning-coach`) - A lightweight, single-pass skill (no subagents) that teaches one concept or skill so you understand it, remember it, and can explain it back. Each lesson runs in four parts: real examples from easy to hard, the concept with a metaphor for each point (definition, the problem it solves, when to use it or not, and what it is often confused with), graded exercises from recall to challenge with no answers given first, and a teach-back where you explain it as if teaching someone else and get graded on it. When you get something wrong, it finds the gap, explains it again more simply, and checks again. It only runs when you type `/learning-coach`; the model does not invoke it automatically. Written in Vietnamese.
12. **Grounded Answer** (`/grounded-answer`) - A lightweight, single-pass skill (no subagents of its own) that answers a question only from your documents. It splits the question into points and gives each point exactly one label: ✅ Answered (the documents say it directly, quoted word for word with `file:line` or the page and section in a connector), ⚠️ Uncertain (it has to be inferred, the text is vague, or the sources conflict; it gives a one-line reason and the quote, and when sources conflict it quotes both sides without picking one), or ❌ Unknown ("Not found in the sources read.", which speaks only for the sources it read). Knowledge from outside the documents never goes into a labeled answer; it may appear only on a separate "Outside the documents (unverified)" line under a ❌ or ⚠️ point, and only when it really helps. The source is the file or folder you name, a connector you name (Google Drive, Confluence, and so on; if it is missing or not logged in, it says so and stops instead of switching source), or, if you name none, a targeted search of the current folder, handing large searches to the built-in `Explore` subagent. It is read-only and ends by listing the sources it read and what it could not check. Labels, the answer format, and an example live in `templates.md`. It only runs when you type `/grounded-answer`; the model does not invoke it automatically. Written in Vietnamese; the answer follows your language.

The plugin also ships desktop notification hooks (macOS and Linux, enabled by default) that alert you when Claude finishes, asks a question, or needs permission. See [Desktop Notifications](#desktop-notifications). A `PostToolUse` hook also formats Kotlin files with ktlint after each write; see [Kotlin Formatting (ktlint)](#kotlin-formatting-ktlint).

The workflow keeps a few rules: agree the requirements before code, score options before choosing one, keep every commit green, and review with an agent that did not see the plan and cannot edit files.

## Installation

### Via Claude Code Marketplace (Recommended)

Add the marketplace catalog:

```bash
claude plugin marketplace add hungnb94/claude-workflow
```

Install the plugin:

```bash
claude plugin install workflow@claude-workflow
```

### Local Development and Testing

To test or develop locally without installing from the marketplace, run Claude Code with the `--plugin-dir` flag:

```bash
claude --plugin-dir .
```

To validate the plugin manifests and components locally:

```bash
# Validate marketplace catalog manifest
claude plugin validate --strict .

# Validate plugin manifest and individual components
claude plugin validate --strict .claude-plugin/plugin.json
claude plugin validate --strict skills/
claude plugin validate --strict agents/

# Verify release tag compatibility between plugin.json and marketplace.json
claude plugin tag --dry-run .

# Run zero-dependency semantic and structural integrity audit
python3 scripts/verify-integrity.py

# Run unit tests
python3 -m unittest discover tests

# Lint hook scripts (requires shellcheck)
shellcheck -s sh hooks/*.sh

# Validate JSON syntax across repository
python3 -c "import json, pathlib; [json.load(open(f, 'r', encoding='utf-8')) for f in pathlib.Path('.').rglob('*.json') if '.workflows' not in f.parts and 'node_modules' not in f.parts and '.git' not in f.parts]; print('All JSON files valid')"

# Validate YAML syntax across repository (requires pyyaml: pip install pyyaml)
python3 -c "import yaml, pathlib; [yaml.safe_load(open(f, 'r', encoding='utf-8')) for f in pathlib.Path('.').rglob('*') if f.suffix in ('.yml', '.yaml') and '.workflows' not in f.parts and 'node_modules' not in f.parts and '.git' not in f.parts]; print('All YAML files valid')"

# Lint Markdown documentation
npx -y markdownlint-cli -c .markdownlint.json "**/*.md" --ignore ".workflows/**" --ignore "node_modules/**"
```

## Workflow Architecture

### Four-Step Feature Workflow

```text
B1: Requirements      B2: Solution            B3: Code                 B4: Review + fix
(main session,   -->  (solution-brainstorm -> ([fw-3-implement]   -->  [fw-4-review] (Opus, read-only)
 asks you,             caller mode)            one per batch,           then one [fw-3-implement]
 AC table)                                     max 3 batches,           per round, then once
                                               commit per row)          [fw-3-evidence]
      |                      |                       |                        |
      v                      v                       v                        v
01-requirements.md     02-solution.md         03-implementation.md     04-review-<n>.md
```

Each step reads the file the previous step wrote and starts only when that file begins with `Trạng thái: xong`.

### Architectural Principles

1. **Target Workspace Portability**: The plugin code remains immutable and read-only. All runtime workflow artifacts are written directly into the target project's `<repo root>/.workflows/<slug>/` directory using absolute paths.
2. **Progressive Disclosure & Token Economy**: Agent frontmatter descriptions are concise (under 40 tokens), minimizing system prompt overhead during registry discovery. Detailed instructions, rubrics, and workflows are placed in the markdown body and loaded only when a subagent is spawned.
3. **Independent Quality Gate (Least Privilege)**: The review agent (`fw-4-review`) has no `Edit` or `Write` tool. It reads only the agreed requirements, the platform standards, and the diff, runs the tests, and reports findings, so it does not grade the plan it never saw.
4. **One Writer at a Time**: Code is written only by `fw-3-implement`, one fresh agent per batch of steps, per review round, or per evidence fix, never two at once, so the requirements and design are read once per agent instead of once per step. The main session writes the workflow files and reads the diff. `fw-3-evidence` writes only evidence files into `.workflows/<slug>/evidence/` and never touches code or tests. The other subagents only read: the brainstorm generators, the judge, and the reviewer.

## Usage

### Running Feature Workflow

For software feature development and code tasks that change observable behavior:

```bash
# Direct slash command (when installed or running in workspace)
/feature-workflow "<story description, Jira key, or .md path>"

# Canonical plugin-namespaced command
/workflow:feature-workflow "<story description, Jira key, or .md path>"
```

The workflow asks you questions in B1 and waits for you to confirm the requirements, then runs B2-B4 on its own. It also stops to ask when the task is a bug that already happened or a 1-2 line change, when `.workflows/<slug>/` or the `feature/<slug>` branch already exists, when the working tree has uncommitted changes, when no option scores at least 4 on both extensibility and maintainability, when tests stay red after two fixes, or when Blocker or Major findings remain after the second review round. It commits on `feature/<slug>` (when you started on the default branch), and prints the `git push -u origin <branch>` command at the end; nothing is pushed.

### Platform standards

Feature Workflow and Solution Brainstorm detect the platform from `skills/solution-brainstorm/platforms.md` and load its standards skill on their own, both through the shared `standards-lookup.md`, so there is no separate command per platform. Feature Workflow shows the detected platform and standards in the requirements summary for you to confirm. To add standards for a new platform, add a standards skill and point the platform's **Standards** line in `platforms.md` to it. You can also load a standards skill by hand:

```bash
/android-standards
/kmp-standards
```

### Running Issue Writing

Draft a well-formed Jira or GitHub issue from a short description:

```bash
/issue-writing "<what the issue is about, e.g. a bug you saw>"
# or, with the plugin namespace:
/workflow:issue-writing "<what the issue is about, e.g. a bug you saw>"
```

The model may also use it automatically when you ask to write a ticket, bug report, or user story. It only drafts text; it does not create issues in Jira or GitHub.

### Running PR Explainer

Explain a pull request in two versions, a plain-language metaphor and a technical one:

```bash
/pr-explainer "<PR number or URL, or paste the diff>"
# or, with the plugin namespace:
/workflow:pr-explainer "<PR number or URL, or paste the diff>"
```

The model may also use it automatically when you ask to explain a PR to non-technical people. It only drafts text; it does not post a comment unless you ask.

### Running Solution Brainstorm

Brainstorm 18 solutions for a coding task from two knowledge lenses, narrow them to 9, let a blind judge shortlist 3, and get a recommendation:

```bash
/solution-brainstorm "<the task or problem to solve>"
# or, with the plugin namespace:
/workflow:solution-brainstorm "<the task or problem to solve>"
```

The model can also run it automatically when you explicitly ask for options or approaches (for example "what are the ways to…" or "compare approaches for…"), but not for plain implement or fix requests. It only analyzes and proposes. It does not write code or edit files, and it waits for you to choose an option.

### Running Distill Expertise

Distill proven knowledge on a topic from teachers whose students also succeeded, and save it as a reference document (a main file of principles with the source code, prompts, and quotes kept verbatim with links, plus a sources file) to `./docs/research`:

```bash
/distill-expertise "<topic, optionally: learn from <teacher>>"
# or, with the plugin namespace:
/workflow:distill-expertise "long-term crypto investing"
```

The model does not run it automatically; it starts only when you type the command. When you name a teacher, it skips the search but still vets that person.

### Running Atomic Commit

Split your uncommitted changes into atomic commits with well-formed messages:

```bash
/atomic-commit
# or, with the plugin namespace and an optional hint:
/workflow:atomic-commit "only what is staged"
```

The model may also use it automatically when you ask it to commit your changes. It shows a commit plan and waits for your approval, unless you clearly say to commit now. It does not push and does not open a pull request.

### Running Jira Lookup

Read a Jira work item and its comments before you start on it:

```bash
/jira-lookup "<Jira key or URL, e.g. PROJ-123>"
# or, with the plugin namespace:
/workflow:jira-lookup "<Jira key or URL>"
```

The model may also use it automatically when you mention a Jira key or paste a Jira link. It needs the Atlassian CLI `acli`, logged in with `acli jira auth login --web`. It only reads; it does not comment, transition, assign, or edit unless you ask.

### Running Agent Authoring

Get best-practice guidance while you write a skill, hook, slash command, subagent, or CLAUDE.md:

```bash
/agent-authoring "<what you want to create or change>"
# or, with the plugin namespace:
/workflow:agent-authoring "add a hook that blocks edits to migrations/"
```

The model also loads it automatically whenever you ask to create, edit, or review one of these artifacts, or to set up an agent task that runs unattended. It reads only the reference file for the artifact you are writing, and it ends by telling you which check it ran and what it did not test.

### Running Learning Coach

Learn a concept through examples, metaphors, exercises, and a teach-back:

```bash
/learning-coach "<topic>"
# or, with the plugin namespace:
/workflow:learning-coach "<topic>"
```

It only runs when you type the command; the model does not invoke it automatically.

### Running Grounded Answer

Ask a question and get an answer only from your documents, with each point labeled ✅, ⚠️, or ❌ and quoted with its location:

```bash
/grounded-answer [file | folder | connector] "<question>"
# or, with the plugin namespace:
/workflow:grounded-answer [file | folder | connector] "<question>"
```

Name a file, a folder, or a connector to read only that source; name none to search the current folder. It only runs when you type the command; the model does not invoke it automatically.

## Desktop Notifications

The plugin registers hooks (`hooks/hooks.json`) that run `hooks/notify.sh` to show a desktop alert with a sound. They are enabled by default and work on **macOS and Linux only**. On any other OS the script exits silently.

| Event | When | Body | Sound (macOS / Linux) |
|---|---|---|---|
| `Stop` | Claude finishes responding | `Done — ready for review` | Glass / `complete` |
| `PreToolUse` (`AskUserQuestion`) | Claude asks you a question | The question text | Ping / `message` |
| `Notification` (`permission_prompt`, `elicitation_dialog`) | Claude needs permission or input | The notification message | Ping / `message` |

The title is `Claude Code · <project folder name>`. The script never blocks Claude and always exits with status 0.

To turn the alerts off, set this in your shell profile:

```bash
export CLAUDE_WORKFLOW_NOTIFY=0
```

Optional tools:

- macOS: `terminal-notifier` is used when installed (`brew install terminal-notifier`), otherwise the built-in `osascript`. The hook uses the first `terminal-notifier` on `PATH` that runs, so a broken copy (for example the x86_64 Ruby gem on Apple silicon without Rosetta) is skipped. Version 2.0.0 can post nothing on recent macOS; if no alert shows, run `brew upgrade terminal-notifier`.
- Linux: `notify-send` for the alert, and `canberra-gtk-play` or `paplay` for the sound (falls back to the terminal bell).
- `jq`: reads the question text, notification message, and project folder from the hook input. Without it, alerts use generic text (`Claude has a question for you`, `Claude needs permission`) and the current directory name.

A question asked through `AskUserQuestion` can trigger two alerts, one from the `PreToolUse` hook and one from the `Notification` hook.

### Click to return to the tab (macOS)

With `terminal-notifier` installed, clicking an alert brings back the terminal tab that runs that Claude session, even with many tabs open:

- **Terminal.app and iTerm2**: the click selects the tab (iTerm2: the session) with the session's tty, brings its window to the front, and activates the app. `hooks/focus-terminal.sh` finds the tty when the alert is sent and selects the tab when you click.
- **First click**: macOS asks you to allow automation of Terminal or iTerm2. If you deny it, a click only brings the app to the front. You can change this later in System Settings → Privacy & Security → Automation.
- **Closed tab**: clicking an old alert only brings the app to the front, with no error.
- **tmux, and other terminals** (Ghostty, WezTerm, kitty, the VS Code terminal): a click only brings the terminal app to the front; it does not pick a tab or pane.
- Each tab keeps only its latest alert in Notification Center; a new alert from the same tab replaces the old one.

Without `terminal-notifier` (the `osascript` fallback) and on Linux, alerts work as before and a click does not return to the tab.

## Kotlin Formatting (ktlint)

A `PostToolUse` hook (matcher `Edit|Write|MultiEdit`, timeout 30s) runs `hooks/ktlint-format.sh` after Claude writes a file. For `.kt` and `.kts` files (including `build.gradle.kts`) it runs `ktlint --format` on that single file; ktlint reads your `.editorconfig` and no style flags are passed. The hook is always on and has no flag to disable it.

Install the tools: `brew install ktlint jq`. Alternatively, place an executable `ktlint` at the project root (`CLAUDE_PROJECT_DIR`, falling back to the `cwd` in the hook input).

Binary lookup order: `ktlint` on `PATH` first, then `./ktlint` at the project root. `PATH` wins when both exist.

The hook exits 0 and prints nothing when:

- the file is not a Kotlin file, does not exist, or its path contains glob characters (`*`, `?`, `[`, `]`, `{`, `}`)
- `jq` or `ktlint` is not installed, or the hook input is missing `file_path` or is not valid JSON
- ktlint succeeds (the file is fixed in place)
- ktlint fails without printing anything

When ktlint still reports violations it cannot autocorrect, the hook exits 2 and sends the report to Claude on stderr, truncated to 20 lines (with a `... (N more lines truncated)` marker).

Notes:

- The file changes right after Claude writes it, so Claude may need to re-read it before its next edit.
- The hook runs for every project. If a project does not use ktlint (for example it uses ktfmt or Spotless, or has no `.editorconfig`), ktlint's default style is applied and may produce noisy diffs.

## Subagents Reference

### Feature Workflow Subagents

| Subagent | Role | Model | Tools | Footprint (Tokens) | Responsibility |
|---|---|---|---|---|---|
| `fw-3-implement` | Implementer | Inherit | Read, Edit, Write, Bash, Grep, Glob | ~35 | Code a numbered list of items (the rows of one step batch, one review round's findings, or the failed evidence checks) in a fresh context, run the checks and commit each item when green, and return one status line per item; `STEP` starts with a `LOẠI` line naming the list kind, and B4 findings keep the reviewer's `#` numbers; never touch `.workflows/` or spawn subagents |
| `fw-3-evidence` | Evidence Verifier | Inherit | Read, Bash, Grep, Glob, Write | ~80 | Once after B4, before the final report, run the build and test commands and check each AC in a fresh context, save fresh evidence in `.workflows/<slug>/evidence/`, grade the machine and `verify` criteria, and return a status table; never edit code, commit, or read the plan |
| `fw-4-review` | Independent Reviewer | Opus | Read, Grep, Glob, Bash | ~23 | Review the diff against the agreed requirements and platform standards without seeing the plan; report Blocker/Major/Minor with file:line (no Edit or Write) |

*Note: footprint values measured via `claude plugin details`.*

### Solution Brainstorm Subagents

| Subagent | Role | Model | Tools | Responsibility |
|---|---|---|---|---|
| `sb-1-generator` | Option Generator | Sonnet | Read, Grep, Glob, WebSearch, WebFetch | Propose distinct options through one knowledge lens from `lenses.md`, without judging them |
| `sb-2-judge` | Blind Option Judge | Opus | Read, Grep, Glob | Score anonymized option cards on the fixed rubric once per reading order (the second the reverse of the first) and return a ranked shortlist |

## Automated Release Lifecycle

The version is bumped inside each Pull Request, not after the merge. The developer sets the version, a PR gate checks it, and when the PR is squash-merged into `main` the release pipeline only tags that version and publishes a GitHub Release. No bot commit lands on `main`, so every PR stays a single commit.

### Bumping the Version in a PR

Bump from the latest release tag on your branch, then commit the two manifests with the rest of the change:

```bash
git fetch --tags
python3 scripts/bump-version.py --pr-title "feat: add new skill"            # print the suggested bump
python3 scripts/bump-version.py --bump-type minor --write-manifests        # write it to plugin.json and marketplace.json
```

The command always computes from the latest release tag, so running it again does not bump twice.

### Suggested Bump

The suggestion comes from the PR title, body, and labels (Conventional Commits). You choose the final bump, because you know the scope of the change:

| PR Convention / Marker | Suggested Bump | Resulting SemVer | Example PR Title |
|---|---|---|---|
| `!` after type/scope, or `BREAKING CHANGE:` in body | Major | `X+1.0.0` | `feat!: redesign subagent communication protocol` |
| `feat` or `feat(...)` | Minor | `X.Y+1.0` | `feat(skills): add automated verification skill` |
| `fix`, `perf`, `refactor`, `revert` | Patch | `X.Y.Z+1` | `fix: resolve manifest version synchronization bug` |
| `docs`, `chore`, `ci`, `test`, `style`, `build` | None | No release | `docs: update installation instructions` |
| `skip-release` or `no-release` PR label | None | No release | Any title with label `skip-release` |

### PR Version Gate

`.github/workflows/version-check.yml` runs `scripts/bump-version.py --check` on every PR and keeps one comment on the PR with the result and the suggested bump. The check fails when:

- `plugin.json` and `marketplace.json` versions differ, or the version is not `X.Y.Z`;
- the version is lower than the latest release tag, or skips past the next patch, minor, or major version (this also catches two PRs that took the same version: once one merges, the other must bump again);
- the PR needs a release (`feat`, `fix`, `perf`, `refactor`, `revert`, or breaking) but the version was not bumped and the PR has no `skip-release` label;
- the PR is a breaking change but the bump is not major.

A bump that differs from the suggestion in any other way only adds a warning to the comment. A PR that bumps the version is released even when its type would not suggest a release.

The gate is enforced by branch protection on `main`: the `Version Check` status is required, and branches must be up to date before merging, so the check re-runs after another PR is released. Only squash merge is enabled.

### Release Pipeline

`.github/workflows/release.yml` runs on every push to `main`:

1. **Serialized Concurrency**: Release runs are serialized (`concurrency: group: release, cancel-in-progress: false`).
2. **Tag Detection**: Reads the version from `.claude-plugin/plugin.json`. When tag `v$VERSION` already exists, the run stops without releasing.
3. **Pre-Release Integrity Gate**: `scripts/verify-integrity.py --check-tag "v$VERSION"` verifies manifest synchronization, subagent reference integrity, tool permissions, and description token budgets before publishing.
4. **Git Tag & GitHub Release**: Tags the merged commit as `v$VERSION` and publishes a release with notes generated from merged PRs.

Running the workflow by hand (`workflow_dispatch`) retries a release that failed part-way. It never bumps the version.

## Project Structure

```text
claude-workflow/                 # Repository root (plugin identifier: workflow)
├── .claude-plugin/
│   ├── plugin.json              # Plugin manifest (version 1.0.0, author, repo)
│   └── marketplace.json         # Marketplace catalog distribution manifest
├── agents/
│   ├── fw-3-evidence.md         # Feature workflow final check: Runs the checks and creates fresh evidence per AC
│   ├── fw-3-implement.md        # Feature workflow B3/B4 and final evidence fixes: Codes a list of items, one commit each, in a fresh context
│   ├── fw-4-review.md           # Feature workflow B4: Independent read-only reviewer (Opus)
│   ├── sb-1-generator.md        # Brainstorm: Options through one knowledge lens
│   └── sb-2-judge.md            # Brainstorm: Blind rubric judge (Opus, read-only)
├── hooks/
│   ├── hooks.json               # Hooks (Stop, AskUserQuestion, Notification notifiers; PostToolUse ktlint format)
│   ├── focus-terminal.sh        # POSIX sh helper for notify.sh: finds the session tab and focuses it on click (macOS)
│   ├── ktlint-format.sh         # POSIX sh ktlint formatter for Kotlin files (PostToolUse)
│   └── notify.sh                # POSIX sh notifier for macOS/Linux (opt-out: CLAUDE_WORKFLOW_NOTIFY=0)
├── scripts/
│   ├── bump-version.py          # Version bump suggestion, manifest sync, and PR version gate
│   └── verify-integrity.py      # Pre-release integrity check and gatekeeper
├── skills/
│   ├── feature-workflow/
│   │   └── SKILL.md             # 4-step /feature-workflow
│   ├── android-standards/
│   │   ├── SKILL.md             # Android/Kotlin standards with mandatory rules and a read-when table
│   │   ├── migration.md         # Java→Kotlin migration and bridge rules (read when a task touches Java)
│   │   └── references.md        # Sources for the Android rules
│   ├── kmp-standards/
│   │   ├── SKILL.md             # Kotlin Multiplatform standards with mandatory rules
│   │   └── references.md        # Sources for the KMP rules
│   ├── issue-writing/
│   │   ├── SKILL.md             # Skill for /issue-writing (single pass, no subagents)
│   │   ├── templates.md         # Story, Bug, Task, Spike templates
│   │   └── references.md        # Verified sources for the rules
│   ├── pr-explainer/
│   │   ├── SKILL.md             # Skill for /pr-explainer (single pass, no subagents)
│   │   ├── templates.md         # Facts table, metaphor and technical templates
│   │   └── references.md        # Verified sources for the rules
│   ├── atomic-commit/
│   │   ├── SKILL.md             # Skill for /atomic-commit (single pass, no subagents)
│   │   ├── templates.md         # Message, type table, commit plan, examples
│   │   └── references.md        # Verified sources for the rules
│   ├── jira-lookup/
│   │   └── SKILL.md             # Skill for /jira-lookup (single pass, no subagents, read-only acli lookup)
│   ├── solution-brainstorm/
│   │   ├── SKILL.md             # Skill for /solution-brainstorm (lens generators and a blind judge, read-only)
│   │   ├── lenses.md            # Knowledge lens catalog: what each option generator reads and asks
│   │   ├── platforms.md         # Platform registry: detect signals, architecture, patterns (agent artifacts point to agent-authoring)
│   │   ├── legacy-techniques.md # Shared legacy refactoring catalog (cost ladder, techniques, Mikado), read by brainstorm
│   │   ├── standards-lookup.md  # Shared procedure that turns platforms.md into the standards to apply, read by brainstorm and the feature workflow
│   │   ├── comment-policy.md    # Shared code comment policy (no comment by default, WHY only), read by brainstorm and the feature workflow
│   │   └── templates.md         # Fixed 7 criteria and output format
│   ├── distill-expertise/
│   │   ├── SKILL.md             # Skill for /distill-expertise (single pass, no subagents, web research)
│   │   ├── templates.md         # Counts, principle and sources formats, source material rules, pre-save checklist, chat summary
│   │   ├── evidence-domains.md  # Domain registry: student evidence, proxy, freshness, Apply form, source material form
│   │   └── knowledge-filters.md # Evidence labels, red flags, mentor rules, principle filters, inference rule
│   ├── agent-authoring/
│   │   ├── SKILL.md             # Skill for /agent-authoring: shared rules and a routing table by artifact type
│   │   ├── skills.md            # Writing skills: description, layout, frontmatter, evals
│   │   ├── hooks.md             # Writing hooks: when to use one, events, exit codes, plugin scope
│   │   ├── commands.md          # Slash commands vs skills, arguments
│   │   ├── subagents.md         # When to delegate, one writer at a time, least privilege
│   │   ├── claude-md.md         # What belongs in CLAUDE.md and AGENTS.md
│   │   └── references.md        # Principles and their public sources
│   ├── learning-coach/
│   │   └── SKILL.md             # Skill for /learning-coach (single pass, user-only; written in Vietnamese)
│   └── grounded-answer/
│       ├── SKILL.md             # Skill for /grounded-answer (single pass, user-only, read-only; written in Vietnamese)
│       └── templates.md         # Three labels, fixed ❌ sentence, answer format, and an example
├── tests/
│   ├── test_bump_version.py     # Unit tests for version calculation
│   ├── test_focus_terminal.py   # Unit tests for the focus-terminal helper
│   ├── test_ktlint_format_hook.py # Unit tests for the ktlint format hook
│   ├── test_notify_hooks.py     # Unit tests for notification hooks
│   └── test_verify_integrity.py # Unit tests for integrity gate
├── .gitignore                   # Ignore rules (.workflows, .idea, OS files)
└── README.md                    # Documentation
```

## Thinking Tools

The workflow subagents operate on structured analytical frameworks:

- **Backward Planning**: Start from the verified end state, work backward to uncover prerequisite dependencies.
- **Second- and Third-Order Effects**: Evaluate downstream implications and system trade-offs before committing changes.
- **Game Theory**: Anticipate component interactions and edge-case behaviors under varied conditions.
- **Blue Ocean Strategy**: Seek high-leverage architectural solutions rather than complicated local workarounds.
- **Kaizen**: Continuous improvement through progressive review cycles and automated remediation.

## License

This project is licensed under the MIT License.
