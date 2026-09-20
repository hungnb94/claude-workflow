# Claude Workflow

A collection of structured workflows for feature development and generic task execution in Claude Code.

## Overview

This project provides two main workflow frameworks:

1. **Feature Workflow** (`agents/feature-workflow/`) - A comprehensive 6-phase workflow for building new features
2. **Generic Task Workflow** (`agents/generic-task-workflow/`) - A flexible workflow for general-purpose tasks

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

## Agents

The `agents/` directory contains specialized workflow agents:

- **feature-workflow/** - Agent that executes the full feature development lifecycle
- **generic-task-workflow/** - Agent for handling ad-hoc tasks with the same structured approach

## Usage

### Running a Feature Workflow

```bash
# Use the feature workflow agent for new feature development
# The agent will guide you through all 6 phases
```

### Running a Generic Task Workflow

```bash
# Use the generic task workflow agent for standalone tasks
# Follows the same 6-phase structure but more flexible
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
│   ├── feature-workflow/
│   └── generic-task-workflow/
├── skills/
│   ├── fw-1-spec.md      # Feature workflow phase 1
│   ├── fw-2-research.md  # Feature workflow phase 2
│   ├── fw-3-plan.md      # Feature workflow phase 3
│   ├── fw-4-impl.md      # Feature workflow phase 4
│   ├── fw-5-review.md    # Feature workflow phase 5
│   ├── fw-6-fix.md       # Feature workflow phase 6
│   ├── gtw-1-spec.md     # Generic task workflow phase 1
│   ├── gtw-2-research.md # Generic task workflow phase 2
│   ├── gtw-3-plan.md     # Generic task workflow phase 3
│   ├── gtw-4-impl.md     # Generic task workflow phase 4
│   ├── gtw-5-review.md   # Generic task workflow phase 5
│   └── gtw-6-fix.md      # Generic task workflow phase 6
└── README.md
```

## Getting Started

1. Choose the appropriate workflow for your task
2. Start with the Spec phase to define clear requirements
3. Progress through each phase sequentially
4. Use the Review and Fix phases to ensure quality

---

*Built for systematic, high-quality software development with Claude Code*