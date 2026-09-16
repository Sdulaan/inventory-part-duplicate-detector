# Duplicate Checking Conditions Semantics Audit

> **Subsequent semantic correction:** This audit remains an accurate account of
> the old code at its recorded commit. Clarified product intent subsequently
> changed selected `CONTRACT`: it is now a request-scoped hard final-group
> equality constraint, while unselected `CONTRACT` remains cross-site eligible.
> The prior 158-group result and `CG-000010` trace are retained as the
> `PRE_SITE_HARD_CONSTRAINT_BASELINE`, not the current expected behavior. See
> `REQUEST_SCOPED_SITE_CONSTRAINT.md` for implementation and acceptance proof.

## 1. Executive answer

**Primary classification:**
`DUPLICATE_CONDITIONS_BEHAVIOR_CORRECT_BUT_UI_MISLEADING`

**CONTRACT classification:** `CONTRACT_RETRIEVAL_AND_EVIDENCE`

**UNIT_MEAS classification:** `UNIT_MEAS_RETRIEVAL_AND_EVIDENCE`

**Demo safety:** `DEMO_BLOCKED_UNTIL_CONDITION_SEMANTICS_FIXED`

Selecting a checkbox does not create a final-group must-match constraint. It
adds a canonical field name to `selected_fields`. The current implementation
uses that list as:

1. a composite equality key for the standard S1 blocking channel; and
2. equal-weight positive/negative business evidence in deterministic scoring.

Some fields also have specialized rules, but those rules apply whether or not
their checkboxes are selected. In particular, HSN/SAC and Product Category
mismatches are hard identity conflicts. Site and Inventory UOM have legacy
hard-boundary behavior, but the authoritative current-product Group-First path
deliberately relaxes both for physical-identity review.

`CG-000010` is not a provenance or projection error. It belongs to the
historical request exactly as stated. Seven bounded cross-site hybrid proposals
became seven `REVIEW_SUPPORT` edges. Three missing cross-pairs were evaluated
later as `NON_GROUPABLE/CROSS_SITE_SCOPE_ONLY`, not `CANNOT_LINK`. GF5 therefore
accepted the five-member set as `POSSIBLE_DUPLICATE_GROUP_REVIEW` with 70%
support density and no cannot-link.

This behavior is explicitly authorized by the Group-First architecture and its
tests, but it contradicts the visible promises “Same-site duplicate scan”,
“Same-site mode is strict”, and “Duplicate-checking conditions”. A reasonable
user would expect checked Site to require one site per result. That expectation
is false for the authoritative G2-v2 result, so the demo should not present this
screen until its wording is corrected.

## 2. Preflight and scope

The audit began from:

| Check | Result |
|---|---|
| Branch | `demo-authoritative-integration` |
| HEAD | `f22bf4ba0683fe2a0132965b5040b4c85108cbd8` |
| Initial `git status --short` | empty |
| Backend diff from `9a72448c2b96cbbf152aabc2142c1f3d4b3ac7d5` | only `acceptance_provenance.py`, `scan_determinism_audit.py`, and `test_acceptance_provenance.py` |
| Semantic backend drift | none found |
| Provider calls | 0 |

The protected workbook was not listed, opened, inspected, hashed, moved,
modified, staged, or deleted. No `.env`, API key, provider secret, or external
provider was accessed. The live database was queried read-only through the
already-running local Docker backend; no database state was changed.

## 3. Checkbox to request mapping

`frontend/src/pages/NewScan.jsx` obtains the field definitions from
`GET /api/config/fields`; its fallback list is the same eleven optional fields.
The backend source is `FIELD_DEFINITIONS` in `backend/app/core/constants.py`.

| UI label | Request/canonical key | Default selected |
|---|---|---:|
| Site | `CONTRACT` | yes |
| Purchase Type | `TYPE_CODE` | no |
| Inventory UOM | `UNIT_MEAS` | yes |
| Com Group 01 | `PRIME_COMMODITY` | no |
| Com Group 02 | `SECOND_COMMODITY` | no |
| Safety Code | `HAZARD_CODE` | no |
| Accounting Group | `ACCOUNTING_GROUP` | no |
| Product Code | `PART_PRODUCT_CODE` | no |
| Product Family | `PART_PRODUCT_FAMILY` | no |
| Product Category | `PRODUCT_CATEGORY_ID` | no |
| HSN/SAC Code | `HSN_SAC_CODE` | no |

Checkboxes are independent and multiple selections are allowed. A click adds
or removes its key in the component's `selected` array. Changing mode does not
change the selection. Selection is local React state until submission, then the
raw array is sent and persisted in `duplicate_scan.selected_fields`. Changing a
selection invalidates the previous validation result.

For unique field names, click order does not change comparison membership or
scores. The raw order is sent and stored, while validation context and discovery
fingerprints sort/deduplicate the fields. Matched-field explanation order can
still reflect request order. The API does not reject duplicate field names, so
non-UI callers should not rely on duplicate-input semantics.

The browser-equivalent multipart payload is:

```text
file=<CSV binary>
scan_name=Inventory duplicate scan
threshold=75
selected_fields=["CONTRACT","UNIT_MEAS"]
column_mapping={<canonical field>:<uploaded heading>, ...}
sensitive_mode=true
scan_mode=SAME_SITE_DUPLICATE
product_authority=current_product
```

The `selected_fields` value is a JSON string inside multipart form data, not a
JSON request property.

## 4. Request to backend mapping

Both `POST /api/scans/validate-only` and `POST /api/scans/upload` in
`backend/app/api/routes_scans.py` declare `selected_fields: str = Form("[]")`.
`parse_selected_fields` in `backend/app/services/validation_service.py`:

- returns `[]` for a missing/empty value;
- parses values beginning with `[` as JSON and uppercases/strips each item;
- otherwise accepts a comma-separated string and uppercases/strips items;
- preserves order and duplicates; and
- does not enforce the `SELECTABLE_FIELDS` allowlist or explicitly require the
  decoded JSON value to be a list.

Consequently, an omitted field and explicit `selected_fields=[]` are equivalent
at these endpoints. `['CONTRACT', 'UNIT_MEAS']` reaches `ScanRunner.run`
unchanged after uppercase/trim normalization. Validation warns for missing
selected columns and fields at least 50% blank. A missing selected field is
ignored by blocking and is non-comparable in scoring. A high-null selected
field is skipped as a standard blocking key, although nonblank values can still
participate in later scoring.

`ScanRepository.create` JSON-serializes the list. The discovery configuration
and fingerprint sort and deduplicate it. The canonical record catalog itself is
unchanged by the selection.

## 5. Stage-by-stage S0-S10 effect

| Stage | Reads selected fields? | Effect | Can change membership? | Can create hard rejection? | Can alter evidence tier? | Main symbols |
|---|---|---|---:|---:|---:|---|
| S0 canonical records | No (apart from scan metadata) | Catalogs the same usable rows and canonical values | No | No | No | `ScanRunner.run`, `create_or_get_scan_record_catalog` |
| S1 candidate proposals | Yes | Standard channel groups by the exact composite of usable selected columns; list also enters the discovery fingerprint. Threshold-dependent standard exclusions change hybrid search/cap context. All generated standard pairs, not only above-threshold pairs, are persisted as proposals. | Yes | No; proposal creation is not a rejection | No | `generate_candidate_pairs`, `standard_candidate_pairs`, `HybridCandidateRetriever.retrieve`, `persist_discovery_proposals` |
| S2 scoring inputs | Yes | Comparable selected fields form one business score: matched/comparable × 100, worth 20% of final score; no comparable values defaults to 50 | Indirectly | Selection mismatch alone: no | Yes | `_field_matches`, `evaluate_candidate` |
| S3 GF4 signed evidence | Yes | Every proposal is rescored with the persisted fields and current-product discovery mode; selected matches/mismatches can move the edge between support tiers | Yes | Only field-independent hard rules/technical contradictions; not merely because a field is selected | Yes | `DeterministicIdentityContext`, `evaluate_canonical_identity_relationship`, `classify_identity_edge` |
| S4 GF5 family/work-unit inputs | Indirectly, and directly for targeted checks | Neighborhoods and GF4 edges carry prior effects. Targeted evaluator reloads persisted fields and the external scan mode | Yes | HSN/category/technical conflicts can create cannot-link; Site/UOM do not create cannot-link in the present Group-First contract | Yes | `_resolution_input`, `CanonicalEvaluatorTargetedEvidenceProvider` |
| S5 candidate partitions | No direct read | Candidate groups are derived from the affected edge lookup; selected fields can therefore change feasible partitions/objectives | Yes | Derived cannot-links veto partitions | Derived | `_candidate_groups`, `_select_partition` |
| S6 selected groups | No direct read | Selected partition is persisted | Yes | Derived only | Derived | `_build_group`, `_select_partition` |
| S7 conflicts | No direct read | Derived from protected cannot-links/constraints | Yes | Derived only | No | `_protected_conflict`, resolution persistence |
| S8 deferred | No direct read | Missing/ambiguous/exhausted outcomes can differ because proposals and evidence differ | Yes | No | No | `resolve_identity_groups` |
| S9 unassigned | No direct read | Complement of accepted group members | Yes | No | No | `resolve_identity_groups` |
| S10 projection/export | No semantic read | Projects the already-selected G2-v2 membership and all canonical business fields; checkbox selection does not hide/show columns | No new change | No | No | `build_and_persist_g2_v2_projection`, `IdentityReadService`, XLSX/CSV export services |

The proven historical and diagnostic runs first diverge at S1 because the
selected list changes the standard blocking relation set and the immutable
discovery configuration/fingerprint. Threshold also changes which
above-threshold standard pairs are excluded from hybrid retrieval, which can
change channel provenance and bounded hybrid selection. Threshold does not
filter all Group-First proposals or GF4 edges: `CG-000010` contains several
proposal edges scored 74.35 under threshold 75.

## 6. Semantics of every exposed checkbox

Legend: `C` candidate retrieval key, `D` supporting evidence, `E` negative
evidence, `F` threshold/scoring input, `B*` hard mismatch rule independent of
checkbox selection. Every field is cataloged and exported whether selected or
not; selection itself has no projection/display role.

| UI label / key | Selected-field roles | Specialized behavior independent of selection | GF4/GF5 result |
|---|---|---|---|
| Site / `CONTRACT` | C, D, E, F | Requested same-site mode hard-blocks legacy scoring/retrieval; current-product GF2-GF4 deliberately uses `DISCOVERY`. Site remains a hybrid context/anchor-boundary signal. | Cross-site selected-field mismatch lowers business score. It is not a cannot-link; targeted same-site checks become `NON_GROUPABLE/CROSS_SITE_SCOPE_ONLY`. |
| Purchase Type / `TYPE_CODE` | C, D, E, F | A type mismatch can downgrade otherwise-strong lexical trust as `CROSS_FIELD_IDENTITY_INCOHERENCE`. | No hard mismatch/cannot-link solely for type. |
| Inventory UOM / `UNIT_MEAS` | C, D, E, F | UOM relationship, mapping quality, penalty and tier affect hybrid ranking. Legacy scoring hard-rejects mismatch, but Group-First identity evaluation sets `allow_uom_mapping_review=True`. | Mismatch can lower score/priority and remains mapping context; it is not identity authority or a current cannot-link. |
| Com Group 01 / `PRIME_COMMODITY` | C, D, E, F | None beyond explanation text | Soft selected business evidence only. |
| Com Group 02 / `SECOND_COMMODITY` | C, D, E, F | None beyond explanation text | Soft selected business evidence only. |
| Safety Code / `HAZARD_CODE` | C, D, E, F | `STRICT_MISMATCH_FIELDS` can produce strict-sounding explanation text, but no hard business rule enforces it. | Soft selected business evidence; no cannot-link. The explanation wording is stronger than the rule decision. |
| Accounting Group / `ACCOUNTING_GROUP` | C, D, E, F | None | Soft selected business evidence only. |
| Product Code / `PART_PRODUCT_CODE` | C, D, E, F | None beyond explanation text | Soft selected business evidence only. |
| Product Family / `PART_PRODUCT_FAMILY` | C, D, E, F | Distinct part-number-family retrieval is derived from part numbers, not from this checkbox | Soft selected business evidence only. |
| Product Category / `PRODUCT_CATEGORY_ID` | C, D, E, F, B* | Any nonblank case-insensitive mismatch is a hard `REJECT`, independent of selection | Proposed mismatches become `CANNOT_LINK/IDENTITY_RULE_PRODUCT_CATEGORY_ID_MISMATCH`. |
| HSN/SAC Code / `HSN_SAC_CODE` | C, D, E, F, B* | Any nonblank case-insensitive mismatch is `DATA_CONFLICT`, independent of selection | Proposed mismatches become `CANNOT_LINK/IDENTITY_RULE_HSN_SAC_CODE_MISMATCH`. |

There is no `UI_OPTION_WITH_NO_EFFECT`: every checkbox affects standard
blocking and scoring when its canonical column is usable. Most are wired
identically. HSN/SAC, Product Category, Site, Inventory UOM, and Purchase Type
also have the independent special cases above.

Standard S1 grouping uses pandas equality on raw column values and is therefore
case-sensitive (`PCS` and `pcs` can occupy different standard blocks). Pair
scoring and the hard rules trim and compare case-insensitively. Hybrid UOM
classification also treats the `PCS`/`pcs` values in `CG-000010` consistently.

## 7. CONTRACT / Site deep dive

### Controlling path

1. Selecting Site adds `CONTRACT` to the standard composite group key.
2. Equality adds selected-field business support; mismatch subtracts that share
   of the 20% business component.
3. `evaluate_hard_business_rules` would hard-block a contract mismatch when its
   input mode is `SAME_SITE_DUPLICATE`, regardless of checkbox selection.
4. For `product_authority=current_product`, orchestration maps the requested
   mode to `group_first_primary` and
   `identity_discovery_scan_mode_for_orchestration` returns `DISCOVERY`.
5. GF2 hybrid eligibility and GF4 evaluation therefore do not apply the
   same-site rejection. Cross-site hybrid proposals require an
   `EXACT_DESCRIPTION` or `PART_NUMBER_FAMILY` anchor; weak channels alone
   cannot create them.
6. GF5 targeted evidence uses the saved external scan mode. A contract mismatch
   then returns `CROSS_SITE`, but `classify_identity_edge` explicitly excludes
   `CONTRACT` from affirmative identity mismatch groups and emits
   `NON_GROUPABLE/CROSS_SITE_SCOPE_ONLY`, not `CANNOT_LINK`.
7. GF5 vetoes a group on cannot-link, not on every non-groupable relationship.
   A sufficiently cohesive review partition may therefore span sites.

Explicit answers for the authoritative current-product path:

| Question | Answer | Evidence |
|---|---|---|
| Can different CONTRACT values enter one S1 relationship? | Yes | Hybrid site-neutral `DISCOVERY` allows bounded cross-site exact-description/part-family anchored proposals; `CG-000010` has seven. |
| Can they enter the same GF4 family/neighborhood? | Yes | GF4 uses the same `DISCOVERY` context; all seven real proposals became `REVIEW_SUPPORT`. |
| Can they enter one GF5 candidate partition? | Yes | Contract mismatch is explicitly non-identity context and is not a cannot-link. |
| Can they appear in one final suggested group? | Yes | `CG-000010` is persisted G2-v2 proof. |

For `legacy_compatibility`, the requested same-site mode is preserved and the
hard boundary remains. The checkbox itself is still not what creates that
boundary; scan mode does.

## 8. UNIT_MEAS / Inventory UOM deep dive

Selecting Inventory UOM adds raw `UNIT_MEAS` to standard composite blocking and
to the equal-weight selected business score. Score comparisons are trimmed and
case-insensitive. Hybrid retrieval always classifies the UOM relation and uses
its penalty/mapping quality in ranking, even when the checkbox is off.

The legacy pair path rejects a nonblank UOM mismatch independently of selection.
The current Group-First identity path deliberately passes
`allow_uom_mapping_review=True` in hybrid post-scoring and canonical GF4/targeted
evaluation. Its persisted UOM context says `identity_authority=false`.
`classify_identity_edge` also excludes `UNIT_MEAS` from identity cannot-links;
an otherwise unsupported mismatch becomes `NON_GROUPABLE/UOM_MAPPING_ONLY`.
Accordingly, selected Inventory UOM is not a hard final-membership condition.

This audit concerns the canonical Inventory UOM field only. No Purchase UOM or
Sales UOM checkbox, canonical field, or behavior exists in this branch, and no
omitted development-branch behavior was inferred.

## 9. Controlled four-case fixture

The diagnostic fixture is
`backend/tests/test_duplicate_checking_conditions_semantics_audit.py`. It uses
four rows with one description, unique part numbers, A/B/D at ST001, C at ST002,
A/B/C in PCS, and D in KG. All cases use threshold 75,
`SAME_SITE_DUPLICATE`, current Group-First authority, local deterministic
retrieval, and provider guards that fail the test if called.

Hybrid exact-description discovery filled the relations omitted by each
standard block, so all four cases produced S1 pairs AB, AC, AD, BC, BD, and CD.
That does not make the selections inert: their GF4 scores changed exactly as
the 20% selected-field component specifies.

| Case | AB | AC | AD | BC | BD | CD |
|---|---:|---:|---:|---:|---:|---:|
| `[]` | 85.71 | 85.71 | 85.71 | 85.71 | 85.71 | 85.71 |
| `[CONTRACT]` | 95.71 | 75.71 | 95.71 | 75.71 | 95.71 | 75.71 |
| `[UNIT_MEAS]` | 95.71 | 95.71 | 75.71 | 95.71 | 75.71 | 75.71 |
| `[CONTRACT, UNIT_MEAS]` | 95.71 | 85.71 | 85.71 | 85.71 | 85.71 | 75.71 |

All 24 case/pair edges were `REVIEW_SUPPORT`; no selected mismatch became a
cannot-link. Each GF5 run explored 96 candidate partitions. Symmetric
review-only alternatives produced `UNRESOLVED_OWNERSHIP_AMBIGUITY`, so no group
was selected and A-D remained unassigned in every case. This is a valid
controlled result: selected fields changed evidence scores but did not create
hard equality or force final grouping.

Focused verification: `1 passed`, provider calls 0.

## 10. `CG-000010` end-to-end trace

The authoritative API for live scan 23 returned 158 G2-v2 groups. XLSX labels
are assigned by enumerating the authority-selected snapshot sorted by canonical
group reference, so offset 9 is `CG-000010`. Its canonical reference is
`g2v2-group-0d6949f9ae68dc0ae4cafa60efdc2a42c0a0d7785a7eb9059b166e6494a5621b`.

Scan 23 persisted:

```text
selected_fields = ["CONTRACT", "UNIT_MEAS"]
threshold = 75
scan_mode = SAME_SITE_DUPLICATE
orchestration = group_first_primary
GF2/GF4 effective scan_mode = DISCOVERY
provider_request_count = 0
```

The five canonical members are:

| Member | Source row | Part number | Description | CONTRACT | UNIT_MEAS | Type | Other exposed fields |
|---|---:|---|---|---|---|---|---|
| A | 2360 | `RR-PART-003` | `RR-PART-003` | ST013 | PCS | Manufactured | null |
| B | 2361 | `EA-PART-003` | `EA-PART-003` | ST007 | PCS | Manufactured | null |
| C | 2365 | `SD-PART003` | `SD-PART003` | ST004 | `pcs` | Manufactured | null |
| D | 2395 | `JP-PART-003` | `JP-PART-003` | ST011 | PCS | Manufactured | null |
| E | 2396 | `SA-PART-003` | `SA-PART-003` | ST012 | PCS | Manufactured | null |

Site values are read directly from canonical records; the XLSX did not replace
or corrupt them. The lower-case ST004 UOM is equivalent in case-insensitive
scoring/UOM classification but is preserved for display.

Seven S1 cross-site proposals connected the group:

| Pair | Proposal channels | GF4 score | GF4 class |
|---|---|---:|---|
| A-B | character, lexical, part-number family, technical identity | 74.35 | `REVIEW_SUPPORT` |
| A-C | character, lexical, part-number family, technical identity | 74.35 | `REVIEW_SUPPORT` |
| B-C | character, lexical, part-number family, technical identity | 74.35 | `REVIEW_SUPPORT` |
| B-D | character, lexical, part-number family, technical identity | 74.35 | `REVIEW_SUPPORT` |
| B-E | character, lexical, part-number family, technical identity | 76.92 | `REVIEW_SUPPORT` |
| C-D | character, lexical, part-number family, technical identity | 74.35 | `REVIEW_SUPPORT` |
| C-E | character, lexical, part-number family, technical identity | 76.51 | `REVIEW_SUPPORT` |

Every proposal records `CROSS_SITE_SCOPE` and `SCAN_MODE_DISCOVERY`. The
part-number-family channel is the bounded cross-site anchor; the other channels
enrich provenance. In GF4, UOM matched, CONTRACT mismatched, so the two selected
fields yielded a 50% business score. The effective `DISCOVERY` mode prevented a
site hard rejection. Empty HSN/category fields created no protected conflict.

The three initially missing pairs A-D, A-E, and D-E were requested as GF5
`BRIDGE_CROSS_CHECK`s. Because targeted evaluation uses the persisted external
same-site mode, all three became `NON_GROUPABLE` with
`CROSS_SITE_SCOPE_ONLY`. They did not become cannot-links.

GF5 evaluated all 10 possible relationships: seven review support, three
non-groupable, zero strong support, zero cannot-link, and zero missing. The
positive graph is connected without an unresolved articulation/branch risk.
Seven positive edges exceed the chain-only-with-neutral-gaps guard for five
members. The selected complete-pairwise partition therefore became a five-row
`POSSIBLE_DUPLICATE_GROUP_REVIEW`, with support density 0.7. G2-v2 and the XLSX
faithfully projected that membership.

The exact point where cross-site membership becomes possible is the
Group-First orchestration conversion from requested `SAME_SITE_DUPLICATE` to
GF2-GF4 `DISCOVERY`. The later decisive point is the edge classifier's treatment
of contract mismatch as non-identity `NON_GROUPABLE`, rather than a GF5-vetoing
`CANNOT_LINK`.

Classification of the special case: **`CORRECT_BY_DESIGN` plus
`UI_SEMANTICS_MISMATCH`**. The numbered causes are not mutually exclusive in
the evidence: implementation behavior is intentionally correct, while the
visible wording overstates it. `HISTORICAL_REQUEST_MISATTRIBUTION` and
`OUTPUT_PROJECTION_DEFECT` are disproved.

## 11. Actual vs intended semantics

### `ACTUAL_IMPLEMENTATION_SEMANTICS`

Selected conditions are soft, equal-weight retrieval-and-evidence inputs, not
general final-group constraints. Standard discovery uses their equality as a
composite block. GF4 scoring rewards matches and penalizes mismatches. Any hard
field rule is separately coded and generally independent of checkbox state.
Current-product physical-identity discovery is site-neutral and treats UOM as
mapping context; final review groups may span selected Site/UOM values if their
overall evidence satisfies GF5 and no cannot-link exists.

### `PROVEN_INTENDED_SEMANTICS`

The original technical architecture documents selected fields as standard
candidate grouping keys and as the 20% business-field score. It does not state
that checking a field is a final group equality constraint.

Commit `58ff90450338a6806f3c508135d6e798d431d653` (“Allow cross-site identity
discovery”), its architecture doc, and `test_iqr1a_cross_site_discovery.py`
explicitly require current-product GF2-GF4 to be site-neutral while preserving
legacy scan-mode behavior. They also prove that cross-site discovery must have
an exact-description or part-number-family anchor and that site-neutrality
alone is not support. Thus the behavior that explains `CG-000010` is intentional
repository architecture, not an accidental missing check.

No source attributes the checkbox or cross-site policy to a Senior Functional
Consultant or another business requester. The code/commit origin is proven; the
business-request origin is `ORIGIN_NOT_PROVEN`.

Evidence classification:

| Evidence | Classification |
|---|---|
| `NewScan.jsx` labels and helper copy | UI_LABEL_ONLY |
| `candidate_generator.py`, `decision_engine.py`, `scan_runner.py`, `identity_edge.py` | IMPLEMENTATION |
| `test_iqr1a_cross_site_discovery.py` | TEST_CONTRACT |
| `IQR1A_CROSS_SITE_DISCOVERY_BOUNDARY_CORRECTION.md` and Group-First roadmap | ARCHITECTURE_DECISION |
| Technical architecture candidate/scoring sections | DOCUMENTED_PRODUCT_INTENT for standard blocking/scoring |
| Commit/blame history | Proven repository change origin, not proof of business requester |

## 12. UI accuracy and demo risk

A reasonable user seeing “Same-site duplicate scan”, “Same-site mode is
strict”, and a checked Site under “Duplicate-checking conditions” would expect
every suggested group member to have the same site. The authoritative
current-product output demonstrably does not enforce that expectation.

`SAME_SITE_DUPLICATE` is accurate for the persisted requested scope and the
legacy compatibility scorer, but not as a description of authoritative
Group-First physical-identity membership. “Duplicate-checking conditions” is
also inaccurate because the controls are standard blocking and scoring fields,
not universal must-match conditions. The “Review strictness” threshold copy is
similarly broader than its actual Group-First effect: it is not a global GF4 or
final-group cutoff.

The output is a review suggestion, not an automatic merge, and its detailed
evidence is truthful. Nevertheless, the setup screen makes a material hard
boundary promise that the result violates. Under the audit's safety rule, this
is `DEMO_BLOCKED_UNTIL_CONDITION_SEMANTICS_FIXED` even though the engine behavior
is correct by design.

## 13. Smallest recommended correction

Perform one UI-copy-only task: rename **Duplicate-checking conditions** to
**Candidate discovery and scoring fields**, and replace the same-site helper
with explicit text that current-product identity review can surface bounded
cross-site candidates and that Site/UOM selections are not must-match final
group constraints. Include a focused frontend copy test.

Do not change retrieval, GF4, GF5, cannot-links, thresholds, scan mode storage,
schema, or exports in that task. If product stakeholders instead want a hard
same-site final-group promise, that is a separate policy decision and engine
change, not a wording fix.

## 14. Safety and verification

- Production behavior and frontend copy were not changed.
- Only this report and the diagnostic test fixture were added.
- Provider calls: 0.
- Protected workbook: untouched and uninspected.
- `.env` and secrets: untouched and uninspected.
- No push, amend, reset, rebase, tag change, or destructive cleanup occurred.
