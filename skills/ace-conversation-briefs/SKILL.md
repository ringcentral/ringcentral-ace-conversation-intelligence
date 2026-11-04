---
name: ace-conversation-briefs
description: Walk into every customer call prepared. Build executive, manager, and voice-of-customer briefs; prepare for upcoming conversations; recap completed calls; capture next steps and sentiment; and find the calls that support a claim. Use when someone needs context before or after a customer conversation.
metadata:
  short-description: Walk into every customer call prepared
---

# ACE Conversation Briefs & Insights

Two related jobs: **synthesize** many conversations into a brief, and **retrieve** the specific
conversations behind a claim.

The server's tool descriptions are authoritative for schema, resolution, and date policy. This
skill covers only what they omit.

## Quick Start

1. Establish audience, scope, and period — a brief for an exec is not a brief for a team lead.
2. Resolve the scope entity (team, category, tracker, agent) or take a customer phone number.
3. Choose the result grain, using supported cross-view context or dedicated views
   **under one consistent date range**.
4. Pull evidence calls with `search_interactions`, selecting `interactionId`.
5. Synthesize: headline metrics, movers versus the prior period, evidence.

## Mechanics

Argument shapes, entity resolution, date policy, and windowing: `references/ace-mechanics.md`
(required). The rules below cover only what this skill adds.

When dates are omitted, use and disclose the last seven days without asking for dates. Interpret
explicit calendar dates in the user’s established timezone. For longer ranges, follow the
conservative 29-elapsed-day chunking and boundary rules in that reference. A trend still requires
a user-chosen interval; ask if it is absent.

## The one rule that breaks everything

Any summary, recap, topic, highlight, or "what was discussed" request uses `view: "bulletSummary"`
**and explicitly selects both `summaryValues` and `interactionId`**.

Synthetic example: a seven-day UTC calendar window, not a tenant finding. Replace dates with
the user’s actual window and timezone.

<!-- ace-example: briefs-summary-evidence -->
```json
{ "tool": "search_interactions",
  "arguments": { "view": "bulletSummary",
    "dateRange": { "from": "2026-08-15T00:00:00Z", "to": "2026-08-21T23:59:59.999Z" },
    "select": ["interactionId", "interactionDate", "summarySectionName", "summaryValues"],
    "page": 1, "perPage": 100 } }
```

A `select` list without `summaryValues` can return records without the summary text needed for
the answer. Use `bulletSummary` for discussion content; `interaction` supplies call metadata.
Supported cross-view selections can add scores, sentiment, tasks, or signals as bounded context;
they do not promise every field or a complete call history from one query. Child/sibling arrays
contain at most ten records per owner and need not be restricted to the child matching `where`.
Ten returned items do not mean ten total items. Inspect any cited child for the claimed match;
if it does not match, retrieve appropriately scoped evidence or disclose the limitation.
When completeness matters, retrieve the dedicated view with its own filters and pagination,
and verify coverage. Capped projections cannot establish complete outcomes, mentions, or FCR.

## Workflow

### A brief (executive, manager, or VoC)

1. **Frame it.** Audience, scope, period. Ask if the audience is unclear — an exec brief leads
   with movement and risk; a manager brief leads with team and agent detail; a VoC brief leads
   with customer experience and issues.
2. **Resolve the scope.** Team (then `hostId oneOf memberIds`), category, tracker, or agent.
   Queue and disposition names are not resolver types: discover exact `interaction` bucket keys.
3. **Fan out under one date range** — every query in the brief uses the identical `dateRange`, or
   the sections contradict each other:
   - Volume and recorded duration — `aggregate_interactions` `view: "interaction"`, separate
     `count` and `average` on `duration` requests; verify any broader handle-time definition
   - Sentiment mix — `view: "sentiment"`, group by `sentimentValue`
   - Quality — `view: "scorecard"`, `average` on `scorecardScore`
   - Satisfaction — `view: "csat"`, `average` on `scorecardScore`
   - Topics — `view: "bulletSummary"`, group by `summarySectionName`
   - Themes — resolve the insight topic, use returned `themeType` as `theme` and `signalType`
     as a filter value on `view: "insights"`. Inspect actual `strOutcome` / `boolOutcome`
     evidence before aggregating that generic outcome with `aggregate_interactions`
   - Follow-through — `view: "tasks"`, group by `nextStepResolutionStatus`
   Skip any section that returns nothing and say it was empty rather than omitting it silently.
4. **Movers.** Repeat the two or three headline aggregates over the immediately preceding period
   of equal length. Report direction and size. Without a baseline query, describe the level and
   do not claim a change.
5. **Evidence.** `search_interactions` the calls behind the most notable findings, `select` including
   `interactionId`, and cite them.
6. **Synthesize.** Headline metrics, what moved, evidence-supported possible drivers, topics and themes, and what
   needs attention. Keep it to what was queried.

### Before and after a customer conversation

There is no account or opportunity resolver — scope a customer by **phone number**.

- **Before:** prior calls (`view: "interaction"`), open follow-ups (`view: "tasks"`, filter
  `nextStepResolutionStatus`), sentiment trajectory (`view: "sentiment"` with `sentimentInteractionScenario`),
  prior topics (`view: "bulletSummary"` with `summaryValues`), and stated pain points
  (resolve the pain-point topic, then `search_interactions` `view: "insights"` with returned
  theme and `signalType` filter; select `interactionId`, outcomes, and evidence text). Produce: where
  things stand, what is open, what to raise.
- **After:** the latest call's summary, next steps with assignees, sentiment and its reason, plus
  any competitor or churn signal on that call, using the same resolved insight workflow.
  Deduplicate signal evidence by `interactionId`. Produce: recap and owned next steps.

### Finding specific calls

Retrieval is supported — do not claim otherwise.

- **By title** — `view: "interaction"`, filter on `callTitle`.
- **By summary keyword** — `view: "bulletSummary"`, `summaryValues contains` supports analyzed
  keyword/full-text matching. It does not promise semantic matching or exact quoted-phrase
  behavior. Select `summaryValues` and `interactionId`, then inspect returned bullets. A
  summary match or absence does not prove every transcript mention; a configured tracker or
  resolved signal can provide additional, separately attributed evidence.
- **By tracker hit** — `view: "callTrackers"` with a resolved `trackerId`.
- **By `reviewedBy`** — follow the three-view union and `(interactionId, updatedById)`
  deduplication in `references/ace-mechanics.md`; it is not scorecard-only.
- **By internal QA score** — `view: "scorecard"`.
- **By internal coaching feedback** — `view: "feedback"`; `updatedById` identifies the reviewer.
- **By customer or survey feedback** — `view: "csat"`; clarify bare “feedback” when its
  provenance is unclear.
- **By listening activity** — `view: "callListened"`; its date range is listening time, and
  `listenedUserId` identifies the listener. Retrieve `interactionId` before following the calls
  into summaries or other evidence views.
- **By participant name** — `participantName contains` supports analyzed keyword matching; it
  is not entity resolution, semantic search, or guaranteed literal substring matching.
- **By score, sentiment, category, or follow-up state** — choose the root for the requested
  evidence rows; supported parent/sibling filters can constrain that cohort. Qualify colliding
  QA/CSAT fields, such as `scorecard.scorecardScore` and `csat.scorecardScore`. Resolve insight
  topics on any root; only insights takes top-level `theme`, while other roots use resolved
  `themeType` and `signalType` conditions in `where`.
- **One known call** — `search_interactions` filtered by `interactionId` across `bulletSummary`, `tasks`,
  `sentiment`, and `scorecard` as needed; cross-view selections can supply bounded context,
  with dedicated retrieval for complete evidence.

`search_interactions` returns one page of at most 100 rows per request, starting at page 1.
Use `aggregate_interactions` for population metrics. Retrieved calls are examples, not totals.
Keep signal, task, question, and distinct-interaction grain separate when combining sections;
read score units and numeric coverage from responses before comparing QA or survey results.

## Limits to state, not to invent

- **Verbatim transcript sentences are not available.** Summaries, bullets, tracker phrases, and
  sentiment reasons are. Say exactly this, and do not generalize it into "ACE cannot search call
  content" — it can, through the views above.
- **No account, deal, or opportunity resolver.** Customer scope is a phone number.
- Filtering by call title **is** supported. Grouping by two dimensions at once is not — one
  grouping per aggregate, so run separate queries and combine them in the report.

## Reporting

Lead with the answer, not the method. Give the period and scope once, up front. Attribute every
number to the view it came from when it could be ambiguous (internal `scorecard` versus
customer-answered `csat`, in particular).

Cite evidence calls per `references/link-building.md`: aggregate headline numbers carry no
link, and linked calls must come from a `search_interactions` that selected `interactionId`.

## References

**Read `references/ace-output-contract.md` on every answer.** It holds the checks that apply to
all ACE work: name what you resolved, show the denominator, cite evidence, decide the
presentation, separate measurement from inference, respect permission denials.

**A reference cited for the shape you are running is required reading before you answer**,
not optional background. Open it when its row applies. The rules that decide whether an answer
is correct or merely plausible live in these files, and the workflow above does not repeat them.

| Situation | Reference |
| :-- | :-- |
| Argument shapes, date policy, windowing, disclosure | `references/ace-mechanics.md` |
| Pre-answer output contract (required every answer) | `references/ace-output-contract.md` |
| Valid fields per view and theme | `references/ace-field-map.md` |
| Period-over-period movers | `references/shape-comparison.md` |
| Trends inside a brief | `references/shape-trend.md` |
| Top topics or themes | `references/shape-ranking.md` |
| Mix and distribution sections | `references/shape-breakdown.md` |
| Charts | `references/ace-charting.md` |
| Citing calls as links | `references/link-building.md` |
| Metric formulas, coverage, and denominators | `references/ace-formulas.md` |
