---
name: jira-task
description: Fetch Jira work item details (summary, description, status, parent, links, comments, attachments) with the Atlassian CLI `acli` before working on a task. Use whenever the user mentions a Jira key like PROJ-123 in a ticket context, or pastes a <site>.atlassian.net/browse/... link, or says "làm task jira", "đọc ticket", "xem task". Read-only by default; do not comment, transition, assign, or edit unless the user asks.
---

# Jira task lookup via acli

Requires the Atlassian CLI `acli` on `PATH`, logged in to the user's Jira site (`acli jira auth status` shows the site and account).
A key looks like `[A-Z][A-Z0-9_]+-\d+`. Strings such as `UTF-8`, `SHA-256`, or `ISO-8601` match the pattern but are not Jira keys; do not look them up.

## When the user gives a Jira key or URL

1. Extract the key (from `https://<site>.atlassian.net/browse/PROJ-123` take `PROJ-123`).
2. Fetch the item in two calls. The plain text output shows only key, type, summary, status, assignee, and description; it silently drops every other field, even ones named in `--fields`. In `--json` the description is Atlassian Document Format, which is hard to read. So read the text in plain mode and the relations in JSON:

   ```bash
   acli jira workitem view PROJ-123
   acli jira workitem view PROJ-123 --fields priority,parent,labels,fixVersions,issuelinks,subtasks --json | jq '.fields | {priority: .priority.name, parent: (.parent | if . then "\(.key) \(.fields.summary)" else null end), labels, fixVersions: [.fixVersions[].name], links: [.issuelinks[] | if .outwardIssue then "\(.type.outward) \(.outwardIssue.key) \(.outwardIssue.fields.summary)" else "\(.type.inward) \(.inwardIssue.key) \(.inwardIssue.fields.summary)" end], subtasks: [.subtasks[] | "\(.key) [\(.fields.status.name)] \(.fields.summary)"]}'
   ```

3. Fetch comments (they often carry scope decisions, repro steps, QA feedback):

   ```bash
   acli jira workitem comment list --key PROJ-123 --order +created --limit 1000
   ```

   The default `--limit` is 50, and `--paginate` does not fetch past `--limit`, so always pass a large `--limit`. If the output's `total` is larger than the number of comments shown, tell the user that some comments are missing.

   The table output is very wide. If it is hard to read, use `--json` and extract only the author and body text (both are plain strings in this output). The JSON may contain one object per page, and `.comments[]` reads all of them:
   `acli jira workitem comment list --key PROJ-123 --limit 1000 --json | jq -r '.comments[] | "[\(.id)] \(.author): \(.body)\n"'`

4. List attachments every time. Files such as stack traces are often attached without being mentioned in the description:

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
acli jira workitem comment create --key PROJ-123 --body-file <file>   # multi-line text: write it to a scratch file first
acli jira workitem transition --key PROJ-123 --status "Code Review" --yes
```

## Troubleshooting

- `unauthorized` / not logged in: ask the user to run `! acli jira auth login --web`.
- "outdated version" warning is harmless; ignore it.
- `acli jira auth status` shows the current site and account.
