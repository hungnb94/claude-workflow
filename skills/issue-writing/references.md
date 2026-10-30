# Issue Writing - Sources

These sources back the rules in SKILL.md and templates.md. All links were checked on 2026-10-28.

## Stories and sizing

| Source | What it says | Used for |
|---|---|---|
| [Atlassian: User stories](https://www.atlassian.com/agile/project-management/user-stories) | A user story is a short request told from the user's point of view. | Story template |
| [Mountain Goat Software: User stories](https://www.mountaingoatsoftware.com/agile/user-stories) | Mike Cohn: a story is a reminder for a conversation, not a full spec. The "As a, I want, so that" form is a tool. | Story template, Missing information |
| [Agile Alliance: INVEST](https://www.agilealliance.org/glossary/invest/) | Good stories are Independent, Negotiable, Valuable, Estimable, Small, and Testable. | Size and splitting |
| [Atlassian: Epics, stories, and themes](https://www.atlassian.com/agile/project-management/epics-stories-themes) | An epic is a large body of work that is broken into stories. | Input too big (epic) |

## Acceptance criteria and Given/When/Then

| Source | What it says | Used for |
|---|---|---|
| [Atlassian: Acceptance criteria](https://www.atlassian.com/work-management/project-management/acceptance-criteria) | Acceptance criteria are clear, testable conditions. They are agreed before work starts. | Acceptance criteria |
| [Cucumber: Gherkin reference](https://cucumber.io/docs/gherkin/reference/) | Given sets the context, When is the action, Then is the expected outcome. | Acceptance criteria |
| [Cucumber: Better Gherkin](https://cucumber.io/docs/bdd/better-gherkin/) | Keep each scenario to one behavior. Describe what happens, not each UI step. | Acceptance criteria |
| [Martin Fowler: Given When Then](https://martinfowler.com/bliki/GivenWhenThen.html) | Short overview of the Given/When/Then style. | Acceptance criteria |

## Ready and Done

| Source | What it says | Used for |
|---|---|---|
| [Atlassian: Definition of Ready](https://www.atlassian.com/agile/project-management/definition-of-ready) | A ready item is clear enough for the team to start. | Definition of Ready and Done |
| [The Scrum Guide](https://scrumguides.org/scrum-guide.html) | Defines the Definition of Done as a shared quality commitment. It does not define a Definition of Ready (checked: the phrase does not appear). | Definition of Ready and Done |

## Bug reports

| Source | What it says | Used for |
|---|---|---|
| [Simon Tatham: How to Report Bugs Effectively](https://www.chiark.greenend.org.uk/~sgtatham/bugs.html) | Say what you did, what you expected, and what happened. Separate facts from guesses. | Bug reports, Bug template |
| [Linux kernel: Reporting issues](https://www.kernel.org/doc/html/latest/admin-guide/reporting-issues.html) | Give exact versions and a way to reproduce the problem. | Bug reports, Bug template |
| [Chromium: Bug reporting guidelines](https://www.chromium.org/for-testers/bug-reporting-guidelines/) | Give clear steps, the environment, and the expected and actual results. | Bug reports, Bug template |

## Spikes

| Source | What it says | Used for |
|---|---|---|
| [Scaled Agile Framework: Spikes](https://framework.scaledagile.com/spikes) | A spike is research or a small experiment to answer a question or lower risk before building. | Spike template |
| [Mountain Goat Software: Spikes](https://www.mountaingoatsoftware.com/blog/spikes) | Start from a specific question. Limit the time. The output is knowledge, not shippable code. | Spike template |

## GitHub

| Source | What it says | Used for |
|---|---|---|
| [GitHub Docs: Syntax for issue forms](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms) | Issue forms are YAML files in `.github/ISSUE_TEMPLATE`. Fields can be required with `validations`. | Jira vs GitHub |
| [GitHub Docs: Configuring issue templates](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/configuring-issue-templates-for-your-repository) | Templates live in `.github/ISSUE_TEMPLATE`. A `config.yml` file sets up the template chooser. | Jira vs GitHub |
| [GitHub Docs: Creating an issue](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-an-issue) | How issues are created and which fields they can have. | Jira vs GitHub |
| [GitHub Docs: Linking a pull request to an issue](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue) | Keywords close, fix, and resolve (and their forms) close an issue when the pull request merges into the default branch. Use `owner/repo#123` for another repository. | Jira vs GitHub |
| [GitHub Docs: Adding sub-issues](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues) | Sub-issues break larger work into tasks under a parent issue. | Jira vs GitHub, Links and dependencies |
| [GitHub Docs: Creating issue dependencies](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-issue-dependencies) | An issue can be marked as blocked by, or blocking, another issue. | Jira vs GitHub, Links and dependencies |
| [GitHub Docs: Basic writing and formatting syntax](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax) | GitHub Flavored Markdown, including task lists written as `- [ ]`. | Output format |

## Jira

| Source | What it says | Used for |
|---|---|---|
| [Atlassian Support: What is a work item](https://support.atlassian.com/jira-software-cloud/docs/what-is-an-issue/) | Jira now says "work item" for what older versions call an issue. A key is a space key plus a number. | Jira vs GitHub |
| [Atlassian Support: What are work types](https://support.atlassian.com/jira-cloud-administration/docs/what-are-issue-types/) | Software spaces have Epic, Story, Task, Bug, and Subtask by default. Admins can change them. | Jira vs GitHub |
| [Atlassian Support: Link work items](https://support.atlassian.com/jira-software-cloud/docs/link-issues/) | Link types include blocks, is blocked by, duplicates, and relates to. Admins can configure them. | Links and dependencies |
| [Atlassian Support: Markdown and keyboard shortcuts](https://support.atlassian.com/jira-software-cloud/docs/markdown-and-keyboard-shortcuts/) | The Atlassian editor in Jira Cloud converts Markdown as you type. | Output format |

## Design choices without a single source

These are design decisions, not quotes from a source.

- Use `TBD` plus an open question instead of guessing. This protects against invented details.
- Keep titles under about 70 characters. This is a rule of thumb.
- Use the severity scale Critical, Major, Minor, Trivial. This is a common convention. Teams often use their own scale.
- The 3C idea (Card, Conversation, Confirmation, by Ron Jeffries) is behind "keep stories short and list open questions". No direct link is given because it was not checked.
