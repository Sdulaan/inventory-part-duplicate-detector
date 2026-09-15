# Determinism: cache representation and GF5 ordering correction

Classification: `DETERMINISM_CACHE_AND_GF5_ORDERING_VERIFIED`

Baseline: `a7c9bbf589e94dd22118388f0e9a4893cc136489` on
`llm-assisted-mvp`. Provider calls: **0**.

## Corrected causes

The Scan 34/35 audit first proved that `record_ref_key`, which contains the scan
ID, was used at lexical, character, hybrid-cap, and neighborhood ordering
boundaries. Retrieval now uses a separate `retrieval_order_key` while retaining
`record_ref_key` for persistence, API, review, and audit references.

`retrieval-order-key-v1` is SHA-256 over UTF-8 canonical JSON with sorted keys
and compact separators:

```json
{"contract_version":"retrieval-order-key-v1","source_record_fingerprint":"<lowercase fingerprint>","source_row_ordinal":0}
```

The source fingerprint covers the canonical source fields defined by the
canonical-record catalog. The zero-based source-row ordinal makes identical
duplicate rows distinct. Neither scan IDs nor database IDs participate.
Canonical pair ordering is `(min(endpoint_key), max(endpoint_key))`.

Decision ordering was changed in exact/bounded lexical retrieval, fixed-seed
character LSH insertion/candidate retention/exact rerank, hybrid channel merge,
per-record/family/tier/global caps, proposal ordering, and neighborhood anchor
and member ordering. Persistence and API references were not redefined.

The cold path originally scored the embedder's raw `float32` vector, while the
cache stored a seven-decimal JSON representation. On the 5,327-row input,
88,823 components changed at that boundary (maximum absolute delta
`5.960464477539063e-08`); one observed component changed from
`0.20412415266036987` to `0.20412419736385345`, and its vector norm changed
from `1.0` to `1.000000238418579`. Fresh and loaded vectors now both pass
through the existing seven-decimal canonical representation before scoring;
the cache key remains semantic retrieval text fingerprint plus model version.

GF5 generated the same semantic hypotheses but sorted them by scan-salted
`hypothesis_id`. That changed bounded recursive traversal and could change the
selected result. Resolver v2 retains database IDs in contracts and persistence,
but orders work units, targeted requests, candidate hypotheses, and partition
signatures by scan-independent record/member keys. The frozen objective remains
exactly `(covered, likely_members, strong, -review, -group_count)` and the
equal-best stable-intersection/defer policy is unchanged.

## Three-scan acceptance

The source was reconstructed losslessly from the immutable canonical fields of
historical Scan 34, retaining all 5,327 rows in source order. The three scans ran
in a new SQLite database with Group-First primary mode and every LLM provider
disabled. Scan 1 was cold; Scans 2 and 3 used the warmed cache.

| Semantic stage | Count | SHA-256 in scans 1, 2, and 3 |
|---|---:|---|
| S0 canonical records | 5,327 | `8107a36194f3bab4209a1f714fc7412a76288b11b2a7b93d536a9c20b55d6257` |
| S1 proposals, provenance, priority | 20,492 | `4f2df0eb716ec0d9b06ec65c33cfb6cca1673ccce84559dfe56fbc9f42cdd2fd` |
| S2 evidence inputs | 20,492 | `726f1206ede9210c10fdcc797c594523887a41156453cb981c82315a0d9ad38f` |
| S3 GF4 classified edges | 20,492 | `682473a17a9edcbf66e940194a6287852a057f32655863948459bb12fc975468` |
| S4 GF5 neighborhoods | 1,313 | `7fe6c3e5138cf3274ccc8bcf786f6accd1528af3e9690f06d20230a6b5c97259` |
| S5 GF5 objective inputs | 1 | `268e78c48b662ff301dde75d68a4792e994350b41f2dc4c9abc2aff0cbbdb6b9` |
| S6 selected groups | 158 | `a84dbe3aca0391c688ab79ea0723bc95b168d70ef0741a1c09259f43fe7c006a` |
| S7 conflicts | 27 | `aeecfb4f30e9a00819fc2a6b5f414e55768032730d2a67805f646d3f7c0af860` |
| S8 deferred work units | 40 | `6de165cafcdd79dfb469e5060b604ab19d84fb0b31e590edcbeb40c71b9ae2b0` |
| S9 unassigned records | 4,982 | `cdbab036c0dad18e918c56edb0a976d24317a74d3240cfe82a0ea99e7e2742c6` |
| S10 final projection | 158 | `0a8a5ba1c699d9f810d1c555509a462d04530b113f8564c8c9d9b5edd92e341b` |

`candidate_partitions_explored` was exactly **171,251** in every scan. Corrected
groups comprise 45 Stronger Evidence and 113 Review Evidence groups, with 27
conflicts, 40 deferred work units, and 4,982 unassigned records.

Canonical group comparison is diagnostic, not ground truth:

| Historical reference | Common | Corrected only | Historical only |
|---|---:|---:|---:|
| Scan 34 (158 groups) | 131 | 27 | 27 |
| Scan 35 (157 groups) | 132 | 26 | 25 |

## Safety, cache, process, performance, and XLSX

- Cold and repeated-warm proposal payloads are identical, including character
  ranks and hybrid priorities.
- Focused tests pass with `PYTHONHASHSEED=1`, `2`, and `3`.
- Head/Tail protected cannot-link, Bicycle generic-only deferral, R18C lexical
  demotions, human authority, and append-only review persistence tests pass.
- Real output has zero accepted cannot-link pairs and zero duplicate accepted
  memberships. `GF5_PARTITION_POLICY_V1` and all five objective terms remain
  unchanged.
- Full scans took 270.883 s cold, 270.350 s warm, and 281.837 s warm. Discovery
  stages took 43.623 s, 26.303 s, and 28.082 s; GF5 took 201.246 s, 216.760 s,
  and 222.121 s. Retrieval-key construction costs approximately 70.974 ms per
  5,327 keys (13.323 microseconds/key) in an isolated 100-run measurement.
- The corrected XLSX exported in 7.586 s and opens with exactly `Overview`,
  `Review Groups`, `Group Index`, `Detailed Data`, and `Technical Reference`.
  It contains 158 group-index rows and 345 member rows in each member-level
  sheet, matching runtime, with zero formula cells.

## Restored claim

For the same input, engine version, configuration, and deterministic reference
data, the system produces the same semantic candidate/group result independent
of scan ID and cache state. Scan-local IDs, timestamps, filenames, and API
references may differ. This is a determinism claim, not an accuracy,
production-readiness, or automatic-merge claim.
