---
name: jira-task
description: Fetch Jira work item details (summary, description, status, parent, links, comments, attachments) with the Atlassian CLI `acli` before working on a task. Use whenever the user mentions a Jira key like PROJ-123, or pastes a <site>.atlassian.net/browse/... link, or says "làm task jira", "đọc ticket", "xem task". Read-only by default; do not comment, transition, assign, or edit unless the user asks.
---

# Jira task lookup via acli

Requires the Atlassian CLI `acli` on `PATH`, logged in to the user's Jira site (`acli jira auth status` shows the site and account).
A key looks like `[A-Z][A-Z0-9]+-\d+`.

## When the user gives a Jira key or URL

1. Extract the key (from `https://<site>.atlassian.net/browse/PROJ-123` take `PROJ-123`).
2. Fetch the item (plain text output is readable; prefer it over `--json`):

   ```bash
   acli jira workitem view PROJ-123 --fields summary,issuetype,status,assignee,priority,parent,labels,fixVersions,issuelinks,subtasks,description
   ```

3. Fetch comments (they often carry scope decisions, repro steps, QA feedback):

   ```bash
   acli jira workitem comment list --key PROJ-123 --order +created
   ```

   The table output is very wide. If it is hard to read, use `--json` and extract only author + body text, e.g.
   `acli jira workitem comment list --key KEY --json | jq -r '.comments[] | "[\(.id)] \(.author): \(.body)\n"'`
   (`author` and `body` are plain strings in this output.)

4. If the description mentions attachments, screenshots, or stack traces:

   ```bash
   acli jira workitem attachment list --key PROJ-123
   ```

   acli cannot download attachment content. Tell the user which files exist and ask them to share the ones that matter.

5. Follow references when relevant: parent story (`parent`), "Cloned from X", linked issues in `issuelinks`, or keys mentioned in description/comments. View them with the same `view` command, but only the ones that change the understanding of the task (do not crawl everything).

6. Summarize for the user before coding: type, status, goal, acceptance criteria / expected behavior, repro steps (for bugs), scope limits stated in comments, related tickets. Then continue with the actual task.

## Other useful read commands

```bash
# My open tasks
acli jira workitem search --jql "assignee = currentUser() AND statusCategory != Done ORDER BY updated DESC" --limit 20
# Subtasks of a story
acli jira workitem search --jql "parent = PROJ-100"
# Open in browser
acli jira workitem view PROJ-123 --web
```

## Writing to Jira (only when the user asks)

Posting is visible to the whole team, so confirm the exact text with the user before running:

```bash
acli jira workitem comment create --key PROJ-123 --body "..."
acli jira workitem transition --key PROJ-123 --status "Code Review" --yes
```

## Troubleshooting

- `unauthorized` / not logged in: ask the user to run `! acli jira auth login --web`.
- "outdated version" warning is harmless; ignore it.
- `acli jira auth status` shows the current site and account.
