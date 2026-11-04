---
name: ace-team-performance
description: Find who needs coaching—and what to coach them on. Compare and rank agents or teams, and build coaching reviews using QA scores, AI scores, talk behavior, customer interactions, and development plans. Use for performance comparisons, coaching evidence, benchmarks, and improvement opportunities.
metadata:
  short-description: Find who needs coaching—and what to coach them on
---

# ACE Team Performance & Coaching

Three jobs on the same data: **compare** two agents or teams, **rank** a group, or build a
**coaching review** for one agent.

The server's tool descriptions are authoritative for schema, resolution, and date policy. This
skill covers only what they omit.

## Quick Start

1. Resolve the agent(s) or team(s) with `resolve_entities` — never guess a `hostId`.
2. Aggregate scorecard scores over the period.
3. Aggregate talk behavior — **one numeric metric per aggregate**.
4. Pull representative high and low calls as evidence.
5. Report against a baseline you actually queried.

## Mechanics

Argument shapes, entity resolution, date policy, and windowing: `references/ace-mechanics.md`
(required). The rules below cover only what this skill adds.

When dates are omitted, use and disclose the last seven days without asking for dates. Interpret
explicit calendar dates in the user’s established timezone. For longer ranges, follow the
conservative 29-elapsed-day chunking and boundary rules in that reference. A trend still requires
a user-chosen interval; ask if it is absent.

## Data

**Quality** — `view: "scorecard"` is internal QA review; `view: "csat"` is customer answered.
Read units, ranges, and direction from response metadata or the current published tool/view
contract, favoring explicit per-response units when supplied. If neither establishes them, say
they are unknown and avoid normalization or assumptions about which direction is better. Never
infer a scale from numeric magnitude or assume a universal scale. Numeric
metrics: `scorecardScore`, `scorecardQuestionScore`. `hostId` is the agent who owns the call; `updatedById` is the reviewer.

Treat QA scores as `scorecard`, internal coaching feedback as `feedback`, and customer or
survey feedback as `csat`. Clarify bare “feedback” only when internal coaching and customer
survey provenance would change the answer. `reviewedBy` is a derived union of `scorecard`,
`feedback`, and `callListened`, not a scorecard-only field. Follow the complete retrieval and
`(interactionId, updatedById)` deduplication in `references/ace-mechanics.md`; do not add
per-view aggregates or recreate the RBAC eligibility and exclusion rules.

For cross-view cohorts, qualify the seven colliding fields with `scorecard.` or `csat.`:
`scorecardId`, `scorecardScore`, `scorecardQuestionScore`, `scorecardQuestion`,
`scorecardQuestionType`, `updatedById`, `updatedByName`. For example, retrieve QA rows on
`view: "scorecard"` filtered by `csat.scorecardScore`, selecting both
`scorecard.scorecardScore` and `csat.scorecardScore`. Establish the survey units and requested
threshold first; keep internal QA and customer-survey provenance separate. Do not reinterpret
unqualified fields globally or invent prefixes for other fields.

**Talk behavior** — `view: "powerskill"`. There is no `metricType` argument; use dotted
`<metricType>.value` and `<metricType>.user`. Search chooses its backing type from a single
metric type in `orderBy` first, then `select`, then `where`. A single metric sort permits
several metric types in `select`: sort by `talkToListenRatio.value` while also selecting
`patience.value` and `talkingSpeed.value` for bounded context. Without a metric sort,
multiple selected types are ambiguous.

Aggregates choose one type from output `groupBy`/`metric`, falling back to `where` only
when neither chooses one. A filter may reference another metric: average `talkTime.value`
while filtering `talkingSpeed.value`. Keep **one numeric metric per aggregate**; seven
population averages require seven aggregates, not averages of a projected search page.
Types: `talkTime`, `talkToListenRatio`, `interruptions`, `patience`, `longestMonologue`,
`fillerWordRate`, `talkingSpeed`.

Child/sibling projections contain at most ten records per owner and need not be the child
matching `where`. Retrieve scoped evidence when a projected value does not satisfy the
filter; do not cite it as matching evidence or treat these arrays as complete populations.

**Sentiment** — `view: "sentiment"` (`sentimentValue`, `sentimentInteractionScenario`) for how customers
responded.

**Listening activity** — `view: "callListened"` returns one row per listening event.
`listenedUserId` is the listener, `hostId` is the agent who owns the call, `listenedAt` is when
the listening event occurred, and `listenedDuration` is seconds listened. Use it to measure
coaching adoption or retrieve calls a manager listened to; keep event counts distinct from
approximate distinct-call `uniqueCount`.

**Coaching feedback** — `view: "feedback"` returns one row per internal feedback activity.
`updatedById` identifies the reviewer, `hostId` identifies the agent, and `feedbackAt`
identifies when the feedback was created. Keep feedback-activity counts distinct from reviewed
meeting counts.

**Agents** — group by `hostId`, then resolve the bucket
ids back to names.

**Teams** — resolve `["team"]`, take `memberIds`, filter `hostId oneOf memberIds` in **one call per
metric per team, whatever the team's size**. Do not chunk the id list,
do not partition a global breakdown, and do not write a script. A team's own `entityId` is **not** a
valid call filter. Comparing two teams means two queries with identical `dateRange` and `metric`. Full
procedure and the per-agent-detail exception: `references/ace-mechanics.md`.

**Team hierarchy** — ACE has no org-hierarchy field. "Sub-teams of X" must be derived by roster
containment, which is expensive; declare that cost and offer to take named teams instead.
See "Deriving teams and hierarchy" in `references/ace-mechanics.md` before attempting it.

## Workflow

### Coaching review for one agent

Follows the approved `agent-coaching-review` sequence:

1. `resolve_entities` `entityTypes: ["user"]` with the agent name. **Stop** on no match or
   unresolved ambiguity.
2. If a scorecard is named, resolve `entityTypes: ["scorecard"]`. Stop if unresolved.
3. `aggregate_interactions` `view: "scorecard"` for that agent and period — counts and averages, plus the
   resolved `scorecardId` if supplied.
4. `aggregate_interactions` `view: "powerskill"` for the relevant metric types over the same scope,
   **one numeric metric per aggregate**.
5. `search_interactions` `view: "scorecard"`, then `view: "interaction"`, for representative low and high scoring
   calls, bounded by a sensible call limit, `select` including `interactionId`. **This step is mandatory** —
   scores without example calls give a manager nothing to coach from. If it is skipped, say so
   explicitly and say why.
6. **Optional — actual development plans.** If the agent may already have a development plan, offer
   to pull it via `search_development_plans` (`personalizedUsers` for the period, then
   `personalizedUserRecords` / `personalizedDetails`). Label it as **separate provenance** from the
   analytics evidence above — a plan is an assigned coaching record, not a measured metric. Ask
   before adding it; it requires development-plan permission.

**Stop conditions:** the agent cannot be resolved, or no scorecard data exists for the period.
Never rank or diagnose an agent from missing data — say the data is absent.

**Never present a team comparison unless a team baseline was actually queried.** If the user wants
"versus the team", run the team aggregate; do not imply a comparison from the individual numbers
alone.

### Read a development plan

When the user asks about an actual **development plan**, **coaching plan**, or **plan** (an assigned
coaching record — distinct from the analytics coaching review above), use
`search_development_plans`. This is a different tool and a different data source from the
scorecard/talk aggregates.

A `coachingId` or `teamCoachingId` is **never** resolved by `resolve_entities` — obtain it from a
list resource first, then read the detail.

**Personalized (one agent):**

1. `personalizedUsers` with `startDate` and `endDate` (both required) — returns the development-plan
   status and identifiers returned for each user in the range. Start here for "who has a plan";
   use an actual returned `coachingId` only when this response supplies one.
2. `personalizedUserRecords` with `userId` — one agent's past reports and their `coachingId`.
3. `personalizedDetails` with `coachingId` — one report; optional `coachingType` returns the
   strength or opportunity side.
4. `personalizedInteractions` with the actual `coachingId` and `coachingDataId` returned by the
   selected report/detail — the example calls behind one plan item. Never invent a nonempty id
   or reuse an id from another report. If an expected id is absent, say the detail is unavailable.

**Team (group):** `teamHistory` (`teamId`) → `teamDetails` (`teamCoachingId`) → `teamUsers`
(`teamCoachingId`, members and per-member status). Every detail id must come from the selected
list/history result. Resolve a named user or team only for its supported identity; never resolve
a coaching report id or substitute a team id for `teamCoachingId`.

**Permission-gated.** On a denial, follow the output contract's permission rule: report
insufficient permissions and stop — never tool-hop to the same data.

### Compare two agents or two teams

See `references/shape-comparison.md`. For agents, split A vs B in one query with `groupBy: hostId`
plus a `where` restricting to the two resolved ids. For teams, run one query per member set with
identical dates, metric, and non-team filters, changing only each team’s member scope.

The output contract already requires the denominator, evidence calls, and a deliberate presentation
choice — those apply here and are not repeated. **Comparison adds three:**

1. **Member count per side**, alongside call volume. Two teams of very different sizes are not
   comparable per agent without it. Report incomplete rosters and overlapping membership.
2. **Name the scorecard.** When QA scores differ sharply, check whether the two sides are scored on
   the *same* `scorecardId` and report which. Different scorecards may make the scores
   incomparable; do not attribute that gap to the people.
3. **Same metric and scored-call coverage.** Compare identical score definitions, units,
   scorecards, cohort eligibility, period lengths, and missing-value treatment. Compute coverage
   per `references/ace-formulas.md`: scorecard rows can repeat a call, so dividing their raw
   `docCount` by interaction count does not establish coverage. Use complete distinct scored
   interactions or verified distinct-count semantics; otherwise label coverage unknown.

### Rank a group

See `references/shape-ranking.md`. Ranking by `count` is direct. Ranking by average score or
a speaker metric requires over-fetching (~3× N) and sorting client-side, because buckets truncate
by document count, not by your metric. Over-fetching does not prove a global ranking; disclose
the fetched cohort and truncation. Bottom-N needs a stated volume floor.

Every bucket must contain the requested numeric metric before it can be ranked. If patience
buckets contain only `key` and `docCount`, report that the patience averages are missing; counts
cannot substitute for them. Keep missing metrics distinct from zero. Compare the same metric
and cohort/coverage rules throughout; use a bounded alternative only if it establishes those
same semantics, with its limitations disclosed.

Ranking agents by how often they hold the overall lowest score is **not supported** — grouping by
`hostId` with a `minimum` metric returns each agent's own minimum. Say so rather than substituting it.

## Reporting

A metric table (metric, value, baseline, gap), then behavior — what the talk metrics suggest
about how this agent runs a call — then evidence calls, then recommendations tied to a specific
measured gap.

Rules that keep it honest:

- Name the exact resolved candidates and the scorecard used.
- Show the verified numeric observation count beside each average, and distinct-call volume
  separately when established. Flag low coverage or volume; never substitute question or
  speaker counts for call counts.
- Distinguish `scorecard` (internal review) from `csat` (customer answered) explicitly — they are
  different questions and must never be merged into one "quality score".
- A talk metric is a behavioral indicator, not a verdict. High talk-to-listen may be correct on a
  demo and wrong on a discovery call.
- No invented composites: use real fields, not "efficiency %" or "conversion rate".

## References

**Read `references/ace-output-contract.md` on every answer.** It holds the checks that apply to
all ACE work: name what you resolved, show the denominator, cite evidence, decide the
presentation, separate measurement from inference, respect permission denials.

**A reference cited for the shape you are running is required reading before you answer**,
not optional background. Open it when its row applies. The rules that decide whether an answer
is correct or merely plausible live in these files, and the workflow above does not repeat them.

| Situation | Reference |
| :-- | :-- |
| Argument shapes, date policy, windowing, baselines, disclosure | `references/ace-mechanics.md` |
| Pre-answer output contract (required every answer) | `references/ace-output-contract.md` |
| Metric formulas, coverage hazard, denominators | `references/ace-formulas.md` |
| Valid fields per view | `references/ace-field-map.md` |
| Agent vs agent, team vs team | `references/shape-comparison.md` |
| Top or bottom N | `references/shape-ranking.md` |
| Score movement over time | `references/shape-trend.md` |
| Score distributions | `references/shape-breakdown.md` |
| Charts | `references/ace-charting.md` |
| Citing calls as links | `references/link-building.md` |
