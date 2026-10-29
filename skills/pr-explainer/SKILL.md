---
name: pr-explainer
description: Explain a pull request in two versions from the same facts. One is a short plain-language version built on a single everyday metaphor for non-technical readers (PM, QA, business). The other is a technical version with the verified root cause, the fix, impact, and how it was tested. Use when the user asks to explain a PR, bug fix, or change to non-technical people, or wants a PR comment that explains why a bug happened. Do not use to write a PR description or commit message, review code, fix bugs, or post comments unless the user asks.
---

# PR Explainer

This skill drafts two explanations of one pull request. The user copies the text. The skill does not post a comment unless the user clearly asks.

Write these instructions in plain English. Write the output in the user's language. If that is unclear, use the PR's language.

## When to use

- The user wants a PR or bug fix explained to people who are not engineers.
- The user wants a PR comment that explains why a bug happened.
- The user wants a technical root-cause summary for reviewers.
- The PR is not a bug fix, but people need to know why the change was made.

## When not to use

- Writing a full PR description or commit message.
- Reviewing code.
- Fixing a bug.
- Writing an issue. Use `issue-writing` instead.
- Posting a comment when the user did not ask for it.

## Supporting files

Find the folder of this skill with "Base directory for this skill". If it is not shown, search with Glob for `**/pr-explainer/templates.md`.

- Read `templates.md` before you write.
- Read `references.md` only when the user asks where a rule comes from.
- If you cannot read `templates.md`, use these minimum parts and tell the user.
  - Facts table: problem, root cause, fix, impact, verified by.
  - Metaphor version: what went wrong, why it matters, how we fixed it, where the comparison stops.
  - Technical version: summary, root cause, fix and why, impact, verification, verified vs not confirmed.

## Workflow

### Step 1. Collect the input

Use the first source that works. Order: a PR number or URL, a diff or text the user pasted, the PR of the current branch. Never replace input the user gave with the current branch.

```bash
gh pr view <number> --json title,body,files,commits,closingIssuesReferences,comments,headRefName,headRefOid
gh pr diff <number>
gh issue view <issue-number>   # each issue in closingIssuesReferences, not the PR number
```

For the current branch, run the same commands without `<number>`.

- For a large diff, run `gh pr diff <number> --name-only` first. Then read the files that matter.
- Without `gh` or a login, use `git log <base>..HEAD` and `git diff <base>...HEAD` only when the PR is the current branch. Otherwise, or if that fails, ask the user to paste the diff and the description.
- Read the code around the changed functions to confirm the cause. Read logs and tests if they exist. The local files show the PR code only when `git rev-parse HEAD` equals `headRefOid`. If not, read a file at the PR head with `gh api "repos/{owner}/{repo}/contents/<path>?ref=<headRefOid>" -H "Accept: application/vnd.github.raw"`, or say which local version you read.
- Run read-only commands only. Do not check out a branch. Do not edit files.

### Step 2. Fill the facts table

Use the table in `templates.md`. Decide if the PR is a bug fix or a change. Mark each root cause `Verified` with evidence, or `Not confirmed`. Follow "Missing information" below.

### Step 3. Pick and check the metaphor

Choose one everyday metaphor before you write. It must be familiar to the reader and to the culture of the output language. Fill the mapping check in `templates.md`. If it distorts scope, severity, or cause, pick another. Write the "where the comparison stops" sentence.

### Step 4. Write the two versions

Write the metaphor version first, then the technical version. Use only the facts table. For a PR that is not a bug fix, use "Non-bug changes" in `templates.md`.

### Step 5. Self-check

Run the final checklist. Compare the text with the final diff. If the PR has new commits since its description, trust the diff.

### Step 6. Return the draft

Use the output format below. Do not offer to post unless the user mentioned posting. Say only that this is a draft. Post only as described in "Posting to the PR".

## Writing rules

### Both versions

- Put the conclusion first.
- Describe the same problem, cause, fix, and impact.
- Avoid vague lines such as "Fix bug" or "improve stability".
- Stay blameless. Do not name the person who caused the bug. Talk about the system.
- Do not make the problem bigger or smaller than it is.

### Metaphor version

- Use one metaphor and keep it to the end.
- Write 100 to 200 words, about one minute of reading. Count the whole copy block, labels included.
- Use short sentences, active voice, and familiar words.
- Use no technical terms. If you must use one, explain it in the same sentence.
- Say "why it matters" in business words: what users saw or lost.
- Do not guess the cause. If the root cause is `Not confirmed`, say in the metaphor that the team is still confirming why.
- In Vietnamese, use a natural everyday metaphor. Do not translate word for word.

### Technical version

- Cite files, functions, and commits.
- Explain the mechanism: what triggers the bug and why the old code was wrong.
- Give the fix and why it was chosen.
- Give impact and risks.
- Say how it was verified: which test, how it was run.
- Keep Verified and Not confirmed in separate lists.
- Never invent test names or results.

## Missing information

Never invent a root cause, file, function, commit, number, test name, test result, or count of affected users.

- Blocking gap: there is no diff and no description, or it is unclear which PR. Ask first. Ask at most 5 questions in one message.
- Non-blocking gap: write `Not confirmed` in the facts table and the technical version. The metaphor version says it is not yet clear. Do not guess. List "Open questions" after the two versions.
- If the user says "just draft it", write with `Not confirmed` and do not ask more.
- A partly supported guess may be written. Label it "Hypothesis" and give the evidence.

## Edge cases

- Not a bug fix (feature, refactor, performance, docs, chore): use "Non-bug changes". For a refactor, say "no behavior change" only with evidence.
- The fix is a workaround, or the root cause is unknown: say so in both versions.
- Several unrelated changes: use one facts table and one pair for the main change. List the side changes briefly in the technical version. If there are several independent bug fixes, ask the user to choose, or write one numbered pair per fix (at most 3).
- Revert PR: the problem is what the earlier change broke. Name the reverted commit.
- Security fix: give no exploit details in either version. Remind the user to check the text before posting in a public repo.
- Very large diff: read `--name-only` first and focus on files with behavior changes. State what you did not read.
- The user wants one version only: return only that one. Never add a third version.
- The PR body or comments already explain the change: use them as input and check them against the diff. If they conflict, trust the diff and tell the user.
- No good metaphor: if no everyday metaphor maps the facts without distortion, write the plain-language version without a metaphor and say why in one line outside the copy block.

## Posting to the PR

Post only when the user clearly asks, for example "post it" or "comment on the PR". If it is unclear, ask whether to post both versions in one comment or only one.

Write the text to a temporary file outside the repo (for example from `mktemp`), and delete it after posting. Then run `gh pr comment <number> --body-file <file>`. To fix the comment you posted, add `--edit-last` only if your last comment on the PR is that comment. Check with `gh pr view <number> --json comments` first; `--edit-last` edits whatever your last comment is. Without `gh`, give the text for the user to paste. Report the comment URL after posting.

## Output format

Return in this order.

1. Facts: a short facts table outside the copy block, so the user can check it.
2. Plain-language version (metaphor): a clear heading, then the text in a four-backtick markdown block. In Vietnamese, use "Phiên bản dễ hiểu (ẩn dụ)".
3. Technical version: a clear heading, then the text in a four-backtick markdown block. In Vietnamese, use "Phiên bản kỹ thuật".
4. Metaphor check: the mapping table, outside the copy block.
5. Open questions and Assumptions, if any.
6. One line: "This is a draft. I have not posted it." In the output language. If you posted it on request, give the comment URL instead.

If the user asks for no facts table, leave out items 1 and 4. If there is no metaphor version (one version only, or no good metaphor), leave out item 4.

## Final checklist

- [ ] The facts table is filled. Every root cause is Verified with evidence or marked Not confirmed.
- [ ] Both versions describe the same problem, cause, fix, and impact. Nothing contradicts the facts table.
- [ ] The text still matches the final diff.
- [ ] Metaphor version: one metaphor only, 100 to 200 words, no unexplained technical terms.
- [ ] Metaphor version: says what went wrong, why it matters, and how it was fixed.
- [ ] Metaphor version: has "where the comparison stops". The mapping check passed for scope, severity, and cause.
- [ ] Technical version: cites files, functions, or commits, and explains the mechanism.
- [ ] Technical version: gives the fix and why, impact and risks, and how it was verified.
- [ ] Technical version: Verified and Not confirmed are apart. No vague lines.
- [ ] A PR that is not a bug fix uses the "why this change" framing.
- [ ] No invented facts. No blame on a person. No exploit details for a security fix.
- [ ] The language matches the user or the PR. A Vietnamese metaphor reads naturally.
- [ ] Nothing was posted unless the user asked.

## Sources

The rules rest on Google eng-practices, digital.gov plain language, Simon Tatham, the Google SRE Book, a practitioner blog (The Muse), and the GitHub CLI manual. See `references.md`.
