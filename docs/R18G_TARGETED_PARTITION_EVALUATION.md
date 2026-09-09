# R18G-B2 targeted human partition evaluation

Classification: `R18G_B2_CURRENT_PARTITION_OBJECTIVE_SUPPORTED`

Next: `R18H_FREEZE_CURRENT_GF5_PARTITION_POLICY`

Later, after the policy freeze is committed and verified:
`R18G_C_SEALED_HOLDOUT_VALIDATION`.

## Baseline and evidence boundary

Evaluation began from commit
`03dfdc42fbf8958777a86a41a1527bfdb39ce211` on `llm-assisted-mvp`, with
`deterministic-demo-v1` unchanged at
`d510cf3c18b3a8448d0f79be3e59c398efb32eae`. The evaluator is offline analysis
only. Runtime detector/GF5 behavior is unchanged and provider calls are zero.

The completed sealed holdout was not opened, parsed, copied, hashed for human
content, inspected, evaluated, or used to derive label counts. Its labels remain
unseen. Evaluation inputs reject holdout-named paths.

## Targeted submission integrity

| Item | Value |
|---|---|
| Submitted workbook | `r18g_targeted_partition_completion.xlsx` |
| Bytes | 18,113 |
| SHA-256 | `da0b74553e6b2080e5c25c55a50d6d9a0e769ce6982495920c292c54f9a056ce` |
| Reference type | `SINGLE_SENIOR_DOMAIN_EXPERT_TARGETED_PARTITION_DEVELOPMENT` |
| Evidence strength | `MEDIUM_SINGLE_SENIOR_EXPERT` |

Validation passed for exactly two required IDs, exact 5/4 member counts and nine
member rows, unchanged source fields and prior whole-group judgments, complete
P1..P20/UNRESOLVED vocabulary, zero formulas in partition IDs, zero additional
detector/system fields, and zero holdout IDs. The submitted workbook was not
re-saved or altered. This is Development/architecture evidence from one Senior,
not independent validation or high-certainty ground truth.

The prior whole-group counts remain 11 SAME, 32 NOT ONE, and five INSUFFICIENT.
No missing multi-member partitions were inferred from comments.

## Raw and canonical human partitions

Partition labels are interpreted only within each group. Canonical H-labels are
derived from member-set equivalence; their numbering has no cross-group meaning.

### `R18G-D09438A953125080`

| Part number | Raw | Canonical |
|---|---|---|
| `SD-M-CANDLE2` | P1 | H1 |
| `SD-CANDLE` | P1 | H1 |
| `SD-P-CPURCH2` | P2 | H2 |
| `SD-M-CANDLE` | P1 | H1 |
| `SD-P-WAX3` | P2 | H2 |

Human blocks are `{SD-M-CANDLE2, SD-CANDLE, SD-M-CANDLE}` and
`{SD-P-CPURCH2, SD-P-WAX3}`. Comments state assumptions that prefix M means
Manufactured and prefix P means Disassembly Component. The explicit later
partition controls this evaluation. Because the earlier prose referred to the
two inputs as different objects while the explicit partition groups them
together, the qualitative state is
`QUALITATIVE_COMMENT_PARTITION_TENSION`. This is recorded as context and is not
converted into a rule or an alternate inferred partition.

### `R18G-FFF38D9F3046F48C`

| Part number | Raw | Canonical |
|---|---|---|
| `MLR-SAL2-02.25.2023` | P3 | H1 |
| `MLR-PUR-02.25.2023` | P4 | H2 |
| `MLR-MANU-02.25.20232` | P5 | H3 |
| `MLR-INV-02.25.2023` | P6 | H4 |

Each record is its own human block. The repeated comment is "Similar Product
with different Revenue streams." The qualitative state is `NONE_OBSERVED`;
the comment is context only and creates no rule.

## Current versus ADR comparison

The alternatives were reconstructed from the frozen scan-31 Development
evidence and the exact objective ordering used to create the R18G-A challengers.
Singletons are retained in complete partition correspondence but are not
duplicate candidate groups. Cannot-link safety is preserved in both alternatives.

### Candle comparison — `R18G-CMP-654CF67DD6776F85`

- Human: `{SD-M-CANDLE2, SD-CANDLE, SD-M-CANDLE}` +
  `{SD-P-CPURCH2, SD-P-WAX3}`.
- Current objective: the same 3+2 blocks.
- ADR shadow: one block containing all five records.

| Measure | Current | ADR shadow |
|---|---:|---:|
| Human-mixed candidate groups | 0 | 1 |
| Human-pure candidate groups, size >= 2 | 2 | 0 |
| Human SAME pairs preserved | 4/4 | 4/4 |
| Human DIFFERENT pairs incorrectly co-grouped | 0 | 6 |
| Human partitions fragmented | 0 | 0 |
| Unresolved members | 0 | 0 |
| Coverage | 5 | 5 |

Current is `EXACT_HUMAN_PARTITION_MATCH`; ADR is `UNSAFE_COARSENING`.
Per-comparison decision: `CURRENT_STRONGLY_PREFERRED`.

### MLR comparison — `R18G-CMP-FAD492DE1A454CF6`

- Human: four singleton blocks.
- Current objective: `{MLR-SAL2-02.25.2023, MLR-MANU-02.25.20232}` +
  `{MLR-PUR-02.25.2023, MLR-INV-02.25.2023}`.
- ADR shadow: one block containing all four records.

| Measure | Current | ADR shadow |
|---|---:|---:|
| Human-mixed candidate groups | 2 | 1 |
| Human-pure candidate groups, size >= 2 | 0 | 0 |
| Human SAME pairs preserved | 0/0 | 0/0 |
| Human DIFFERENT pairs incorrectly co-grouped | 2 | 6 |
| Human partitions fragmented | 0 | 0 |
| Unresolved members | 0 | 0 |
| Coverage | 4 | 4 |

Both alternatives are `UNSAFE_COARSENING`, but current limits false
co-membership to two explicit pairs while ADR creates all six false pairs.
Per-comparison decision: `CURRENT_STRONGLY_PREFERRED`.

## GF5 objective decision

Both targeted sets are complete and interpretable. Current is exactly
human-coherent on the first and materially less coarsened on the second. ADR
introduces a human-mixed five-member group in the first case and increases
incorrect pair co-memberships from two to six in the second. Explicit human
partition evidence is not ignored, and all compared candidate groups preserve
cannot-link safety.

Final Development decision:
`R18G_B2_CURRENT_PARTITION_OBJECTIVE_SUPPORTED`.

This authorizes no runtime change in R18G-B2. The single next task is
`R18H_FREEZE_CURRENT_GF5_PARTITION_POLICY`. Only after that freeze is committed
and verified may R18G-C reveal and evaluate the sealed holdout.

## Frozen artifacts and verification

| Ignored artifact | Bytes | SHA-256 |
|---|---:|---|
| `r18g_targeted_partition_reference.csv` | 2,491 | `864d6d3610434fa1b9cbee3fcaa32d3db0fead8982d7d8644260b5f6192e99f7` |
| `r18g_targeted_partition_candidate_evaluation.csv` | 2,092 | `874eb5086b11f3be2e61c7f5c37f5c756b3e3c051be95b60068c6c4e03a90fe7` |
| `r18g_targeted_partition_summary.json` | 12,028 | `bb54faeaa828a9d3474f5eabd7dec44127cb2ee0f1d4d1dbabb011738599a9d4` |

Repeated evaluation reproduced all three hashes byte-for-byte. Focused tests
cover targeted reference validation, label-independent canonicalization,
within-group label scope, human co-membership, candidate purity,
exact/refinement/coarsening classifications, conservative alternative and final
decisions, qualitative tension without mutation, and the holdout firewall.

## Later sealed-holdout contract

After policy freeze, R18G-C will assess whole-group SAME/NOT ONE/INSUFFICIENT,
human-mixed accepted groups, Likely-versus-Review behavior, partition-sensitive
cases, cannot-link safety, deferred-family behavior, and cross-site behavior.
If opened, the holdout is consumed; no tuning against it is allowed without
explicitly recording consumption and obtaining new evidence.
