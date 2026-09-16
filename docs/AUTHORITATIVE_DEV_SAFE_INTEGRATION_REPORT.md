# Authoritative solution and safe dev integration

## Classification

`AUTHORITATIVE_DEV_INTEGRATION_VERIFIED_WITH_NONBLOCKING_OMISSIONS`

The demo candidate starts exactly from verified commit `9a72448c2b96cbbf152aabc2142c1f3d4b3ac7d5`. Only the independently visual SEBSA brand-mark hunk was manually integrated. No dev backend, schema, dependency, API, identity, review, or export behavior was imported.

## Git lineage and forensic pointers

- Starting `llm-assisted-mvp` HEAD / bad merge: `b81ef5fb5b343731790635f7024ac01d6be9b19b`
- Bad merge parents: `9a72448c2b96cbbf152aabc2142c1f3d4b3ac7d5` and `3865053338c8d332e4ccea3d3c91168ca165f316`
- Verified authoritative commit: `9a72448c2b96cbbf152aabc2142c1f3d4b3ac7d5`
- Current dev HEAD at preflight: `f2b51ce91ae2037afe643dbc6e301fe893575c48`
- Backup pointer: `backup/llm-assisted-mvp-bad-merge` -> `b81ef5f`
- Backup pointer: `backup/dev-before-demo-integration` -> `f2b51ce`
- Integration branch: `demo-authoritative-integration`
- Safe integration commit: `a8191ad` (`Integrate safe dev branding`)

Neither original branch was moved, reverted, rebased, or rewritten. No tag was created or changed.

## Dev delta classification

Every one of the 41 paths differing between `9a72448c` and current dev has exactly one classification. “Manual visual hunk” means only the explicitly described lines were used; the rest of that path's dev delta was rejected.

| Dev path | Classification | Decision |
|---|---|---|
| `.claude/launch.json` | `UNKNOWN_UNSAFE_FOR_DEMO` | omit editor metadata |
| `backend/app/api/routes_config.py` | `SHARED_INFRASTRUCTURE_NEEDS_MANUAL_INTEGRATION` | omit; coupled to rejected custom-field schema |
| `backend/app/api/routes_identity_groups.py` | `DUPLICATE_SOLUTION_CONFLICT` | omit identity/export API changes |
| `backend/app/api/routes_scans.py` | `DUPLICATE_SOLUTION_CONFLICT` | omit scan-contract changes |
| `backend/app/core/config.py` | `DUPLICATE_SOLUTION_CONFLICT` | omit automatic `.env` loading |
| `backend/app/core/constants.py` | `DUPLICATE_SOLUTION_CONFLICT` | omit changed identity field semantics |
| `backend/app/db/migrations.py` | `DUPLICATE_SOLUTION_CONFLICT` | omit scan/identity migration |
| `backend/app/db/models.py` | `DUPLICATE_SOLUTION_CONFLICT` | omit scan/identity model changes |
| `backend/app/engine/business_rules.py` | `DUPLICATE_SOLUTION_CONFLICT` | omit pair-only strict rules |
| `backend/app/engine/column_semantics.py` | `DUPLICATE_SOLUTION_CONFLICT` | omit part-type semantic change |
| `backend/app/engine/decision_engine.py` | `DUPLICATE_SOLUTION_CONFLICT` | omit pair-scoring contract change |
| `backend/app/engine/scoring.py` | `DUPLICATE_SOLUTION_CONFLICT` | omit pair-scoring contract change |
| `backend/app/repositories/custom_field_repository.py` | `DEV_CHANGE_DEPENDS_ON_REJECTED_DUPLICATE_CHANGE` | omit |
| `backend/app/repositories/scan_repository.py` | `DUPLICATE_SOLUTION_CONFLICT` | omit persisted scan semantic change |
| `backend/app/schemas/schemas.py` | `SHARED_INFRASTRUCTURE_NEEDS_MANUAL_INTEGRATION` | omit custom-field contracts |
| `backend/app/services/identity_read_export_service.py` | `DUPLICATE_SOLUTION_CONFLICT` | omit authority/export change |
| `backend/app/services/identity_read_xlsx_export_service.py` | `DUPLICATE_SOLUTION_CONFLICT` | omit dev and `f2b51ce` reviewed-XLSX changes |
| `backend/app/services/llm_triage_service.py` | `DUPLICATE_SOLUTION_CONFLICT` | omit candidate-processing semantic change |
| `backend/app/services/scan_runner.py` | `DUPLICATE_SOLUTION_CONFLICT` | omit pair-only wiring |
| `backend/app/services/scan_service.py` | `DUPLICATE_SOLUTION_CONFLICT` | omit scan contract change |
| `backend/app/services/validation_service.py` | `DUPLICATE_SOLUTION_CONFLICT` | omit raw error exposure and coupled custom/XLSX intake |
| `backend/requirements.txt` | `DEV_CHANGE_DEPENDS_ON_REJECTED_DUPLICATE_CHANGE` | omit dependency churn |
| `backend/tests/test_custom_fields.py` | `DEV_CHANGE_DEPENDS_ON_REJECTED_DUPLICATE_CHANGE` | omit tests for rejected feature |
| `backend/tests/test_llm_auto_triage.py` | `DUPLICATE_SOLUTION_CONFLICT` | omit changed triage contract tests |
| `backend/tests/test_part_types.py` | `DEV_CHANGE_DEPENDS_ON_REJECTED_DUPLICATE_CHANGE` | omit tests for rejected feature |
| `frontend/package-lock.json` | `DEV_CHANGE_DEPENDS_ON_REJECTED_DUPLICATE_CHANGE` | omit dependency churn |
| `frontend/src/App.jsx` | `DUPLICATE_SOLUTION_CONFLICT` | omit removal of Load Test route |
| `frontend/src/api/client.js` | `DEV_CHANGE_DEPENDS_ON_REJECTED_DUPLICATE_CHANGE` | omit custom-field client API |
| `frontend/src/components/ExportAuthorityPanel.jsx` | `DUPLICATE_SOLUTION_CONFLICT` | omit reviewed-export workflow change |
| `frontend/src/components/Layout.jsx` | `SAFE_UNRELATED_DEV_CHANGE` | manually integrate only SEBSA mark; retain Load Test navigation |
| `frontend/src/pages/LoadTest.jsx` | `DUPLICATE_SOLUTION_CONFLICT` | retain authoritative page; reject deletion |
| `frontend/src/pages/NewScan.jsx` | `DUPLICATE_SOLUTION_CONFLICT` | retain Sensitive Data Mode and scan-mode semantics |
| `frontend/src/pages/ScanResults.jsx` | `DEV_CHANGE_DEPENDS_ON_REJECTED_DUPLICATE_CHANGE` | omit reviewed-XLSX client path |
| `frontend/src/styles.css` | `SAFE_UNRELATED_DEV_CHANGE` | manually integrate only `.sebsa-mark`; omit broad restyle/custom-field CSS |
| `frontend/src/utils/customFieldUi.js` | `DEV_CHANGE_DEPENDS_ON_REJECTED_DUPLICATE_CHANGE` | omit |
| `frontend/src/utils/identityExportUi.js` | `DEV_CHANGE_DEPENDS_ON_REJECTED_DUPLICATE_CHANGE` | omit reviewed-XLSX behavior |
| `frontend/src/utils/identityGroupUi.js` | `DEV_CHANGE_DEPENDS_ON_REJECTED_DUPLICATE_CHANGE` | omit reviewed-XLSX target |
| `frontend/src/utils/partTypeUi.js` | `DEV_CHANGE_DEPENDS_ON_REJECTED_DUPLICATE_CHANGE` | omit |
| `frontend/src/utils/productJourneyUi.js` | `DUPLICATE_SOLUTION_CONFLICT` | retain sensitive-mode validation freshness |
| `frontend/tests/customFieldUi.test.mjs` | `DEV_CHANGE_DEPENDS_ON_REJECTED_DUPLICATE_CHANGE` | omit |
| `frontend/tests/partTypeUi.test.mjs` | `DEV_CHANGE_DEPENDS_ON_REJECTED_DUPLICATE_CHANGE` | omit |

Files imported whole: `0`. Shared files manually integrated: `2`. Whole paths omitted: `39`; unsafe remainders were also omitted from both manually integrated paths.

## AUTHORITATIVE_DUPLICATE_SURFACE

| Path / area | Authoritative symbols or responsibility | Why authoritative | Representative protection | Dev changed? |
|---|---|---|---|---|
| `backend/app/engine/normalizer.py` | deterministic token normalization | identity input semantics | `test_normalizer.py`, `test_semantic_alias_reference.py` | no |
| `backend/app/reference_data/semantic_aliases.py`, `semantic_aliases.v1.json` | versioned aliases and logical fingerprint | frozen semantic reference | `test_semantic_alias_reference.py` | no |
| `backend/app/engine/candidate_generator.py`, `candidate_evaluation_features.py` | bounded candidates and reusable evidence | candidate membership | candidate and feature tests | indirectly through changed callers |
| `backend/app/services/lexical_retrieval.py` | exact indexed lexical retrieval | proposal membership/order | exact lexical and tie tests | no |
| `backend/app/services/character_retrieval.py` | fixed-seed character retrieval | proposal membership/order | character contract/selection tests | no |
| `backend/app/services/hybrid_retrieval.py` | channel fusion, caps, order | authoritative bounded discovery | hybrid, scan-independent ordering tests | indirectly through changed runner |
| `backend/app/llm/cache.py`, embedding cache services | canonical vector storage/reload | fresh/warm equivalence | cache-save and determinism tests | no |
| `backend/app/services/canonical_record_service.py` | immutable canonical record catalog and `retrieval_order_key` | GF1 identity source | canonical catalog tests | no in bad merge; missing dev custom attributes is a rejected gap |
| identity discovery/neighborhood services | proposals and overlapping neighborhoods | GF2/GF3 inputs | identity discovery/neighborhood tests | indirectly through scan changes |
| `backend/app/engine/identity_evidence_evaluator.py`, `identity_edge.py` | signed GF4 evidence and cannot-links | hard identity safety | identity evidence/edge tests | no in bad merge; dev strict rules bypassed it |
| `backend/app/resolution/resolver.py`, `identity_resolution_service.py` | GF5 objective, partition safety, deterministic traversal | group authority | resolver contracts/golden/persistence/determinism tests | no in bad merge; dev custom semantics never reached it |
| identity group projection/read services | GF6 snapshots and selected read authority | visible product truth | group projection/read/API tests | dev changed read/export surfaces |
| review models, schemas, repository, service | append-only human authority | final human decision semantics | review/API/persistence tests | dev changed adjacent shared schema/routes |
| identity CSV/XLSX export services | advisory and human-authoritative exports | client artifact contract | group export and XLSX tests | yes; rejected except no visual dependency |
| `backend/app/db/models.py`, `migrations.py` | scan, identity, review persistence | durable authority | schema/migration/recovery tests | yes; rejected |
| `backend/app/services/scan_runner.py` and scan routes | GF1-GF6 orchestration and privacy inputs | normal product path | orchestration, recovery, real-ingestion tests | yes; rejected |
| `frontend/src/pages/NewScan.jsx`, `ScanResults.jsx` | scan, list/detail, evidence, review workflow | client authority semantics | product journey, group-first UI, review tests | yes; authoritative versions retained |
| `ExportAuthorityPanel.jsx` and identity UI utilities | export/review wording and routes | prevents authority inversion | export and review UI tests | yes; authoritative versions retained |
| demo fixture and determinism diagnostics | rehearsed and repeatable acceptance | demo safety | `test_gf12_showable_product_demo.py`, determinism tests | no |

The logical semantic-alias reference remains schema version `1`, reference version `semantic-aliases-v1`, fingerprint `0484679a78e61b2f3564c40ca7ef7f7d2b69c1a98e24d24ecdedf65eccdc4367`, with map sizes 19/2/11. `co -> coconut` and `a -> amp` remain unchanged. GF5 objective remains `(covered, likely_members, strong, -review, -group_count)`.

## Why our duplicate solution remains authoritative

The final branch has **zero backend differences** from `9a72448c`. The only source differences are the SEBSA text span in `Layout.jsx` and its CSS rule. Load Test, Sensitive Data Mode, scan-mode selection, validation freshness, canonical records, candidate semantics, GF4 cannot-links, GF5 ordering/objective, human review, APIs, schema, dependencies, and the five-sheet XLSX implementation are byte-for-byte the authoritative version.

The bad merge's three tests failed on `b81ef5f` (`0` supporting candidates, `0` strict custom-field rejections, and `0` Purchase-UOM rejections). Their associated feature is deliberately absent here rather than exposed with false semantics. Implementing custom-field or Purchase/Sales identity behavior would change the duplicate solution and requires a separate architect-approved Group-First design.

## Verification

- Baseline smoke before import: `72 passed` covering the 17-row demo, GF4, GF5, cache and deterministic ordering.
- Safe branding slice: `148 passed` frontend tests; Vite production build succeeded with 42 modules.
- Full backend: `1881 passed, 15 skipped`, no failures, in 246.89 seconds.
- 17-row demo: all 24 tests passed within the smoke/full suites; scan, read authority, review persistence, reviewed CSV and system XLSX were exercised with zero providers.
- XLSX: full suite passed the authoritative five-sheet contract (`Overview`, `Review Groups`, `Group Index`, `Detailed Data`, `Technical Reference`), zero formulas, advisory wording, vertical group merges and flat detailed data.
- Provider calls: `0`; no `.env`, API key, provider secret, or configured database was accessed.

### Real-data and determinism result

The historical CSV was read from the raw Git blob `f6889ef:data/List_20260709_093045.csv` into a disposable temporary directory. It matched authorized SHA-256 `8740777d660a16661585e6141de7be3309219b7758dd12486f3abb1a05b1110b`; the protected XLSX was never touched.

Two independent provider-free runs completed and matched exactly:

| Metric | Run 1 | Run 2 |
|---|---:|---:|
| records | 5,327 | 5,327 |
| discovery proposals | 20,477 | 20,477 |
| groups | 164 | 164 |
| stronger/likely groups | 1 | 1 |
| review groups | 163 | 163 |
| conflicts | 21 | 21 |
| deferred | 42 | 42 |
| unassigned | 4,972 | 4,972 |
| targeted requests/results | 327 | 327 |
| provider calls | 0 | 0 |

The runs took 212.00 and 206.46 seconds and both completed as visible, authoritative Group-First products with zero deprecated pair/G2-v1/shadow writes. These results prove current-code repeatability but differ from the prompt's historical 158/45/113/27/40/4,982/271 reference. Because this branch has no backend difference from `9a72448c`, the difference is not caused by a dev import. A separate baseline provenance audit is required before claiming equivalence to the historical aggregate.

## Known limitations and next action

- Custom fields, Purchase/Sales part types, XLSX upload, separate reviewed-XLSX export, and broad dev restyling are omitted because their dev implementations are duplicate-coupled or depend on rejected schema/API behavior.
- The branch is safe for the rehearsed 17-row demo and authoritative five-sheet export. It must not be advertised as supporting the omitted dev features.
- The original `llm-assisted-mvp` should remain untouched until after the demo and explicit architect approval.
- Next action: architect reviews this branch and the real-data baseline discrepancy; only then decide whether to promote it or authorize a separate Group-First implementation of omitted features.
