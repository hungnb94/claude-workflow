# Templates

Read by `distill-expertise`. The counts below are the only ones. Change a count here, not in `SKILL.md`.

## Contents

- Counts
- Report: Main file, Source material rules, Sources file
- Self-check
- Chat summary

## Counts

- Candidates: 10-12
- Kept: 6
- Min schools: 3
- Votes: N is the number of independent voices among the kept teachers; teachers who learned from the same teacher, or who belong to the same school (school of thought, not university or employer), count as one voice. Sharing a company alone does not merge voices. `Consensus` = at least two thirds of N, rounded up (4 when N = 6). `Lone view` = 1 voice, kept only when that teacher ranks first. `Partial support` = anything in between.
- Few voices: when N < 3, use no vote labels. Write `k/N` only, and warn at the top of the report that the result is not reliable enough to synthesize. In named mode, write "single-teacher report" instead of the warning.
- Shortfall: when fewer teachers qualify than Kept, keep only those who do and say "only M teachers qualified". When the qualified teachers span fewer than Min schools schools, keep the best of each school and say "only S schools qualified". Votes then use the smaller N.
- Principle lines: prose lines per principle, `Consensus` 30-45, `Partial support` 20-30, `Lone view` 10-15. Under **Few voices**, principles with the highest k get the `Consensus` length and the rest the `Partial support` length.
- Main file: at most 400 prose lines.
- Source material: the code blocks, quotes, and tables inside a principle's Source material part do not count toward **Principle lines** or **Main file**. When the prose does not fit, cut prose first, starting with the principles with the lowest k. Never cut source material or a verifiable detail (number, quote, command, code) to fit.
- Excerpt: aim for 5-30 lines per code block. A longer block that cannot be trimmed stays whole inside its principle.
- Metaphor: at most 1 per principle, at most 2 sentences, only in Mechanism, and only when it matches the idea exactly.
- This week: 3 actions.
- Chat summary: 5-7 principles
- Max slug: 60 characters
- File name: `YYYY-MM-DD-<topic-slug>.md`, with today's date and a lowercase ASCII slug of the topic: strip diacritics (`đ` becomes `d`), turn every character that is not `a-z` or `0-9` (spaces, `/`, `+`, `.`, quotes) into `-`, collapse repeated `-`, and trim `-` at both ends. Leave out a "learn from <teacher>" part. If nothing is left (for example a topic in a non-Latin script), transliterate it, or use `topic`. If the slug is longer than **Max slug**, keep its first **Max slug** characters. If the next character is not `-`, the cut splits a word, so go back to the last `-` in the kept part (if it has none, keep the cut). Then trim `-` again. The cap keeps the name far below the 255-byte file name limit, which the Write tool's temporary `.tmp.<pid>.<hash>` suffix also counts against. The report has 2 files: the main file, and the sources file with the same name and `-sources` before `.md`. The two names move together: when either of them exists, add the same `-2`, `-3`, and so on to the slug of both.

## Report

Write the two files in the user's language and translate the headings. Keep technical terms in English. Copy source material in its original language.

### Main file

A reference document, not a course: each principle keeps the original knowledge (code, prompts, configuration, quotes, numbers) verbatim, with a link to read the full source. Teacher names appear only inside a quote ("X: ..."), in the principle footer, and in the named-mode Warnings line; vetting goes to the sources file. Use these parts in this order.

```markdown
# <Topic>

- Date: <YYYY-MM-DD>
- Reliability: <one line: what the principles rest on, for example "public, checkable cases; no measured follower success rate">
- Warnings: <the Few voices warning or "single-teacher report", any Shortfall statement, and in named mode the named teacher's red flags and weak evidence; leave the line out if none>
- Assumptions: <what you assumed from the arguments; leave the line out if none>

## Reading path

### Quick glossary

| Term | Plain meaning |
|---|---|

Only terms the principles use. No principle uses a term that is not here or explained where it first appears.

### Reading order

| Principle | Statement | Label | Read first | Why here |
|---|---|---|---|---|

Order principles from the ones a reader can use alone to the ones that build on them; "Read first" names the earlier principles each one needs. This order sets the principle numbers in both files. Under **Few voices**, the Label column holds `k/N`.

### This week

As many actions as **This week** in Counts, each one concrete and linked to its principle.

## Principle <n>. <Principle, stated concretely>

### Statement
One sentence that can be checked or measured: what to do, when, and with which threshold.

### Source material
The original knowledge, verbatim, in the Source material form of the domain row, following the **Source material rules**. Real cases from the sources go here.

### Mechanism
Why it works, as the sources explain it, pointing to the source material item it explains. At most **Metaphor** in Counts.

### Thresholds and steps
The exact numbers, limits, and ordered steps the sources give, each pointing to the source material item it comes from.

### When not to use
The cases where the sources say it fails or does not apply.

### Pitfalls
Short bullets: the myths, common mistakes, and ways the principle is misapplied or gamed that belong to this principle (from filter 1 in `knowledge-filters.md`), and the disagreement on this principle with when to pick which side.

### Apply
In the Apply form of the domain row. Point to the source material it reuses instead of retelling it. Each item says what failure it guards against and how to measure it.

`<vote label (k/N), or only k/N under Few voices>, <other labels if any>` · <teacher - source title (date), link>; ...

## Other pitfalls

Only myths, mistakes, or disagreements that fit no principle. Leave the part out if there are none.
```

### Source material rules

Every item in a Source material part follows these rules.

1. One lead-in sentence comes before each block: what it shows and where it comes from.
2. Every code block has a language tag (`python`, `bash`, `json`, `yaml`; `text` for prompts and plain output).
3. Copy the real code from the source. Cut only the lines that do not bear on the principle, and mark each cut with a comment in the block's own language (`// ...`, `# ...`, `<!-- ... -->`). Do not rename, rewrite, or tidy what you keep. Aim for **Excerpt** in Counts.
4. When the source shows the output or result, put it in its own block right after the code.
5. The explanation comes after the block, never instead of it.
6. A change is shown as the before block and the after block next to each other (or one `diff` block), with what changed named under them.
7. Every block, quote, and table ends with its source and date: `Source: <file path, commit, or URL> (<YYYY-MM-DD>)`. Add the license when you copy a long block and the source states one.
8. Never replace code, a prompt, a configuration, a command, or a quote with a description of it in words. A long block that cannot be trimmed stays whole inside its principle; nothing moves to the end of the file. If you could not read the original, say so instead of writing a paraphrase.

### Sources file

```markdown
# Sources: <Topic>

- Domain type: <row from evidence-domains.md, and its freshness limit>
- Teachers kept: <M> of <candidates searched>, from <number> schools, <N> independent voices
- How votes were counted: <who counted as one voice and why, the thresholds for this N, and which sources quoted in principles did not vote>

## Votes by principle

| Principle | Statement | Voices for (who) | k/N | Label |
|---|---|---|---|---|

Principle numbers match the main file. Under **Few voices**, write `-` in the Label column.

## Teachers

| Teacher | School | Own results (label) | Student evidence (label) | Skin in the game | Red flags | Note |
|---|---|---|---|---|---|---|

## Dropped candidates

One line each, with the reason.
```

## Self-check

Run this before saving. Fix every failed item, then check again.

- [ ] Every principle footer has a source link, a date, and a vote label with its count (under **Few voices**, the count `k/N` only), and it matches the principle's row in the sources file's vote table.
- [ ] Each vote count matches its label under **Votes** (or **Few voices**), and N counts independent voices only.
- [ ] Every example, threshold, number, quote, and code block comes from a source that the principle footer links; an inference follows the rule in `knowledge-filters.md` and never states a threshold, number, or code.
- [ ] No principle is too vague to be wrong (filter 2), and each Statement is one sentence that can be checked.
- [ ] Principles whose newest source is older than the domain's freshness limit carry `Possibly outdated`.
- [ ] Each principle has the seven parts of the principle template in order, and its Source material part is not empty.
- [ ] Every source material item (code block, prompt, configuration, quote, table) ends with a link and a date.
- [ ] No paragraph describes code, a prompt, a configuration, or a command without the verbatim block it describes in the same principle.
- [ ] Every code block has a language tag, marks its cuts with comments in its own language, and is followed by its output when the source shows one; a change is shown as before and after.
- [ ] The prose of each principle fits **Principle lines** and the main file fits **Main file**; no source material was cut to fit.
- [ ] Each principle follows **Metaphor**: at most one metaphor, of at most two sentences, and only in Mechanism.
- [ ] Every myth, common mistake, and disagreement found sits in a principle's Pitfalls or in Other pitfalls; there is no separate table for them, and Other pitfalls is left out when empty.
- [ ] Teacher names in the main file appear only in quotes, footers, and the named-mode Warnings line.
- [ ] The kept teachers span at least **Min schools** schools, or the shortfall is stated (in named mode, the report says "single-teacher report" instead).
- [ ] Every claim about a teacher has an evidence label, and the report judges no one's character.
- [ ] Every Apply item says what failure it guards against and how to measure it.
- [ ] The two file names share one slug, which has at most **Max slug** characters and does not end in `-` or in a cut word.

## Chat summary

```markdown
Saved:
- <main file path>
- <sources file path>

Start here: <the This week actions, one line each with its principle>

<top principles, as many as Chat summary in Counts, one line each with its vote label>

Teachers kept: <M>, <N> independent voices, from <number> schools. <warning or note from Few voices>
```
