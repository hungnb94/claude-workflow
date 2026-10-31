---
name: atomic-commit
description: Split uncommitted changes into atomic commits and write each message with Conventional Commits and Chris Beams rules. Use when the user asks to commit changes, split changes into commits, or write a commit message. Do not use to push, open a pull request, or amend, rebase, or squash existing commits unless the user asks.
---

# Atomic Commit

This skill reads the uncommitted changes, groups them into atomic commits, shows a plan, and commits after the user approves. It does not push and does not open a pull request. It uses no subagents.

Write in plain English. Use short sentences.

If you are running as a step inside a workflow that has its own commit rules, follow that workflow. Example: feature-workflow makes exactly one commit per slice. Use only the message rules and the staging safety rules from this skill. Do not stop for plan approval.

A workflow that has already finished does not count. When the user runs this skill after a workflow ends (for example, refactor-code-workflow suggests `/atomic-commit` for its `test:` and `refactor:` commits), use the full workflow below, including the plan approval.

## When to use

- The user asks to commit the current changes.
- The user wants the changes split into several commits.
- The user wants a commit message written or checked.
- The user says "commit what is staged".

## When not to use

- Pushing, or opening a pull request.
- Amending, rebasing, squashing, or rewording existing commits, unless the user asks clearly.
- Writing a PR description (use pr-explainer).
- Writing an issue (use issue-writing).
- Reviewing code.

## Supporting files

Find the folder of this skill with "Base directory for this skill". If it is not shown, search with Glob for `**/atomic-commit/templates.md`.

- Read `templates.md` before you write the plan or any message.
- Read `references.md` only when the user asks where a rule comes from.
- If you cannot read `templates.md`, use the message rules and the type list in this file, and tell the user.

## What atomic means

A commit is atomic when it meets all of these:

- It is one logical change. The header does not need "and".
- The repo still builds and passes tests after it.
- It can be reverted alone, with no other commit.
- The tests for the code go in the same commit as the code.
- Refactoring, formatting, and renaming are separate from behavior changes, and come first.

These are rules for grouping. Do not run the build or the tests for each commit. When you cannot meet all of them, keep the repo working first, and merge groups instead of splitting them wrongly.

## Workflow

### Step 1. Check the repository state

Run `git status`.

- A merge, rebase, cherry-pick, or unmerged paths are in progress: stop and tell the user. Do not commit.
- Nothing is staged, modified, or untracked: say there is nothing to commit and stop. Never create an empty commit.

### Step 2. Read all changes

```bash
git diff --cached
git diff
git ls-files --others --exclude-standard
```

For a big diff, run `git diff --stat` first and then read file by file. Read the content of untracked files.

### Step 3. Exclude unsafe files

Never stage these. List them separately in the plan.

- Possible secrets: `.env`, `.env.*`, `*.pem`, `*.key`, `id_rsa*`, `credentials*`, `*secret*`.
- Build and workflow artifacts: `.workflows/`, `dist/`, `build/`, `out/`, `node_modules/`, `*.log`, `.DS_Store`.

These patterns are heuristics. If a match looks like real source (for example `SecretsManager.kt` or `src/build/`), do not exclude it silently. List it under Questions.

If a secret file is already staged, do not commit it. Tell the user. Offer `git restore --staged -- <path>` and run it only if the user agrees.

### Step 4. Group the changes

- Staged changes are commit 1. Keep them as they are. You may suggest the message.
- If the user said "commit what is staged", make only that commit and leave the rest.
- Group the rest by the rules in "What atomic means".
- Order: refactor, format, and preparation first. Then behavior changes. Then independent docs and chores.
- Two changes mixed in one hunk: keep them in one commit and write the reason in the plan.
- A big diff or unclear boundaries: ask the user. Offer one or two options. Do not guess.
- These always move as whole files: untracked, deleted, renamed, binary, and mode-only changes.

### Step 5. Show the plan and stop

Use the "Commit plan template" in `templates.md`. Then wait for the answer.

Skip the wait only when the user clearly says to commit now, for example "commit now", "just commit", or "commit luôn". If the user changes the plan, update it and show it again.

### Step 6. Stage and commit each group, in order

- Whole files: `git add -- <path>...`. For a rename, add the old and the new path. For a deleted file, `git add -- <old-path>` stages the deletion.
- Part of a file: follow "Staging part of a file".
- Before each commit, run `git diff --cached --name-only` and `git diff --cached --stat`. They must match the group. If not, run `git restore --staged -- <path>` for the extra files and check again.
- Commit with `git commit -F <file>`, using a temp file outside the repo, or a quoted heredoc: `git commit -F - <<'EOF'`. Do not put the message in double quotes with `-m`. The shell runs backticks and `$(...)` inside double quotes, and messages often contain backticks.
- Run `git status` to see what is left.

### Step 7. If a hook fails

The commit was not created. Read the error and fix the cause. If a hook changed files, stage those files of the group again, with the same method as before. For a file split by hunk, use `git apply --cached` again, not `git add`, so the other groups' hunks stay out. Then create a new commit. Never use `--no-verify`. Never use `--amend` for this.

If you cannot fix it, or the fix is outside this change, stop. Tell the user the error. Leave the index as it is.

### Step 8. Report

Use the "Final report template". Run `git log --oneline -n <count>` to list the new commits. Say that nothing was pushed.

## Commit message rules

- Format: `<type>[(<scope>)]: <subject>`, a blank line, then an optional body.
- The header is the whole first line, including the `type(scope):` prefix. Aim for 50 characters or less. 72 is the hard limit.
- Use the imperative mood: "add", not "added" or "adds".
- Start the subject with a lowercase letter after the colon. Conventional Commits replaces the Beams capital-letter rule here.
- Do not end the subject with a period.
- Put one blank line between the header and the body.
- Wrap body lines at 72 characters. Explain what and why, not how.
- The scope is optional. Footers and trailers are out of scope. Add them only if the user asks.
- Use only these 11 types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.
- The target repo wins. If it has its own commit rules (a commitlint config, a CONTRIBUTING file, or a clear pattern in `git log --oneline -n 20`), follow them where they differ from these, and say so in the plan.

## Staging part of a file

Use this only for tracked text files with more than one separate change. Do not use `git add -p` or `git add -i`. They need an interactive terminal. Do not edit the file by hand to split it.

```bash
tmp=$(mktemp -d)
git diff -- <file> > "$tmp/full.patch"
```

1. Create `$tmp/part.patch`. Copy the file header lines (`diff --git`, `index`, `---`, `+++`) and only the chosen hunks. Copy them as they are. Do not change any content line.
2. Apply the patch to the index only:

   ```bash
   git apply --cached --recount "$tmp/part.patch"
   ```

3. Check the result. The index must hold only the chosen hunks. The working tree must keep the rest.

   ```bash
   git diff --cached -- <file>
   git diff -- <file>
   ```

4. Commit, then repeat for the next group. Remove `$tmp` at the end.

If `git apply` fails, merge those hunks into one commit and write the reason in the plan. Do not force it.

## Safety rules

- Never run `git add -A`, `git add .`, or `git commit -a`.
- Stage only with `git add -- <path>` or `git apply --cached`.
- Never use `--no-verify`.
- Never amend, rebase, squash, or reset existing commits unless the user asks clearly.
- Never push. Never open a pull request.
- Never commit secrets or artifacts from Step 3.
- Never create an empty commit.

## Edge cases

| Case | What to do |
|---|---|
| Clean working tree | Say there is nothing to commit. No empty commit. |
| Merge, rebase, or conflict in progress | Stop and tell the user. |
| Huge diff or unclear boundaries | Ask the user. Do not guess. |
| Two changes in one hunk | One commit. Write the reason in the plan. |
| Binary file | Commit the whole file in one commit. |
| Renamed file | Add the old and the new path together. |
| Deleted file | `git add -- <old-path>` stages the deletion. |
| Untracked file | Read it. Add it as a whole file. |
| Secret already staged | Do not commit. Tell the user. |
| Hook fails | Fix the cause. Make a new commit. See Step 7. |
| User wants only what is staged | Commit only the staged part. |
| User asks to amend | Do it only because the user asked clearly. |
| User asks to push | Say this skill does not push. Give the command for the user to run. |

## Final checklist

- [ ] The user approved the plan, or clearly said to commit now.
- [ ] Each commit is one logical change, with its tests.
- [ ] `git diff --cached` matched the group before each commit.
- [ ] Every header is 50 characters or less where possible, and never over 72.
- [ ] Every type is one of the 11 types.
- [ ] No secret or artifact file was staged. They are listed in the plan.
- [ ] No `--no-verify`, no amend, no empty commit.
- [ ] Nothing was pushed.
