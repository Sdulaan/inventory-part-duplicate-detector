# Professional XLSX Overview redesign

## Status

`XLSX_OVERVIEW_PROFESSIONAL_REDESIGN_VERIFIED`

Demo classification: `DEMO_SAFE_WITH_PROFESSIONAL_XLSX_OVERVIEW`.

The `Overview` sheet is now a compact client dashboard. This is a
presentation-only change: it consumes the persisted scan row, the
authority-selected `IdentityReadSnapshot`, and existing review-state data. It
does not rerun or modify duplicate detection.

## Why the layout changed

The earlier Overview exposed the correct information, but its sequential
label/value tables made the main findings slow to scan. Diagnostic outcomes
sat beside the candidate-group breakdown, unreviewed groups were described
with deferred terminology, and technical metadata had similar visual weight
to client-facing results.

The redesigned sheet uses this hierarchy:

1. Report Header
2. Scan Information
3. Findings at a Glance
4. Additional Findings Requiring Attention
5. Human Review Progress
6. Advisory / Authority Notice
7. How to Use This Workbook
8. Report Details / Technical Footer

The header describes candidate groups as suggestions for human review. Scan
Information uses four compact cards. Findings use static KPI blocks, while
conflicting and deferred families are deliberately separated from the
candidate-group arithmetic. The technical footer retains traceability with
reduced visual prominence.

## Authoritative data sources

| Displayed value | Source |
|---|---|
| Scan Date | Persisted `completed_at`, falling back to persisted `started_at` |
| Duplicate-checking Conditions | Persisted `selected_fields`, labelled and ordered by `FIELD_DEFINITIONS` |
| Records Analysed | Persisted `total_records`, with the existing historical snapshot fallback |
| Carried Out By | Existing export constant `IFS APP Test` |
| Candidate-group and diagnostic counts | Authority-selected `IdentityReadSnapshot` counters |
| Records in Candidate Groups | Member counts from the authority-selected groups |
| Human Review Progress | Existing persisted review-state mapping |

The timestamp is displayed as `DD Mon YYYY, HH:MM` without conversion or an
invented timezone. Conditions use a bullet separator, for example
`Site • Inventory UOM`, and wrap rather than truncate.

## Human-review terminology

Algorithmic `Deferred Families` remains a diagnostic outcome in Additional
Findings. It is not used to describe groups that a person has not reviewed.
Human Review Progress instead reports:

- `Reviewed` as reviewed groups out of all candidate groups;
- `Awaiting Review` as candidate groups without a persisted review;
- `Confirmed` for the existing confirmation decision types;
- `Rejected` for `KEEP_ALL_SEPARATE`; and
- `Deferred by Reviewer` only for an explicit `UNSURE` decision.

Thus reviewed plus awaiting review equals total candidate groups, while the
three human-disposition counts describe reviewed decisions supported by the
existing model.

## Preserved contracts and verification

The workbook still contains exactly, and in order:

1. `Overview`
2. `Review Groups`
3. `Group Index`
4. `Detailed Data`
5. `Technical Reference`

The four non-Overview sheets are unchanged. Tests prove the new sections,
client-readable date, condition variants, authoritative counts, distinct
review terminology, non-overlapping merges, semantic input immutability, and
formula-free output. A safe 5,327-record workbook was generated and rendered
in Microsoft Excel; its Overview had clear hierarchy, readable text, aligned
metrics, subordinate technical details, exactly five sheets, and zero
formulas.

The immediately preceding Site-selected acceptance remains authoritative:
208 candidate groups, 82 Stronger Evidence, 126 Review Evidence, 32
conflicting families, 32 deferred families, 436 grouped records, and 4,891
unassigned records. Its request fingerprint remains
`fab4c9e6de6bad086bd14b4582d16b9ad64ecb2330b7663f2cf7cab5fff3faff`.
The Site-unselected display remains `Inventory UOM` and does not infer Site.

No selected-field, Site, UOM, threshold, retrieval, normalization, GF4, GF5,
cannot-link, group-membership, conflict/deferred, review-authority, API,
database, frontend, provenance, or provider behavior changed. Provider calls
remain zero.
