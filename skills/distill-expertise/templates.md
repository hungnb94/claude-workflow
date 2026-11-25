# Templates

Read by `distill-expertise`. The counts below are the only ones. Change a count here, not in `SKILL.md`.

## Contents

- Counts
- Report: Main file, Answers file, Sources file
- Self-check
- Chat summary

## Counts

- Candidates: 10-12
- Kept: 6
- Min schools: 3
- Votes: N is the number of independent voices among the kept teachers; teachers who learned from the same teacher, or who belong to the same school (school of thought, not university or employer), count as one voice. Sharing a company alone does not merge voices. `Consensus` = at least two thirds of N, rounded up (4 when N = 6). `Lone view` = 1 voice, kept only when that teacher ranks first. `Partial support` = anything in between.
- Few voices: when N < 3, use no vote labels. Write `k/N` only, and warn at the top of the report that the result is not reliable enough to synthesize. In named mode, write "single-teacher report" instead of the warning.
- Shortfall: when fewer teachers qualify than Kept, keep only those who do and say "only M teachers qualified". When the qualified teachers span fewer than Min schools schools, keep the best of each school and say "only S schools qualified". Votes then use the smaller N.
- Lesson lines: `Consensus` 50-70, `Partial support` 30-45, `Lone view` 15-25. Under **Few voices**, lessons with the highest k get the `Consensus` length and the rest the `Partial support` length.
- Main file: at most 550 lines, not counting the appendix. Cut words to fit, never verifiable details (numbers, quotes, commands, code).
- Appendix: a code or configuration block longer than 15 lines goes to the appendix of the main file; the lesson keeps a short summary of what each part guards against and links to it.
- Examples: 2 per lesson (1 in a `Lone view` lesson), easy to hard.
- Self-check questions: 3 per lesson (1 in a `Lone view` lesson).
- This week: 3 actions.
- Chat summary: 5-7 lessons
- Max slug: 60 characters
- File name: `YYYY-MM-DD-<topic-slug>.md`, with today's date and a lowercase ASCII slug of the topic: strip diacritics (`đ` becomes `d`), turn every character that is not `a-z` or `0-9` (spaces, `/`, `+`, `.`, quotes) into `-`, collapse repeated `-`, and trim `-` at both ends. Leave out a "learn from <teacher>" part. If nothing is left (for example a topic in a non-Latin script), transliterate it, or use `topic`. If the slug is longer than **Max slug**, keep its first **Max slug** characters. If the next character is not `-`, the cut splits a word, so go back to the last `-` in the kept part (if it has none, keep the cut). Then trim `-` again. The cap keeps the name far below the 255-byte file name limit, which the Write tool's temporary `.tmp.<pid>.<hash>` suffix also counts against. The answers file and the sources file use the same name with `-answers` and `-sources` before `.md`. The three names move together: when any of them exists, add the same `-2`, `-3`, and so on to the slug of all three.

## Report

Write the three files in the user's language and translate the headings. Keep technical terms in English.

### Main file

The lessons. Teacher names appear only inside a quote ("X: ...") and in the lesson footer; vetting goes to the sources file. Use these parts in this order.

```markdown
# <Topic>

- Date: <YYYY-MM-DD>
- Reliability: <one line: what the lessons rest on, for example "public, checkable cases; no measured follower success rate">
- Warnings: <the Few voices warning or "single-teacher report", any Shortfall statement, and in named mode the named teacher's red flags and weak evidence; leave the line out if none>
- Assumptions: <what you assumed from the arguments; leave the line out if none>

## Learning path

### Quick glossary

| Term | Plain meaning |
|---|---|

Only terms the lessons use. No lesson uses a term that is not here or explained where it first appears.

### Learning order

| Lesson | Principle | Label | Learn first | Why here |
|---|---|---|---|---|

Order lessons from the habits a reader can start alone to the ones that build on them; "Learn first" names the earlier lessons each one needs.

### This week

As many actions as **This week** in Counts, each one concrete and linked to its lesson.

## Lesson <n>. <Principle, stated concretely>

### Examples
Real cases from the sources, as many as **Examples** in Counts, easy to hard. Keep the real numbers, quotes, and commands.

### Concept and metaphor
Definition, essence, and the problem it solves, in plain words. At most two metaphors, only where they make the idea easier to remember, and each must match the idea exactly. Then a "Confused with" table:

| Confused with | The difference |
|---|---|

### Detailed knowledge
Why it works (the mechanism the teachers give), the exact thresholds and steps, and when not to use it.

### Pitfalls
Short bullets: the myths, common mistakes, and ways the principle is misapplied or gamed that belong to this lesson (from filter 1 in `knowledge-filters.md`), and the disagreement on this lesson with when to pick which side.

### Apply
In the Apply form of the domain row. Keep the core of the sources: prompts, rule lines, commands, code, routines. Each item says what failure it guards against. End with how to measure it.

### Self-check
As many questions as **Self-check questions** in Counts, climbing from understand to apply to analyze a realistic case. Each has an id `<lesson>.<n>` and ends with "Answer: see `<answers file name>`, <id>". No answers here.

`<vote label (k/N), or only k/N under Few voices>, <other labels if any>` · <source title (date), link>; ...

## Other pitfalls

Only myths, mistakes, or disagreements that fit no lesson. Leave the part out if there are none.

## Teach-back

One question asking the reader to explain the core of the report to a colleague in their own words, with an example. No grading rubric.

## Appendix

Long code and configuration (**Appendix** in Counts), each block under a heading that the lesson links to. Leave the part out if there is none.
```

### Answers file

```markdown
# Answers: <Topic>

## Lesson <n>. <Principle>

### <id>
<The answer, with why. End with the part of the lesson it relies on, for example "Relies on: Examples 2, Pitfalls".>
```

### Sources file

```markdown
# Sources: <Topic>

- Domain type: <row from evidence-domains.md, and its freshness limit>
- Teachers kept: <M> of <candidates searched>, from <number> schools, <N> independent voices
- How votes were counted: <who counted as one voice and why, the thresholds for this N, and which sources quoted in lessons did not vote>

## Votes by lesson

| Lesson | Principle | Voices for (who) | k/N | Label |
|---|---|---|---|---|

## Teachers

| Teacher | School | Own results (label) | Student evidence (label) | Skin in the game | Red flags | Note |
|---|---|---|---|---|---|---|

## Dropped candidates

One line each, with the reason.
```

## Self-check

Run this before saving. Fix every failed item, then check again.

- [ ] Every lesson footer has a source link, a date, and a vote label with its count (under **Few voices**, the count `k/N` only), and it matches the lesson's row in the sources file's vote table.
- [ ] Each vote count matches its label under **Votes** (or **Few voices**), and N counts independent voices only.
- [ ] Every example, threshold, number, quote, and code block comes from a source that the lesson footer links; an inference follows the rule in `knowledge-filters.md` and never states a threshold, number, or code.
- [ ] No lesson is too vague to be wrong (filter 2).
- [ ] Lessons whose newest source is older than the domain's freshness limit carry `Possibly outdated`.
- [ ] Each lesson has every part of the lesson template, and its length fits **Lesson lines**; the main file fits **Main file**, and every block over **Appendix** sits in the appendix.
- [ ] Every self-check id has an entry in the answers file, and every answer names the part of the lesson it relies on.
- [ ] Every myth, common mistake, and disagreement found sits in a lesson's Pitfalls or in Other pitfalls.
- [ ] Teacher names in the main file appear only in quotes and footers.
- [ ] The kept teachers span at least **Min schools** schools, or the shortfall is stated (in named mode, the report says "single-teacher report" instead).
- [ ] Every claim about a teacher has an evidence label, and the report judges no one's character.
- [ ] Every Apply item links to its lesson's principle and says how to measure it.
- [ ] The three file names share one slug, which has at most **Max slug** characters and does not end in `-` or in a cut word.

## Chat summary

```markdown
Saved:
- <main file path>
- <answers file path>
- <sources file path>

Start here: <the This week actions, one line each with its lesson>

<top lessons, as many as Chat summary in Counts, one line each with its vote label>

Teachers kept: <M>, <N> independent voices, from <number> schools. <warning or note from Few voices>
```
