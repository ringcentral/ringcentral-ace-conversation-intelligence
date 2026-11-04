# ACE mechanics

Rules that the ACE MCP server's own tool descriptions either omit, or state but that models
still get wrong in practice.

The server's tool descriptions remain authoritative for schema, view dispatch, entity
resolution, and date policy. This guidance targets the five-tool surface: `resolve_entities`,
`search_interactions`, `aggregate_interactions`, `search_admin_settings`, and
`search_development_plans`. If the connected declaration differs, report the mismatch and use
only supported operations.

## resolve_entities: `query` XOR `ids`

Pass **either** `query` (fuzzy forward lookup) **or** `ids` (exact reverse lookup). Never both.

The schema rejects the combination. When that happens:

1. Retry **once** with `query` alone.
2. If that still fails, report the failure and stop.

Never re-issue the same rejected call, and never iterate variations of it. A repeated
`query`+`ids` call cannot succeed, so a retry loop only burns the tool budget and ends with no
answer.

The durable value of this section is the recovery procedure above — a schema rejection is not
self-correcting, so fix the call rather than retrying it. That procedure is not in the schema.

To list everything of a type, omit `query` and `ids` entirely. Do not pass an empty string.
Supported types are `trackers`, `scorecard`, `callType`, `user`, `team`, and `insights`.
Resolve separate named people or concepts with separate queries; a combined phrase is not a batch
lookup. Start at `page: 1`, use `perPage` at most 50, and check paging before claiming completeness.
Reverse lookup accepts at most 50 ids per call. Never ask the user for ids.

Synthetic example only: “Example Agent” is a fictional lookup, not a real resolved identity.

<!-- ace-example: resolver-query -->
```json
{"tool":"resolve_entities","arguments":{"entityTypes":["user"],"query":"Example Agent","page":1,"perPage":50}}
```

## dateRange shape

`dateRange` is always required on `search_interactions` and normally required on
`aggregate_interactions`. It has exactly two keys, both timezone-aware ISO 8601:

```json
{ "dateRange": { "from": "2026-08-01T00:00:00Z", "to": "2026-08-21T23:59:59.999Z" } }
```

Only `from` and `to`. No `from1`, no `from_`, no suffixed or numbered variants — those are
rejected and the rejection is not self-correcting. If a date-range error comes back, fix the
key names first before changing anything else.

The only undated exception is an aggregate with `view: "interaction"` and a direct
`groupId oneOf` containing 1–500 nonempty IDs. That condition must be the whole `where`
or a direct leaf of a top-level `and`. `equals`, `or`, `not`, or membership buried only
in a nested group does not qualify. This bounded transfer-group follow-up must use
retrieved IDs; it is not permission to run an unbounded historical query.

## Date policy

- Use the user's established timezone. For explicit calendar dates, start at local midnight
  and end at the final included day's last supported instant (milliseconds: `23:59:59.999`).
  The end is inclusive: next-day midnight includes an unwanted boundary record. Resolve the
  offset separately at each boundary, including across daylight-saving changes.
- For an ordinary query with no timeframe or vague “recently”, proceed with the last seven days and disclose the
  exact bounds and timezone. Clarify only a consequential ambiguity, such as explicit local
  dates with no established timezone; never silently substitute UTC.
- Published descriptions disagree between “≤30 days” and “<30 days”. Use a conservative
  **29 elapsed days at most per request**, not a claimed API maximum. Calendar windows must
  also pass the elapsed-time check across offset changes.
- These interaction date and paging rules do not replace the separate schemas for Admin
  Settings or development plans.

## Filter and search shape

A filter is one `{field, op, value}` condition or a recursive group
`{combinator: "and" | "or" | "not", conditions: [...]}`. A `not` group has exactly one
child; nest an `and` or `or` group inside it when negating several conditions.
Search starts at `page: 1`, with `perPage` from 1 to 100. Select the evidence fields needed,
page without changing scope, and state how many records were retrieved versus the reported total.

Choose the root `view` for the intended returned-row or metric grain. Every view can filter
mapped parent and sibling fields through the interaction parent; no `join` argument is needed.
A cross-view filter establishes a cohort, not a new output grain. Use qualified
`scorecard.<field>` / `csat.<field>` for colliding QA/survey fields (see `ace-field-map.md`).
Resolve insight topics before filtering on any root. Only `view: "insights"` takes a top-level
`theme`; on other roots use generic `signalType` and `themeType` conditions in `where`.

Translate review and feedback language by provenance, not by a guessed boolean:

- **QA review / review score** uses `view: "scorecard"`; `updatedById` identifies the reviewer
  and `hostId` identifies the agent who owns the call.
- **internal coaching feedback** uses `view: "feedback"`, one row per feedback activity.
- **customer feedback / survey feedback** uses `view: "csat"`. Bare **feedback** is ambiguous;
  ask whether the user means internal coaching feedback or a customer-answered survey.
- **call listened / listening activity** uses `view: "callListened"`, one row per listening
  activity. Its `dateRange` filters `listenedAt`, not the call date.

`reviewedBy` is a derived meeting metric, not a field or one-view aggregate. Retrieve every
matching row from `scorecard`, `feedback`, and `callListened` with `interactionId`,
`updatedById`, and `updatedByName`, paging each view to verified completion. Server-side RBAC
already limits eligible reviewers and excludes deleted, AI-generated, and call-note activities;
do not recreate those rules with guessed client-side filters. Drop rows without either id, union
the three result sets, and deduplicate by `(interactionId, updatedById)`. Count the remaining
distinct meetings per `updatedById`: repeated activities by the same reviewer on one meeting
count once, while one meeting reviewed by two eligible reviewers counts once for each reviewer.
Resolve or use the returned reviewer name only after the id-based calculation.

Never sum per-view `count` or `uniqueCount` results for `reviewedBy`; the same meeting can
appear in more than one activity view. If all pages cannot be retrieved, report partial coverage
instead of a population metric. Preserve each view’s published date semantics and disclose them
when they differ. For other positive cohorts, retrieve the matching child records with
`interactionId`, then apply those returned ids to the target view. Do not infer “not reviewed”,
“no feedback”, or “not listened” from an empty child result: absence still requires an anti-join
or existence contract the published tools do not currently provide.

Cross-view `select` does not expand sorting, grouping, or numeric-metric allowlists.
Child/sibling projections contain at most ten records per owner and are not necessarily
narrowed to the child that matched `where`. They cannot prove a complete child population or
correlated FCR outcomes. Do not cite a nonmatching projected child as the filter's evidence;
retrieve appropriately scoped child records or disclose the evidence limit.
`participantName contains` is analyzed keyword matching, with no
substring, exact-phrase, or semantic-match guarantee.

For `view: "powerskill"`, search selects its backing metric from a single metric type in
`orderBy` first, then `select`, then `where`. A metric sort permits multiple metric types in
`select` as sibling projections; without it, multiple selected types are ambiguous. Aggregates
choose one type from `groupBy`/`metric`, falling back to `where` only when neither chooses one.
Filters may reference other metric siblings. An aggregate still requests only one numeric
metric; filter breadth does not change its output grain.

## Transfer-group pagination

Cursor paging is opt-in and only supported for `view: "interaction"`,
`groupBy: {kind: "groupBy", field: "groupId", limit: 500, page: {}}` (limit at most 500).
Copy the opaque response `nextPage.after` exactly into `groupBy.page.after` for the next
request. Keep dates, filters, metric, grouping and page size unchanged. Stop when `nextPage`
is absent **or** buckets are empty: a final nonempty page may still carry a cursor.

These pages are ordered by group key, not count or metric rank. The top-level `docCount`
repeats the full scoped interaction count on every page, including interactions without
`groupId`; never sum it across pages. Retain each group's count separately. Enumerate all
pages on both sides of a transfer comparison, including the human follow-up batches.
Partial retrieval, inconsistent totals or concurrent indexing prevent an unqualified
completeness claim. For the AI-to-human calculation, read `ace-formulas.md`.

## Push the computation to the server

Prefer server aggregates for population metrics, and **never present a figure you could not
actually compute**. Check response coverage and units before treating a result as complete.

Almost everything is answerable server-side in a single call: a metric for a team or any filtered
set, a breakdown, a trend, a distribution, a ranking by count. Only combine results yourself when
no single query can express the answer — see the next section.

## Combining results across queries

For additive metrics, request `total` and the matching `countNonNull` of that same field,
with identical filters and grouping. Only when both describe the **same observation grain**:

Combined average = **Σ totals / Σ non-null observation counts**, dividing once at the end.

`docCount` is not automatically the average's denominator. Missing scores and repeated
question or signal records break that assumption. If the denominator or grain cannot be
verified, retain the per-window averages and report that a combined average is unavailable.
Never average averages. See `ace-formulas.md`.

## Long ranges: split and combine

1. Cover the entire requested period with disjoint windows, each at most 29 elapsed days.
   With inclusive millisecond bounds, the next window starts one millisecond after the prior
   end. Use the supported precision; do not overlap or leave gaps.
2. Keep view, theme (only for insights), filters, metric and interval identical.
3. Sum only additive counts/totals at the same grain. Merge identical time-bucket keys only
   with verified sums and non-null denominators; distinct counts and overlapping populations
   are not additive. Report partial windows or unknown denominators instead of fabricating totals.

Never silently shorten the requested period. If only part can be covered, say which part.

## Scoping to a team

Resolve the team, then filter `hostId oneOf memberIds` in **one scoped call per metric**.
A team's own `entityId` is not a valid call filter.

Argument fragment (replace member ids with resolver results):

```json
{"where":{"field":"hostId","op":"oneOf","value":["<resolved-member-id>"]}}
```

Check that the returned roster is complete and deduplicate member ids first. An empty or
partial roster does not justify an unfiltered query. Report unavailable coverage; do not claim
a whole-team result. Use one filtered aggregate per metric when the declared limits permit it.

Keep the full authorized team filter when paging records or grouping agents. If response
limits prevent full coverage, disclose the subset; never silently narrow the requested team.

Comparing two teams is two such calls per metric, with identical `dateRange` and `metric`.

**Per-agent detail inside a team** uses the same member filter and `groupBy: hostId`.
Check which roster members have buckets and whether the bucket list is truncated. Do not
replace a scoped query with an unfiltered global breakdown. Missing buckets are not zero scores.

## Deriving teams and hierarchy

ACE has **no org-hierarchy field**. Teams are flat, named groups (`"<Person>'s team"`) with member
ids, and nothing records that one team sits under another.

A named team resolves instantly and cheaply — always prefer that. Only when the user names a
**parent** ("the sub-teams under X") is anything more needed, and then:

- **Declare the cost first.** A complete sweep means paging the full team list (up to 50 per page —
  the maximum `perPage`; the default is 10) and
  comparing hundreds of ids — expensive. Say so, and offer the cheap alternative: ask the user to
  name the sub-teams. Only run the sweep if they accept the cost.
- **If you cannot complete the sweep, say the result may be incomplete.** Page until the
  candidates returned across pages reach `paging.totalElements`, and report how many teams were
  examined out of the total. A
  partial sweep silently turns "the sub-teams" into "some arbitrary sub-teams".
- **Require full containment**, not overlap: every `memberId` of the candidate must appear in the
  parent's set. Partial overlap means nothing.
- **Never call it a reporting line.** Say "membership is fully contained within X's team". Two teams
  can both sit inside a third with no relationship between them, and containment is an inference
  from rosters, not org data.
- **List every qualifying team** with its member count, and ask which to compare rather than
  silently picking two.

## Labeling agent buckets

Group agents by `hostId`, then call `resolve_entities` with
those ids to recover display names. If resolution fails, use an unresolved-agent label and
say so; do not disclose raw ids unless explicitly requested.

## Ranking by a non-count metric

Ordinary bucket order and `groupBy.limit` truncate by **document count**, not by your chosen metric — so
`limit: 10` with an average metric returns the 10 busiest, not the 10 highest-scoring. Ranking by
`count` needs no special handling; ranking by any other metric requires over-fetching and
client-side sorting. The full procedure, and the bottom-N volume floor, live in `shape-ranking.md`.
Cursor-paged `groupId` buckets are the exception: their order is by key and is never a ranking.

**Ranking by improvement or change** requires two windows and a delta — one aggregate cannot
express it. Query the current period and the prior equal-length period, then rank the difference.
Both windows must be the same length, or the delta is meaningless.

## Baselines

There is no benchmark or target API. A baseline is either:

- the same aggregate over the immediately preceding period of equal length, or
- a labeled median across the buckets already returned (a fetched-set reference, not a
  population benchmark). Compute a population mean only with verified weighting.

Say which one was used. Never present a baseline as an external or official target.

## Trend intervals

`trend` group-bys require an explicit `interval` of `day`, `week`, or `month`. If the user
did not choose one, ask before the trend query, recommending an interval yielding roughly
6–20 buckets where practical. This interval requirement does not change the disclosed
seven-day default for an omitted date range.

## docCount semantics

On `view: "interaction"`, `docCount` counts interactions. On `view: "callListened"`, `docCount`
and `count` count listening events; fieldless `uniqueCount` estimates distinct calls listened
to. For `callTrackers`, verify whether
the returned count represents hit records or distinct interactions; do not assume repeated
hits on one call are deduplicated. Use fieldless `uniqueCount` for call prevalence only when
supported and its distinct-interaction semantics are established. Scorecard question records
and signal rows can also repeat an interaction. Treat counts at their verified grain; see
the coverage and first-contact guidance in `ace-formulas.md`.

## Resolve before declining

Resolve named people, trackers, teams, scorecards, categories, and insight topics only through
the supported entity types. A competitor question resolves its insight topic, then inspects
observed outcome values; a competitor is not an entity type. For product names, use observed
`productMentions` labels unless an actual tracker/category representation has been established.
Do not attempt unsupported product, competitor, queue, or disposition resolver lookups.

When a name returns several candidates and the choice materially changes the answer, present the
candidates and stop. When one candidate clearly dominates, use it and name the exact candidate
used in the report.

## Disposition and queue values: discover, never guess

`callDispositions` and `callQueueName` are **not** `resolve_entities` entity types — there is no
lookup for them. They are upstream free text, tenant-configured, and case-sensitive (`"Abandoned"`
and `"abandoned"` are different values to an `equals`/`oneOf` filter). Guessing a value and getting
zero rows back reads as "no matches" — it is actually "wrong string", and the two are
indistinguishable from the response alone.

Before filtering, discover exact values with `aggregate_interactions`, `view: "interaction"`,
`groupBy: {field: "callDispositions"}` (or `"callQueueName"`), and `metric: {kind: "count"}`
over the relevant scope. Use bucket keys verbatim. These fields can filter insights but are
**not groupable on insights**; never move that discovery grouping to `view: "insights"`.

## Disclosure: state real limits, invent none

These limits are real. State them plainly when they apply:

- **No CRM deal or opportunity resolver.** There is no account, deal, or opportunity entity.
  Customer scope is a phone number. Never imply a deal record was looked up.
- **No org-chart data.** Departments and full org charts are not available, and teams exist
  only as a list of member ids. Direct reporting lines _are_ available — `search_admin_settings`
  `usersSearch` can inspect manager filters only when the user explicitly asks about Admin
  Settings. It is not a fallback for denied or incomplete analytics/team resolution.
- **No verbatim transcript sentences.** Summaries, bullets, tracker phrases, and sentiment
  reasons are available; raw transcript text is not.
- **Read-only.** Nothing can be created, updated, or sent.

Use the published schema and returned evidence to distinguish unsupported operations from
unknown data. Correct a structured validation error once using its guidance; stop repeated
failures. Explain the limitation without exposing raw upstream errors. On permission denial,
report insufficient permissions and stop; never retry through another tool or resource.
Use `search_development_plans` only for explicit plan requests, obtaining coaching report ids
from its list resources, not `resolve_entities`. Authentication alone grants neither boundary.

Never exhaust the tool budget silently. If an answer cannot be completed, say what was retrieved,
what is missing, and what would be needed.

## Empty results are not errors

A query that returns zero buckets or rows is a valid answer meaning "no matching data in this
period". Report it as such. Do not retry with widened filters unless the user asks, and never
interpolate across an empty window in a trend.

## Numbers come from aggregates

Use `aggregate_interactions` for counts, totals, averages and the inputs to rates or shares.
Use `view: "insights"` plus its resolved theme for signal metrics. Search returns a page, not
a population metric. A bounded, completely retrieved and verified set may support explicit
deduplication/correlation, but disclose that method and coverage; a sample never supports a
population count. A missing requested metric cannot be replaced with `docCount`.

## The output contract lives elsewhere

The pre-answer checklist — **"Before you answer — the output contract"** — is its own
required-reading file: `ace-output-contract.md`. Read it on every answer. It governs how results
are presented; this file governs how they are queried.
