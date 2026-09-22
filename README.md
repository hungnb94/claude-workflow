# Claude Workflow

[![CI](https://github.com/hungnb94/claude-workflow/actions/workflows/ci.yml/badge.svg)](https://github.com/hungnb94/claude-workflow/actions/workflows/ci.yml)

Structured agent workflows for feature development and generic tasks in Claude Code.

## Overview

Claude Workflow packages two structured workflow frameworks powered by 13 specialized subagents into an official Claude Code Plugin:

1. **Feature Workflow** (`/feature-workflow`) - A 7-phase engineering workflow for software feature development: requirement specification, industry research, throwaway best-practice role-model draft, architecture planning, implementation with tests, independent code review, and automated remediation.
2. **Generic Task Workflow** (`/generic-task-workflow`) - A 6-phase analytical workflow for non-code tasks: requirement specification, methodology research, deliverable planning, content execution, independent quality audit, and automated remediation.

Each workflow applies rigorous engineering discipline: scope definition before execution, industry best practice comparison, second-order effect analysis (with optional backward planning), heterogeneous model routing (Opus for planning, Sonnet for execution), and independent review gates with strict tool isolation.

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
Phase 5: Impl    Phase 6: Review     Phase 7: Fix
[fw-5-impl] -->  [fw-6-review]  -->  [fw-7-fix]
 (Sonnet)         (Sonnet, NO Edit)   (Sonnet)
      |                |                   |
      v                v                   v
 05-impl.md      06-review.md         07-fix.md
```

*Generic Task Workflow (`/generic-task-workflow`) keeps the original six-phase pipeline
(`gtw-1-spec` → `gtw-2-research` → `gtw-3-plan` → `gtw-4-impl` → `gtw-5-review` → `gtw-6-fix`,
writing `01-spec.md` .. `06-fix.md`) — it has no role-model phase.*

### Architectural Principles

1. **Target Workspace Portability**: The plugin code remains immutable and read-only. All runtime workflow artifacts are written directly into the target project's `<repo root>/.workflows/<slug>/` directory using absolute paths.
2. **Progressive Disclosure & Token Economy**: Agent frontmatter descriptions are concise (under 40 tokens), minimizing system prompt overhead during registry discovery. Detailed instructions, rubrics, and workflows are placed in the markdown body and loaded only when a subagent is spawned.
3. **Independent Quality Gate (Least Privilege)**: Review agents (`fw-6-review`, `gtw-5-review`) are strictly prohibited from using the `Edit` tool. They can only read, search, execute tests, and report findings to prevent self-grading bias.
4. **Heterogeneous Model Routing**: Phase 3 (role-model) and Phase 4 (planning) agents use `model: opus` — Phase 3 for reference-implementation quality, Phase 4 for deep analytical reasoning, mandatory second-order effect evaluation, and optional Backward Planning. All other phases use `model: sonnet` for speed and deterministic execution.
5. **Open/Closed Principle & Extensibility**: Code generated and refactored across the pipeline adheres to OCP: open for extension via data-driven dispatch tables, registry patterns, strategies, or generalizations, while closed for modification without patching cascading conditionals (`if-elif ==`). Balanced strictly against YAGNI to prevent over-engineering (no unnecessary abstract classes or factories when lightweight data mappings suffice).

## Usage

### Running Feature Workflow

For software feature development, refactoring, and code tasks:

```bash
# Direct slash command (when installed or running in workspace)
/feature-workflow "<story description, Jira key, or .md path>"

# Canonical plugin-namespaced command
/workflow:feature-workflow "<story description, Jira key, or .md path>"
```

### Running Generic Task Workflow

For standalone non-code tasks, documentation, project planning, and research:

```bash
# Direct slash command (when installed or running in workspace)
/generic-task-workflow "<task description, Jira key, or .md path>"

# Canonical plugin-namespaced command
/workflow:generic-task-workflow "<task description, Jira key, or .md path>"
```

## Subagents Reference

### Feature Workflow Subagents

| Subagent | Role | Model | Tools | Footprint (Tokens) | Responsibility |
|---|---|---|---|---|---|
| `fw-1-spec` | Senior Business Analyst | Sonnet | Read, Grep, Glob, Write, Bash | ~20 | Survey scope, define integration points and acceptance criteria |
| `fw-2-research` | Senior Research Specialist | Sonnet | Read, Grep, Glob, Write, Bash, WebSearch, WebFetch | ~30 | Research industry best practices and conduct gap analysis |
| `fw-3-role-model` | Reference Implementer | Opus | Read, Grep, Glob, Write, Bash | ~15 | Write throwaway best-practice reference snippets (no real source edits) |
| `fw-4-plan` | Senior Solution Architect | Opus | Read, Grep, Glob, Write, Bash | ~20 | Second-order effect analysis, trade-off evaluation, and deliverable design |
| `fw-5-impl` | Senior Execution Engineer | Sonnet | Read, Grep, Glob, Write, Edit, Bash | ~20 | Implement code deliverables and verify with tests |
| `fw-6-review` | Senior Quality Auditor | Sonnet | Read, Grep, Glob, Write, Bash | ~20 | Independent review against AC, classify findings (No Edit tool) |
| `fw-7-fix` | Senior Remediation Engineer | Sonnet | Read, Grep, Glob, Write, Edit, Bash | ~20 | Remediate review findings and prepare release notes |

### Generic Task Workflow Subagents

| Subagent | Role | Model | Tools | Footprint (Tokens) | Responsibility |
|---|---|---|---|---|---|
| `gtw-1-spec` | Senior Business Analyst | Sonnet | Read, Grep, Glob, Write, Bash, WebSearch, WebFetch | ~50 | Survey non-code requirements and establish acceptance criteria |
| `gtw-2-research` | Senior Research Specialist | Sonnet | Read, Grep, Glob, Write, Bash, WebSearch, WebFetch | ~50 | Research methodologies and benchmark against standards |
| `gtw-3-plan` | Senior Solution Architect | Opus | Read, Grep, Glob, Write, Bash | ~50 | Structure deliverables and evaluate trade-offs |
| `gtw-4-impl` | Senior Execution Engineer | Sonnet | Read, Grep, Glob, Write, Edit, Bash | ~60 | Author and generate target deliverables |
| `gtw-5-review` | Senior Quality Auditor | Sonnet | Read, Grep, Glob, Write, Bash | ~60 | Independent quality audit (No Edit tool) |
| `gtw-6-fix` | Senior Remediation Engineer | Sonnet | Read, Grep, Glob, Write, Edit, Bash | ~50 | Remediate audit findings and prepare final handoff |

*Note: Measured via `claude plugin details`. The total always-on footprint across all skills and subagents is ~808 tokens added to session overhead, well below typical context constraints.*

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
│   ├── fw-7-fix.md              # Remediation: Issue resolution
│   ├── gtw-1-spec.md            # Generic BA: Task scope and boundaries
│   ├── gtw-2-research.md        # Generic Research: Methodology benchmarks
│   ├── gtw-3-plan.md            # Generic Architect: Deliverable planning (Opus)
│   ├── gtw-4-impl.md            # Generic Execution: Content generation
│   ├── gtw-5-review.md          # Generic Auditor: Quality audit (no Edit)
│   └── gtw-6-fix.md             # Generic Remediation: Finding remediation
├── scripts/
│   ├── bump-version.py          # Semantic version calculation and manifest sync
│   └── verify-integrity.py      # Pre-release integrity check and gatekeeper
├── skills/
│   ├── feature-workflow/
│   │   └── SKILL.md             # Orchestrator for /feature-workflow
│   └── generic-task-workflow/
│       └── SKILL.md             # Orchestrator for /generic-task-workflow
├── tests/
│   ├── test_bump_version.py     # Unit tests for version calculation
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
