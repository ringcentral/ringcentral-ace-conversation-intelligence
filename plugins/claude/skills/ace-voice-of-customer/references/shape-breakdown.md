# Shape: breakdown

A single number, or one dimension split by value — no ranking, no time axis.

Covers "how many", "what's the split", "what's the distribution", and "how many fall under X".

## Single metric, no grouping

An aggregate needs at least one of `groupBy` or `metric`, so a bare total is just a metric:

Synthetic executable example: fictional resolved member ids, with the user's established
Asia/Kolkata timezone. It counts inbound calls owned by either example member, excluding
very short calls. Real ids must come from resolution.

<!-- ace-example: aggregate-composite-scope -->
```json
{"tool":"aggregate_interactions","arguments":{"view":"interaction","dateRange":{"from":"2026-08-01T00:00:00+05:30","to":"2026-08-07T23:59:59.999+05:30"},"where":{"combinator":"and","conditions":[{"field":"hostId","op":"oneOf","value":["11111111-1111-4111-8111-111111111111","22222222-2222-4222-8222-222222222222"]},{"field":"callDirection","op":"equals","value":"Inbound"},{"combinator":"not","conditions":[{"field":"duration","op":"lessThan","value":30}]}]},"metric":{"kind":"count"}}}
```

Synthetic evidence search in the same example period; `contains` is a keyword match, not
semantic or guaranteed exact-phrase search. Its page cannot establish a population count.

<!-- ace-example: summary-search-page-one -->
```json
{"tool":"search_interactions","arguments":{"view":"bulletSummary","dateRange":{"from":"2026-08-01T00:00:00+05:30","to":"2026-08-07T23:59:59.999+05:30"},"where":{"field":"summaryValues","op":"contains","value":"billing"},"select":["interactionId","interactionDate","hostName","summaryValues"],"orderBy":[{"field":"interactionDate","order":"desc"}],"page":1,"perPage":100}}
```

## Split by an exact value

`kind: "groupBy"` on a string or boolean field valid for that view, with an optional `limit`.
The following examples are argument fragments:

```json
{ "groupBy": { "kind": "groupBy", "field": "callQueueName", "limit": 20 },
  "metric": { "kind": "count" } }
```

Common dimensions: `callQueueName`, `callDispositions`, `callDirection`,
`interactionType`, `source`, `agentType` (`interaction`); `callTypeName` (`callCategories`);
`sentimentValue` (`sentiment`); `nextStepResolutionStatus` (`tasks`); `trackerInteractionScenario`
(`callTrackers`); `scorecardQuestionType` (`scorecard`, `csat`); `summarySectionName`
(`bulletSummary`).

`callDispositions` values are upstream free text (for example `Voicemail`, `Abandoned`) — read
them from the buckets, never invent one to filter on.

Choose the root for the intended metric grain; use mapped parent/sibling `where` conditions
to define the cohort without changing that grain. Parent-owned interaction buckets can use
child numeric metrics, such as average `csat.scorecardScore` by `hostId`, but those values
retain child observation grain. Child-owned buckets on the interaction root support only
`count` / `uniqueCount`; use a child root for its own allowed numeric combinations.

On insights, `callTypeId` / `callTypeName` group embedded category entries. Their bucket counts
and `countNonNull` are category-entry counts; `uniqueCount` gives distinct parent interactions.
Resolve the signal topic and category before using their values.

For transfer `groupId`, interaction aggregates support cursor paging with `kind: "groupBy"`,
`limit` at most 500 and initial `page: {}`. Copy `nextPage.after` into `page.after` until no
cursor or empty buckets; final nonempty pages may still have a cursor. These are key-ordered
pages, not a ranking. Top-level `docCount` repeats the full count, including missing groups;
never sum it across pages. AI-to-human handover requires complete AI and human enumeration
and the weighted AI-leg formula in `ace-formulas.md`, not a ratio of group counts.

## Distribution of a number

Two kinds, both on numeric fields only.

**Even buckets** — `histogram` with `bucketSize`:

```json
{ "groupBy": { "kind": "histogram", "field": "duration", "bucketSize": 60 } }
```

**Custom bands** — `rangeGroupBy` with `ranges`, each needing `from`, `to`, or both:

```json
{ "groupBy": { "kind": "rangeGroupBy", "field": "duration",
               "ranges": [{ "to": 120 }, { "from": 120, "to": 600 }, { "from": 600 }] } }
```

Use `rangeGroupBy` when the question names thresholds ("under two minutes", "over ten minutes")
and `histogram` when it asks for the shape of the distribution.

Numeric fields available include `duration` on `interaction` / `insights`; QA/CSAT score and
question-score fields (including qualified forms) and all seven powerskill `.value` fields
on `interaction`; own score/question scores on `scorecard` / `csat`; the chosen
`<metricType>.value` on `powerskill`. Consult the grouping and metric allowlists separately;
tracker/task start and end offsets are not numeric metrics.

## Reporting

Report counts at their verified grain and shares only with a compatible independently
established denominator. State the total separately: limited or overlapping buckets do not
sum to the whole. Disclose truncation and the shown/total bucket counts when available; do
not invent an unknown bucket total. On insights, resolve the topic then group `strOutcome`
or `boolOutcome` according to the observed type, not a topic-named field. Missing outcomes
remain unknown. Check metric presence and response units before describing a distribution.

For a distribution, give the shape in words (concentrated, long tail, bimodal) alongside the
numbers, and name the modal bucket.
