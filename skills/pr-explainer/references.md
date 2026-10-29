# PR Explainer - Sources

These sources back the rules in SKILL.md and templates.md. All links were checked on 2026-10-29.

## Change descriptions

| Source | What it says | Used for |
|---|---|---|
| [Google eng-practices: CL descriptions](https://google.github.io/eng-practices/review/developer/cl-descriptions.html) | Say what changes and why. The first line is specific and stands alone. The body gives the problem, why this approach, and its limits. Avoid vague lines such as "Fix bug". Check the description against the final change. | Technical version, Final checklist |

## Plain language

| Source | What it says | Used for |
|---|---|---|
| [digital.gov: Plain language principles](https://digital.gov/guides/plain-language/principles) | Write for the reader. Use familiar words, active voice, and lists. Put the main point first. | Metaphor version, Writing rules |

## Facts and blame

| Source | What it says | Used for |
|---|---|---|
| [Simon Tatham: How to Report Bugs Effectively](https://www.chiark.greenend.org.uk/~sgtatham/bugs.html) | Say what happened. Separate facts from guesses. | Verified vs Not confirmed |
| [Google SRE Book: Postmortem culture](https://sre.google/sre-book/postmortem-culture/) | Postmortems are blameless. They focus on systems and contributing causes, not on people. | Blameless wording |

## Explaining with analogies

| Source | What it says | Used for |
|---|---|---|
| [The Muse: Four ways to explain tech concepts to your non-tech coworkers](https://www.themuse.com/advice/four-ways-to-explain-tech-concepts-to-your-nontech-coworkers) (practitioner blog, not a standard) | Compare the idea to something the reader knows. Prepare the comparison ahead. Do not switch comparisons midway. Start with the problem. Invite questions. | Metaphor version |

## GitHub CLI

| Source | What it says | Used for |
|---|---|---|
| [gh pr view](https://cli.github.com/manual/gh_pr_view) | Shows a pull request. The `--json` flag selects fields. | Step 1 |
| [gh pr diff](https://cli.github.com/manual/gh_pr_diff) | Shows the diff of a pull request. The `--name-only` flag lists changed files. | Step 1 |
| [gh pr comment](https://cli.github.com/manual/gh_pr_comment) | Adds a comment. The `--body-file` flag reads the text from a file. The `--edit-last` flag edits your last comment. | Posting to the PR |

## Design choices without a single source

These are design decisions, not quotes from a source.

- Both versions come from one facts table. This keeps them from contradicting each other.
- The metaphor version is 100 to 200 words. This is the user's choice, not a standard.
- The metaphor mapping check and the "where the comparison stops" line are a skill design.
- The skill drafts text only. It posts a comment only on an explicit request. This is a safety choice.
