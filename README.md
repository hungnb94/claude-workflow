# Claude Workflow

[![CI](https://github.com/hungnb94/claude-workflow/actions/workflows/ci.yml/badge.svg)](https://github.com/hungnb94/claude-workflow/actions/workflows/ci.yml)

Structured agent workflows for feature development in Claude Code, plus best-practice issue writing, two-version PR explanations, atomic commits, and solution brainstorming.

## Overview

Claude Workflow packages one structured workflow framework powered by 7 specialized subagents, two priming skills that delegate to it (Android and KMP standards), plus four lightweight skills (issue writing, PR explainer, atomic commit, and solution brainstorm), into an official Claude Code Plugin:

1. **Feature Workflow** (`/feature-workflow`) - A 7-phase engineering workflow for software feature development: requirement specification, industry research, throwaway best-practice role-model draft, architecture planning, implementation with tests, independent code review, and automated remediation. Large stories are automatically split into budgeted stacked slices (≤~400 production LOC, ≤~15 files each), with one local branch per slice and one or more commits per planned task (refactor, add, change, switch, remove), never pushed. For untested legacy code, Phase 4 applies a cheapest-first cost ladder (Sprout/Wrap Method/Class, then Feathers dependency-breaking with a characterization harness, then Branch by Abstraction, then Strangler Fig, with the Mikado Method as an overlay; details in the shared `legacy-techniques.md` catalog) and records why cheaper rungs fall short.
2. **Android Standards Workflow** (`/android-standards-workflow`) - A priming skill that loads Android/Kotlin best practices (Coroutines, Flow, SOLID, Clean Architecture, MVVM, Java→Kotlin migration) plus Android scope rules (migrate only when logic changes substantially, behavior tests, no single-consumer abstractions), and delegates to Feature Workflow with those standards as immutable constraints. Slash-command-only (`disable-model-invocation: true`).
3. **KMP Standards Workflow** (`/kmp-standards-workflow`) - A priming skill that loads Kotlin Multiplatform best practices (shared code/source set organization, expect/actual, Gradle multiplatform, cross-target coroutines/Flow, Android/iOS/JVM/Native performance) and delegates to Feature Workflow with those standards as immutable constraints. Slash-command-only (`disable-model-invocation: true`).
4. **Issue Writing** (`/issue-writing`) - A lightweight, single-pass skill (no subagents) that drafts Jira or GitHub issues from plain-English templates: User Story/Feature, Bug, Task/Chore, and Spike. It applies title, acceptance criteria (checklist or Given/When/Then), INVEST sizing, and bug-report rules, and marks missing data as TBD with open questions instead of guessing. The model can also invoke it automatically. Written in English, unlike the other skills.
5. **PR Explainer** (`/pr-explainer`) - A lightweight, single-pass skill (no subagents) that explains one pull request in two versions built from the same facts table: a short plain-language version with one everyday metaphor for PMs, QA, and business readers, and a technical version with the verified root cause, the fix and why, impact, and only the checks that actually ran, plus suggested checks for QA. It reads the PR with `gh` when available, marks unknown causes as not confirmed instead of guessing, and only drafts text; it posts a comment only when you ask. Written in English, and the output is always in English.
6. **Atomic Commit** (`/atomic-commit`) - A lightweight, single-pass skill (no subagents) that splits uncommitted changes into atomic commits. It reads staged, unstaged, and untracked changes, groups them into one logical change per commit, shows a commit plan, and waits for your approval unless you say to commit now. Messages follow Conventional Commits (the 11 types the PR title check accepts) and the Chris Beams rules. It can split a file by hunk with `git apply --cached`, never uses `git add -A` or `--no-verify`, excludes secrets and `.workflows/`, and never pushes or opens a PR. The model can also invoke it automatically. Written in English. Inside a workflow with its own commit rules, the workflow wins.
7. **Solution Brainstorm** (`/solution-brainstorm`) - A slash-command-only, single-pass skill (no subagents) that thinks through a coding task before any code is written. It reads the codebase, detects the platform (Android, Kotlin Multiplatform, iOS, Flutter, Web frontend, Backend) and architecture, asks whether to migrate when it finds outdated tech, then lists 12 options in one table and narrows them to 3 (Minimal, Balanced, Durable) with a fixed 6-criteria score table (1-5, with a total out of 30 for each option). It ends with a recommendation and asks you to choose. It only analyzes and proposes: it never writes code or edits files. For untested legacy code it maps each kept option to the shared legacy-techniques cost ladder and requires tests for the new code. Android and Kotlin Multiplatform rules are read from the existing standards files, not copied. Skeletons and any follow-up implementation follow the shared `comment-policy.md` (no comments by default, WHY only), which the feature workflow agents also read. Written in English; the output follows your language.

The plugin also ships desktop notification hooks (macOS and Linux, enabled by default) that alert you when Claude finishes, asks a question, or needs permission. See [Desktop Notifications](#desktop-notifications). A `PostToolUse` hook also formats Kotlin files with ktlint after each write; see [Kotlin Formatting (ktlint)](#kotlin-formatting-ktlint).

The workflow applies rigorous engineering discipline: scope definition before execution, industry best practice comparison, second-order effect analysis (with optional backward planning), heterogeneous model routing (Opus for planning, Sonnet for execution), and independent review gates with strict tool isolation.

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

### Seven-Phase Feature Workflow Pipeline

```text
Phase 1: Spec    Phase 2: Research   Phase 3: Role-model   Phase 4: Plan
[fw-1-spec]      [fw-2-research]     [fw-3-role-model]     [fw-4-plan]
 (Sonnet)   -->   (Sonnet)      -->   (Opus, NO Edit)  -->  (Opus)
      |                |                     |                   |
      v                v                     v                   v
 01-spec.md      02-research.md      03-role-model.md      04-plan.md
                                                                  |
+-----------------------------------------------------------------+
|
v
Phase 5: Impl    Phase 6: Review     Phase 7: Fix   (each runs per slice)
[fw-5-impl] -->  [fw-6-review]  -->  [fw-7-fix]
 (Sonnet)         (Sonnet, NO Edit)   (Sonnet)
      |                |                   |
      v                v                   v
 05-impl-<n>.md  06-review-<n>.md     07-fix-<n>.md
```

### Architectural Principles

1. **Target Workspace Portability**: The plugin code remains immutable and read-only. All runtime workflow artifacts are written directly into the target project's `<repo root>/.workflows/<slug>/` directory using absolute paths.
2. **Progressive Disclosure & Token Economy**: Agent frontmatter descriptions are concise (under 40 tokens), minimizing system prompt overhead during registry discovery. Detailed instructions, rubrics, and workflows are placed in the markdown body and loaded only when a subagent is spawned.
3. **Independent Quality Gate (Least Privilege)**: The review agent (`fw-6-review`) is strictly prohibited from using the `Edit` tool. It can only read, search, execute tests, and report findings to prevent self-grading bias.
4. **Heterogeneous Model Routing**: Phase 3 (role-model) and Phase 4 (planning) agents in Feature Workflow use `model: opus` for deep analytical reasoning, mandatory second-order effect evaluation, and optional Backward Planning. All other phases use `model: sonnet` for speed and deterministic execution.
5. **Open/Closed Principle & Extensibility**: Code generated and refactored across the pipeline adheres to OCP: open for extension via data-driven dispatch tables or generalizations, while closed for modification without patching cascading conditionals (`if-elif ==`). Balanced strictly against YAGNI to prevent over-engineering (no unnecessary abstract classes or factories when lightweight data mappings suffice). Rule of three: no abstraction before ≥2 real consumers.
6. **Small Stacked PRs**: Feature Workflow plans slices in Phase 4 and runs Phases 5-7 per slice. Each slice is one local branch `<slug>/<n>-<slice-name>`, based on the previous slice, within the size budget. Inside a slice, Phase 4 plans tasks: each task is the smallest unit with its own test cycle and ends with its own commit of one kind (`refactor`, `add`, `change`, `switch`, `remove`). Phase 6 reviews each commit against the task list, and Phase 7 adds each fix as a new commit of one kind instead of rewriting history. The workflow never pushes or opens PRs.

## Usage

### Running Feature Workflow

For software feature development and code tasks that change observable behavior:

```bash
# Direct slash command (when installed or running in workspace)
/feature-workflow "<story description, Jira key, or .md path>"

# Canonical plugin-namespaced command
/workflow:feature-workflow "<story description, Jira key, or .md path>"
```

With no plan-approval stop (Phase 4 flows straight into Phase 5), the workflow commits each slice locally on its own stacked branch and finally prints the `git push -u origin <branch>` commands with suggested PR titles and descriptions; nothing is pushed.

### Running Android Standards Workflow

For Android/Kotlin feature development that should follow Google-recommended best practices (Coroutines, Flow, SOLID, Clean Architecture, MVVM, incremental Java→Kotlin migration). This primes the standards and delegates to Feature Workflow.

```bash
# Direct slash command (when installed or running in workspace)
/android-standards-workflow "<story description, Jira key, or .md path>"

# Canonical plugin-namespaced command
/workflow:android-standards-workflow "<story description, Jira key, or .md path>"
```

PRs are split into stacked slices per Feature Workflow; the Android rules keep each slice small (migrate only when logic changes substantially, behavior tests, no single-consumer abstractions). Slices are committed locally and the push commands are printed at the end.

### Running KMP Standards Workflow

For Kotlin Multiplatform feature development that should follow JetBrains-recommended best practices (shared code/source set organization, expect/actual, Gradle multiplatform, cross-target coroutines/Flow, Android/iOS/JVM/Native performance). This primes the standards and delegates to Feature Workflow.

```bash
# Direct slash command (when installed or running in workspace)
/kmp-standards-workflow "<story description, Jira key, or .md path>"

# Canonical plugin-namespaced command
/workflow:kmp-standards-workflow "<story description, Jira key, or .md path>"
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

Brainstorm 10 solutions for a coding task, narrow them to 3, and get a recommendation:

```bash
/solution-brainstorm "<the task or problem to solve>"
# or, with the plugin namespace:
/workflow:solution-brainstorm "<the task or problem to solve>"
```

The model does not run it automatically; it starts only when you type the command. It only analyzes and proposes. It does not write code or edit files, and it waits for you to choose an option.

### Running Atomic Commit

Split your uncommitted changes into atomic commits with well-formed messages:

```bash
/atomic-commit
# or, with the plugin namespace and an optional hint:
/workflow:atomic-commit "only what is staged"
```

The model may also use it automatically when you ask it to commit your changes. It shows a commit plan and waits for your approval, unless you clearly say to commit now. It does not push and does not open a pull request.

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

- macOS: `terminal-notifier` is used when installed, otherwise the built-in `osascript`.
- Linux: `notify-send` for the alert, and `canberra-gtk-play` or `paplay` for the sound (falls back to the terminal bell).
- `jq`: reads the question text, notification message, and project folder from the hook input. Without it, alerts use generic text (`Claude has a question for you`, `Claude needs permission`) and the current directory name.

A question asked through `AskUserQuestion` can trigger two alerts, one from the `PreToolUse` hook and one from the `Notification` hook.

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
| `fw-1-spec` | Senior Business Analyst | Sonnet | Read, Grep, Glob, Write, Bash | ~20 | Survey scope, identify extension points, and define acceptance criteria |
| `fw-2-research` | Senior Research Specialist | Sonnet | Read, Grep, Glob, Write, Bash, WebSearch, WebFetch | ~30 | Research extensible OCP patterns and benchmark against conventions |
| `fw-3-role-model` | Reference Implementer | Opus | Read, Grep, Glob, Write, Bash | ~15 | Author throwaway reference implementations demonstrating OCP patterns and anti-patterns |
| `fw-4-plan` | Senior Solution Architect | Opus | Read, Grep, Glob, Write, Bash | ~20 | Design extensible approach, evaluate OCP trade-offs, and plan deliverables |
| `fw-5-impl` | Senior Execution Engineer | Sonnet | Read, Grep, Glob, Write, Edit, Bash | ~20 | Implement extensible deliverables following OCP without patching conditionals |
| `fw-6-review` | Senior Quality Auditor | Sonnet | Read, Grep, Glob, Write, Bash | ~20 | Independent review against AC, classify findings, and audit OCP extensibility (No Edit tool) |
| `fw-7-fix` | Senior Remediation Engineer | Sonnet | Read, Grep, Glob, Write, Edit, Bash | ~20 | Remediate review findings at root cause without branching hotfixes |

*Note: footprint values measured via `claude plugin details`.*

## Automated Release Lifecycle

Claude Workflow implements zero-touch continuous delivery. Every Pull Request merged into the `main` branch triggers an automated release pipeline (`.github/workflows/release.yml`) that analyzes Conventional Commits metadata, increments the semantic version, synchronizes manifests, passes pre-release integrity gates, and publishes a GitHub Release.

### Semantic Version Determination

The release pipeline inspects the merged PR title, description body, and GitHub labels to calculate the next Semantic Version 2.0.0 (`X.Y.Z`):

| PR Convention / Marker | Version Bump | Resulting SemVer | Example PR Title |
|---|---|---|---|
| `!` after type/scope, or `BREAKING CHANGE:` in body | Major | `X+1.0.0` | `feat!: redesign subagent communication protocol` |
| `feat` or `feat(...)` | Minor | `X.Y+1.0` | `feat(skills): add automated verification skill` |
| `fix`, `perf`, `refactor`, `revert` | Patch | `X.Y.Z+1` | `fix: resolve manifest version synchronization bug` |
| `docs`, `chore`, `ci`, `test`, `style`, `build` | Skip | No release | `docs: update installation instructions` |
| `skip-release` or `no-release` PR label | Skip | No release | Any title with label `skip-release` |

### Pipeline Workflow Steps

1. **Serialized Concurrency**: Release runs are strictly serialized (`concurrency: group: release, cancel-in-progress: false`) to eliminate race conditions when multiple PRs merge in close succession.
2. **Version Bump & Manifest Sync**: `scripts/bump-version.py` determines the next version and updates `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`.
3. **Pre-Release Integrity Gate**: `scripts/verify-integrity.py --check-tag "v$NEXT_VERSION"` verifies manifest synchronization, subagent reference integrity, tool permissions, and description token budgets before publishing.
4. **Recursive Loop Prevention**: Manifest commits include `[skip ci]` to prevent triggering infinite CI cycles.
5. **Git Tag & GitHub Release**: Creates tag `v$NEXT_VERSION` and generates release notes automatically linking merged PRs and authors.

### Skipping Releases

To merge a PR without triggering a version bump or release (for example, maintenance PRs or internal documentation updates), apply the `skip-release` or `no-release` label to the Pull Request prior to merging.

## Project Structure

```text
claude-workflow/                 # Repository root (plugin identifier: workflow)
├── .claude-plugin/
│   ├── plugin.json              # Plugin manifest (version 1.0.0, author, repo)
│   └── marketplace.json         # Marketplace catalog distribution manifest
├── agents/
│   ├── fw-1-spec.md             # BA: Spec and acceptance criteria
│   ├── fw-2-research.md         # Research: Best practices and gap analysis
│   ├── fw-3-role-model.md       # Reference: Throwaway best-practice sample (Opus)
│   ├── fw-4-plan.md             # Architect: Second-order effects analysis (Opus)
│   ├── fw-5-impl.md             # Execution: Implementation and unit tests
│   ├── fw-6-review.md           # Auditor: Independent review (no Edit)
│   └── fw-7-fix.md              # Remediation: Issue resolution
├── hooks/
│   ├── hooks.json               # Hooks (Stop, AskUserQuestion, Notification notifiers; PostToolUse ktlint format)
│   ├── ktlint-format.sh         # POSIX sh ktlint formatter for Kotlin files (PostToolUse)
│   └── notify.sh                # POSIX sh notifier for macOS/Linux (opt-out: CLAUDE_WORKFLOW_NOTIFY=0)
├── scripts/
│   ├── bump-version.py          # Semantic version calculation and manifest sync
│   └── verify-integrity.py      # Pre-release integrity check and gatekeeper
├── skills/
│   ├── feature-workflow/
│   │   └── SKILL.md             # Orchestrator for /feature-workflow
│   ├── android-standards-workflow/
│   │   ├── SKILL.md             # Orchestrator for /android-standards-workflow
│   │   └── standards.md         # Android/Kotlin best practices reference
│   ├── kmp-standards-workflow/
│   │   ├── SKILL.md             # Orchestrator for /kmp-standards-workflow
│   │   └── standards.md         # Kotlin Multiplatform best practices reference
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
│   └── solution-brainstorm/
│       ├── SKILL.md             # Skill for /solution-brainstorm (single pass, no subagents)
│       ├── platforms.md         # Platform registry: detect signals, architecture, patterns
│       ├── legacy-techniques.md # Shared legacy refactoring catalog (cost ladder, techniques, Mikado), read by brainstorm and the feature workflow
│       ├── comment-policy.md    # Shared code comment policy (no comment by default, WHY only), read by brainstorm and the feature workflow
│       └── templates.md         # Fixed 6 criteria and output format
├── tests/
│   ├── test_bump_version.py     # Unit tests for version calculation
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
