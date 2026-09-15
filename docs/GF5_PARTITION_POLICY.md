# GF5 partition policy contract

## Versioned authority

```text
policy_id: GF5_PARTITION_POLICY_V1
status: FROZEN
objective: (covered, likely_members, strong, -review, -group_count)
evidence_basis: R18D + R18G-B + R18G-B2
```

This contract freezes the already-implemented GF5 partition-selection ordering;
it does not change runtime behavior.

## Objective interpretation

The lexicographic objective means:

1. maximize covered members;
2. then maximize members belonging to Likely groups;
3. then maximize Strong-support contribution;
4. then prefer fewer Review-support contributions;
5. then prefer fewer groups.

Review evidence remains useful. It is lower-authority and more ambiguous than
Strong evidence, so its quantity is not rewarded when coverage, Likely value,
and Strong contribution are otherwise equal. This policy does not suppress,
discard, or change the meaning of `REVIEW_SUPPORT`.

There is no additional winner tie-break. If materially different partitions
have the same complete objective, GF5 retains every equal best signature,
emits only groups common to every best signature, and marks ownership ambiguous
so the unresolved remainder is deferred. Canonical fingerprints and group IDs
order output; they do not select a winner between equal objectives.

## Non-negotiable safety constraints

- Protected cannot-link co-membership is never allowed.
- Accepted group membership remains disjoint within a projection.
- Naive connected-component merging is prohibited.
- Missing data is never positive identity proof.
- Site is context, not physical-identity proof.
- Technical identity contradictions remain authoritative.
- Bounds, incomplete required evidence, and unresolved equal partitions defer
  rather than becoming optimistic acceptance.

## Evidence basis and claim limit

R18D found Review evidence useful but heterogeneous and concentrated largely in
deferred/conflict contexts. It also identified a mismatch between the runtime
objective and the earlier ADR wording. R18G-B2 then evaluated explicit targeted
partitions from one highly experienced Senior Functional Consultant. Both
Development comparisons preferred current: one was an exact human match, while
the other produced fewer false co-memberships than the Review-maximizing ADR
alternative.

This is Development/architecture evidence, not dual-reviewed adjudication, a
gold standard, a production accuracy benchmark, or independent validation.
Freezing the objective does not claim that the resolver is perfect.

## Residual debt

`GF5-GROUP-PARTITION-RESIDUAL-MIXING` is `OPEN`.

The objective is frozen, but candidate evidence or hypothesis construction can
still yield imperfect partitions. In the second R18G-B2 case, current was safer
than ADR but still created two human-mixed pairs. This debt must not be fixed by
changing the frozen objective without new group-level evidence and explicit
architect authorization.

## Frozen identities

| Identity | Value |
|---|---|
| Resolver algorithm | `constrained-identity-resolver-v1` |
| Resolver configuration version | `constrained-identity-resolver-config-v1` |
| Resolver configuration fingerprint | `2584f95836d0f37d73dea545d64eab6b9cfbefc67cfa29d5dd0a01b5fda92448` |
| Policy fingerprint | `0a073ca6b0b06e31f115e892a8a27b579717cdf483f6923cc8f7bc6d362d2826` |
| Pre-freeze resolver source blob | `ea8620c42c9c461509eb1fd5175e037c0c7839f3` |

The freeze commit is the commit titled `Freeze current GF5 partition policy`
that first contains this contract and its regression tests. Its immutable SHA
is recorded in the R18H closeout and is the required R18G-C baseline. Embedding
a commit's own SHA inside that same commit is self-referential, so consumers
must resolve the titled commit directly and verify this policy fingerprint.

## Change control and holdout use

Changing the objective, its component order/direction, or equal-objective
behavior requires new group-level evidence and explicit architect authorization.
After the R18H freeze commit exists and the working tree is verified, R18G-C is
authorized to reveal the sealed holdout exactly once for independent validation.
Once revealed, it is consumed and cannot be used for tuning while still being
called holdout evidence.
