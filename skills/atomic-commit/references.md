# Atomic Commit - Sources

These sources back the rules in SKILL.md and templates.md. All links were checked on 2026-10-31.

## Message format

| Source | What it says | Used for |
|---|---|---|
| [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/) | Commits use the form `type: description`. Types other than `feat` and `fix` may be used, for example `docs:`. | Commit message rules, Types |
| [Chris Beams: How to write a Git commit message](https://cbea.ms/git-commit/) | The seven rules: blank line after subject, 50 characters (not a hard limit, 72 is), capitalize, no period, imperative, wrap body at 72, explain what and why. | Commit message rules, Commit message template |
| `.github/workflows/pr-governance.yml` (this repo, not a web link) | Lists the 11 allowed types and does not require a scope. | Types, Commit message rules |

## Atomic commits

| Source | What it says | Used for |
|---|---|---|
| [Pro Git: Contributing to a Project](https://git-scm.com/book/en/v2/Distributed-Git-Contributing-to-a-Project) | Try to make each commit a logically separate changeset. | What atomic means |
| [Linux kernel: Submitting patches](https://docs.kernel.org/process/submitting-patches.html) | Separate each logical change into a separate patch. | What atomic means |
| [Google Engineering Practices: Small CLs](https://google.github.io/eng-practices/review/developer/small-cls.html) | Keep related test code in the same change. Do refactorings in a separate change from feature changes. | What atomic means, Step 4 |

## Staging and hooks

| Source | What it says | Used for |
|---|---|---|
| [git-apply](https://git-scm.com/docs/git-apply) | `--cached` applies the patch only to the index. `--recount` is an option of the command. | Staging part of a file |
| [git-commit](https://git-scm.com/docs/git-commit) | `--no-verify` bypasses the pre-commit and commit-msg hooks. | Safety rules, Step 7 |
