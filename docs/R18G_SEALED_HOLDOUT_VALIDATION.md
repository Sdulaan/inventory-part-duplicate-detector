# R18G-C consumed group holdout validation

Classification: `R18G_C_HOLDOUT_REVEALS_CRITICAL_GROUP_QUALITY_DEFECT`

Next: `ARCHITECT_REVIEW_HOLDOUT_DEFECT`

## Frozen validation baseline

R18G-C evaluated the previously unseen group holdout against R18H commit
`9b5ea1af7a51ccaf25e6c73fb807f96f1a77ba11`. The authoritative
`GF5_PARTITION_POLICY_V1` objective remains frozen and unchanged:

```text
(covered, likely_members, strong, -review, -group_count)
```

No detector, evidence, R18C, candidate-generation, GF5, threshold, status,
generic guard, cannot-link, persistence, API, UI, export, or presentation rule
was changed. Provider calls were 0.

## Reveal and evidence preservation

The first content read occurred at `2026-09-10T05:56:41.528097Z`. At that
instant the holdout changed irreversibly from unseen to
`CONSUMED_FOR_GF5_GROUP_VALIDATION`. It must not be called sealed in future.
Any correction informed by these results requires a new independent holdout for
a later validation claim.

| Evidence | Bytes | SHA-256 |
|---|---:|---|
| Submitted completed workbook | 22,495 | `74dca4a84c480cbb2d20ae8e2706470c0d1f806afa6fb67951362d2224ddec5c` |
| Local comparison template | 15,567 | `6ae10d7e28c1db898129efed06066b8077218650fcddbb56185d7c49791925e1` |
| Original generated blank recorded by manifest | 12,390 | `4f0b31b7639b12ab3b28c8ca8a68c89c50090d2158e956b37417655a0128fb33` |
| Pre-reveal internal mapping | 35,768 | `0816aca7d198b00bbe21ffbd3acb2cbb4fd5bc0643330b1954d78a3debc32a53` |
| Dataset manifest | 3,873 | `4ffd9eb734431e83604a4f9634e33eabb8f42a8e675d7112f8ad90bd6edc8cb8` |
| Derived human reference before system join | 8,318 | `ce214efc66832e1ff63d708e63252e153a330e7ac9a2735d44d055e0aa01e433` |

The local comparison template's bytes differ from the original generation
manifest, but its instructions, exact 16 IDs, counts, member/source cells, and
partition bases match the completed submission. The submitted workbook was
never repaired, normalized in place, or re-saved.

## Integrity and semantic recovery

All reference gates passed:

- exactly 16 expected and unique holdout IDs;
- zero missing, foreign, or duplicate IDs;
- Development and holdout IDs are disjoint;
- 36 member rows and 36 partition rows reconcile;
- reviewer-visible schemas, instructions, member/source cells, and partition
  bases are unchanged;
- all five required human fields are populated;
- zero formulas in authoritative human-input fields;
- zero detector/system fields, pair-label/comment leakage, or LLM data in the
  reviewer-visible sheets;
- mapping and dataset version `r18g-group-human-evidence-v1` reconcile.

Raw labels were preserved. One raw
`MIXED_GROUP_MULTIPLE_IDENTITIES` value met every approved strict-recovery
condition and was normalized to `NOT_ONE_IDENTITY` with reason
`HUMAN_USED_REASON_TOKEN_AS_SEMANTIC_NOT_ONE_IDENTITY_LABEL`. No other label was
normalized.

## Whole-group holdout matrix

Counts are shown explicitly because this is a deliberately stratified N=16
engineering holdout.

| Frozen system hypothesis | SAME ONE | NOT ONE | INSUFFICIENT | Total |
|---|---:|---:|---:|---:|
| Accepted Likely | 2 | 6 | 0 | 8 |
| Accepted Review | 2 | 3 | 0 | 5 |
| Deferred family | 0 | 2 | 0 | 2 |
| Conflict context | 0 | 1 | 0 | 1 |
| Partition-sensitive current | 0 | 0 | 0 | 0 |
| Other current hypothesis | 0 | 0 | 0 | 0 |
| **Total** | **4** | **12** | **0** | **16** |

The raw distribution was 4 `SAME_ONE_IDENTITY`, 11 `NOT_ONE_IDENTITY`, and 1
strictly recoverable mixed token. Confidence was 6 High, 9 Medium, and 1 Low.
Group sizes were fourteen pairs, one three-member group, and one five-member
group. All 16 were same-site; therefore this holdout provides no direct
cross-site validation.

The generic-only stratum contained one group, judged NOT ONE. The remaining 15
contained 4 SAME and 11 NOT ONE. Evidence provenance was 14
`SHADOW_LEXICAL_ONLY_OR_UNRESOLVED` groups (4 SAME, 10 NOT ONE) and 2
`SHADOW_TRUSTED_IDENTITY_PRESENT` groups (both NOT ONE).

## Accepted-group findings

### Likely

Of 8 accepted `LIKELY_DUPLICATE_GROUP` hypotheses:

- 2 were human-supported groups: one High and one Medium confidence;
- 6 were human-rejected groups, all Medium confidence;
- therefore there were 0 `CRITICAL_GROUP_QUALITY_FAILURE` instances under the
  narrow High-confidence severity rule, but 6
  `SERIOUS_GROUP_QUALITY_FAILURE` instances.

Those six repeated Likely rejections are the material holdout defect. They are
not treated as six independent proofs of one algorithmic cause: four comments
used `UNCLEAR` basis and two used `DOMAIN_EXTERNAL`. The reasons span different
model/type/variant, domain knowledge, a different critical attribute, and
generic/copied text. Architecture review must localize whether candidate
construction, evidence semantics, group status, the partition policy, source
quality, or reviewer semantics caused the pattern.

### Review

Of 5 accepted `POSSIBLE_DUPLICATE_GROUP_REVIEW` hypotheses:

- 2 were human-supported;
- 3 were human-rejected, comprising Review burden / false hypotheses;
- none was treated as an automatic merge failure.

This Review noise remains compatible with a clearly human-in-the-loop product
contract. It does not cause the critical classification; the repeated accepted
Likely rejections do.

## Partition-sensitive and invariant findings

The reviewer entered no explicit partition IDs. Derived semantics therefore
record 10 forced binary separations, 4 one-identity implications, and 2
multi-member `PARTITION_DETAIL_UNAVAILABLE` cases. There are zero explicitly
comparable partition-sensitive cases, so this holdout cannot directly answer
whether the frozen objective unsafe-coarsens an unseen detailed human
partition. No detailed split was inferred from comments.

Frozen current accepted membership independently passed both hard invariants:

```text
accepted protected cannot-link violations = 0
duplicate accepted membership violations = 0
```

The two deferred-family hypotheses were both judged NOT ONE (High confidence),
so their cautious disposition is supported. The conflict-context hypothesis
was also judged NOT ONE. No item-specific rule is introduced.

## Senior comment-basis limits

Comment basis was 5 `DOMAIN_EXTERNAL`, 1 `MIXED`, 10 `UNCLEAR`, and 0
`SOURCE_VISIBLE`. Reasons and comments were used qualitatively without LLM/NLP
reinterpretation and were not converted into rules. Because no judgment was
marked solely source-visible, system misses cannot be attributed wholly to the
deterministic algorithm from this evidence alone. That limitation does not erase
the repeated human rejection of client-visible Likely groups; it makes causal
diagnosis an architect-review responsibility.

## Pre-declared graduation gates

| Gate | Result | Evidence |
|---|---|---|
| A. No accepted cannot-link violation | PASS | 0 |
| B. No duplicate accepted membership | PASS | 0 |
| C. No High-confidence NOT ONE accepted as Likely | PASS | 0 |
| D. No repeated explicit unsafe coarsening | PASS, limited | 0 explicit comparable cases |
| E. No generalized defect affecting frozen group output | **FAIL** | 6 repeated Medium-confidence NOT ONE Likely groups |
| F. Review noise fits human-review contract | PASS | 3 NOT ONE Review hypotheses remain advisory |
| G. No safety-rule weakening required | PASS | generic/site/cannot-link rules remain intact |

Gate E fails because six of eight unseen accepted Likely hypotheses were
human-rejected. This is a repeated, material client-visible Likely-group pattern,
not an isolated Review false hypothesis. It meets the predeclared critical
failure criterion even though Gate C's narrower High-confidence trigger did not
fire.

## Classification, limits, and next action

Final classification:

```text
R18G_C_HOLDOUT_REVEALS_CRITICAL_GROUP_QUALITY_DEFECT
```

This is a small stratified engineering holdout. It supports a severe-defect
signal and safety sanity checks, not a production accuracy percentage,
population precision/recall, statistical calibration, marketing claim, or
proof that every rejection shares one cause.

`GF5-GROUP-PARTITION-RESIDUAL-MIXING` remains OPEN and is now reassessed with
independent diagnostic evidence. R18G-C performs no post-reveal tuning.

```text
NEXT = ARCHITECT_REVIEW_HOLDOUT_DEFECT
```

Group Confidence Index, LLM work, XLSX-vNext, and Identity Context Projection
are not started. R19A is not authorized from this failed graduation result.

## Deterministic artifacts and tests

Ignored artifacts:

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `r18g_holdout_group_reference.csv` | 8,318 | `ce214efc66832e1ff63d708e63252e153a330e7ac9a2735d44d055e0aa01e433` |
| `r18g_holdout_group_evaluation.csv` | 18,522 | `3b1e106fad3fed75849e7a983f4eccfb898bd0f755e7db0f40a3b11e84880f46` |
| `r18g_holdout_partition_evaluation.csv` | 3,814 | `ec74f42a68abec8d49fcecc62feb1dfeffca70479882ee833a4cc2f1e3d62278` |
| `r18g_holdout_summary.json` | 8,311 | `2427149241a5418f311b993ab2fa7cbd7911a91d0e425976b77b34ce9f4b3f5f` |

Focused tests cover 16-ID reconciliation, Development/holdout disjointness,
raw-label preservation, strict mixed-token recovery, partition canonicalization,
human and severity classification, cannot-link and disjoint-membership gates,
deterministic graduation, and consumed-holdout governance status.

Verification result: 114 focused tests passed. The only emitted warning was the
pre-existing pytest configuration warning for
`asyncio_default_fixture_loop_scope`. Ruff was not installed in the local
virtual environment, so no Ruff result is claimed.
