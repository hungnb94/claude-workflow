# PR Explainer - Sources

These sources back the rules in SKILL.md and templates.md. All links were checked on 2026-10-29.

## Principles

| Concept | Essence | Metaphor to remember |
|---|---|---|
| Conclusion first | The reader can stop after any sentence and still have the main point. | A news bulletin: the headline and first line tell the story, and the rest adds detail. |
| Why over what | The diff already shows what changed. The comment says why it broke and why it matters. | A doctor explains the diagnosis, not only the prescription. |
| Broken invariant | Name the rule the code must always keep. The root cause is the broken rule, and the fix restores it. Extra guards are a safety net, not the fix. | A restaurant kitchen where only the head chef seasons the food. If another cook adds salt too, the fix is to restore that rule, not to add a taster at the pass. |
| Structurally accurate metaphor | Match the causal structure (who acts on what, and in what order), not only how things look. | A key's teeth must fit the lock. A double bank withdrawal is the wrong key for a bug where one side reads while the other is mid-write. |
| Say where the metaphor breaks | Every comparison simplifies. Say what it does not cover. | The map is not the territory. |
| Only record what was done | List only checks that ran, with how and result. Plans go to Not confirmed or Suggested checks for QA. | Meeting minutes record only what was witnessed, not what people plan to do. |

These metaphors are memory aids chosen for this skill, not quotes.

## Change descriptions

| Source | What it says | Used for |
|---|---|---|
| [Google eng-practices: CL descriptions](https://google.github.io/eng-practices/review/developer/cl-descriptions.html) | Say what changes and why. The first line is specific and stands alone. The body gives the problem, why this approach, and its limits. Avoid vague lines such as "Fix bug". Check the description against the final change. | Technical version, Final checklist |

## Plain language

| Source | What it says | Used for |
|---|---|---|
| [digital.gov: Plain language principles](https://digital.gov/guides/plain-language/principles) | Write for the reader. Use familiar words, active voice, and lists. Put the main point first. | Metaphor version, Writing rules |

## Writing order

| Source | What it says | Used for |
|---|---|---|
| [Wikipedia: Bottom line up front](https://en.wikipedia.org/wiki/Bottom_line_up_front) (overview, not a standard) | Open with the most important point or action, then give the background. | Conclusion first |
| [Wikipedia: Inverted pyramid](https://en.wikipedia.org/wiki/Inverted_pyramid_(journalism)) (overview, not a standard) | Put the most important facts first, in falling order of importance. The text can be cut from the end without losing the core. | Conclusion first |

## Reader needs

| Source | What it says | Used for |
|---|---|---|
| [Diátaxis](https://diataxis.fr/) | Organize documentation by what the reader needs. | Two versions, one reader per version |

## Facts and blame

| Source | What it says | Used for |
|---|---|---|
| [Simon Tatham: How to Report Bugs Effectively](https://www.chiark.greenend.org.uk/~sgtatham/bugs.html) | Say what happened. Separate facts from guesses. | Verified vs Not confirmed, Only record what was done |
| [Google SRE Book: Postmortem culture](https://sre.google/sre-book/postmortem-culture/) | Postmortems are blameless. They focus on systems and contributing causes, not on people. | Blameless wording, Broken invariant wording about systems |

## Explaining with analogies

| Source | What it says | Used for |
|---|---|---|
| [The Muse: Four ways to explain tech concepts to your non-tech coworkers](https://www.themuse.com/advice/four-ways-to-explain-tech-concepts-to-your-nontech-coworkers) (practitioner blog, not a standard) | Compare the idea to something the reader knows. Prepare the comparison ahead. Do not switch comparisons midway. Start with the problem. Invite questions. | Metaphor version |
| [Wikipedia: Structure-mapping theory](https://en.wikipedia.org/wiki/Structure-mapping_theory) (overview, not a standard) | An analogy maps relations, not surface features. Relations in a connected system transfer. | Mapping check: same causal structure |
| [Wikipedia: Map-territory relation](https://en.wikipedia.org/wiki/Map%E2%80%93territory_relation) (overview, not a standard; Korzybski) | A model is not the thing it models. A good map has a similar structure. | Where the comparison stops |

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
- Keep two versions, not one layered comment. The two readers have different needs (Diátaxis), and one facts table keeps the versions consistent. No strong evidence for one layered comment was found on 2026-10-29.
- The output is always English. This is a design choice for international reviewers and stable headings. Chat outside the copy blocks follows the user's language.
- Broken invariant, "Safety net, not the fix", "Suggested checks for QA", and the banned phrases ("should pass", "will be tested", "CI will check") are skill design, not quotes.
