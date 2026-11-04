---
name: ace-capabilities
description: Discover the features, data, and capabilities relevant to your role. Explore the trackers, scorecards, call categories, teams, signal topics, surveys, integrations, and organizational configuration available in ACE. Use when someone is getting started, exploring available data, or needs help choosing the right ACE analysis.
metadata:
    short-description: Discover the features, data, and capabilities relevant to your role
---

# ACE Capabilities

Tell the user what ACE can answer, show them what their organization actually has, and hand off
to the skill that fits. This skill orients — it does not analyze.

The server's tool descriptions are authoritative for schema, resolution, and date policy. This
skill covers only what they omit.

## Quick Start

1. State the capability map — the five analysis families below.
2. Discover the real inventory with `resolve_entities`, **one entity type per call**, no `query`
   and no `ids`.
3. State the honest limits.
4. Route: name the skill that fits, or propose two or three first questions built from entities
   that actually came back.

## Mechanics

Argument shapes, entity resolution, date policy, and windowing: `references/ace-mechanics.md`
(required). The rules below cover only what this skill adds.

For ordinary interaction analytics with dates omitted, use and disclose the last seven days
without asking. Bounded transfer-group follow-ups follow the exception in the mechanics reference. Interpret
explicit calendar dates in the user’s established timezone. For longer ranges, follow the
conservative 29-elapsed-day chunking and boundary rules in that reference. A trend still requires
a user-chosen interval; ask if it is absent.

## What ACE can answer

| Family                         | Answers                                                                                                                                         | Skill                                |
| :----------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------- | :----------------------------------- |
| Team performance & coaching    | Compare agents or teams, rank them, build a coaching review from QA scores and talk behavior                                                   | `ace-team-performance`               |
| Deals intelligence             | Competitor mentions, churn risk, promotion response, stalled customer activity, scheduling outcomes                                             | `ace-deals-intelligence`             |
| Conversation briefs & insights | Executive, manager, or VoC briefs; pre- and post-call prep; call recaps; finding the specific calls behind a claim                              | `ace-conversation-briefs`            |
| Voice of customer              | Satisfaction level and drivers, CSAT movement, first-contact resolution, customer pain points                                                   | `ace-voice-of-customer`              |
| Business insights              | Call volume, handle time, queues, dispositions, categories, tracker trends, listening activity, duration distributions, AI-to-human handover                          | `ace-business-insights`              |
| Organization configuration     | Users, reporting lines, teams, roles, license mappings, integrations, locales, and the scorecard/CSAT/tracker/category catalogs and their setup | this skill (`search_admin_settings`) |

## Available tools and views

The five tools are `resolve_entities`, `search_interactions`, `aggregate_interactions`,
`search_admin_settings`, and `search_development_plans`. Use the connected ACE tool namespace;
never substitute a different connection to work around a permission denial.

Both interaction tools select among thirteen views: `interaction`, `bulletSummary`, `tasks`,
`sentiment`, `callCategories`, `callTrackers`, `callListened`, `feedback`, `productMentions`, `scorecard`, `csat`,
`powerskill`, and `insights`. Only `insights` requires a resolved `theme`; use returned
`signalType` as a filter value and observed generic outcomes, not topic-specific columns.

User-facing language maps by provenance: QA scores use `scorecard`, internal coaching feedback
uses `feedback`, customer or survey feedback uses `csat`, and listening activity uses
`callListened`. Ask what bare “feedback” means when internal coaching and customer-survey
interpretations would change the answer. `reviewedBy` is the RBAC-filtered, deduplicated union
of `scorecard`, `feedback`, and `callListened` described in `references/ace-mechanics.md`;
it is not a direct field or a scorecard-only metric.

Choose the root for the requested rows or metric grain. Supported sibling filters enable
product-scoped outcomes, QA cohorts restricted by qualified CSAT scores, and talk metrics
filtered by another talk metric. Cross-view selections provide bounded context, not complete
child evidence. Route those analyses to the corresponding family above. AI-to-human handover
belongs to business insights: dated AI groups plus bounded undated human-group lookups, with
a full AI-leg denominator. These analytics capabilities do not broaden Admin Settings or
assigned development-plan access; those remain separate, explicitly requested inspections.

## Discovering this organization's data

Run these separately — one entity type per call. A single call requesting several types is
materially slower. Supported types are only `trackers`, `scorecard`, `callType`, `user`, `team`,
and `insights`. Queues, dispositions, products, and competitors are not resolver entity types.
Discover queue/disposition bucket values on `interaction`; inspect product labels on
`productMentions`; resolve a competitor-related insight topic before inspecting its outcomes.

Argument fragments for `resolve_entities` (not complete tool calls):

```json
{ "entityTypes": ["trackers"] }
{ "entityTypes": ["scorecard"] }
{ "entityTypes": ["callType"] }
{ "entityTypes": ["team"] }
{ "entityTypes": ["insights"] }
```

For each, report `paging.totalElements` only when consistent with the returned candidates and
pagination; name a representative handful that actually returned. Page from 1, with `perPage`
at most 50, for a requested complete inventory. Disclose any incomplete list. Empty records
with positive or contradictory totals establish neither identities nor a reliable count; report
the inconsistency rather than inventing people or claiming there are none.

**Only ever name entities that came back.** Never illustrate with a plausible-sounding tracker or
scorecard name — an invented example reads as a real capability claim.

If a discovery call fails, report the user-facing failure without raw upstream details. Do not convert a transient failure into a
statement that the organization has no data.

For richer _setup_ metadata — published vs unpublished status, editability, theme settings — the
Admin Settings catalog below goes deeper than `resolve_entities` lists, which provide identity/topic candidates rather than a complete configuration catalog.

## Organization configuration

Use `search_admin_settings` **only** when the user directly asks to inspect Admin Settings or
organization configuration — who reports to a manager, what roles exist, whether an integration is
connected, which scorecards are published. Do not use it for analytics, and **never** use it to
resolve ids for the analytics tools — that is `resolve_entities`' job alone.

Pick one `resource` per call:

| Resource               | Returns                                                           | Required params |
| :--------------------- | :---------------------------------------------------------------- | :-------------- |
| `users`                | List people (filter by `managerId`, `contains`)                   | —               |
| `usersSearch`          | Prefix search + role/team/email/job-title/manager/user-id filters | —               |
| `teams`                | List teams                                                        | —               |
| `roles`                | List roles                                                        | —               |
| `roleUsers`            | One role and its assigned users                                   | `roleId`        |
| `licenseMappings`      | License-to-onboarding-role mappings                               | —               |
| `integrations`         | Integration catalog by type, with connection/sync metadata        | —               |
| `companyInformation`   | AI-insights company profile and configured product labels                                       | —               |
| `organization`         | Company settings                                                  | —               |
| `locales`              | Supported locale choices                                          | —               |
| `callCategories`       | Selected call categories + setup/usage/editability                | —               |
| `scorecardTemplates`   | QA scorecard catalog (`includeUnpublished`, `callCategoryIds`)    | —               |
| `csat`                 | Customer-satisfaction survey catalog                              | —               |
| `trackerTemplates`     | Tracker search (`trackerTagIds`, `callCategoryIds`)               | —               |
| `insightThemes`        | AI insight-theme catalog                                          | —               |
| `insightThemeSettings` | One theme's effective categories and exclusions                   | `themeType`     |

List resources support only their documented filters, pagination, and sorting. Results may contain
personal and organization data. Company product strings are configuration labels, not a
canonical product registry: do not infer product ids, aliases, or relationships from them.
Manager-filtered user results show direct reports within the returned coverage, not a complete
organization chart. Empty users with contradictory totals do not identify people or establish
a reliable total. Report the inconsistency and preserve the resource’s permission boundary.

**Every resource is permission-gated.** On a denial, follow the output contract's permission
rule: report insufficient permissions and stop — never tool-hop to the same data.

## The honest limits

State these when they apply, and do not go beyond them:

- **No CRM deals or opportunities.** There is no account, deal, or opportunity entity. Customer
  scope is a phone number. ACE never claims to have looked up a deal record.
- **No org charts or departments.** Full org charts and department structures are not
  available, and teams exist only as named groups with member ids. Direct reporting lines _are_
  available — `search_admin_settings` `usersSearch` filters by manager.
- **No verbatim transcripts.** Summaries, bullets, tracker phrases, sentiment reasons, and scores
  are available; raw transcript sentences are not.
- **Read-only.** Nothing can be created, updated, assigned, or sent.

Use published capabilities and supported queries to distinguish unavailable operations from
unknown tenant data. Never invent a resolver type or bypass a permission denial to test a limit.

## Actual development plans

When the user directly asks for an assigned development/coaching plan, route to
`ace-team-performance` and `search_development_plans`. This is a separate permission boundary
and data source from analytics coaching recommendations. Follow list/history → detail using
actual returned coaching report ids; `resolve_entities` cannot resolve those ids. Do not add
plan access to a general onboarding or analytics question without the user’s request. On a
permission denial, report insufficient permissions and stop.

## Routing

Name the skill and hand off. If the request is genuinely ambiguous, ask one question that
discriminates — usually the audience ("for coaching, or for an exec summary?") or the artifact
("a number, or the calls behind it?").

Do not answer the analysis yourself here. `resolve_entities` lists entities; it does not produce
metrics. Any count, average, trend, or ranking belongs to a capability skill and its
`aggregate_interactions` calls, including `view: "insights"` for resolved signal topics.

## References

**Read `references/ace-output-contract.md` on every answer.** It holds the checks that apply to
all ACE work: name what you resolved, show the denominator, cite evidence, decide the
presentation, separate measurement from inference, respect permission denials.

**A reference cited for the shape you are running is required reading before you answer**,
not optional background. Open it when its row applies. The rules that decide whether an answer
is correct or merely plausible live in these files, and the workflow above does not repeat them.

| Situation                                          | Reference                           |
| :------------------------------------------------- | :---------------------------------- |
| Argument shapes, date policy, disclosure rules     | `references/ace-mechanics.md`       |
| Pre-answer output contract (required every answer) | `references/ace-output-contract.md` |
| Which fields and views exist                       | `references/ace-field-map.md`       |
| Metric formulas and count interpretation | `references/ace-formulas.md` |
| Charts when the output contract calls for them | `references/ace-charting.md` |
| Citing evidence calls | `references/link-building.md` |
| Ranking guidance referenced by mechanics | `references/shape-ranking.md` |
