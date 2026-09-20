# Claude Workflow

[![CI](https://github.com/hungnb94/claude-workflow/actions/workflows/ci.yml/badge.svg)](https://github.com/hungnb94/claude-workflow/actions/workflows/ci.yml)

Six-phase structured agent workflows for feature development and generic tasks in Claude Code.

## Overview

Claude Workflow packages two structured workflow frameworks powered by 12 specialized subagents into an official Claude Code Plugin:

1. **Feature Workflow** (`/feature-workflow`) - A 6-phase engineering workflow for software feature development: requirement specification, industry research, architecture planning, implementation with tests, independent code review, and automated remediation.
2. **Generic Task Workflow** (`/generic-task-workflow`) - A 6-phase analytical workflow for non-code tasks: requirement specification, methodology research, deliverable planning, content execution, independent quality audit, and automated remediation.

Each workflow applies rigorous engineering discipline: scope definition before execution, industry best practice comparison, backward planning with second-order effect analysis, heterogeneous model routing (Opus for planning, Sonnet for execution), and independent review gates with strict tool isolation.

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

### Six-Phase Sequential Pipeline

```text
Phase 1: Spec       Phase 2: Research     Phase 3: Plan
[fw-1-spec /        [fw-2-research /      [fw-3-plan /
 gtw-1-spec]   -->   gtw-2-research]  -->  gtw-3-plan]
 (Sonnet)            (Sonnet)              (Opus)
      |                   |                     |
      v                   v                     v
 01-spec.md          02-research.md        03-plan.md
                                                |
+-----------------------------------------------+
|
v
Phase 4: Impl       Phase 5: Review       Phase 6: Fix
[fw-4-impl /        [fw-5-review /        [fw-6-fix /
 gtw-4-impl]   -->   gtw-5-review]    -->  gtw-6-fix]
 (Sonnet)            (Sonnet, NO Edit)     (Sonnet)
      |                   |                     |
      v                   v                     v
 04-impl.md          05-review.md          06-fix.md
```

### Architectural Principles

1. **Target Workspace Portability**: The plugin code remains immutable and read-only. All runtime workflow artifacts are written directly into the target project's `<repo root>/.workflows/<slug>/` directory using absolute paths.
2. **Progressive Disclosure & Token Economy**: Agent frontmatter descriptions are concise (under 40 tokens), minimizing system prompt overhead during registry discovery. Detailed instructions, rubrics, and workflows are placed in the markdown body and loaded only when a subagent is spawned.
3. **Independent Quality Gate (Least Privilege)**: Phase 5 review agents (`fw-5-review`, `gtw-5-review`) are strictly prohibited from using the `Edit` tool. They can only read, search, execute tests, and report findings to prevent self-grading bias.
4. **Heterogeneous Model Routing**: Phase 3 planning agents use `model: opus` for deep analytical reasoning, Backward Planning, and second-order effect evaluation. All other phases use `model: sonnet` for speed and deterministic execution.

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
| `fw-3-plan` | Senior Solution Architect | Opus | Read, Grep, Glob, Write, Bash | ~20 | Backward planning, trade-off evaluation, and deliverable design |
| `fw-4-impl` | Senior Execution Engineer | Sonnet | Read, Grep, Glob, Write, Edit, Bash | ~20 | Implement code deliverables and verify with tests |
| `fw-5-review` | Senior Quality Auditor | Sonnet | Read, Grep, Glob, Write, Bash | ~20 | Independent review against AC, classify findings (No Edit tool) |
| `fw-6-fix` | Senior Remediation Engineer | Sonnet | Read, Grep, Glob, Write, Edit, Bash | ~20 | Remediate review findings and prepare release notes |

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

## Project Structure

```text
claude-workflow/                 # Repository root (plugin identifier: workflow)
├── .claude-plugin/
│   ├── plugin.json              # Plugin manifest (version 1.0.0, author, repo)
│   └── marketplace.json         # Marketplace catalog distribution manifest
├── agents/
│   ├── fw-1-spec.md             # BA: Spec and acceptance criteria
│   ├── fw-2-research.md         # Research: Best practices and gap analysis
│   ├── fw-3-plan.md             # Architect: Backward planning (Opus)
│   ├── fw-4-impl.md             # Execution: Implementation and unit tests
│   ├── fw-5-review.md           # Auditor: Independent review (no Edit)
│   ├── fw-6-fix.md              # Remediation: Issue resolution
│   ├── gtw-1-spec.md            # Generic BA: Task scope and boundaries
│   ├── gtw-2-research.md        # Generic Research: Methodology benchmarks
│   ├── gtw-3-plan.md            # Generic Architect: Deliverable planning (Opus)
│   ├── gtw-4-impl.md            # Generic Execution: Content generation
│   ├── gtw-5-review.md          # Generic Auditor: Quality audit (no Edit)
│   └── gtw-6-fix.md             # Generic Remediation: Finding remediation
├── skills/
│   ├── feature-workflow/
│   │   └── SKILL.md             # Orchestrator for /feature-workflow
│   └── generic-task-workflow/
│       └── SKILL.md             # Orchestrator for /generic-task-workflow
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
