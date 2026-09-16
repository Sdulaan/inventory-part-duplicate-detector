# Acceptance provenance manifest

## Classification

```text
ACCEPTANCE_PROVENANCE_MANIFEST_VERIFIED
```

Acceptance and rehearsal tooling can now write a schema-v1, machine-readable
provenance manifest beside each generated artifact. This is diagnostic tooling
only. Production scan execution, API contracts, database schema, identity
semantics, providers, frontend behavior, and exports are unchanged.

The supported determinism claim is exactly:

> Same input + same engine version + same request/configuration + same deterministic reference data → same semantic result.

## Schema-v1 contract

`backend/app/benchmarks/acceptance_provenance.py` writes these top-level fields:

| Field | Contents |
|---|---|
| `schema_version` | Integer `1` |
| `canonical_serialization` | `utf8-sorted-keys-compact-separators-v1` |
| `artifact_type` | Logical acceptance-artifact kind |
| `generated_at_utc` | Non-semantic generation timestamp |
| `repository` | Commit, branch, and truthful dirty boolean |
| `input` | Logical label, exact safe-input byte size/SHA-256, row count, header SHA-256, S0 SHA-256, and row-order SHA-256 |
| `request` | Scan/site mode, sorted selected fields, threshold, candidate mode, sensitive-mode state, source type, semantic feature flags/options, and section SHA-256 |
| `configuration` | Orchestration, discovery/retrieval, evidence, GF5 resolution, projection, cache contracts, and section SHA-256 |
| `reference_data` | Extensible named references plus bundle SHA-256 |
| `runtime` | Python, platform, SQLite, selected semantic package versions, and semantic-runtime SHA-256 |
| `semantic_fingerprints` | Separate S0 through S10 names, counts, and SHA-256 values |
| `counts` | Records, proposals, groups/tier split, conflicts, deferred, unassigned, targeted requests, partitions, member rows, and provider calls |
| `provider_calls` | Must be zero or manifest generation fails |

If source bytes are unavailable, the input contract records
`byte_sha256: null` and `byte_hash_status: NOT_AVAILABLE`. It never invents a
hash. A supplied CSV is parsed and its data-row count must equal persisted S0.

## Canonical fingerprints

Request, configuration, reference bundle, and semantic runtime fingerprints use:

```text
SHA-256(
  UTF-8(
    JSON with sorted object keys, compact separators, and no timestamp
  )
)
```

Selected fields are sorted and deduplicated because their request semantics are
unordered. Thresholds are normalized to JSON numbers represented as floats.
Stage fingerprints remain separate; S0-S10 are never collapsed into one digest.
The generation timestamp and repository dirty state are provenance fields, not
inputs to semantic section fingerprints.

## Secret and path boundary

The writer constructs its configuration from allowlisted persisted scan fields.
It does not inspect `.env` or environment variables. Before writing, it
recursively rejects secret-shaped keys and values, including API keys, tokens,
passwords, credentials, credential-bearing connection strings, and common
provider-key forms. Only a logical input label is serialized; an absolute input
path is rejected. Git status contributes one boolean and never a list of changed
or untracked paths.

Manifest creation fails if any persisted provider count is nonzero, any S0-S10
stage is absent, input rows disagree with the scan, unsafe content is detected,
or the output cannot be written. Such failure blocks the acceptance diagnostic;
it cannot affect ordinary production scanning.

## Tooling integration

The existing read-only determinism audit now writes
`scan_<id>.acceptance_provenance.json` for each audited scan. It accepts optional
safe-input provenance:

```powershell
cd backend

.\.venv\Scripts\python.exe -m app.benchmarks.scan_determinism_audit `
  --database <disposable-or-read-only-scan-database> `
  --scan-a <first-scan-id> `
  --scan-b <second-scan-id> `
  --output-directory <artifact-directory> `
  --input <safe-csv> `
  --input-label <logical-filename> `
  --repository-root .. `
  --sensitive-mode false
```

The standalone writer supports one completed Group-First scan and is suitable
for demo rehearsal or another artifact-generation gate:

```powershell
.\.venv\Scripts\python.exe -m app.benchmarks.acceptance_provenance `
  --database <disposable-or-read-only-scan-database> `
  --scan-id <scan-id> `
  --output <artifact-name>.acceptance_provenance.json `
  --repository-root .. `
  --artifact-type <logical-artifact-type> `
  --input <safe-csv> `
  --input-label <logical-filename> `
  --sensitive-mode false
```

The database is opened read-only. The protected workbook is never an authorized
input to this tooling.

## Historical 158 manifest and 164 differentiation

`artifacts/determinism_cache_and_gf5_ordering/historical_158.acceptance_provenance.json`
was generated from the completed controlled replay and the exact safe 5,327-row
CSV. It records:

- request: `SAME_SITE_DUPLICATE`, `CONTRACT` plus `UNIT_MEAS`, threshold `75`;
- input SHA-256:
  `8740777d660a16661585e6141de7be3309219b7758dd12486f3abb1a05b1110b`;
- S0-S10 hashes matching the historical acceptance exactly;
- 20,492 proposals, 158 groups, 45 Stronger Evidence, 113 Review Evidence,
  27 conflicts, 40 deferred, 4,982 unassigned, 271 targeted requests,
  171,251 candidate partitions, 345 member rows, and zero provider calls;
- request SHA-256:
  `07a25571a21412c03d9fe694383b85ba7e2bfdd9d1879fcfeb3affeee95abadc`.

The same canonical request contract with no selected fields and threshold `60`
has SHA-256
`7a93e99d2d9cfbad49c5a9f158d5c45d3e7413c678e1f011c50d986ef83e511f`.
The manifest therefore distinguishes the 158 baseline from the deterministic
164 diagnostic without relying on prose.

The historical manifest truthfully records `repository.dirty: true`: it was
generated while this new tooling and its documentation were uncommitted. It
records generation provenance rather than retroactively claiming a clean tree.

## Verification

Focused tests cover schema/version, canonical serialization, exact input byte
and header hashes, row-count validation, request/configuration/reference/runtime
capture, separate S0-S10 storage, semantic counts, dirty-tree truthfulness,
selected-field order invariance, threshold fingerprint differentiation,
secret/path rejection, and the zero-provider gate.

The 17-row demo remains semantically unchanged. Frontend files are untouched.
Provider calls are zero.
