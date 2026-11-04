# Charting

## Pick the highest tier the client actually supports

1. **Native visualization tools** — if the client exposes a chart-rendering tool and the shape
   is chartable, you **must** render with it. Do not fall back to a table for convenience.
2. **Code execution** — if a code interpreter is available, render with Python (`matplotlib`,
   `plotly`) or JavaScript (`Chart.js`).
3. **Client markup** — Mermaid, Vega-Lite JSON, or inline SVG when the surface renders them.
4. **Text fallback** — aligned Unicode bars (`█`, `░`). Always available; never apologize for it.

Do not describe a chart you did not render. Produce the chart; give a table alone only when no
   chart surface exists, or the answer is a single scalar with nothing to plot.

**This ladder is about rendering only.** Chart returned aggregates or explicitly validated
derivations from `ace-formulas.md`; rendering cannot repair missing metrics or denominators.
The same numerical answer must be reachable on a client that can render only text.

## Chart per shape

| Shape | Chart | Notes |
| :-- | :-- | :-- |
| Comparison | Grouped bars — one group per metric, two series | Normalize only when scales differ, and label the normalization |
| Trend | Line or area over the stitched buckets | Overlay a verified, labeled baseline when available |
| Trend + driver | Dual axis — volume on the left, quality on the right | Label both axes with the real field name |
| Ranking | Horizontal bars, sorted, with a median reference line | Label each bar with its value |
| Breakdown (category) | Bars, or stacked share-of-total | Show the total separately from the shown buckets |
| Breakdown (numeric) | Histogram | Keep bucket order numeric, never sorted by count |

## Axes must be real fields

Label axes with fields that exist in the capability contract. Never invent a composite —
"efficiency %", "conversion rate", "success rate", and "quality index" are not ACE fields and
fabricating them invites fabricated numbers underneath.

Use `duration`, `scorecardScore` / `scorecardQuestionScore`, `<metricType>.value` for speaker
metrics, and count at its verified grain. Prefer response units and ranges; when absent,
use the explicit current tool/view contract per `ace-formulas.md`. Label a derived signal share with its resolved topic, observed outcome and denominator; do not call
a signal-record share a call rate.

Where a share is charted, state numerator and denominator in the label or caption.

## Honesty in charts

- An empty bucket is a gap, not a zero. Break the line or mark it; never let missing data read as
  a collapse.
- Small samples: annotate any bucket or bar whose call volume is below the stated floor.
- Different returned units or scales need separate axes or an explicit, justified rescale.
  Never turn categorical sentiment or missing scores into invented numeric values.
- Truncated bucket lists must say so in the caption.
- Label the timezone, observation grain and partial-window/search/bucket coverage. Do not
  fabricate missing values, an unmeasured median, or an “other” category from overlapping buckets.
