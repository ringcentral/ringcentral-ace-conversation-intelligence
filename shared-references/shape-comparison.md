# Shape: comparison

Two named things, side by side, over one period. Agents, teams, categories, queues, trackers,
products, or two periods of the same thing.

## Procedure

1. **Resolve both sides first**, with a separate `resolve_entities` query for each named
   person or concept. One combined phrase does not batch independent names. Attempt both
   sides before declaring either unavailable; clarify consequential candidate ambiguity.
2. **Split A vs B in one query** where the dimension is groupable: `groupBy` on the dimension,
   plus a `where` filter restricting it to the two resolved ids (`oneOf`). One query, two
   buckets under the same requested scope. Check missing buckets and returned coverage.
3. **Use one filtered query per entity** when the dimension is not groupable on the needed view —
   teams are the common case. Keep `dateRange`, metric and all non-entity filters identical;
   only the resolved entity or roster filter changes.
4. **Repeat per dataset** the question needs (volume, scorecard, speaker metric, sentiment,
   CSAT). One metric type per `powerskill` call.
5. **Report the difference** as B − A and, when meaningful, `(B − A) / A × 100`, naming A
   as the baseline. If A is zero, percentage change is undefined. Verify the requested metrics
   are present and units match; do not substitute counts. Show non-null observation counts,
   call coverage and missingness, or state that those denominators are unknown.

## Teams

Resolve `["team"]`, take `memberIds`, and filter `hostId oneOf memberIds` — **one call per metric
per team using its complete, deduplicated roster**. Disclose missing roster coverage. Do not
partition a global breakdown, and do not fall back to a script. A team's own `entityId` is not a
valid call filter. Full procedure: "Scoping to a team" in `ace-mechanics.md`.

Report each team's member count beside its call volume and averages — two teams of very
different sizes are not comparable per agent without them.

## Products, trackers, and named concepts

For a product comparison, distinguish product-mention evidence from a named tracker or
category. When the request names trackers, resolve each with `entityTypes: ["trackers"]`;
if discovery establishes a category representation, resolve each with `["callType"]`.
Do not assume every product has a tracker or that its name is a resolver entity type.
Distinguish an unresolved name from a resolved entity with no matching data.

## Period-over-period

Comparing the same entity across two periods is two identical queries with different
`dateRange` values. Use matching calendar periods in the established timezone, account for daylight-saving
offsets and partial periods, and disclose any mismatch. Split either period into disjoint
windows of at most 29 elapsed days as described in `ace-mechanics.md`.

## Reporting

- A metric table: metric, A, B, absolute difference, relative change from A where defined.
- Call volume per side, so unstable averages are visible.
- The exact resolved candidates used, by name.
- Behavioral reading of *why* the leader leads, only where a queried metric supports it.

Do not invent composite metrics. "Efficiency %", "conversion rate", and "success rate" are not
ACE fields — use real ones: average `duration`, `scorecardScore`, `talkToListenRatio.value`,
CSAT average, a resolved insight outcome share with a verified denominator, or a
`trackerInteractionScenario` share. Separate QA from CSAT and model-derived satisfaction.
