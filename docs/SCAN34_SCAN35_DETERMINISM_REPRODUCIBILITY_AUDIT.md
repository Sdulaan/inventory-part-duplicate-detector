# Scan 34 / Scan 35 Determinism and Reproducibility Audit

## Decision

```text
classification = SCAN34_35_REPRODUCIBILITY_DEFECT_CAUSE_PROVEN
causal subtype = RANKING_OR_CAP
severity = SERIOUS_DETERMINISM_DEFECT
provider calls = 0
```

Scan 34 and Scan 35 consumed semantically identical, identically ordered 5,327-row
catalogs, but their candidate-discovery results differ. The earliest unequal stage
is S1, candidate-discovery proposals. The concrete cause is a scan-local record
reference being used as the stable secondary ordering key in bounded lexical and
character retrieval. A new scan ID therefore changes top-K/candidate-pool tie
ordering and, through the hybrid caps, changes which pairs reach GF4 and GF5.

This is a diagnostic result only. No runtime behavior is changed by this task.

## Safety and evidence boundary

The audit used the existing SQLite persistence and source code at commit
`48c12d9c2c868142c11a0882769122b3d2837dda`. It did not open, inspect, hash, or
modify the protected root XLSX. It did not inspect `.env`, use credentials, make
provider calls, or start Docker.

The database does not persist a source filename or source-byte hash on a scan, and
the exact CSV bytes are no longer available through a safe tracked artifact.
Consequently, byte equality cannot be independently recomputed from persistence.
This is an observability gap, not evidence of unequal input. The architect's
external assertion that the same file was used is corroborated by equality of
every persisted canonical field and source-record fingerprint at every source row.

| Check | Result | System evidence |
| --- | --- | --- |
| `INPUT_BYTES_EQUAL` | `NOT_PERSISTED_NOT_DIRECTLY_VERIFIABLE` | `duplicate_scan` has source type only; no filename/content hash is persisted |
| `INPUT_ROWS_EQUAL` | `true` | 5,327 rows in each scan |
| `INPUT_ROW_ORDER_EQUAL` | `true` | ordered `(source_row_index, source_record_fingerprint)` sequences are equal |
| `CANONICAL_RECORD_SNAPSHOTS_EQUAL` | `true` | scan-neutral full snapshot hash is `8107a36194f3bab4209a1f714fc7412a76288b11b2a7b93d536a9c20b55d6257` for both |

The scan-neutral snapshot hash contains all persisted canonical source and
normalized fields, `source_row_index`, `source_record_fingerprint`, and the
normalization version. It excludes only the database ID, scan ID, scan-local
record reference, and creation timestamp.

## Stage fingerprints

All collections and pair endpoints were canonicalized before hashing. Record
identity below is `(source_row_index, source_record_fingerprint)`, not a database
ID or scan-local record reference. Group collections use sorted member sets.

| Stage | Scan 34 count / hash | Scan 35 count / hash | Equal? |
| --- | --- | --- | --- |
| S0 canonical record snapshots | 5,327 / `8107a36194f3bab4209a1f714fc7412a76288b11b2a7b93d536a9c20b55d6257` | 5,327 / `8107a36194f3bab4209a1f714fc7412a76288b11b2a7b93d536a9c20b55d6257` | yes |
| S1 candidate-discovery proposals | 20,492 / `b952fc9a78ec1c1fe0d9e2e540aa85399ab69a7809b0b61c8bb6f6e851fe20a1` | 20,492 / `36fcf0bfeb4cf249880d49ea1c9f45d7d3b699100f535726478511a5a99320ec` | **no** |
| S2 deterministic evidence inputs | 20,492 / `d0b8f33c6ef33cffea2e2ead2355083129f5bcc1b9c08c11f84c4891fc2b472e` | 20,492 / `5db2abbe0df745f4e78b9ee886b1a5d45c4c66c71493240ec0bf808b42448c3c` | no |
| S3 GF4 classified evidence edges | 20,492 / `44664caf274a809d540948802bdc7473c70eb0ca7f94ed0155c69ab236a7f4e2` | 20,492 / `f0dc9893218ba4586be4a71ac1462028c03fd41cb4a100badef582d7e7526dbd` | no |
| S4 GF5 eligible neighborhoods | 1,289 / `975ac9857eebcf36a08f09c8410cf17cebc639533575535d9bcc69541395bb38` | 1,284 / `ccdb730f7d0407af53b30985dd4f3b0a1c7e72be335e24721c47555bf123ad45` | no |
| S5 GF5 objective-input summary | 1 / `2216283102772143e55177da7bd106df3dcac6e06efefe4782853a18a7bf271b` | 1 / `35a9a39804a4e11cd0f600573669855b25c62494d3c8620008c1d5ba2123340c` | no |
| S6 GF5 selected groups | 158 / `f8d9be56bedcd82b078cbdeb7816f1a3daa5a16e2461d17042d7852f96d85813` | 157 / `bdcbc3fb0a14aad3dc53bf2141871ae1e1e8c49d4cd91aa26bc937d6aa9db2bf` | no |
| S7 conflicts | 28 / `c261db0b8140fde4f62578dc41b3c714fdab2523ba9be16a6bbe003eb8f1738e` | 27 / `f0db4779d0850ae44b84759902f29ca2c25a3ef69747d3a792551245817a11fc` | no |
| S8 deferred work units | 40 / `8d9352f2d0676ef6ad194040b2f9e1e35318728bdd620bb3f711cbb56fb998d0` | 40 / `11e670c2c33888d1046ddb9c82d595e14d819869b6190e6489fd0cf2530ff9d6` | no |
| S9 unassigned records | 4,986 / `67c30f8506c0e6a4109473e80a65578f7cae80aecb50fa71afa9aede1bba8b41` | 4,988 / `475d14d60a4eab5fcb0706bddeb8345515dddca802b482c824ffc5c0b9a56239` | no |
| S10 G2 v2 group projection | 158 / `771ccfa9f600c1437ac4fb37592233b3fad16bdf863abad56efc797cc077448e` | 157 / `41d3ebae6bbe07c18a5bfcec4441649fbb5a69fc447926893b25dea946f25d4c` | no |

S5's persisted summary includes the resolver configuration and work metrics.
Candidate partitions themselves are not persisted. Scan 34 explored 203,708
partitions across 202 work units; Scan 35 explored 186,474 across 201 work units.
That difference is downstream of S1 and is not classified as the cause.

## Exact divergence

The S1 pair sets have 20,443 pairs in common, 49 only in Scan 34, and 49 only
in Scan 35. Thus the pair-set symmetric difference is exactly 98. Among the
20,443 common pairs, 451 proposal payloads have changed retrieval rank/provenance
metadata, but all 20,443 common S2 scoring payloads and all common S3 GF4
classifications and scores are identical. GF4 is deterministic for equal input;
it simply receives different pairs.

The normal selected-field generator was reconstructed from the canonical rows.
Its capped 20,000-pair output exactly matches the `STANDARD_BLOCKING` pair set in
both scans. The 98-pair S1 delta therefore originates in hybrid retrieval, not in
CSV ingestion or the standard blocking generator.

Final G2 v2 membership contains:

| Result | Count |
| --- | ---: |
| Common member sets | 149 |
| Common member sets whose status changed | 0 |
| Scan-34-only member sets | 9 (4 stronger, 5 review) |
| Scan-35-only member sets | 8 (2 stronger, 6 review) |

Fourteen of the seventeen changed two-member groups have their direct pair
proposed in only the scan where that group exists. The other three direct pairs
are proposed and classified identically in both scans, but are affected by the
different surrounding proposal graph and bounded GF5 work-unit construction.
Examples align with the reported cases:

| Scope | Source rows | Example | Direct-pair trace |
| --- | --- | --- | --- |
| Scan 34 only, stronger | 3024 / 3705 | `HT PART 01` / `HT PART 03` | proposal absent in Scan 35 |
| Scan 34 only, stronger | 2477 / 2575 | `PP-NI-INV-PART3` / `PP-NI-INV-PART1` | proposal absent in Scan 35 |
| Scan 34 only, stronger | 4094 / 4474 | `HP-SALES03` / `HP-SALES04` | proposal absent in Scan 35 |
| Scan 34 only, review | 1176 / 4459 | `BICYCLE` / `SS BICYCLE` | proposal absent in Scan 35 |
| Scan 35 only, stronger | 76 / 80 | `SGB1` / `SG-B1` | same strong edge in both; surrounding graph differs |
| Scan 35 only, stronger | 1705 / 1706 | `VIMPART16` / `VIMPART17` | proposal absent in Scan 34 |
| Scan 35 only, review | 1863 / 3054 | `KM-INV-2` / `KM-INP2` | proposal absent in Scan 34 |
| Scan 35 only, review | 3859 / 4952 | `SD-PP1` / `ED-PP1` | proposal absent in Scan 34 |

The generated changed-family trace contains the proposal channels, GF4 class,
and full-precision persisted deterministic score for every changed direct pair.

## Proven causal mechanism

`canonical_record_ref_key(scan_id, source_row_index)` hashes a payload containing
the scan ID. Despite being scan-local, this reference is used as if it were a
cross-run canonical ordering key:

1. Character LSH sorts index insertion by `record_ref_key` and uses that key for
   exact-rerank ties.
2. Exact lexical retrieval also uses `record_ref_key` as its secondary top-K key.
3. Hybrid retrieval then applies top-K 5 per channel, top-K 10 per record, family
   cap 25, tier caps 250/200/50, and global cap 500.
4. A different scan ID reorders tied or bounded candidates, changing the selected
   500 hybrid pairs before GF4.

The real 5,327-record hybrid path was replayed offline with record content,
row order, configuration, fixed LSH seed, vectorizer, and exclusions held fixed.
Only the record-reference list changed:

| Controlled replay | Selected | Semantic hash | Result |
| --- | ---: | --- | --- |
| Scan-34-derived references, cold cache | 500 | `7162c73f4f9d09bcfc8b992ce20ce53cee0d2b6d723b85981ff008461213ef10` | family A |
| Scan-34-derived references, warm cache | 500 | same | family A |
| Scan-35-derived references, cold cache | 500 | `eafdf21c5b254395825e435fad99703ea4b901c4a2e6efad24070c314e02b118` | family B |
| Scan-35-derived references, warm cache | 500 | same | family B |
| Scan-independent row/fingerprint references, cold run 1 | 500 | `589135ef88738c28625e958f42084d32500ed22e9d4cc240bce228327cf33296` | stable family C |
| Scan-independent row/fingerprint references, cold run 2 | 500 | same | stable family C |

The Scan-34 versus Scan-35 replay has exactly 98 pair memberships in its
symmetric difference, matching the persisted S1 symmetric difference exactly.
The isolated character stage alone changes 7,111 unordered pair memberships when
only the scan-local references change. This establishes causality independently
of later evidence scoring and GF5.

Three fresh product scans were not run: the original CSV bytes are not retained
in a safe artifact, reconstructing a different CSV would not satisfy the exact-byte
requirement, and adding scans to the live database would unnecessarily mutate demo
state. The controlled replay is faithful to the decision path and stronger for
causality because it varies exactly one input.

## Alternative-cause checks

| Suspected family | Finding |
| --- | --- |
| Python unordered collections | Sets exist in LSH candidate gathering, but retained pools are canonically sorted. Focused runs with `PYTHONHASHSEED=1`, `2`, and `3` all produced `43535bf7f62459f18ce791c52fe32ef31d2a0eeb32748b98194bd8b816a5edeb`. Not causal here. |
| SQL ordering | Critical proposal and neighborhood loads use explicit ordering. Embedding-cache loads do not order rows, but materialize a fingerprint-keyed map and vectors are retrieved by requested fingerprint order. No semantic SQL-order cause was found. |
| Ranking ties and caps | **Causal.** A scan-local hash is the secondary key at top-K/candidate-pool boundaries. |
| Randomness | Character LSH uses fixed NumPy PCG64 seed 1101. Repeats with the same references are identical. |
| Concurrency | The scan runner executes the relevant stages synchronously; no completion-order aggregation was found in this path. |
| Persisted cross-scan state | Both scans have zero human identity constraints. No prior group/review state feeds discovery. Not causal. |
| Cache state | The latest persisted embedding was generated on 2026-09-01, before both scans, so both were warm. Controlled cold/warm replays are semantically identical. Not causal. |
| Floating point | Every common S2 score and S3 class is identical. Changed pairs arise before threshold classification. Not causal. |
| Export-only illusion | S1, GF4, GF5, unassigned sets, and persisted G2 v2 projections differ. The XLSX layer is not causal. |

## Severity and demo posture

Severity is `SERIOUS_DETERMINISM_DEFECT`: identical system-consumed input and the
same configuration produce different identity group membership because scan ID
affects bounded candidate selection. No source records are overwritten or silently
mutated, so current evidence does not support `DATA_INTEGRITY_DEFECT`.

Until corrected and rerun:

- Do not claim that the same input always produces exactly the same groups.
- Do not use a new 5,327-row live rerun as reproducibility evidence.
- A separately verified stable 17-row rehearsal may remain the primary demo.
- A frozen known-good large scan/export may be shown only as example output, not
  as a reproducibility benchmark.

## Smallest next task

Introduce one scan-independent retrieval-order identity derived from immutable
source-row position plus source-record fingerprint, and use it only for lexical,
character-LSH, and hybrid secondary ordering. Retain the existing scan-local
record reference for persistence ownership. Add a regression that runs identical
records under two scan IDs and requires identical hybrid pairs, GF4 edges, and
G2 v2 member sets. Do not change thresholds, evidence rules, or GF5 policy.

## Reproduction

The committed diagnostic is read-only and does not load application settings:

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.benchmarks.scan_determinism_audit `
  --database ..\inventory_detector.db `
  --scan-a 34 `
  --scan-b 35 `
  --output-directory ..\artifacts\scan34_35_determinism
```

Generated outputs are:

- `scan34_35_stage_fingerprints.json`
- `scan34_35_group_diff.csv`
- `scan34_35_changed_family_trace.csv`
- `scan34_35_rerun_matrix.csv`
