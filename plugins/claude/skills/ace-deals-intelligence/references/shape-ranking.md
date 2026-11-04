# Shape: ranking

Top or bottom N of something, by some metric.

## The trap

`groupBy.limit` truncates by **document count**, not by your metric. `limit: 10` with an average
metric returns the ten *busiest* buckets, then averages those — not the ten highest-scoring.

## Procedure

1. **Resolve named people, teams, trackers or categories** and build the scope filter.
   Queue/disposition names are not resolver types: discover exact bucket values instead.
2. **Pick the view that carries the metric** — `interaction` for volume/duration, `scorecard` for QA,
   `csat` for satisfaction, `callTrackers` for hit frequency, `powerskill` for talk behavior,
   `tasks` for follow-through, `insights` plus its resolved theme for signal outcomes.
3. **Choose the group-by dimension.** It must be groupable on the selected view. Prefer
   native views: `trackerId` on `callTrackers`, `callTypeName` on `callCategories`, and
   `callQueueName`/`callDispositions` on `interaction`. Other views may advertise child
   groupings; verify their policy and grain. For agents, prefer `hostId` and resolve labels.
4. **Top-N by count** — request N and verify the returned count ordering. A truncated top-N
   result cannot answer bottom-N, which needs complete candidate coverage.
5. **Ranking by any other metric** — over-fetch `limit` to about 3× N (more when N is small), read
   the metric the server already returns on each bucket, sort, cut to N, and state that entities
   outside the fetched buckets were not considered. This is only a ranking **among retrieved
   candidates**, not a proven global top-N. For a global claim, establish complete candidate
   coverage. Exclude missing metrics explicitly; never rank using `docCount` in their place.
6. **Label the buckets.** `hostId` buckets are ids — resolve them to names before reporting.
7. **Capture volume and verified non-null observation counts per entity** alongside the metric.
   If the metric denominator is unknown, state it; raw record volume may overstate support.
8. **Context** — the median across all fetched buckets, so each rank has something to be measured against.

## Bottom-N

Same procedure sorted ascending, plus a **volume floor**: exclude buckets below a stated minimum
verified observation count (5 is a reasonable disclosed default), or the list becomes "entities with almost no data" rather
than "weakest performers". Always state the floor.

## Ranking by improvement or change

One aggregate cannot express this. Query the current period and the prior equal-length period
separately, then rank the per-entity delta. Use matching periods, units and measured populations; window each into disjoint spans of
at most 29 elapsed days. Handle missing metrics and zero baselines explicitly.

## Not supported

Ranking agents by how often they hold the overall lowest score. Grouping by `hostId` with a
`minimum` metric returns each agent's own minimum, which is a different question. Say so rather
than substituting the aggregate that happens to run.

## Reporting

Rank, entity name, metric value with units, verified sample count, and gap versus the fetched-set
median. Show a share or concentration only for an additive count/total with a valid denominator;
a mean score is not a share of total. Then
concentration (how much the top N holds), outliers and caveats (small samples, ties, the volume
floor, the over-fetch cut), and what the leaders do differently — only where a queried metric
supports it.
