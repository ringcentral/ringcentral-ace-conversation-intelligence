# Evidence links

How to cite a specific call as a hyperlink.

## Link pattern

A call is addressable at one URL. Nothing else in ACE has a page of its own.

```
https://ace.ringcentral.com/calls/{interactionId}
```

Substitute the `interactionId` returned by `search_interactions`. Nothing else is required — no
query parameters, no path prefix, no trailing slash.

- **The id needs no transformation.** ACE's `interactionId` is the call's UUID, the same value the web app's
  `/calls/:interactionId` route expects. Use it exactly as returned.
- **`groupId` is never a call-link target.** It correlates transfer legs, not a call page.
  Retrieve and inspect a search result's `interactionId` for AI or human leg evidence.
- **Do not add query parameters.** The call page does read several, but they select UI state rather
  than content, and the values they accept differ between panes — a wrong one opens the call with no
  tab selected at all. The bare URL always opens correctly.
- **Timestamp deep-linking is not supported.** No parameter seeks the player. See rule 5.
- **One host.** `https://ace.ringcentral.com` is the only base URL to emit. Never construct any other base URL.

## What the server gives you

The ACE MCP server exposes **no** URL, permalink, deep-link, or recording-link field. There is
nothing to return directly — every link must be constructed from an id plus the pattern above.

What is available:

- **`interactionId`** — selectable on all ten call record views (`interaction`, `bulletSummary`, `tasks`,
  `sentiment`, `callCategories`, `callTrackers`, `productMentions`, `scorecard`, `csat`, `powerskill`) **and on `view: "insights"`**. It is the only linkable identifier the search tool returns.
- **`callTitle`** — selectable on `interaction`.
- **`interactionDate`**, **`hostName`**, **`hostEmail`** — selectable on every call record view, for link
  text and disambiguation.
- On signals rows: **`interactionDate`** and **`hostId`**, plus **`signalText`**, **`summary`**, and
  **`reasoning`** — the last three are the best source for the "why this call is evidence" clause.

## The hard constraint: only search results are linkable

`aggregate_interactions` returns **buckets**, not records. A bucket has a key and a
count — no `interactionId`. Do not use grouping by `interactionId` to obtain evidence; insights does not support that
grouping. Retrieve and inspect search records for citations.

Therefore:

- **A headline metric can never carry a link.** "CSAT fell to 3.4" and "competitor mentions rose
  18%" both come from aggregates and are cited as numbers, not links.
- **To link the calls behind a number**, run a follow-up search with the same `where` and
  `dateRange` — `search_interactions` with the same view and, for insights, theme — with `select`
  including `interactionId`, and link those rows.
- **Undated transfer aggregates need a dated evidence search.** `search_interactions` always
  requires `dateRange`. For human legs found through an undated group lookup, establish a
  suitable evidence period before searching, retain the group/scope filters, and disclose
  coverage. Do not assume the AI cohort dates contain every human leg or invent a call id.
- Those linked examples are **illustrative, not exhaustive** — a search returns at most one
  100-row page. Say "for example" rather than implying the linked set is the whole.

## Linking signals evidence

Signals rows link exactly like call rows, through the same `interactionId`, with three additions:

1. **`select` `interactionId` explicitly on `search_interactions`, `view: "insights"`** too. A signals aggregate gives you the size
   of a pattern; only the search gives you addressable calls.
2. **A signal row may not carry a usable `interactionId`.** Cite it unlinked and state the
   evidence limitation; never synthesize an id or use phone-level correlation to invent one.
3. **Several signal rows can share one call.** Two competitor mentions on the same call are two
   rows and one call — deduplicate by `interactionId` before rendering links, or the evidence list
   overstates how many conversations were actually found.

There is **no signal-level, theme-level, or customer-level page to link to**. `customerPhoneNos`
identifies a customer, but ACE has no customer or account record, so it is never a link target —
only a filter, and at most display text.

## Rules

1. **`select` `interactionId` explicitly** on any `search_interactions` request whose rows will be cited,
   including `view: "insights"`. Verify that each cited row actually contains a usable id
   before constructing its link.
2. **Never emit a link for an id you did not retrieve** in this session's tool results. Do not
   reconstruct an id from memory, pattern, or inference.
3. **One link per real call.** Do not synthesize a link for an aggregate bucket, a tracker phrase,
   a signal row, a theme, a transfer `groupId`, a customer phone number, or a summary bullet — none of those have their
   own addressable id here. Deduplicate by `interactionId` so one call yields one link.
4. **If the id is missing, cite unlinked.** Degrade to title + date + host rather than dropping the
   evidence or inventing a target.
5. **Never put a timestamp in a link.** `trackerStartTime` and `nextStepsStartTime` locate a moment inside
   a call, but no URL parameter seeks the player there — the link always opens at the start of the
   recording. Still cite the moment **as text** beside the link ("the pricing objection lands at
   12:04"), so the reader knows where to scrub.
6. **A link is not access.** It resolves only for readers who can already open that call in ACE.
   These tools cannot mint a shareable external link, so never describe a citation as something you
   have shared or granted.

## Link text

Link the **call title**. Where `callTitle` is empty or absent, fall back to `hostName` plus
`interactionDate` — "Alex Example, 12 Aug 2025". For insight rows, resolve `hostId` to a name first;
use a date-based label if unresolved. Never use a bare UUID as link text: it is unreadable and
tells the reader nothing about why the call was cited.

Render `interactionDate` as `12 Aug 2025` rather than echoing the raw serialized value.

Add one clause on **why** each call is evidence — the score, the sentiment, the tracker hit — so the
citation stands on its own.

## Citation styles

Two ways to present linked evidence. Pick per claim, by how many calls back it.

- **Inline descriptive link** — when a claim rests on **one** call, or the citation is the subject
  of the sentence ("listen to [this call](…) at 12:04"). The link text carries the why.
- **Footnote references** — when a claim rests on **multiple** calls, or in any structured artifact
  (brief, recap, comparison). Put numeric markers in the prose and collect the links at the bottom:

    ```
    The aggregate shows lower CSAT; these illustrative calls mention billing complaints [1][2].

    ### References
    [1] [Acme renewal review](https://ace.ringcentral.com/calls/{interactionId}) — 12 Aug 2025, Alex Example — CSAT 2
    [2] [Bright onboarding call](https://ace.ringcentral.com/calls/{interactionId}) — 11 Aug 2025, Sam Sample — CSAT 3
    ```

**Consistency check (required before answering).** Every marker resolves to exactly one reference
line, and every reference line is cited by at least one marker. No orphan markers, no dangling
references, no renumbering halfway. Footnotes fail silently when this drifts — check it.

## Rendering evidence in the answer

- **Always a markdown link, never a bare URL.** A 36-character UUID inside a bare link wraps badly
  and drowns the sentence around it.
- **Group evidence into a list** rather than scattering links through prose. One line per call, in a
  consistent shape:

    ```
    - [Acme renewal review](https://ace.ringcentral.com/calls/{interactionId}) — 12 Aug 2025, Alex Example —
      CSAT 2, competitor named twice
    ```

- **Three to five distinct linked examples per claim when available.** State when fewer usable
  examples were retrieved; never invent citations to reach a quota. A search returns up to 100 rows; forty links bury the
  argument and imply an exhaustiveness a single page of results cannot support.
- **Link each call once per answer.** If one call is evidence for two claims, link it on first
  mention and refer to it by title afterwards. Rule 3 deduplicates within a list; this deduplicates
  across the whole answer.
