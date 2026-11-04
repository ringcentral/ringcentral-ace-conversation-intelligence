---
name: ace-business-insights
description: Gain actionable business insights from customer conversations. Analyze call volume, duration, direction, queues, dispositions, categories, tracked topics, follow-up completion, listening activity, and operational trends. Use for questions about call activity, how it is distributed, and how it changes over time.
metadata:
    short-description: Gain actionable business insights from customer conversations
---

# ACE Business Insights

Operational analytics on call activity, and the general-purpose home for any supported question
that is not specifically about coaching, satisfaction, competitors, or briefs.

The server's tool descriptions are authoritative for schema, resolution, and date policy. This
skill covers only what they omit.

## Quick Start

1. Resolve named trackers, categories, agents, or teams using supported entity types. Discover
   queue and disposition values from `interaction` buckets; use exact returned keys.
2. Pick the view for the returned rows or metric grain; use supported parent/sibling filters
   to define its cohort. Common roots: `interaction`, `callCategories`, `callTrackers`,
   `callListened`, `feedback`, `productMentions`, `tasks`.
3. Aggregate — `metric` for a number, `groupBy` for a split, `trend` for movement.
4. Report with the total, the resolved candidate used, and what was truncated.

## Mechanics

Argument shapes, entity resolution, date policy, and windowing: `references/ace-mechanics.md`
(required). The rules below cover only what this skill adds.

For ordinary analytics with dates omitted, use and disclose the last seven days without asking.
The bounded human-leg lookup below deliberately omits dates. Interpret
explicit calendar dates in the user’s established timezone. For longer ranges, follow the
conservative 29-elapsed-day chunking and boundary rules in that reference. A trend still requires
a user-chosen interval; ask if it is absent.

## Data

**`view: "interaction"`** — the operational core. Groupable: `callQueueName`, `callDispositions`,
`callDirection`, `agentType`, `interactionType`, `source`, `duration`, `hostId`,
`interactionDate`, `groupId`. Numeric metrics include `duration`, QA/CSAT score and question-score
fields (including qualified forms), and the seven powerskill `.value` fields. Parent-owned
buckets can aggregate these child values at child observation grain; child-owned buckets on
this root allow only fieldless `count` / `uniqueCount`. Consult `references/ace-field-map.md`
for each operation. Also selectable: `callTitle`, `interactionId`, `hostName`.

`callDispositions` and `callQueueName` are tenant-configured text, not resolver entity types.
Discover each with its own `interaction` grouping over the relevant scope, then use bucket keys
verbatim in filters. A guessed string returning zero rows does not prove the queue is empty.

**`view: "callCategories"`** — `callTypeName`. Resolve a named category first.

**`view: "callTrackers"`** — `trackerId`, `trackerInteractionScenario`, `trackerPhrase`. Resolve a named
tracker first.

**`view: "callListened"`** — one row per listening event. Its date range filters `listenedAt`;
`interactionDate` remains the call date. Use `count` for listening events, fieldless
`uniqueCount` for an approximate distinct-call count, and `listenedDuration` for seconds listened.
Group by `listenedUserId` for listener adoption, then resolve those user ids to names. A permission
denial does not mean there was no listening activity. “Not listened” requires unsupported absence
semantics and must not be inferred from an empty child result.

**`view: "feedback"`** — one row per internal coaching-feedback activity. Its date range
filters `feedbackAt`; `interactionDate` remains the call date. `updatedById` is the reviewer,
and `hostId` is the agent who owns the call. Use the required `reviewedBy` derivation in
`references/ace-mechanics.md` when the question combines scorecards, feedback, and listening;
never add their per-view counts.

**`view: "productMentions"`** — group by `productMentions`; select that label with
`productMentionIsCreatedManual` and `productMentionRsUserId` when provenance matters. Distinguish
manual attribution from detected mentions using returned evidence. Product labels are not a
canonical product registry or resolver type. Verify mention-record versus distinct-call grain
before reporting prevalence.

**`view: "tasks"`** — `nextStepResolutionStatus`, `nextSteps`. Follow-up
completion and ownership.

Agent breakdowns: group by `hostId` (never `hostName`), then resolve the bucket ids to names.
Teams: resolve `["team"]`, filter `hostId oneOf memberIds`.

Supported product, sentiment, tracker, listening, feedback, and qualified QA/CSAT filters can restrict the cohort
without changing its root or count grain. Resolve named trackers and insight topics first;
use observed product labels. Only an insights root takes top-level `theme`; on other roots,
put the resolved `themeType` and `signalType` values in `where`. Filterability does not grant
sorting, grouping, or metric support.

## Workflow

### A plain number

`metric` alone, no grouping. An aggregate needs at least one of `groupBy` or `metric`.

Synthetic example: the scope is an example seven-day UTC calendar window, not a tenant finding.
Use the actual user window and timezone in a real request.

<!-- ace-example: business-inbound-count -->
```json
{
  "tool": "aggregate_interactions",
  "arguments": {
    "view": "interaction",
    "dateRange": { "from": "2026-08-01T00:00:00Z", "to": "2026-08-07T23:59:59.999Z" },
    "where": { "field": "callDirection", "op": "oneOf", "value": ["Inbound"] },
    "metric": { "kind": "count" }
  }
}
```

### A split

`kind: "groupBy"` on a field valid for the view, with an optional `limit`.
`average` on `duration` measures recorded duration; verify units and whether that matches the
user’s handle-time definition. See `references/shape-breakdown.md`.

### A distribution

`histogram` with `bucketSize` for the shape, or `rangeGroupBy` with `ranges` when the question
names thresholds ("under two minutes"). Use a numeric field allowed for that grouping;
`duration` is the operational example. Grouping and numeric-metric permissions are separate.

### AI-to-human handover

Read `references/ace-formulas.md` and the transfer pagination rules in
`references/ace-mechanics.md` before calculating this rate.

1. Define the dated AI cohort on `view: "interaction"`, filtering
   `agentType equals ApplicationExtension` within the requested scope. Aggregate `count`
   by `groupId` with `kind: "groupBy"`, `limit` at most 500, and initial `page: {}`.
   Retain every group's AI count and one consistent full-cohort `docCount`, including AI
   legs without a group. Page totals repeat; never sum them.
2. Enumerate all AI pages. Copy opaque `nextPage.after` exactly into `groupBy.page.after`
   without changing filters, dates, metric, grouping, or page size. Stop only when the cursor
   is absent or buckets are empty; a final nonempty page may still supply a cursor.
3. For each disjoint batch of 1–500 retrieved nonempty group IDs, aggregate human legs on
   `view: "interaction"` with `agentType equals User` and `groupId oneOf` as direct leaves
   of a top-level AND, **omitting `dateRange`**. Human legs can fall outside the AI dates.
   Preserve authorized scope without unrelated narrowing. Skip empty batches and enumerate
   every human `groupId` page with the same cursor rules; a limited bucket list is insufficient.
4. Sum each AI group's count once if that group has at least one visible human leg:
   `handedOverAiLegs = sum(aiBucketCount for groups with human legs)`;
   `handoverPercent = 100 * handedOverAiLegs / allAiLegs`.
   Multiple human legs never multiply the numerator; multiple AI legs count individually.
   Missing-group AI legs remain in the denominator. A zero denominator yields no percentage.

For long periods, combine AI counts over disjoint dated windows and deduplicate follow-up
IDs into disjoint batches. Keep each window's full `docCount` once. Report numerator,
denominator, missing-group coverage, and completeness of both sides. Partial pages,
inconsistent totals, or concurrent indexing require a stated limitation; never silently
choose a contradictory total or call a partial calculation complete. Permission denial stops
the workflow, with no access fallback.

For duration, name and keep fixed the measured population: all AI, handed-over AI, or matching
human legs. Combine `total(duration)` and `countNonNull(duration)` over disjoint batches/windows
of that same population, then divide summed totals by summed non-null counts. Include
ungrouped AI legs when measuring all AI. Never mix AI/human durations, average page averages,
or use repeated page totals as weights; no non-null durations means no average.

`groupId` is not a call citation. Retrieve actual `interactionId` values with a dated
`search_interactions` for evidence, establishing a suitable human evidence period rather
than assuming AI dates cover every human leg. Follow `references/link-building.md`.
There is no `metric.kind: handoverRate` or related-call selector.

### Tracker trend

Follows the approved `tracker-trend` sequence:

1. `resolve_entities` `entityTypes: ["trackers"]` with the untrusted tracker name.
2. **Stop** if there is no candidate. If several remain materially ambiguous, present them and
   stop rather than choosing silently.
3. `aggregate_interactions` `view: "callTrackers"` with the selected `trackerId`, the requested
   `dateRange`, and a `trend` group-by using a validated interval — ask for the interval first.
4. Report activity at the verified count grain, direction of change, peak and low periods, **and the exact tracker
   candidate used**.

Do not claim _why_ a tracker moved without retrieving call-level evidence.

### Movement over time

`trend` group-by with an explicit `interval`. Split longer periods into conservative
29-elapsed-day windows and stitch without overlap — see `references/shape-trend.md`.

## Reporting

Give the total separately from the buckets: a limited bucket list is not the whole. If `limit`
truncated the list, say how many buckets were shown and report a total only if response metadata
establishes it. Name the resolved
candidate for any tracker or category. Interpret `docCount` using the selected view’s verified
grain: interactions, tracker hits, product mentions, and tasks are not interchangeable. A
rate needs an independently established denominator at the same grain; repeated items and
overlapping buckets cannot be summed into distinct calls. Read `references/ace-formulas.md`.

Consistent empty results mean "no matching data in this period" at the queried view’s grain.
Contradictory rows and totals need a qualified limitation, not a fabricated zero.

## Limits

- **No org charts or departments** — break out by queue, category, team member set, or agent
  instead. (Direct reporting lines exist via Admin Settings, but not as an analytics dimension.)
- **One grouping per aggregate.** Grouping by two dimensions at once is not supported: run separate queries and
  combine them in the report. Do not tell the user it is impossible to see two dimensions — it
  takes two calls.
- Filtering by `callTitle` **is** supported on `view: "interaction"`.
- `search_interactions` returns one page of at most 100 rows per request, starting at page 1.
  Use aggregates for population metrics; a retrieved page is only evidence, not a total.

## References

**Read `references/ace-output-contract.md` on every answer.** It holds the checks that apply to
all ACE work: name what you resolved, show the denominator, cite evidence, decide the
presentation, separate measurement from inference, respect permission denials.

**A reference cited for the shape you are running is required reading before you answer**,
not optional background. Open it when its row applies. The rules that decide whether an answer
is correct or merely plausible live in these files, and the workflow above does not repeat them.

| Situation                                           | Reference                           |
| :-------------------------------------------------- | :---------------------------------- |
| Argument shapes, date policy, windowing, disclosure | `references/ace-mechanics.md`       |
| Pre-answer output contract (required every answer)  | `references/ace-output-contract.md` |
| Metric formulas, coverage hazard, denominators      | `references/ace-formulas.md`        |
| Valid fields per view                               | `references/ace-field-map.md`       |
| Splits, histograms, ranges                          | `references/shape-breakdown.md`     |
| Movement over time                                  | `references/shape-trend.md`         |
| Busiest queues, top categories                      | `references/shape-ranking.md`       |
| Two queues, periods, or categories side by side     | `references/shape-comparison.md`    |
| Charts                                              | `references/ace-charting.md`        |
| Citing calls as links                               | `references/link-building.md`       |
