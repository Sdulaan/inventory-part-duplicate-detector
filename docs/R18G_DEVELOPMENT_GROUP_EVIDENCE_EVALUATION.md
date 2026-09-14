# R18G-B Development Group Evidence Evaluation

## R18G-B2 decision recorded

The completed targeted reference validated all nine partition assignments and
resolved both previously unresolvable Development comparisons. Current is an
exact 3+2 human match for `R18G-D09438A953125080` and creates two rather than
ADR's six false co-memberships for the four human-singleton members of
`R18G-FFF38D9F3046F48C`. Both cases are `CURRENT_STRONGLY_PREFERRED`; the final
classification is `R18G_B2_CURRENT_PARTITION_OBJECTIVE_SUPPORTED`. See
`docs/R18G_TARGETED_PARTITION_EVALUATION.md`. The sealed holdout remains unseen.

## R18G-B1 follow-up prepared

The separately authorized R18G-B1 follow-up is now
`R18G_B1_AWAITING_TARGETED_PARTITION_HUMAN_INPUT`. Its blinded workbook contains
only `R18G-D09438A953125080` (five members) and
`R18G-FFF38D9F3046F48C` (four members), with prior judgments and source fields
protected and all partition inputs blank. See
`docs/R18G_TARGETED_PARTITION_COMPLETION.md` and stop for the same Senior's
input. The sealed holdout remains unseen and no GF5 objective change is
authorized.

Classification: `R18G_B_PARTITION_DETAIL_REQUIRED`

Next: `R18G_B1_TARGETED_PARTITION_COMPLETION`

R18G-B validated and evaluated only the completed DEVELOPMENT workbook. It
preserved every submitted cell and derived normalized analysis fields
separately. Detector runtime, GF5, group confidence, LLM behavior, exports, and
frontend behavior are unchanged. Provider calls are zero.

## Baseline and holdout firewall

The evaluation began from commit
`036b71ab08ef68d60009db72c5e200f8d3145abc` on `llm-assisted-mvp` with the
protected tag unchanged. The Senior completed the original development workbook
in place, so its bytes were left untouched and the blank DEVELOPMENT template
was reconstructed from the committed R18G-A generator.

The sealed holdout workbook was not opened, parsed, copied, hashed, normalized,
or evaluated. Its human labels remain unseen. The evaluation module accepts no
holdout input and rejects holdout-named paths.

| Evidence boundary | SHA-256 |
|---|---|
| Submitted DEVELOPMENT workbook | `64c5e8e58479172baa296237d23380e54034cb108f6214592e71d29d4f9d1192` |
| Reconstructed blank DEVELOPMENT template | `814e748c45012558bc9a8f656ae39776693a25ff1b6aab430c58e5ab21f005d2` |
| R18G-A manifest | `4ffd9eb734431e83604a4f9634e33eabb8f42a8e675d7112f8ad90bd6edc8cb8` |

## Submission integrity

All fail-closed gates passed: 48 expected and unique IDs, zero missing, foreign,
or duplicate IDs; exact member and source-field reconciliation; member counts
matching the Members sheet; unchanged reviewer-visible schemas; and zero
formulas in authoritative human-input cells. No detector field, pair-level
human evidence, or LLM data was introduced.

The submission contains 48/48 completed Group Review rows. All Partition-sheet
human assignments are blank. Extra formatted blank rows at the bottom of that
sheet contain no evidence and were ignored; its 134 authoritative member rows
reconcile exactly to the blank template.

## Raw-label preservation and semantic recovery

| Raw label | Count |
|---|---:|
| `SAME_ONE_IDENTITY` | 11 |
| `NOT_ONE_IDENTITY` | 24 |
| `INSUFFICIENT_INFORMATION` | 5 |
| `MIXED_GROUP_MULTIPLE_IDENTITIES` | 8 |

All eight unexpected mixed-token entries also use
`MIXED_GROUP_MULTIPLE_IDENTITIES` as their reason, have at least three members,
and contain a non-empty comment; all eight also use the preferred `MIXED`
comment basis. They therefore satisfy the strict recovery rule. Their raw cells
remain unchanged, while the separate normalized value is `NOT_ONE_IDENTITY`
with reason
`HUMAN_USED_REASON_TOKEN_AS_SEMANTIC_NOT_ONE_IDENTITY_LABEL`.

| Normalized label | Count |
|---|---:|
| `SAME_ONE_IDENTITY` | 11 |
| `NOT_ONE_IDENTITY` | 32 |
| `INSUFFICIENT_INFORMATION` | 5 |

No other value was normalized.

## Whole-group development matrix

| Hypothesis source | SAME | NOT ONE | INSUFFICIENT |
|---|---:|---:|---:|
| Current accepted likely | 6 | 4 | 0 |
| Current accepted review | 5 | 14 | 2 |
| Deferred-family hypothesis | 0 | 5 | 1 |
| Conflict-context hypothesis | 0 | 6 | 1 |
| ADR-aligned shadow | 0 | 2 | 1 |
| Other bounded source (Bicycle) | 0 | 1 | 0 |

By group size, the normalized results are:

| Members | SAME | NOT ONE | INSUFFICIENT |
|---:|---:|---:|---:|
| 2 | 11 | 18 | 2 |
| 3 | 0 | 4 | 0 |
| 4 | 0 | 4 | 3 |
| 5 | 0 | 5 | 0 |
| 7 | 0 | 1 | 0 |

The sole cross-site hypothesis is the seven-site Bicycle family and is NOT ONE.
The 47 same-site hypotheses are 11 SAME, 31 NOT ONE, and five INSUFFICIENT.
Generic-only hypotheses are three SAME and two NOT ONE. The full deterministic
matrices by site count, generic state, evidence provenance, native/demoted
Review origin, confidence, and comment basis are frozen in
`r18g_development_summary.json`.

## Current accepted-group development evidence

For ten current `LIKELY_DUPLICATE_GROUP` hypotheses, the Senior labels are six
SAME (60%) and four NOT ONE (40%); one NOT ONE judgment is HIGH confidence.
Comment basis is four DOMAIN_EXTERNAL and six UNCLEAR.

For 21 current `POSSIBLE_DUPLICATE_GROUP_REVIEW` hypotheses, the labels are five
SAME (23.81%), 14 NOT ONE (66.67%), and two INSUFFICIENT (9.52%); two NOT ONE
judgments are HIGH confidence. Comment basis is six DOMAIN_EXTERNAL and 15
UNCLEAR.

Across all 31 sampled current accepted hypotheses, 18 are NOT ONE. These are
important development quality failures, but they are not production precision
or recall: the sample is stratified development evidence from one Senior.

Seven hypotheses contain R18C-demoted Review support: two SAME and five NOT
ONE. The remaining native/no-Review stratum is nine SAME, 27 NOT ONE, and five
INSUFFICIENT.

## Deferred families and Bicycle control

The six ordinary deferred-family hypotheses contain five NOT ONE and one
INSUFFICIENT; none is SAME. This supports caution for those sampled families but
does not prove all deferrals correct.

The blinded seven-record Bicycle control is `R18G-1C739AFB8369435E`. The raw
label is `MIXED_GROUP_MULTIPLE_IDENTITIES`, normalized separately to NOT ONE,
with MEDIUM confidence, the same mixed-group reason, and `MIXED` comment basis.
The Senior states that generic Bicycle descriptions across seven sites do not
establish one confirmed identity and may cover different models. Its source is
CURRENT, while the current GF5 disposition is deferred for
`UNRESOLVED_OWNERSHIP_AMBIGUITY`. This evidence supports retaining generic
safety; it does not authorize promotion or weakening.

## Current-versus-ADR partition evidence

The transparent preference order is SAME, then INSUFFICIENT, then NOT ONE;
confidence is reported independently.

| Shadow group | Size | Shadow judgment | Current development comparator | Outcome |
|---|---:|---|---|---|
| `R18G-B7430E7F5EA181D6` | 4 | INSUFFICIENT / LOW / UNCLEAR | Exact same four-member set appears as `R18G-0DE049304E55ECD6` and `R18G-81BEB254754A8015`, both INSUFFICIENT / LOW / UNCLEAR | `HUMAN_INSUFFICIENT` |
| `R18G-D09438A953125080` | 5 | NOT ONE / MEDIUM / MIXED | No labeled current competitor covering the set | `COMPARISON_NOT_RESOLVABLE` |
| `R18G-FFF38D9F3046F48C` | 4 | NOT ONE / MEDIUM / UNCLEAR | No labeled current competitor covering the set | `COMPARISON_NOT_RESOLVABLE` |

Exact stable member-reference sets and any current comparison sets are recorded
without compression in `r18g_partition_policy_comparison.csv`. All three shadow
hypotheses remain cannot-link safe.

The evidence supplies three partition-sensitive cases, but none supports the
ADR objective: one is human-insufficient and two reject a multi-member shadow
group without specifying the correct split. It therefore cannot show whether
the current GF5 partition or a different ADR-aligned partition is human-correct.
No GF5 objective change is justified yet.

## Targeted partition completion

Blank partitions imply one identity for the 11 SAME groups and forced binary
separation for the 18 two-member NOT ONE groups. Five INSUFFICIENT groups remain
unresolved. Fourteen multi-member NOT ONE groups lack partition detail, but only
two directly control the GF5 objective question.

`PARTITION_DETAIL_REQUIRED = YES`. Request partition completion only for:

| Blinded group | Members |
|---|---:|
| `R18G-D09438A953125080` | 5 |
| `R18G-FFF38D9F3046F48C` | 4 |

Do not request all 48 groups again and do not infer these partitions from free
text.

## Senior reasoning and knowledge boundary

Confidence is 18 HIGH, 23 MEDIUM, and seven LOW. Nine SAME and nine NOT ONE
judgments are HIGH confidence. Comment basis is ten DOMAIN_EXTERNAL, eight
MIXED, and 30 UNCLEAR; no row is marked SOURCE_VISIBLE. DOMAIN_EXTERNAL divides
into six SAME and four NOT ONE, while all eight MIXED cases are NOT ONE.

For SAME, reasons are ten alias/naming-variant and one equivalent-business-
identity. For NOT ONE, reasons are eight mixed groups, six critical-attribute
differences, six model/type/variant differences, five object/function
differences, three generic/copied-text insufficiencies, three alias/naming
entries, and one domain-knowledge-required entry. All five INSUFFICIENT cases
cite generic/copied text.

External or mixed knowledge may explain judgments the deterministic engine
cannot derive from visible fields. Those cases are not automatically detector
defects. Conversely, this submission marks no case SOURCE_VISIBLE, so R18G-B
does not authorize translating any comment directly into a runtime rule.

## Frozen artifacts and verification

| Ignored artifact | Bytes | SHA-256 |
|---|---:|---|
| `r18g_development_group_reference.csv` | 22,864 | `8b44b11ab8f448aa4fd90302b869a09fe41b765402f248ca39df6737af898815` |
| `r18g_development_group_evaluation.csv` | 51,023 | `1f7ed24c78aed55b65ab11de0be417a24b428cf6fbc304198349aaae1805b6fa` |
| `r18g_partition_policy_comparison.csv` | 2,190 | `f6ad72a589820745c44f4dfa394811bfa054cffd076405d0b0e736611ca77308` |
| `r18g_development_summary.json` | 10,310 | `024aa6de41a1916e96ab69c9758f34ae44c950b489a9251f69373be5612a8e51` |

Repeated evaluation reproduced all artifact hashes byte-for-byte. Twelve focused
R18G tests cover the 48-ID/source integrity contract, raw preservation, strict
mixed-token recovery, rejection of arbitrary normalization, partition status,
forced binary semantics, no inferred multi-member split, mapping join,
comparison accounting, the holdout firewall, Bicycle extraction, comment-basis
accounting, and R18G-A generation controls.

## Decision

`R18G_B_PARTITION_DETAIL_REQUIRED`

`NEXT = R18G_B1_TARGETED_PARTITION_COMPLETION`

Stop before R18G-B1. Keep sealed holdout human labels unseen. Runtime GF5 stays
unchanged, and group confidence, LLM advisory, XLSX-vNext, deployment, and
external demo graduation remain not started.
