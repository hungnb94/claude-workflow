---
name: pr-explainer
description: Explain a pull request in two versions from the same facts. One is a short plain-language version built on a single everyday metaphor for non-technical readers (PM, QA, business). The other is a technical version with the verified root cause, the fix, impact, and what was actually tested. The output is always in English. Use when the user asks to explain a PR, bug fix, or change to non-technical people, or wants a PR comment that explains why a bug happened. Do not use to write a PR description or commit message, review code, fix bugs, or post comments unless the user asks.
---

# PR Explainer

This skill drafts two explanations of one pull request. The user copies the text. The skill does not post a comment unless the user clearly asks.

Write these instructions in plain English. The output is always in English: the copy blocks, headings, facts table, mapping check, and the final line. Chat outside the copy blocks (open questions, assumptions, notes) follows the user's language.

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
  - Facts table: problem, root cause, broken invariant (if any), fix, impact, how it was verified (only what ran), suggested checks for QA.
  - Metaphor version: conclusion first, what went wrong, why it matters, how we fixed it, where the comparison stops.
  - Technical version: summary, root cause, fix and why, safety net (if any), impact, how it was verified, suggested checks for QA, verified vs not confirmed.

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

Use the table in `templates.md`. Decide if the PR is a bug fix or a change. Mark each root cause `Verified` with evidence, or `Not confirmed`. If the bug breaks a rule the code must always keep, write it in the "Broken invariant" row. Fill "Suggested checks for QA" from the changed code paths. Follow "Missing information" below.

### Step 3. Pick and check the metaphor

Choose one everyday metaphor before you write. It must be familiar to an English-speaking, international reader. Fill the mapping check in `templates.md`, including who reads, who writes, and when. If it distorts scope, severity, or cause, pick another. Write the "where the comparison stops" sentence.

### Step 4. Write the two versions

Write the metaphor version first, then the technical version. Use only the facts table. For a PR that is not a bug fix, use "Non-bug changes" in `templates.md`.

### Step 5. Self-check

Run the final checklist. Compare the text with the final diff. If the PR has new commits since its description, trust the diff.

### Step 6. Return the draft

Use the output format below. Do not offer to post unless the user mentioned posting. Say only that this is a draft. Post only as described in "Posting to the PR".

## Writing rules

### Both versions

- Conclusion first: write so a reader who stops after any sentence still has the main point.
- Why over what: the diff shows what changed. Say why it broke and why it matters before you list changes.
- Broken invariant: when there is one, state the root cause as the rule that was broken, and the main fix as restoring that rule. Label any extra guard (null check, try/catch, skip) "Safety net, not the fix", apart from the main fix.
- Write each version for one reader. Do not mix both audiences in one version.
- Describe the same problem, cause, fix, and impact.
- Avoid vague lines such as "Fix bug" or "improve stability".
- Stay blameless. Do not name the person who caused the bug. Talk about the system.
- Do not make the problem bigger or smaller than it is.

### Metaphor version

- Use one metaphor from the first line to the last. Do not switch, and do not save it for a closing line.
- Structurally accurate: the metaphor must match who reads, who writes, and when. Looking alike is not enough.
- Say where the metaphor breaks, in "Where the comparison stops".
- Write 100 to 200 words, about one minute of reading. Count the whole copy block, labels included.
- Use short sentences, active voice, and familiar words.
- Use no technical terms. If you must use one, explain it in the same sentence.
- Say "why it matters" in business words: what users saw or lost.
- Do not guess the cause. If the root cause is `Not confirmed`, say in the metaphor that the team is still confirming why.

### Technical version

- Cite files, functions, and commits.
- Explain the mechanism: what triggers the bug and why the old code was wrong.
- Give the fix and why it was chosen.
- Give impact and risks.
- Only record what was done: list only checks that actually ran, with how they ran and the result. Never write "should pass", "will be tested", or "CI will check". Put anything not run in Not confirmed or in "Suggested checks for QA".
- Suggested checks for QA: user actions that go through the changed code path. Take them from the code, not from guesses.
- Keep Verified and Not confirmed in separate lists.
- Never invent test names or results.

## Missing information

Never invent a root cause, file, function, commit, number, test name, test result, or count of affected users.

- Blocking gap: there is no diff and no description, or it is unclear which PR. Ask first. Ask at most 5 questions in one message.
- Non-blocking gap: write `Not confirmed` in the facts table and the technical version. The metaphor version says it is not yet clear. Do not guess. List "Open questions" after the two versions.
- If the user says "just draft it", write with `Not confirmed` and do not ask more.
- A test that did not run is `Not confirmed`, not a result.
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
2. Plain-language version (metaphor): heading "Plain-language version (metaphor)", then the text in a four-backtick markdown block.
3. Technical version: heading "Technical version", then the text in a four-backtick markdown block. It includes "Suggested checks for QA".
4. Metaphor check: the mapping table, outside the copy block.
5. Open questions and Assumptions, if any, in the user's language.
6. One line: "This is a draft. I have not posted it." Always in English. If you posted it on request, give the comment URL instead.

If the user asks for no facts table, leave out items 1 and 4. If there is no metaphor version (one version only, or no good metaphor), leave out item 4.

## Final checklist

- [ ] The facts table is filled. Every root cause is Verified with evidence or marked Not confirmed.
- [ ] Both versions describe the same problem, cause, fix, and impact. Nothing contradicts the facts table.
- [ ] The text still matches the final diff.
- [ ] Metaphor version: one metaphor used from start to end, 100 to 200 words, no unexplained technical terms.
- [ ] Metaphor version: says what went wrong, why it matters, and how it was fixed.
- [ ] Metaphor version: has "where the comparison stops". The mapping check passed for scope, severity, and cause.
- [ ] Technical version: cites files, functions, or commits, and explains the mechanism.
- [ ] Technical version: gives the fix and why, impact and risks, and how it was verified.
- [ ] Technical version: Verified and Not confirmed are apart. No vague lines.
- [ ] A PR that is not a bug fix uses the "why this change" framing.
- [ ] No invented facts. No blame on a person. No exploit details for a security fix.
- [ ] Copy blocks, headings, facts table, and mapping check are in English. Chat outside the blocks follows the user's language. The metaphor is familiar to an international reader.
- [ ] The first sentence of each version is the conclusion. Stopping after any sentence still gives the main point.
- [ ] Each version says why, not only what.
- [ ] If there is a broken invariant, the root cause names it, the fix restores it, and extra guards are labeled "Safety net, not the fix".
- [ ] The mapping check answered "same causal structure: who reads, who writes, and when?".
- [ ] "Where the comparison stops" says where the metaphor breaks.
- [ ] Testing lists only checks that ran, with how and result. No "should pass", "will be tested", or "CI will check". "Suggested checks for QA" come from the code.
- [ ] Each version has one reader.
- [ ] Nothing was posted unless the user asked.

## Sources

The rules rest on Google eng-practices, digital.gov plain language, Simon Tatham, the Google SRE Book, a practitioner blog (The Muse), BLUF and inverted pyramid overviews, Diátaxis, Gentner structure-mapping, Korzybski map-territory, and the GitHub CLI manual. See `references.md`.
