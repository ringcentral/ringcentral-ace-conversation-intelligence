# ACE formulas

How each metric is computed, and — critically — **who computes it**. Prefer server aggregates;
derive only ratios, comparisons, or combinations whose inputs and denominators are established.
Read this before reporting a number. The tool schema controls valid operations; established
units and observed grain control what a result means.

## Server-computed — take the value as-is

Use the returned numeric `metric` for the requested average, total, minimum or maximum.
`docCount` is a count, never a substitute for a missing metric. Check each bucket too; a missing
patience average cannot become a patience ranking merely because counts were returned.

- **`scorecardScore` / `scorecardQuestionScore`** — internal QA on `scorecard`, customer survey
  responses on `csat`. Keep their provenance separate. Do not infer a call-weighted average
  from question-grain rows; describe the server result at its verified grain.
- **Powerskill averages** — server-computed per-speaker metrics. Request one numeric metric
  per aggregate; a search may project sibling metrics when one metric sort fixes its backing
  type. Behavioral metrics are indicators, not verdicts: a high talk-to-listen ratio may
  suit a demo but not discovery.
- **Volume / average duration** — `count` and `average(duration)` on `interaction`. Do not
  silently equate average recorded duration with a broader operational handle-time definition.
- **Breakdowns and trends** — use each returned bucket's count and metric with its coverage.

Read `units.fields`, `units.metric`, `units.bucketKey`, and `units.docCount` where returned.
Prefer explicit per-response metadata. If it is absent, use an explicit unit, scale or direction
of “better” established by the current tool/view contract, and name that basis. Never infer
units from numeric magnitude or a remembered scale. If neither source establishes them, report
the ambiguity; do not rescale. Do not combine conflicting response units. Units may be absent
on empty results. Keep zero, null, missing, no matching data, and unavailable distinct.

## Client-derived — establish the denominator first

### AI-to-human handover

This is a derived calculation; there is no `handoverRate` metric. The starting cohort is
`view: "interaction"`, `agentType equals ApplicationExtension`, within the requested dates
and authorized scope. Count AI interactions, not distinct transfer groups.

1. Enumerate its `groupId` buckets using `kind: "groupBy"`, `limit` at most 500 and
   `page: {}`. Retain each group's AI interaction count and the full top-level AI `docCount`.
   Follow opaque `nextPage.after` unchanged until no cursor or empty buckets; a final
   nonempty page may still return a cursor. `docCount` repeats on pages: take it once per
   disjoint date window, never sum page totals. Keep AI interactions lacking `groupId` in
   the denominator even though no group bucket can represent them.
2. For retrieved group IDs, query `view: "interaction"`, `agentType equals User`, with a
   direct `groupId oneOf` of 1–500 nonempty IDs in the top-level `and`, **without dateRange**.
   Human legs can fall outside the AI cohort dates. Preserve the authorized scope and do
   not add unrelated narrowing. Skip empty ID batches. Completely enumerate the human
   `groupId` buckets too using the same cursor rules; one page is not proof of completeness.
3. Record whether each group has at least one human interaction. Sum the retained AI counts
   only for those groups. Multiple AI interactions count individually; multiple human
   interactions in a group never multiply that group's AI count.

```
handed-over AI interactions = Σ AI interaction count(g), for groups g with ≥1 human interaction
handover rate = handed-over AI interactions / full scoped AI interaction count × 100
```

For long periods, use disjoint AI date windows; combine each group's AI counts across windows
and deduplicate the follow-up IDs into disjoint batches. Do not count a repeated group/page
twice. A zero AI denominator means no percentage, not 0%. Report numerator, denominator,
missing-group coverage and retrieved versus full coverage. Partial pagination, inconsistent
totals or concurrent indexing make this a partial or best-effort result, not a guaranteed
complete snapshot. On permission denial, report insufficient permissions and stop.

**Duration comparisons:** state which legs are measured (all AI, handed-over AI, or matching
human legs). Keep the AI date cohort and human follow-up cohort distinct. For each defined
cohort, request `total(duration)` and `countNonNull(duration)` with identical filters, using
disjoint ID batches (and disjoint dated windows where applicable), then divide summed totals
by summed non-null counts. All-AI duration must include AI legs missing `groupId`; do not
silently restrict it to the enumerable groups. Never average page averages, mix AI/human
populations, or weight by repeated top-level `docCount`. State missing duration coverage;
a zero non-null count yields no average.

### Scored-call coverage

```
coverage = distinct calls with the requested measured score / all scoped calls
```

The numerator must reflect a present score, not merely a scorecard record. A scorecard can have
many question rows per call. Never divide its raw `docCount` by interaction count, and never
try to group scorecards by `interactionId` as a workaround.

Use fieldless `uniqueCount` only when supported for that view and its returned semantics
establish distinct interactions for the measured population. A bounded, fully retrieved search
may instead establish distinct scored ids when completeness and score presence are verified.
Otherwise report that scored-call coverage is unknown. Do not manufacture a percentage from a
sample or label all scoped calls as “eligible” without an eligibility definition.

### First-contact and issue-resolution signals

Resolve each topic, then use `aggregate_interactions`, `view: "insights"`, its returned theme,
and a `signalType` equality filter. Inspect outcome type and exact values first. For a boolean
signal, count the chosen `boolOutcome` over the same signal population; for a string signal,
use an observed `strOutcome`. Combine scope conditions with `combinator: "and"`.

```
known-outcome share = matching outcome observations / observations with known outcomes
```

Also show unknown-outcome coverage. A share of signal records is not an interaction-level rate.
Distinct call prevalence needs distinct ids in both populations, with verified `uniqueCount`
semantics or complete bounded retrieval and deduplication. Never sum overlapping outcome buckets.

**FCR requires correlated evidence:** the same interaction must be both first contact and
resolved. Independent first-contact and resolution percentages, their product, or two filters
that merely match different uncorrelated records do not establish FCR. Correlate complete
per-interaction outcomes under a stated denominator and missing-value rule; if that is not
possible, report the separate signals and say FCR cannot be established.
Cross-view child projections are capped at ten per owner and need not be the filtered child;
they do not establish complete correlated outcomes for this calculation.

### Tracker rate

```
tracker rate = distinct calls containing the tracker hit / scoped calls
```

Verify the count semantics; repeated hits on one call are not additional calls. Label hit
occurrences separately if those are what the response measures. Overlapping trackers do not
form an exclusive partition.

### Mix shares (direction, queue, disposition, category, internal/external)

```
share of bucket = bucket count / independently established total at the same grain
```

A limited bucket sum is not the population total. Multi-valued categories may overlap; shares
need not sum to 100%. Do not construct an “other” bucket by subtraction unless categories are
mutually exclusive and coverage is complete.

### Task completion rate

```
completion = tasks in the verified completed status / tasks in the stated scope
```

Use `view: "tasks"`, the advertised/observed status value, and disclose unknown statuses. This
is a task rate, not a call rate.

### Weighted recombination across windows

For disjoint windows, request `total` and `countNonNull` for the same numeric field with
identical filters/grouping. Verify that both describe the same observations as the average:

```
combined average = Σ totals / Σ non-null observation counts
```

`docCount` includes records that may lack a value. For example, a total of 12 across two
non-null observations and three records gives 6, not 4. Never average averages, substitute
record counts for non-null counts, or assume question/speaker/signal counts are call counts.
If matching denominators or compatible grain are unavailable, retain window results and report
the combined average as unavailable. A zero denominator yields no average, not zero.

### Changes and comparisons

Use `B - A` for absolute change and `(B - A) / A × 100` for relative change with A explicitly
named as the baseline. A zero baseline makes percentage change undefined; show absolute change.
For percentages, distinguish percentage-point change from relative percentage change. Compare
matching windows, scope, units, observation grain, scorecards and missing-value treatment.

## CSAT — provenance-bounded

CSAT uses `scorecardScore` on `view: "csat"`; internal QA uses `view: "scorecard"`. Read each
response's units (or the explicit current view contract when absent) and never merge them
simply because their field names match. Model-derived
end-of-call satisfaction is a third measure: resolve that insight topic and inspect its outcome.
It is neither survey CSAT nor a verified customer rating.
