---
name: pr-explainer
description: Explain a pull request in two versions from the same facts. One is a short plain-language version built on a single everyday metaphor for non-technical readers (PM, QA, business). The other is a technical version with the verified root cause, the fix, impact, and what was actually tested. The output is always in English. Use when the user asks to explain a PR, bug fix, or change to non-technical people, or wants a PR comment that explains why a bug happened. Do not use to write a PR description or commit message, review code, fix bugs, or post comments unless the user asks.
---

# PR Explainer

Draft two explanations of one pull request for the user to copy. Do not post unless the user clearly asks, and do not offer to post unless they mention it.

The output is always in English: copy blocks, headings, facts table, mapping check, and the final line. Chat outside the copy blocks (open questions, assumptions) follows the user's language.

Read `templates.md` (next to this file) before you write. Read `references.md` only when the user asks where a rule comes from.

## Workflow

### Step 1. Collect the input

Use the first source that works: a PR number or URL, a diff or text the user pasted, the PR of the current branch. Never replace input the user gave with the current branch.

```bash
gh pr view <number> --json title,body,files,commits,closingIssuesReferences,comments,headRefName,headRefOid
gh pr diff <number>            # --name-only first for a large diff
gh issue view <issue-number>   # each issue in closingIssuesReferences
```

- Without `<number>`, these read the current branch's PR.
- Without `gh`, use `git log <base>..HEAD` and `git diff <base>...HEAD` only when the PR is the current branch. Otherwise ask the user to paste the diff and description.
- Read the code around the changed functions, plus logs and tests if they exist. Local files show the PR code only when `git rev-parse HEAD` equals `headRefOid`. If not, use `gh api "repos/{owner}/{repo}/contents/<path>?ref=<headRefOid>" -H "Accept: application/vnd.github.raw"`, or say which version you read.
- Read-only: do not check out a branch or edit files.

### Step 2. Fill the facts table

Use the table in `templates.md`. Mark each root cause `Verified` with evidence, or `Not confirmed`. If the PR body conflicts with the diff, trust the diff and tell the user.

### Step 3. Pick and check the metaphor

Choose one everyday metaphor familiar to an international reader. Fill the mapping check in `templates.md`. If it distorts scope, severity, cause, or causal structure, pick another.

### Step 4. Write, check, return

Write the metaphor version, then the technical version, using only the facts table. Run the final checklist, then return the output format below.

## Writing rules

### Both versions

- Conclusion first: a reader who stops after any sentence still has the main point.
- Why over what: the diff shows what changed. Say why it broke and why it matters.
- Broken invariant: when the bug breaks a rule the code must always keep, state the root cause as that rule and the fix as restoring it. Label extra guards (null check, try/catch, skip) "Safety net, not the fix".
- One reader per version. Both describe the same problem, cause, fix, and impact.
- No vague lines ("Fix bug", "improve stability"). No blame on a person. Do not make the problem bigger or smaller.

### Metaphor version

- One metaphor from the first line to the last.
- Structurally accurate: it must match who acts on what and in what order (for a timing bug: who reads, who writes, and when). Looking alike is not enough.
- 100 to 200 words, labels included. Short sentences, familiar words, no unexplained technical terms.
- "Why it matters" in business words: what users saw or lost.
- If the root cause is `Not confirmed`, say the team is still confirming why.

### Technical version

- Cite files, functions, and commits. Explain what triggers the bug and why the old code was wrong.
- Give the fix and why it was chosen, impact, and risks.
- Only record what was done: list checks that actually ran, with how and the result. Never write "should pass", "will be tested", or "CI will check". Anything not run goes to Not confirmed or "Suggested checks for QA".
- Suggested checks for QA come from the changed code paths, not guesses.

## Missing information

Never invent a root cause, file, function, commit, number, test name, test result, or count of affected users.

- Blocking gap (no diff and no description, or unclear which PR): ask first, at most 5 questions.
- Otherwise write `Not confirmed` and list Open questions after the versions. If the user says "just draft it", do not ask.
- A partly supported guess may be written, labeled "Hypothesis" with its evidence.

## Edge cases

- Not a bug fix: use "Non-bug changes" in `templates.md`. Say "no behavior change" only with evidence.
- Workaround or unknown root cause: say so in both versions.
- Several changes: one pair for the main change, side changes listed briefly in the technical version. Several independent bug fixes: ask, or write one pair per fix (at most 3).
- Revert: the problem is what the earlier change broke. Name the reverted commit.
- Security fix: no exploit details. Remind the user to check the text before posting in a public repo.
- Very large diff: focus on files with behavior changes. Say what you did not read.
- One version requested: return only that one.
- No metaphor fits without distortion: write the plain-language version without one and say why outside the copy block.

## Posting to the PR

Post only on a clear request ("post it", "comment on the PR"). If unclear, ask whether to post both versions or one.

Write the text to a temp file outside the repo (`mktemp`), run `gh pr comment <number> --body-file <file>`, delete the file, and report the comment URL. To fix it later, use `--edit-last` only if `gh pr view <number> --json comments` shows that your last comment is that one. Without `gh`, give the text to paste.

## Output format

1. Facts table, outside the copy blocks.
2. "Plain-language version (metaphor)": the text in a four-backtick markdown block.
3. "Technical version": the text in a four-backtick markdown block.
4. Metaphor check: the mapping table.
5. Open questions and Assumptions, if any, in the user's language.
6. "This is a draft. I have not posted it." If you posted on request, the comment URL instead.

Leave out 1 and 4 if the user asks for no facts table. Leave out 4 if there is no metaphor version.

## Final checklist

- [ ] Every root cause is Verified with evidence or Not confirmed. Nothing is invented.
- [ ] Both versions match the facts table and the final diff.
- [ ] Each version opens with the conclusion and says why, not only what.
- [ ] Broken invariant, if any: named as the cause, restored by the fix; guards labeled "Safety net, not the fix".
- [ ] Metaphor: one metaphor, 100 to 200 words, mapping check passed, "where the comparison stops" filled.
- [ ] Technical: cites code, lists only checks that ran, keeps Verified and Not confirmed apart.
- [ ] Output in English. Nothing posted unless asked.
