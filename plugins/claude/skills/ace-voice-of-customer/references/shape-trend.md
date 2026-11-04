# Shape: trend

How a metric moved over time.

## Procedure

1. **Confirm the interval.** `trend` requires `day`, `week`, or `month`. If the user did not
   choose, ask before querying; recommend one yielding roughly 6–20 buckets where practical.
2. **Window the range.** Use the established timezone, inclusive final-day bounds, and
   disjoint windows of at most 29 elapsed days. Compute each boundary offset separately.
3. **Query each window identically** — same `view`, insights `theme` when applicable, `where`, `metric`, and `interval`.
4. **Stitch.** Concatenate buckets in date order, then merge any buckets sharing a key where a
   window boundary split one. To combine a value across windows, use the weighted-recombination
   rule in `ace-formulas.md` (verified `total` and matching non-null counts at the same grain;
   never average averages). Otherwise leave split buckets separate with a limitation.
5. **Baseline** (optional): the same aggregate over the immediately preceding period of equal
   length, with the same grain and units. Do not average bucket averages to create a baseline.
6. **Correlate** (optional): one or two secondary series over the same windows and interval —
   volume against a quality metric, or a speaker metric against scores.

Synthetic executable example for a seven-day window, assuming UTC is the established timezone
and the user chose a daily interval:

<!-- ace-example: csat-daily-trend -->
```json
{"tool":"aggregate_interactions","arguments":{"view":"csat","dateRange":{"from":"2026-07-01T00:00:00Z","to":"2026-07-07T23:59:59.999Z"},"groupBy":{"kind":"trend","field":"interactionDate","interval":"day"},"metric":{"kind":"average","field":"scorecardScore"}}}
```

## Reading the series

- **Direction** — rising, falling, flat, or volatile, with the change from first to last bucket.
- **Peaks and troughs** — name the bucket dates.
- **Gaps** — distinguish no matching records from an unavailable metric or incomplete window. Never
  interpolate across it, and never let an empty bucket read as a zero-value drop.
- **Anomalies** — to explain one, `search_interactions` a few records inside that bucket's own date range.
  Do not assert a cause without retrieving call-level evidence.

## Reporting

Start value, end value, peak with its date, units, direction, and coverage by bucket. Show
absolute change; percentage change requires a nonzero named baseline. Mark partial periods. Then the drivers, and
only claims the retrieved data supports.

A trend over a period shorter than three buckets is not a trend — report the values and say the
series is too short to establish direction.
