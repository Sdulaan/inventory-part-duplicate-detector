# Demo baseline provenance audit: 164 versus historical 158

## Classification

```text
BASELINE_PROVENANCE_DIFFERENCE_EXPLAINED
SCAN_MODE_OR_REQUEST_DIFFERENCE
```

The current branch has no backend drift from the authoritative backend base. The
164-group diagnostic and the historical 158-group acceptance did not use the
same request parameters. The historical request selected `CONTRACT` and
`UNIT_MEAS` and used threshold `75`; the 164-group runtime-localization entrypoint
selected no fields and used threshold `60`. Both used the external request mode
`SAME_SITE_DUPLICATE`; Group-First primary internally used the same `DISCOVERY`
identity-discovery context in both cases.

An isolated replay at current HEAD, using the exact current 5,327-row CSV, a
fresh SQLite database, the provider-free benchmark configuration, and the
historical request tuple, reproduced all historical S0-S10 counts and SHA-256
fingerprints exactly. It also reproduced 158 groups, 171,251 candidate
partitions, and 271 targeted evidence requests. This proves the result difference
is request provenance, not the safe frontend integration, backend drift,
reference-data drift, cache state, persisted review state, or the current runtime.

Provider calls were zero. The protected workbook was not accessed.

## Preflight and evidence boundary

- Branch: `demo-authoritative-integration`
- Audit-start HEAD: `e42752da94bec27960f68972a00c34792387cd6f`
- Authoritative backend base: `9a72448c2b96cbbf152aabc2142c1f3d4b3ac7d5`
- Backend diff from authoritative base to audit-start HEAD: empty
- Audit-start working tree: clean
- Historical acceptance artifact:
  `artifacts/determinism_cache_and_gf5_ordering/three_scan_acceptance.json`
- Historical producer/review evidence:
  `docs/DETERMINISM_CACHE_AND_GF5_ORDERING_FIX.md` and
  `docs/DETERMINISM_FIX_INDEPENDENT_REVIEW.md`
- Current 164 evidence: two existing provider-free
  `gf12c1-r3-runtime-localization-v1` JSON results generated from fresh isolated
  SQLite databases; they completed in 212.004 and 206.458 seconds and returned
  the same aggregate result.
- Causal replay: one fresh isolated SQLite database at audit-start HEAD, using
  the historical persisted request values. The database was created in the OS
  temporary directory and was not an application or repository database.

The historical acceptance JSON is not self-provenancing. It does not store its
Git commit, raw input fingerprint, configuration fingerprint, reference version,
dependency versions, or separate per-run stage tables. The independent review
ties an exact fresh reproduction to commit
`2fd786a5f89e7233dbfeeda33fe3a6515f7200dd`; that is the historical executable
reference used below. Fields absent from both the machine artifact and its
review evidence are reported as `NOT_RECORDED` rather than inferred.

## Provenance comparison

| Dimension | Historical 158 | Current 164 | Equal? | Evidence |
|---|---|---|---|---|
| Commit | Acceptance JSON: `NOT_RECORDED`; independently reproduced at `2fd786a5f89e7233dbfeeda33fe3a6515f7200dd` | `e42752da94bec27960f68972a00c34792387cd6f` with backend base `9a72448c2b96cbbf152aabc2142c1f3d4b3ac7d5` | No | Independent review; Git preflight |
| Backend tree | `8ec591fa0145e310a699da4047e16d4e8b01f81a` at reviewed commit | `de62a2fdb6bf7d4044fefd40e01811f593656b18` at authoritative base and current HEAD | No, but bounded | The only backend changes between references externalize the same semantic alias maps and add their test; current integration has zero backend changes from `9a72448c` |
| Input filename | Reconstructed from immutable canonical fields of historical Scan 34; original filename `NOT_RECORDED` by acceptance artifact | Git raw object `f6889ef:data/List_20260709_093045.csv` | Unknown | Correction report; current extraction record |
| Input SHA-256 | `NOT_RECORDED` for historical raw bytes | `8740777d660a16661585e6141de7be3309219b7758dd12486f3abb1a05b1110b` | `INPUT_BYTES_UNKNOWN` | Acceptance/review omission; current direct byte hash |
| Input size | `NOT_RECORDED` | 3,265,800 bytes | Unknown | Current filesystem metadata |
| Input header | `NOT_RECORDED` as raw CSV metadata | 133-column source header, mapped with `{}` | Unknown at raw-input layer | Current safe CSV inspection; historical artifact omission |
| Input row count | 5,327 | 5,327 | Yes | Acceptance artifact and both current localization results |
| S0 hash | `8107a36194f3bab4209a1f714fc7412a76288b11b2a7b93d536a9c20b55d6257` | `8107a36194f3bab4209a1f714fc7412a76288b11b2a7b93d536a9c20b55d6257` | `S0_EQUAL` | Historical stage artifact; direct current canonical snapshot fingerprint; causal replay |
| Row order | Historical Scan 34 source order, represented by the S0 snapshot | Same canonical source-row ordinals and S0 fingerprint | Yes at canonical layer | S0 includes source-row index/fingerprint and is exactly equal |
| External scan mode | `SAME_SITE_DUPLICATE` | `SAME_SITE_DUPLICATE` | Yes | Read-only persisted Scan 34 metadata; current localization entrypoint |
| Internal identity-discovery mode | `DISCOVERY` under Group-First primary | `DISCOVERY` under Group-First primary | Yes | Persisted causal-replay discovery configuration; orchestration policy |
| Selected fields | `['CONTRACT', 'UNIT_MEAS']` | `[]` | **No** | Read-only historical Scan 34 row and current localization call |
| Threshold | `75` | `60` | **No** | Read-only historical Scan 34 row and current localization call |
| Other request parameters | CSV source; sensitive mode disabled for controlled acceptance/replay; Group-First primary; provider-free benchmark configuration | CSV source; sensitive mode false; Group-First primary; provider-free benchmark configuration | Equal where recorded | Producer documentation, current entrypoint, causal replay |
| Semantic reference | Alias maps embedded in code before externalization; fingerprint not persisted | schema `1`, version `semantic-aliases-v1`, canonical SHA-256 `0484679a78e61b2f3564c40ca7ef7f7d2b69c1a98e24d24ecdedf65eccdc4367` | `REFERENCE_EQUAL` | Git diff proves the same map values were moved to versioned JSON; current-env causal replay matches every historical hash |
| DB state/schema | New SQLite DB; exact schema revision `NOT_RECORDED` | New isolated SQLite DB created from current `Base.metadata`; configured DB not accessed | Semantically equal for replay | Producer report; current result flag; replay construction |
| Review/constraint state | No prior review-derived constraints in the new DB | No prior review-derived constraints in either fresh current DB | Yes | Fresh-DB construction and zero cross-scan state; replay effective-constraint fingerprint is the empty-input value |
| Cache namespace | Semantic retrieval-text fingerprint plus model version `sklearn-hashing-domain-v1`; scan 1 cold and scans 2/3 warm | Same key/model contract; each recorded 164 run used its own fresh DB | Yes | Cache correction report and unchanged cache implementation |
| Cache representation | Seven-decimal canonical embedding vectors | Seven-decimal canonical embedding vectors | Yes | Correction report; unchanged implementation; exact replay |
| Requirements hash | SHA-256 `f0fa86f0286299deb926077f79cc386f53ee07a820fe1b458d0d9814bbfb53dc` | Same | Yes | Direct Git/blob and file comparison |
| Python version | `NOT_RECORDED` | 3.11.9 | Unknown | Historical evidence omission; current interpreter |
| OS / SQLite | `NOT_RECORDED` | Windows `10.0.26200`; SQLite 3.45.1 | Unknown | Historical evidence omission; current runtime |
| Semantic dependency versions | Actual installed versions `NOT_RECORDED`; direct requirements identical | NumPy 2.4.6, pandas 2.3.0, SciPy 1.17.1, scikit-learn 1.7.0, SQLAlchemy 2.0.41, RapidFuzz 3.13.0, Pydantic 2.11.7 | Installed-version equality unknown; not causal | Current package metadata; exact causal replay in current environment |
| S1 proposals | 20,492; `4f2df0eb716ec0d9b06ec65c33cfb6cca1673ccce84559dfe56fbc9f42cdd2fd` | 20,477; hash `NOT_RECORDED` by current aggregate artifact | **No: earliest divergence** | Historical stage artifact; current localization result |
| GF4 / S3 | 20,492; `682473a17a9edcbf66e940194a6287852a057f32655863948459bb12fc975468` | 20,477; hash `NOT_RECORDED` | No | Historical stage artifact; current localization result |
| GF5 / S6 | 158; `a84dbe3aca0391c688ab79ea0723bc95b168d70ef0741a1c09259f43fe7c006a` | 164; hash `NOT_RECORDED` | No | Historical stage artifact; current localization result |
| Final counts | 158 groups; 45 Stronger Evidence; 113 Review Evidence; 27 conflicts; 40 deferred; 4,982 unassigned; 271 targeted requests; 171,251 partitions | 164 groups; 1 likely; 163 review; 21 conflicts; 42 deferred; 4,972 unassigned; 327 targeted requests; partition count not emitted by the aggregate artifact | No | Historical acceptance JSON and current localization JSON |

## Historical stage fingerprints and causal replay

The controlled replay used the exact current CSV bytes and runtime but changed
the request from the 164 diagnostic tuple to the historical tuple. Every stage
matched the committed historical acceptance:

| Stage | Historical count | Historical SHA-256 | Current-env historical-request replay |
|---|---:|---|---|
| S0 canonical records | 5,327 | `8107a36194f3bab4209a1f714fc7412a76288b11b2a7b93d536a9c20b55d6257` | exact |
| S1 candidate proposals | 20,492 | `4f2df0eb716ec0d9b06ec65c33cfb6cca1673ccce84559dfe56fbc9f42cdd2fd` | exact |
| S2 evidence inputs | 20,492 | `726f1206ede9210c10fdcc797c594523887a41156453cb981c82315a0d9ad38f` | exact |
| S3 GF4 classified edges | 20,492 | `682473a17a9edcbf66e940194a6287852a057f32655863948459bb12fc975468` | exact |
| S4 GF5 neighborhoods | 1,313 | `7fe6c3e5138cf3274ccc8bcf786f6accd1528af3e9690f06d20230a6b5c97259` | exact |
| S5 GF5 objective inputs | 1 | `268e78c48b662ff301dde75d68a4792e994350b41f2dc4c9abc2aff0cbbdb6b9` | exact |
| S6 selected groups | 158 | `a84dbe3aca0391c688ab79ea0723bc95b168d70ef0741a1c09259f43fe7c006a` | exact |
| S7 conflicts | 27 | `aeecfb4f30e9a00819fc2a6b5f414e55768032730d2a67805f646d3f7c0af860` | exact |
| S8 deferred | 40 | `6de165cafcdd79dfb469e5060b604ab19d84fb0b31e590edcbeb40c71b9ae2b0` | exact |
| S9 unassigned | 4,982 | `cdbab036c0dad18e918c56edb0a976d24317a74d3240cfe82a0ea99e7e2742c6` | exact |
| S10 projection | 158 | `0a8a5ba1c699d9f810d1c555509a462d04530b113f8564c8c9d9b5edd92e341b` | exact |

The replay also matched:

- `candidate_partitions_explored`: 171,251
- `targeted_evidence_request_count`: 271
- resolution configuration fingerprint:
  `2584f95836d0f37d73dea545d64eab6b9cfbefc67cfa29d5dd0a01b5fda92448`
- resolver algorithm:
  `constrained-identity-resolver-v2-stable-ordering`
- discovery algorithm:
  `identity-discovery-v6-scan-independent-ordering`
- provider calls: 0

## Earliest divergence and causal explanation

S0 is equal. The earliest proven divergence is S1 candidate discovery:
20,492 historical proposals versus 20,477 in the 164 diagnostic.

The two executions supplied different request tuples to `ScanRunner`:

```text
historical 158:
  selected_fields = ["CONTRACT", "UNIT_MEAS"]
  threshold = 75

current 164 diagnostic:
  selected_fields = []
  threshold = 60
```

`selected_fields` participates directly in standard candidate generation,
deterministic scoring, and the persisted identity-discovery configuration.
`threshold` controls which scored standard pairs enter the discovery input. The
combined request difference therefore changes S1 before GF4 or GF5. Replaying
the historical tuple with current input, current backend, current reference
data, and current dependencies restores the complete historical semantic
fingerprint chain. No hidden environment or state premise is needed to explain
the difference.

## Defect and baseline decision

The 164 result is not a product defect. It is deterministic under the explicitly
different diagnostic request: two independent runs returned the same result.
It must not be presented as an exact replay of the historical 158 acceptance.

The 158 result remains the correct historical and rehearsed-demo comparison
baseline when the request selects `CONTRACT` and `UNIT_MEAS` and uses threshold
`75`, with the same input, engine/configuration/reference conditions. It is not a
universal expected count for arbitrary request parameters.

`demo-authoritative-integration` remains safe for the rehearsed demo. The audit
found no backend drift or safety defect, and the authoritative demo request was
reproduced exactly on the current branch. Promotion does not need to wait for a
runtime correction.

## Demo claim boundary and smallest next action

Allowed claim:

> With the 5,327-row canonical input in source order, the provider-free
> Group-First configuration, and the rehearsed request selecting `CONTRACT` and
> `UNIT_MEAS` at threshold `75`, the current authoritative branch exactly
> reproduces the historical 158-group S0-S10 acceptance.

Do not claim that 158 is invariant across request parameters or that the
164 diagnostic is equivalent to the historical request.

Smallest next action: persist a compact request/input/configuration provenance
manifest beside future real-data acceptance artifacts so selected fields,
threshold, scan mode, input SHA-256, commit, reference fingerprint, and runtime
versions cannot be omitted or conflated again. This is a diagnostics-artifact
improvement, not a runtime-behavior change.
