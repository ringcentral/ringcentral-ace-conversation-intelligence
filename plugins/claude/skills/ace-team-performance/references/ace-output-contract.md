# Before you answer — the output contract

**This applies to every ACE answer, in every skill.** A skill's own workflow adds requirements on
top of this; it never replaces it. These are the checks that decide whether an answer is defensible,
and they are easy to skip because producing a plausible-looking answer does not require them.

1. **Read the references your shape cited.** If your skill's routing table names a reference for the
   shape you are running, open it *before* answering. The skill body is deliberately incomplete —
   it does not repeat what the references hold.
2. **Name what you resolved.** State the exact candidate `resolve_entities` returned — which
   tracker, scorecard, team, or theme was actually counted. "Sales team" is not an answer; the
   resolved team and its member count are.
3. **Show the denominator.** Every average, rate, or share carries the count it was computed over.
   Name the observation grain and non-null count when verified; if unknown, say so instead of
   substituting `docCount`. State retrieved versus total coverage, missing values and truncated
   buckets. An empty result is not a zero score. Contradictory totals need a caveat, not a
   silently chosen winner. For any ratio
   or rate, confirm the formula and denominator in `ace-formulas.md` first.
   For AI-to-human handover, show handed-over AI interactions over the full dated AI cohort,
   retaining AI legs without a group in the denominator. State completeness of both AI and
   human group pagination and disclose inconsistent totals or concurrent indexing. Repeated
   page `docCount` values are not additive. Name the AI or human duration cohort and its
   non-null denominator separately. Never present capped child projections as complete
   populations or correlated FCR evidence.
4. **Cite evidence.** Any claim about *why* a number looks the way it does needs specific records
   behind it — `search_interactions` with the matching view (including `insights`) and `interactionId`
   selected. Aggregates establish the measured pattern; records can support an interpretation.
   **Cite 3–5 distinct linked calls per claim when available**, or fewer with an explicit evidence
   limit. Do not invent examples to meet a quota; if no usable id is returned, cite unlinked. Whenever you cite evidence, read `link-building.md` first
   for how to build and present the links.
   A transfer `groupId` is not a call link; retrieve an actual `interactionId` for each citation.
5. **Render a chart when one is possible.** If the client has a chart tool and the answer
   contains a chartable shape — any shape with a row in `ace-charting.md` (trend, breakdown,
   comparison, ranking, trend+driver) — render a chart. A table alone is acceptable only when the
   client has no chart surface, or the answer is a single scalar with nothing to plot. Never
   describe a chart you did not render. See `ace-charting.md`.
6. **Separate measurement from inference.** Report what was queried as fact; label everything else
   as interpretation. Correlation between two series is not causation, a model-derived signal is not
   a verified status, and a behavioral metric is an indicator, not a verdict.
7. **State the scope, exact period and timezone once, up front**, including a disclosed seven-day
   default. Report partial windows and unresolved candidates. Do not expose raw ids or upstream
   errors; use names, readable citations and a plain-language correction or limitation.
8. **Respect permission denials.** When any tool returns a permission denial, report
   "insufficient permissions" and stop — do **not** retry through another tool or a different
   resource to reach the same data. Authentication alone does not imply access; upstream is the
   sole permission authority.

If you skipped any of these, say which and why. A stated gap is a finding; an unstated one is a
defect the reader cannot see.
