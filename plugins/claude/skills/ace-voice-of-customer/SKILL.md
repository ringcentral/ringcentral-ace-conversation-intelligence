---
name: ace-voice-of-customer
description: Know what your customers really think. Analyze CSAT, sentiment, satisfaction drivers, first-contact resolution, issue resolution, customer pain points, and recurring complaint categories. Use when someone wants to understand customer experience, satisfaction changes, unresolved issues, or sources of frustration.
metadata:
  short-description: Know what your customers really think
---

# ACE Voice of Customer

What customers report and experience: satisfaction scores, sentiment, whether their issue got
resolved, and what they are actually raising.

The server's tool descriptions are authoritative for schema, resolution, and date policy. This
skill covers only what they omit.

## Quick Start

1. Resolve any named scope (team, category, agent).
2. Aggregate CSAT over the period, with a baseline if a change is claimed.
3. Add drivers — sentiment, experience themes, resolution status.
4. Retrieve low-scoring calls as evidence.
5. Report level, movement, drivers, evidence.

## Mechanics

Argument shapes, entity resolution, date policy, and windowing: `references/ace-mechanics.md`
(required). The rules below cover only what this skill adds.

When dates are omitted, use and disclose the last seven days without asking for dates. Interpret
explicit calendar dates in the user’s established timezone. For longer ranges, follow the
conservative 29-elapsed-day chunking and boundary rules in that reference. A trend still requires
a user-chosen interval; ask if it is absent.

## Data

**CSAT** — `view: "csat"`, the customer-answered survey. Read score units, range, and direction
from response metadata or the current published tool/view contract, favoring explicit
per-response units when supplied. If neither establishes them, state that they are unknown
and avoid normalization. Never infer a scale from numeric magnitude or assume a universal
scale. Numeric fields: `scorecardScore`, `scorecardQuestionScore`. Group by `scorecardQuestionType` to see which
survey question drives the score, or `hostId` for per-agent satisfaction.

> `csat` is customer answered; `scorecard` is internal QA review. Never merge them or substitute
> one for the other — they answer different questions.

Treat “customer feedback” and “survey feedback” as `csat`, and internal coaching feedback as
`feedback`. Clarify bare “feedback” when those provenances would change the answer. When the
user scopes experience analysis by `reviewedBy`, use the complete three-view union and
`(interactionId, updatedById)` deduplication in `references/ace-mechanics.md`. For one
activity provenance, retrieve `scorecard`, `feedback`, or `callListened` rows and reuse their
`interactionId` values; do not infer missing review, feedback, or listening activity.

Choose the root for the measured rows and use qualified sibling filters for a cross-view
cohort: QA rows on `view: "scorecard"` can be restricted by `csat.scorecardScore`, while
survey rows can be restricted by `scorecard.scorecardScore`. Establish each threshold's
units first. Qualify all seven collisions as `scorecard.<field>` or `csat.<field>`:
`scorecardId`, `scorecardScore`, `scorecardQuestionScore`, `scorecardQuestion`,
`scorecardQuestionType`, `updatedById`, `updatedByName`. Unqualified names retain their
view-dependent behavior; the cohort filter does not merge survey and QA provenance.

**Sentiment** — `view: "sentiment"`: `sentimentValue` (groupable) and `sentimentInteractionScenario`
(selectable, and the most useful field for explaining a score).

**Experience signals** — resolve the requested topic with `entityTypes: ["insights"]`.
Query `search_interactions` / `aggregate_interactions` with `view: "insights"` and returned
`themeType` as `theme`. Returned `signalType` is the value of a `signalType` filter,
never a field name. Select `strOutcome`, `boolOutcome`, and evidence text to inspect actual
outcome type before choosing filters or grouping. Missing outcomes remain unknown.

| Intent | Topic to resolve | How to interpret |
| :-- | :-- | :-- |
| End-of-call satisfaction or root cause | The requested experience topic | Model-derived outcome, separate from survey CSAT |
| Issues, first contact, resolution | Each requested issue or resolution topic | Correlate distinct interactions before an FCR claim |
| Call reasons and pain points | The requested intent or pain-point topic | Use exact observed outcome strings, not invented enums |

Use supported generic `strOutcome` / `boolOutcome` groupings, not topic-specific field names.
Read `references/ace-field-map.md` for operation-specific allowlists.

Scope insight outcomes to an observed `productMentions` label, `sentimentValue`, or resolved
`trackerId` by combining that sibling filter with the resolved `signalType` condition.
For product-filtered first-contact outcomes, group the verified `boolOutcome` on the resolved
insights theme; the resulting outcome share is not FCR. Do not invent `product` or
`firstContact` fields. On a different root, use resolved `themeType` and `signalType` filters
without top-level `theme`. Preserve the cohort across evidence and aggregate requests.
Cross-view selections are bounded context: at most ten child records per owner, possibly
including children that did not match the filter. They do not establish complete outcomes
or FCR; retrieve dedicated, appropriately scoped evidence for those claims.

**Follow-through** — `view: "tasks"`, group by `nextStepResolutionStatus`.

## Workflow

### CSAT level, or a suspected decline

Follows the approved `csat-drop-investigation` sequence:

1. If a team is named, `resolve_entities` `entityTypes: ["team"]`; **stop** on no match or
   unresolved ambiguity. Filter `hostId oneOf memberIds`.
2. `aggregate_interactions` `view: "csat"` with an `average` metric on `scorecardScore`. For
   movement over time, add a `trend` group-by and ask for the interval if absent. A plain level
   question needs no trend clarification.
3. If a baseline period is supplied, run the identical aggregate over it and compare like for like.
   **Otherwise describe the trend without claiming a decline** — a single period cannot establish
   a drop.
4. `search_interactions` `view: "csat"` for low-scoring rows, applying a score threshold when given.
   Collect `interactionId` values.
5. `search_interactions` `view: "interaction"` for those ids to get call context for the evidence section.

### Drivers behind the score

Run these over the **same** `dateRange` as the CSAT aggregate:

- Sentiment mix — group by `sentimentValue`; read `sentimentInteractionScenario` on the worst calls.
- Resolve each relevant experience, issue, resolution, or pain-point topic. Inspect its outcome
  type using `search_interactions` `view: "insights"`, then aggregate the corresponding
  `strOutcome` or `boolOutcome` on that resolved theme and signal.
- Select `interactionId`, the actual outcome, and `signalText`, `reasoning`, or `summary` for
  evidence. Deduplicate repeated interactions; do not equate signal counts with call counts.

Correlation is not cause. Where a driver moves with the score, say they move together and cite the
calls; do not assert causation from aggregates alone.

### First-contact resolution

Resolve first-contact and resolution topics separately, inspect both outcome types and exact
values, and retrieve their outcomes with `interactionId` over the same scope and period. If
stored as separate signal rows, retrieve each signal separately and correlate by returned
interaction id. One row cannot satisfy two different `signalType` equalities.

Establish a complete, distinct-interaction denominator for the stated issue-bearing cohort,
with explicit eligibility and missing-outcome rules. Count only interactions where correlated
evidence establishes both first contact and resolution. Deduplicate repeated rows and report
unknown/conflicting outcomes separately. An independent first-contact percentage, resolution
percentage, or their product is not FCR. A truncated search cannot establish the denominator.
If complete correlation or denominator evidence is unavailable, report the separate signals
and state that FCR cannot be established. See `references/ace-formulas.md`.

Compare periods only with two queried windows and the same cohort/coverage rules.

## Reporting

Level, movement (only if a baseline was queried), drivers ranked by size, evidence calls, and what
to act on. State the scope and period once, up front, and give the response count behind any CSAT
average, with its numeric observation count and survey coverage when verified. A small or
partial sample supports only a qualified conclusion; question rows are not automatically surveys.

Cite evidence per `references/link-building.md`: aggregate headline numbers carry no link;
linked calls come from a `search_interactions` that selected `interactionId`.

## Limits

- CSAT reflects customers who **answered a survey** — it is not the whole customer base, and
  response bias is real. Say so when the count is small.
- Resolved end-of-call satisfaction is a model-derived signal, not a survey answer. Keep the two distinct.
- No verbatim transcript sentences. `sentimentInteractionScenario`, bullets, and signal evidence are available;
  raw transcript text is not.
- No org structure, so satisfaction cannot be broken out by department — only by team member set,
  queue, category, or agent.

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
| Valid fields per view and theme | `references/ace-field-map.md` |
| Period-over-period, or team vs team | `references/shape-comparison.md` |
| CSAT over time | `references/shape-trend.md` |
| Worst queues, categories, or agents | `references/shape-ranking.md` |
| Score and sentiment distributions | `references/shape-breakdown.md` |
| Charts | `references/ace-charting.md` |
| Citing calls as links | `references/link-building.md` |
