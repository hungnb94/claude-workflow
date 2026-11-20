# Templates

Read by `distill-expertise`. The counts below are the only ones. Change a count here, not in `SKILL.md`.

## Counts

- Candidates: 10-12
- Kept: 6
- Min schools: 3
- Votes: N is the number of independent voices among the kept teachers; teachers who share a teacher, a company, or a school count as one voice. `Consensus` = at least two thirds of N, rounded up (4 when N = 6). `Lone view` = 1 voice, kept only when that teacher ranks first. `Partial support` = anything in between.
- Few voices: when N < 3, use no vote labels. Write `k/N` only, and warn at the top of the report that the result is not reliable enough to synthesize. In named mode, write "single-teacher report" instead of the warning.
- Shortfall: when fewer teachers qualify than Kept, keep only those who do and say "only M teachers qualified". Votes then use the smaller N.
- Chat summary: 5-7 principles
- File name: `YYYY-MM-DD-<topic-slug>.md`, with today's date and a lowercase ASCII slug of the topic: strip diacritics (`đ` becomes `d`), and join words with `-`.

## Report

Write the report in the user's language and translate the headings. Keep technical terms in English. Use these parts in this order.

```markdown
# <Topic>

- Date: <YYYY-MM-DD>
- Domain type: <row from evidence-domains.md>
- Teachers kept: <M> of <candidates searched>, from <number> schools, <N> independent voices
- Assumptions: <what you assumed from the arguments, or "none">

## 1. Core knowledge

One block per principle, `Consensus` first, then `Partial support`, then `Lone view`.

### <Principle, stated concretely>

- Labels: <vote label (k/N)>, <other labels if any>
- What to do: <when, how, which threshold>
- Why it works: <the reason the teachers give>
- Supported by: <teacher - source title (date), link>; ...

## 2. Myths

| Popular advice | Why the kept teachers reject it | Source |
|---|---|---|

## 3. Disagreements

| Question | View A (who) | View B (who) | When to pick which |
|---|---|---|---|

## 4. Common mistakes

| Mistake that failed students make | What the teachers do instead | Source |
|---|---|---|

## 5. Apply

In the Apply form of the domain row. Every step links to a principle above and says how to measure it.

## 6. Sources

| Teacher | School | Own results (label) | Student evidence (label) | Skin in the game | Red flags | Note |
|---|---|---|---|---|---|---|

Dropped candidates: one line each, with the reason.
```

## Self-check

Run this before saving. Fix every failed item, then check again.

- [ ] Every principle has a source link, a date, and a vote label with its count.
- [ ] Each vote count matches its label under **Votes** (or **Few voices**), and N counts independent voices only.
- [ ] No principle in Core knowledge is too vague to be wrong (filter 2).
- [ ] Sources older than the domain's freshness limit carry `Possibly outdated`.
- [ ] The kept teachers span at least **Min schools** schools, or the shortfall is stated.
- [ ] Every claim about a teacher has an evidence label, and the report judges no one's character.
- [ ] Myths and Common mistakes are filled, or say "none found".
- [ ] Every Apply step links to a principle.

## Chat summary

```markdown
Saved: <path>

<top principles, as many as Chat summary in Counts, one line each with its vote label>

Teachers kept: <M>, <N> independent voices, from <number> schools. <warning or note from Few voices>
```
