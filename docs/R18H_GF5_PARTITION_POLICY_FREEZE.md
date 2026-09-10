# R18H current GF5 partition-policy freeze

## R18G-C consumption notice

The holdout described below is no longer sealed or unseen. It was first opened
at `2026-09-10T05:56:41.528097Z` and is now
`CONSUMED_FOR_GF5_GROUP_VALIDATION`. R18G-C classified
`R18G_C_HOLDOUT_REVEALS_CRITICAL_GROUP_QUALITY_DEFECT`; no R18G-C tuning changed
the frozen policy. `NEXT = ARCHITECT_REVIEW_HOLDOUT_DEFECT`, and a future
post-correction independent claim requires a new holdout.

Classification: `R18H_CURRENT_GF5_PARTITION_POLICY_FROZEN`

Next: `R18G_C_SEALED_HOLDOUT_VALIDATION`

## Baseline and scope

R18H began from `eb0d9798f2d4eb07aae98a203f654687536296ef` on
`llm-assisted-mvp`, with `deterministic-demo-v1` unchanged at
`d510cf3c18b3a8448d0f79be3e59c398efb32eae`. It reconciles architecture,
governance, and regression tests only. Production resolver source, detector,
GF4/GF5 execution, persistence, API, UI, and exports are unchanged. Provider
calls are zero.

## From R18D confound to R18G decision

R18D established that Review support is heterogeneous: it is useful upstream,
but much of the measured burden occurs in deferred/conflict context. It found no
safe Review-suppression rule and exposed a documentation mismatch—the runtime
penalized Review in otherwise equivalent partitions while the ADR said to
maximize it.

R18G collected blinded whole-group Development evidence from one highly
experienced Senior and then requested explicit partitions only for the two
cases required to resolve that mismatch. R18G-B2 found:

- the current objective exactly matched the first human 3+2 partition, while
  ADR merged five members and created six false cross-identity co-memberships;
- the current objective remained imperfect in the second case, but created two
  false co-memberships versus six under ADR's four-member coarsening.

Both comparisons were `CURRENT_STRONGLY_PREFERRED`, producing
`R18G_B2_CURRENT_PARTITION_OBJECTIVE_SUPPORTED`. This evidence has
`MEDIUM_SINGLE_SENIOR_EXPERT` strength and is Development/architecture evidence,
not independent production accuracy.

## Frozen authoritative policy

`GF5_PARTITION_POLICY_V1` is `FROZEN` with the existing lexicographic objective:

```text
(covered, likely_members, strong, -review, -group_count)
```

GF5 maximizes coverage, then Likely members, then Strong contribution, then
prefers fewer Review contributions, then fewer groups. Review is useful but
lower-authority/higher-ambiguity evidence; it is not bad evidence and is not
suppressed. When complete objectives tie, GF5 does not choose arbitrarily: only
groups common to every best partition are emitted and unresolved ownership is
deferred. Full semantics, fingerprints, invariants, and change control are in
`docs/GF5_PARTITION_POLICY.md`.

## Preserved safety and evidence semantics

Protected cannot-links, disjoint accepted membership, non-transitive group
acceptance, missing-data caution, technical contradictions, and site/UOM context
boundaries remain unchanged. `LexicalTrustAssessment` v1, R18C's cautious
Strong-to-Review downgrade, the distinction between native and R18C-demoted
Review, and all cannot-link semantics are preserved. Pair-level Review
suppression remains unauthorized.

The seven-record Bicycle family remains deferred under the exact generic-only
cohesion guard. Its 21 relationships remain Review support, and the Senior's
NOT ONE / MEDIUM group judgment is directionally consistent with retaining that
caution. No Bicycle-specific runtime rule or promotion is introduced.

## Residual mixing debt

`GF5-GROUP-PARTITION-RESIDUAL-MIXING` is `OPEN`. Current being preferred over
ADR does not mean current is exact in every case. Candidate evidence and
hypothesis construction can still yield imperfect partitions; R18H does not fix
that quality/governance debt.

## Holdout firewall and reveal contract

The 16-group holdout was not opened, parsed, copied, hashed for human content,
inspected, evaluated, or used to derive labels in R18H. At R18H closeout it
remained unseen. R18G-C was authorized only after the R18H commit existed,
policy docs/tests were frozen, runtime was confirmed unchanged, and the working
tree was verified.

R18G-C must test whole-group SAME/NOT ONE/INSUFFICIENT, human-mixed accepted
groups, Likely-versus-Review behavior, partition-sensitive cases, cannot-link
safety, deferred-family behavior, and cross-site behavior against the exact
R18H freeze commit and policy fingerprint. Once labels are revealed the holdout
is consumed; tuning from them requires new evidence and may not retain a holdout
claim.

## Future requirements

Group confidence remains unimplemented. A future design must consider whole-set
cohesion, Strong structure, native Review, R18C-demoted Review, generic-only
evidence, partition ambiguity, cannot-links, residual-mixing risk, and whether
human reasoning depends on source-visible or external-domain evidence. No 0–100
score is authorized.

XLSX-vNext and Identity Context Projection remain unimplemented. The approved
future view keeps one first-class frozen identity set; same-site duplicate
conditions and related cross-site identity records are derived context, not
overlapping first-class groups. Context projection may consume frozen membership
but must never mutate, split, or merge GF5 identity groups.

## Verification

Focused governance tests freeze every objective component in order, current
equal-objective ambiguity behavior, the two structural R18G-B2 lessons, policy
fingerprints, and documentation alignment. Existing resolver, cannot-link,
disjointness, R18C, Bicycle, and Head/Tail regressions are run unchanged.
Production objective before R18H equals production objective after R18H.

Verification result: 102 focused tests passed. The only emitted warning was the
pre-existing pytest configuration warning for
`asyncio_default_fixture_loop_scope`.

Provider calls: 0.
