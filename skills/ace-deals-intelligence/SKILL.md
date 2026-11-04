---
name: ace-deals-intelligence
description: Identify account risks and opportunities early. Analyze competitor activity, churn and retention risk, promotion response, appointment outcomes, objections, and stalled customer activity. Use when someone needs to understand revenue risk, customer attrition, competitive pressure, or why an account has gone quiet.
metadata:
  short-description: Identify account risks and opportunities early
---

# ACE Deals Intelligence

Competitive and revenue-risk analysis from conversation signals: who is being mentioned, who is
at risk of leaving, how offers land, and where scheduling breaks down.

The server's tool descriptions are authoritative for schema, resolution, and date policy. This
skill covers only what they omit.

## Quick Start

1. Resolve the signal topic with `resolve_entities` `entityTypes: ["insights"]` — never guess a
   theme or field name.
2. Resolve named agents and teams; discover queue keys from `interaction` buckets.
3. Inspect outcomes with `search_interactions`, `view: "insights"`, and the resolved theme and signal.
4. Aggregate with `aggregate_interactions` on that view, theme, signal, and verified outcome type.
5. Report with the exact resolved candidates named, and the limits below respected.

## Mechanics

Argument shapes, entity resolution, date policy, and windowing: `references/ace-mechanics.md`
(required). The rules below cover only what this skill adds.

When dates are omitted, use and disclose the last seven days without asking for dates. Interpret
explicit calendar dates in the user’s established timezone. For longer ranges, follow the
conservative 29-elapsed-day chunking and boundary rules in that reference. A trend still requires
a user-chosen interval; ask if it is absent.

## Signals and outcomes

Resolve each requested topic with `entityTypes: ["insights"]`. Take returned `themeType` as
`theme` and returned `signalType` as the **value** of a `signalType` equality filter, never
as a field name. Inspect `strOutcome` / `boolOutcome` or verified response metadata before
choosing outcome filters or grouping. Missing outcomes are unknown, not false.

| User intent | Resolve and verify | Evidence |
| :-- | :-- | :-- |
| Competitors and threat | Competitor mention or threat topic; exact observed outcome values | `signalText`, `reasoning`, `summary` |
| Churn and retention | Risk or churn-reason topic; actual string or boolean outcome | Same fields plus the observed outcome |
| Promotions and offers | Offer, promotion response, or reaction topic | Same fields; do not invent reaction enums |
| Appointments and scheduling | Booking, cancellation, no-show, or objection topic | Same fields; verify boolean versus string first |

Group only supported generic fields such as `signalType`, `strOutcome`, `boolOutcome`,
`hostId`, or `interactionDate` with the matching grouping kind. Do not turn topic names into
selectable, filterable, or groupable columns. Queue and disposition discovery belongs on
`interaction`; they are not groupable on `insights`. Embedded `callTypeId` / `callTypeName`
can group insights by category: bucket counts measure category entries; fieldless
`uniqueCount` counts distinct parent interactions. Categories can overlap, so their counts
must not be summed into a call total. See `references/ace-field-map.md`.

Keep `view: "insights"` for outcome rows or metrics while scoping the cohort with supported
`productMentions`, `sentimentValue`, or resolved `trackerId` filters. Use observed product
labels and sentiment values; a product is not a resolver type. Combine these with the resolved
`signalType` condition and verified typed outcome in `where`; keep the same filters for
evidence and aggregates. Cross-view filtering changes the cohort, not the outcome's grain.
When the user scopes risk by `reviewedBy`, establish that cohort with the three-view union and
`(interactionId, updatedById)` deduplication in `references/ace-mechanics.md`. For one
provenance only, use `scorecard` for QA scores, `feedback` for internal coaching feedback,
`csat` for customer surveys, or `callListened` for listening activity, then reuse returned
`interactionId` values. Do not treat those records as deal outcomes or infer their absence.
For a different result root, omit top-level `theme` and use the resolved `themeType` and
`signalType` in `where`. Filtering or selecting a sibling does not grant grouping or sorting
permission. Projected siblings are limited to ten records per owner and may not be the
matching child; retrieve scoped evidence before citing a projected value as the match.

`callTrackers` (`trackerInteractionScenario`, `trackerPhrase`) covers objection handling where the
organization models objections as trackers. `tasks` (`nextStepResolutionStatus`, `nextSteps`) shows
whether follow-ups were actually closed.

## Workflow

### Competitor, churn, promotion, or scheduling analysis

1. Resolve the topic and use the returned theme and signal as described above. Present candidates
   and stop if the choice materially changes the answer. Resolve each different topic separately.
2. Resolve named scope — `["user"]` for an agent, filtering its returned id on `hostId`;
   `["team"]` for a team, then `hostId oneOf memberIds`. Discover any queue or disposition by its exact bucket key.
3. `search_interactions` with `view: "insights"`, resolved `theme`, and the `signalType`
   filter to inspect outcome type and exact values. Select `interactionId`, `signalType`,
   `strOutcome`, `boolOutcome`, and relevant evidence text.
4. `aggregate_interactions` on the same view, theme, signal, dates, and scope for the shape.
   Group by the verified `strOutcome` or `boolOutcome` with a `count` metric, or query
   a trend with the user-chosen interval. Counts are at the response’s verified grain; signal
   rows are not automatically distinct calls. Establish both populations before giving a share.
5. Retrieve supporting signal rows with `search_interactions`. **Select `interactionId`**
   plus `signalText`, `summary`, or `reasoning` to justify each citation. Deduplicate by
   `interactionId` — several signal rows can belong to one call.
6. Follow returned ids into `tasks`, `sentiment`, and `interaction` views for next steps,
   sentiment reasons, and call context. Keep the same scope and date window.

### Stalled customer activity

Follows the approved `deal-stall-analysis` sequence:

1. If an agent is named, resolve `["user"]`; stop on no match or unresolved ambiguity.
2. Resolve the relevant competitor and retention topics. For each, use `search_interactions`
   `view: "insights"` with its returned theme and `signalType` filter, the customer’s phone
   number, date range, and agent if supplied. Select `interactionId` and evidence text;
   deduplicate the returned ids before follow-up queries.
3. `search_interactions` `view: "tasks"` for those ids — unresolved or missing follow-ups.
4. `search_interactions` `view: "sentiment"` for those ids — sentiment and reasons.
5. `search_interactions` `view: "interaction"` for those ids — dates, hosts, titles, dispositions.

Stop if no calls match, or if the signal rows expose no usable call ids.

## Hard limits

- **There is no account, deal, or opportunity resolver.** Customer scope is a **phone number**.
  Never imply a CRM deal, account, or pipeline record was resolved or read.
- **Stall findings are indicators, not proof of deal state.** Report them as signals worth
  checking, never as a conclusion about whether a deal is lost.
- **Churn risk is a model output on a conversation**, not a verified account status.
- A competitor is not a resolver entity type. Resolve its insight topic, then use exact
  observed outcome values for the competitor filter; a resolver topic is not an outcome value.
- Name the exact resolved candidate in the report so the reader knows what was counted.

## Reporting

Lead with the pattern size at its verified grain and any supported share or movement, then the
breakdown by the observed generic outcome, then deduplicated evidence calls. Close with what is actionable and what
would need CRM data this tool does not have.

Cite evidence calls per `references/link-building.md` — and note that a headline number from
an aggregate carries no link; the calls behind it must be searched separately.

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
| Valid fields per theme and view | `references/ace-field-map.md` |
| Comparing two competitors or periods | `references/shape-comparison.md` |
| Movement over time | `references/shape-trend.md` |
| Ranking competitors or churn reasons | `references/shape-ranking.md` |
| Splits and distributions | `references/shape-breakdown.md` |
| Charts | `references/ace-charting.md` |
| Citing calls as links | `references/link-building.md` |
| Metric formulas, coverage, and denominators | `references/ace-formulas.md` |
