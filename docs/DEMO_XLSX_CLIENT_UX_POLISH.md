# Demo XLSX client UX polish

Classification: `DEMO_XLSX_CLIENT_UX_POLISH_READY`

Reference: the commit containing this document, with subject
`Polish client XLSX review experience`, based on
`71fd71e968c25651debe3f0a0553bccbfbfe131b`.

## Authorized post-freeze correction

The final rehearsal proved the export's semantics, but client inspection of
Scan 34 showed that the three-sheet workbook still looked like an engineering
diagnostic. Long canonical IDs dominated the group index, group values repeated
on every member row, and the workbook did not make the relationship "one
candidate group contains several inventory records" visually immediate.

This one-time patch changes only XLSX presentation, XLSX-focused tests, and
documentation. The detector, GF4, `GF5_PARTITION_POLICY_V1`, GF6, candidate
generation, group membership, review authority, API/CSV contracts, frontend,
database schema, and provider configuration are unchanged.

## Workbook architecture

The workbook opens on five sheets in this order:

1. `Overview` — advisory notice, human-authority statement, business KPIs,
   usage steps, then compact scan metadata.
2. `Review Groups` — the primary client review surface. Columns A:G are
   group-level values merged vertically over each group's exact member rows;
   columns H:U remain distinct member-level cells.
3. `Group Index` — one concise, filterable row per candidate group without
   technical identifiers.
4. `Detailed Data` — one flat, unmerged, filterable row per member, retaining
   all readable source fields.
5. `Technical Reference` — the audit/support mapping for canonical group IDs,
   source rows, stable record references, projection identifiers, and the
   original full deterministic reason.

Canonical group IDs and stable record references are absent from the three
primary working tables. They remain intact and accessible on the final
technical sheet. `Why Suggested` uses a short deterministic mapping; the full
reason remains on `Technical Reference`.

## Exact visual grouping rule

For a group occupying member rows `R..S`, each of `A{R}:A{S}` through
`G{R}:G{S}` is one vertical merged range. No member-level range in columns H:U
is merged. A medium
top and bottom rule plus a restrained alternating neutral fill marks the group
boundary. This preserves original deterministic group and member order while
making two-member and three-or-more-member groups visually unambiguous.

Human review status receives the strongest state treatment: confirmed,
rejected, deferred, and unreviewed states use distinct restrained fills.
System evidence remains a plain categorical tier and never resembles approval,
probability, or a confidence percentage.

## Semantic-preservation proof

Focused tests reconstruct the XLSX rows against
`authority_selected_system_group_rows` and prove unchanged group keys, exact
stable member references, source-row references, member order, all 13 readable
source fields, review states, evidence tiers, human decisions, and comments.
`Detailed Data` contains no body merges and retains the single
`SystemGroupData` table-owned filter. Formula-like source values remain literal
strings. No formulas, provider calls, writeback, or unsupported accuracy or
confidence language are introduced.

The locally available Scan 34 acceptance export preserved exactly:

- 158 candidate groups;
- 341 member rows;
- 51 `Stronger Evidence` groups;
- 107 `Review Evidence` groups;
- 158 `Requires Human Review` states;
- `CG-000002` as one two-row block containing `KA/ASCOMROT1` and
  `AS-COM-ROT`;
- `CG-000003` as one three-row block containing `SD-P2-SCHED`,
  `SD-P1-SCHED`, and `SD-M-SCHED`.

Its generated workbook was 125,665 bytes and completed in 5,689 ms. It opened
and round-tripped with the expected sheet order, 1,106 valid group-level merge
ranges, 341 flat data rows, a table range of `A1:T342`, and zero formulas.
No Scan-34-specific code exists.

## Visual and bounded rehearsal

Microsoft Excel opened the representative reviewed synthetic workbook and
rendered all five sheets. Inspection covered two-member groups, a three-member
group, every supported review-state example, wrapped descriptions/comments,
the flat analytical sheet, and the final technical sheet. The Overview reads
as a client report; Review Groups visibly nests records under one group; Group
Index is scannable; Detailed Data remains analytical; and technical identifiers
do not dominate the primary review flow.

The representative reviewed workbook exported in 1,268 ms, contained four
groups and nine member rows, and preserved one each of human confirmed, human
rejected, review deferred, and requires-human-review presentation states.

Focused XLSX and packaging tests: 22 passed. The broader bounded export,
productization, demo, operational-readiness, privacy, and recovery suite passed
127 tests. Provider calls: 0.

This is presentation evidence, not detector accuracy validation or production
readiness. The demo is re-authorized only for the existing advisory,
human-authoritative workflow and its already-approved claim boundaries.
