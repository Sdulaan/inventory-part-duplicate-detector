# R18G-B1 targeted partition completion

Status: `R18G_B1_AWAITING_TARGETED_PARTITION_HUMAN_INPUT`

## Baseline and scope

Preparation began from commit
`c7167e8642b89729e96cf77483655955cb99eafb` on `llm-assisted-mvp`, with
`deterministic-demo-v1` unchanged at
`d510cf3c18b3a8448d0f79be3e59c398efb32eae`. Runtime detector and GF5 code are
unchanged. Provider calls are zero.

R18G-B established that only two multi-member NOT ONE development hypotheses
need internal partitions to resolve the partition-policy comparison. Reopening
the other 46 reviews would add no required evidence.

| Review group | Members |
|---|---:|
| `R18G-D09438A953125080` | 5 |
| `R18G-FFF38D9F3046F48C` | 4 |

## Package and blinding

The workbook contains exactly the `Instructions`, `Groups`, `Members`, and
`Partition` sheets. Its nine member rows preserve the exact frozen Development
member sets, member numbers, and reviewer-visible source fields. The Senior's
existing raw and normalized whole-group judgment, confidence, reason, comment,
and comment basis reconcile exactly and are shown only as protected context.
Only blank `human_partition_id` and `partition_comment` cells are editable.
Partition IDs are constrained to P1 through P20 or `UNRESOLVED`.

The human-facing workbook exposes no current-versus-shadow marker, GF5 group or
work-unit identity, partition-policy source, system status, edge class, score,
technical evidence, lexical assessment, pair-level human evidence, Reviewer B,
LLM data, or holdout information. The separate ignored internal mapping retains
only the comparison identity required for later R18G-B2 analysis and must not be
given to the Senior.

## Integrity and holdout firewall

Generation fails closed unless the exact two IDs, 5/4 member counts, source
fields, frozen member references, and prior judgments reconcile. Validation
confirmed zero prefilled partition labels, zero formulas in editable cells,
zero detector/system fields, and zero holdout IDs. Holdout-named input or output
paths are rejected. The completed sealed holdout was not opened, parsed, copied,
hashed for human content, inspected, or evaluated; its labels remain unseen.

| Ignored artifact | Bytes | SHA-256 |
|---|---:|---|
| `r18g_targeted_partition_completion.xlsx` | 9,371 | `21c8dc116110fbd0370b36acf5c7d597b58706d3530ef3783bafaec9743d33e4` |
| `r18g_targeted_partition_internal_mapping.csv` | 1,099 | `648ae5766719b4d1790f0e509e6e80c7b50fa5d059dce2743789c7f0b4ef6095` |

Repeated generation reproduced both hashes byte-for-byte. Focused tests cover
exact selection and IDs, member counts and source preservation, prior-judgment
preservation, holdout rejection, empty partition fields, dropdown vocabulary,
detector-field exclusion, stable comparison identity, failure on prior-judgment
mismatch, and artifact determinism.

## Human next action

Follow `docs/R18G_TARGETED_PARTITION_COMPLETION_INSTRUCTIONS.md`. Give only the
targeted workbook to the same Senior, collect P-number or `UNRESOLVED`
assignments for all nine member rows, and return the completed workbook to
engineering. Do not infer or invent any partition. GF5 objective change remains
not authorized; group confidence, LLM advisory, and XLSX-vNext remain not
started.
