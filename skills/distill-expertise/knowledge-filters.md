# Knowledge Filters

Read by `distill-expertise` at Steps 3 and 5. This is the only place for evidence labels, red flags, mentor rules, principle filters, and principle labels.

## Evidence labels

Every claim about a teacher (their results, their students' results) gets one label:

- **Verified**: an independent source confirms it (audited numbers, public records, press that checked it, the students themselves).
- **Self-reported**: only the teacher or their business says it.
- **Unknown**: no data found.

## Red flags

Note each one you find, with its source. Two or more red flags drop the candidate.

- Their main income is selling courses, signals, or memberships, not doing the thing they teach.
- They promise returns or results, or use "guaranteed", "passive", or "in 30 days".
- They show only winners (survivorship bias) and never the share of students who failed.
- Their results cannot be checked, or the numbers change between sources.
- Regulators, courts, or many students have accused them of fraud.
- They pay for testimonials or require them for refunds.

## Mentor rules

1. Student evidence weighs more than their own results. A candidate whose student evidence (or proxy) is `Unknown` never ranks above one with `Verified` or `Self-reported` student evidence.
2. At the same level of student evidence, `Verified` beats `Self-reported`, and then the stronger own results win.
3. Skin in the game breaks ties: they follow their own advice and do the thing for a living.
4. A candidate kept only on proxy or own results gets the note "teaching ability not proven".

## Principle filters

Apply these in order. A principle dropped by one filter does not go on to the next.

1. **Contrast test**: does it separate the people who succeeded from those who failed?
   - Both groups say or do it: drop it as useless.
   - Failed students or popular voices do it and the kept teachers reject it: move it to **Myths**.
   - Failed students do it by mistake rather than by belief: move it to **Common mistakes**.
2. **Concrete enough to be wrong**: it says what to do, when, and with which threshold. Drop vague advice such as "be disciplined" or "write clean code", unless a teacher made it concrete, and then keep the concrete version.
3. **Skin in the game**: the teacher who states it acts on it. If they do not, it does not count as their vote.
4. **Time test**: it has held across several cycles (market cycles, technology generations). It gets a bonus. A newer principle that passed filters 1-3 stays, with the `New, not time-tested` label.

## Principle labels

- **Vote labels**: `Consensus`, `Partial support`, and `Lone view`, with the thresholds from **Votes** in `templates.md` Counts. Count independent voices only.
- **New, not time-tested**: from filter 4.
- **Possibly outdated**: its newest source is older than the domain's freshness limit.
- **Changed view**: the teacher once said otherwise; give the old view and the date of the change.
