# XLSX Overview client scan summary

## Status

`XLSX_OVERVIEW_CLIENT_SUMMARY_VERIFIED`

The authority-selected System Groups workbook now puts a concise client scan
summary and findings summary at the top of `Overview`. This is a reporting-only
enhancement: it reads already-persisted scan metadata and the already-selected
identity projection, and it does not invoke or recompute detection.

## Client-facing fields and sources

| Overview field | Authoritative source |
|---|---|
| Date | Persisted `duplicate_scan.completed_at`; falls back to persisted `started_at` only when completion time is absent. It is serialized with the existing ISO timestamp convention and never uses export time. |
| Duplicate-checking conditions | Persisted `duplicate_scan.selected_fields`. |
| Number of records | Persisted `duplicate_scan.total_records`; the authority-selected snapshot record count is used only for a historical/incomplete row where that value is absent. |
| Carried out by | Export constant `IFS APP Test`. |

Selected fields are deduplicated and displayed in the order of
`FIELD_DEFINITIONS`, which is the same order used by the scan UI. The existing
friendly labels are reused, including Site, Purchase Type, Inventory UOM, Com
Group 01, Com Group 02, Safety Code, Accounting Group, Product Code, Product
Family, Product Category, and HSN/SAC Code. Unknown future canonical names use
a deterministic title-cased fallback instead of failing the export. An empty
selection displays `None selected`.

Site is displayed only when `CONTRACT` was actually selected. The persisted
mode name does not cause Site to appear. For example:

- `CONTRACT, UNIT_MEAS` displays `Site, Inventory UOM`;
- `UNIT_MEAS` displays `Inventory UOM`; and
- an empty selection displays `None selected`.

## Findings summary

The Overview separates group counts from record counts:

- Total candidate groups, Stronger Evidence, Review Evidence, Conflicting
  families, and Deferred families come directly from the authority-selected
  `IdentityReadSnapshot` counters.
- Records in candidate groups is the sum of authoritative projected group
  member counts.
- Unassigned records comes directly from the snapshot's unassigned count.

Conflicting and deferred families are shown as separate outcomes and are not
presented as components that must sum to candidate groups. Candidate groups
remain advisory and are never called confirmed duplicates.

## Preserved workbook and safety contracts

The workbook still contains exactly:

1. `Overview`
2. `Review Groups`
3. `Group Index`
4. `Detailed Data`
5. `Technical Reference`

The other four sheets, Review Groups merge behavior, flat Detailed Data table,
technical identifier placement, safe-cell handling, and zero-formula contract
are unchanged. Existing human-review progress, advisory notice, usage guidance,
and report details remain below the new client summary.

No selected-field, Site, UOM, threshold, candidate, normalization, GF4, GF5,
cannot-link, review, API, database, provenance, or provider behavior changed.
The Site-selected acceptance request fingerprint remains
`fab4c9e6de6bad086bd14b4582d16b9ad64ecb2330b7663f2cf7cab5fff3faff`.

## Real 5,327-record verification

A disposable replay of the safe canonical scan-34 snapshot generated and
inspected both workbooks without retaining an XLSX artifact or accessing the
protected workbook.

The Site-selected Overview displayed persisted completion date
`2026-09-16T04:20:46.500646`, `Site, Inventory UOM`, 5,327 records, and
`IFS APP Test`. Its findings were 208 total candidate groups, 82 Stronger
Evidence, 126 Review Evidence, 32 conflicting families, 32 deferred families,
436 records in candidate groups, and 4,891 unassigned records. It contained
zero cross-site groups and preserved the expected request fingerprint.

The Site-unselected Overview displayed persisted completion date
`2026-09-16T04:23:20.660845`, `Inventory UOM` (without Site), 5,327 records,
and `IFS APP Test`. Its findings were 42 groups, 12 Stronger Evidence, 30
Review Evidence, six conflicting families, six deferred families, 94 grouped
records, and 5,233 unassigned records. Its 18 cross-site groups prove that
unselected Site remains eligible.

Both workbooks had exactly the five required sheets, zero formula cells, zero
provider calls, and zero request-derived persistent constraint rows.
