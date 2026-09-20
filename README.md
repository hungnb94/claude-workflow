# Claude Workflow

A collection of structured workflows for feature development and generic task execution in Claude Code.

## Overview

This project provides two main workflow frameworks:

1. **Feature Workflow** (`skills/feature-workflow/`) - A comprehensive 6-phase workflow for building new features
2. **Generic Task Workflow** (`skills/generic-task-workflow/`) - A flexible workflow for general-purpose tasks

Each workflow follows a systematic approach: Spec → Research → Plan → Implement → Review → Fix.

## Workflow Structure

### Feature Workflow (6 Phases)

| Phase | File | Description |
|-------|------|-------------|
| 1. Spec | `fw-1-spec.md` | Define requirements and acceptance criteria |
| 2. Research | `fw-2-research.md` | Investigate existing code, patterns, and dependencies |
| 3. Plan | `fw-3-plan.md` | Create detailed implementation plan |
| 4. Implement | `fw-4-impl.md` | Execute the implementation |
| 5. Review | `fw-5-review.md` | Code review and quality checks |
| 6. Fix | `fw-6-fix.md` | Address review findings and polish |

### Generic Task Workflow (6 Phases)

| Phase | File | Description |
|-------|------|-------------|
| 1. Spec | `gtw-1-spec.md` | Define task scope and success criteria |
| 2. Research | `gtw-2-research.md` | Gather information and context |
| 3. Plan | `gtw-3-plan.md` | Design approach and steps |
| 4. Implement | `gtw-4-impl.md` | Execute the task |
| 5. Review | `gtw-5-review.md` | Verify completion and quality |
| 6. Fix | `gtw-6-fix.md` | Address any issues found |

## Skills & Agents

The project is structured into workflow skills and specialized subagents:

- **skills/** - Top-level workflow skills invoked by user (`/feature-workflow`, `/generic-task-workflow`)
- **agents/** - Specialized subagents executed during workflow phases (`fw-*.md`, `gtw-*.md`)

## Usage

### Running a Feature Workflow

```bash
# In Claude Code, run the feature-workflow skill for new feature development
/feature-workflow "<story description, Jira key, or .md path>"
```

### Running a Generic Task Workflow

```bash
# In Claude Code, run the generic-task-workflow skill for standalone non-code tasks
/generic-task-workflow "<task description, Jira key, or .md path>"
```

## Philosophy

This workflow system applies structured thinking tools:

- **Backward Planning** - Start from desired outcome, work backwards to steps
- **Second/Third-order Effects** - Consider downstream consequences of decisions
- **Game Theory** - Anticipate stakeholder reactions and system interactions
- **Blue Ocean Strategy** - Find uncontested approaches vs. competing in crowded space
- **Kaizen** - Continuous improvement: always seek better methods

## Project Structure

```
claude-workflow/
├── agents/
│   ├── fw-1-spec.md      # Feature workflow phase 1: Spec & AC
│   ├── fw-2-research.md  # Feature workflow phase 2: Best practices research
│   ├── fw-3-plan.md      # Feature workflow phase 3: Architecture & plan (Opus)
│   ├── fw-4-impl.md      # Feature workflow phase 4: Implementation & test
│   ├── fw-5-review.md    # Feature workflow phase 5: Independent review (no Edit)
│   ├── fw-6-fix.md       # Feature workflow phase 6: Remediation & polish
│   ├── gtw-1-spec.md     # Generic task workflow phase 1: Spec & boundary
│   ├── gtw-2-research.md # Generic task workflow phase 2: Industry research
│   ├── gtw-3-plan.md     # Generic task workflow phase 3: Approach design (Opus)
│   ├── gtw-4-impl.md     # Generic task workflow phase 4: Deliverables creation
│   ├── gtw-5-review.md   # Generic task workflow phase 5: Independent review (no Edit)
│   └── gtw-6-fix.md      # Generic task workflow phase 6: Remediation & handoff
├── skills/
│   ├── feature-workflow/
│   │   └── SKILL.md      # Feature workflow orchestrator skill
│   └── generic-task-workflow/
│       └── SKILL.md      # Generic task workflow orchestrator skill
└── README.md
```

## Getting Started

1. Choose the appropriate workflow for your task
2. Start with the Spec phase to define clear requirements
3. Progress through each phase sequentially
4. Use the Review and Fix phases to ensure quality

---

*Built for systematic, high-quality software development with Claude Code*