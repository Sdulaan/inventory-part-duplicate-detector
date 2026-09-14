# Hard-coded assumption audit: portability before LLM

## Classification

`HARD_CODED_ASSUMPTION_AUDIT_COMPLETE`

Baseline: `d5ce659f8ad41ab906ec238308c0e214ed8433e7` on
`llm-assisted-mvp`. Provider calls: **0**.

This is a code and architecture audit only. No runtime behavior, threshold,
schema, frontend, XLSX, configuration, or LLM integration was changed.

## Executive summary

The counts below use 38 top-level assumption families. Entries inside an alias
family inherit that family's classification and are not double-counted.

| Required classification | Count |
|---|---:|
| `KEEP_IN_CODE` | 16 |
| `MOVE_TO_SIMPLE_CONFIG` | 11 |
| `POSSIBLE_LLM_SEMANTIC_CASE` | 3 |
| `LEAVE_UNTIL_REAL_CLIENT_REQUIREMENT` | 8 |

Runtime test/data leakage findings: **0**. High portability risks: **7**. There
are no P0 correctness or safety defects.

The portability risk is not the deterministic architecture. It is the spread of
domain vocabulary across normalization, retrieval, genericity, object/variant
recognition, functional-role extraction, UOM aliases, and source-column aliases.
Several tables are demonstrably development-domain-specific. In particular,
global `co -> coconut` and `a -> amp` expansion, substring expansion of short
part-code fragments, and the small object-incompatibility ontology can alter
candidate discovery or protected evidence for another client's vocabulary.

The correct next move is a small, versioned reference-data boundary for only the
clearly semantic aliases. It is not a policy engine and it is not LLM work.

## Runtime alias and expansion inventory

Every source token below is shown explicitly. “Tests” identifies direct or
material indirect coverage, not proof that the meaning is universal.

| Map / file | Source token -> target meaning | Runtime scope and effect | Tests | Generality evidence | Portability risk | Classification |
|---|---|---|---|---|---|---|
| `DOMAIN_TOKEN_MAP`, `domain_dictionary.py` | `dec`, `desicated`, `decicated`, `decicatted` -> `desiccated`; `coco`, `co` -> `coconut`; `c01`, `co1` -> `type 1`; `c02`, `co2` -> `type 2`; `flt`, `filt` -> `filter`; `gen` -> `generator`; `hvac` -> `hvac`; `ss` -> `stainless steel`; `stl` -> `steel`; `bat` -> `battery`; `temp` -> `temperature`; `press` -> `pressure` | Global description and part-number normalization; changes similarity, retrieval, technical evidence, and cache keys | `test_normalizer.py`, scoring/retrieval suites | Common engineering usage supports some entries; coconut/type entries are visibly dataset-derived | High: `co` and short codes are ambiguous across clients | `MOVE_TO_SIMPLE_CONFIG` |
| `SPELLING`, `normalizer.py` | `decicated`, `decicatted` -> `desiccated` | Global description correction before all semantic processing | `test_normalizer.py` | Current corpus evidence only | Medium | `MOVE_TO_SIMPLE_CONFIG` |
| `ABBREVIATIONS`, `normalizer.py` | `piece`, `pieces`, `pcs` -> `pcs`; `ss` -> `stainless steel`; `mcb` -> `miniature circuit breaker`; `cu` -> `copper`; `filtration`, `filtering` -> `filter`; `amp`, `amps`, `a` -> `amp` | Global description expansion; changes scoring and evidence | `test_normalizer.py`, `test_similarity.py`, `test_scoring.py` | Most are domain-conventional; bare `a` is not safely universal | High: ordinary article `a` becomes an electrical unit | `MOVE_TO_SIMPLE_CONFIG` |
| `_RETRIEVAL_ALIASES`, `hybrid_retrieval.py` | `mtr` -> `motor`; `brg` -> `bearing`; `de` -> `drive end`; `nde` -> `non drive end`; `assy` -> `assembly`; `bkt` -> `bracket`; `pnl` -> `panel`; `vlv` -> `valve` | Character retrieval text and embedding-cache identity; affects top-K/caps, not final authority directly | hybrid/character/determinism suites | Plausible industrial vocabulary; no cross-client proof | Medium | `MOVE_TO_SIMPLE_CONFIG` |
| `_PART_CODE_ALIASES`, `hybrid_retrieval.py` | `fp` -> `fuelpump`; `com` -> `compressor`; `stat` -> `stator`; `rot` -> `rotor`; `brg` -> `bearing`; `mtr` -> `motor`; `assy` -> `assembly`; `pnl` -> `panel` | Part-number family candidate generation | hybrid retrieval suites and benchmark fixtures | Development examples explain several values; universal meaning is not proven | High: aliases are also substituted inside any chunk of length >=5 | `MOVE_TO_SIMPLE_CONFIG` |
| `CONTEXT_MAP`, `application_context.py` | `gen`, `generator` -> `generator`; `hvac` -> `hvac`; `elec`, `electrical` -> `electrical`; `hyd`, `hydraulic` -> `hydraulic`; `pneu`, `pneumatic` -> `pneumatic`; `auto`, `veh`, `vehicle` -> `vehicle`; `pump` -> `pump`; `comp`, `compressor` -> `compressor` | Context mismatch can cap score at 78 and demote to Review | feature/scoring suites | Broad industrial domain, but token meanings are not universal (`comp`, `auto`) | Medium | `MOVE_TO_SIMPLE_CONFIG` |
| size/side/structure maps, `variant_extractor.py` | `xs` -> `extra small`; `xl` -> `extra large`; `lh` -> `left`; `rh` -> `right`; `comp` -> `component`; `assy` -> `assembly`; `sub` -> `subassembly`; identity spellings for `left/right/front/rear`, size words, and structural roles | Typed variant and structural-role extraction; can create mismatch or downgrade evidence | scoring, directional, signature, and GF4 suites | Common vocabulary, but applicability to an object class is not universal | High because recognized differences affect GF4 | `MOVE_TO_SIMPLE_CONFIG` |
| directional regex aliases, `identity_discriminator.py` | `left side`, `left hand`, `lh`, `l/h`, `l-h`, and bare part-number `left` -> `LEFT`; symmetric right forms -> `RIGHT` | Two-sided shared-base opposition creates protected identity contradiction | directional-side and contradiction suites | Semantic meaning is common; identity consequence depends on domain | High | `MOVE_TO_SIMPLE_CONFIG` |
| UOM aliases, `uom_relationship.py` | `pc`, `pcs`, `piece`, `pieces`, `ea`, `each`, `unit`, `units` -> piece/count; `l`, `lt`, `ltr`, `liter(s)`, `litre(s)` -> litre/volume; `ml`, `milliliter`, `millilitre` -> millilitre/volume; `gal`, `gallon(s)` -> gallon/volume; `qt`, `quart`, `liquid quart`, `liq qt` -> liquid-quart/volume; `m3` -> cubic-metre/volume; `kg`, `kilogram` -> kilogram/mass; `g`, `gram` -> gram/mass; `lb`, `lbs`, `pound` -> pound/mass; `m`, `meter`, `metre` -> metre/length; `cm` -> centimetre/length; `mm` -> millimetre/length; `box`, `pack`, `set`, `roll` -> corresponding package basis | UOM normalization, relationship, retrieval penalty, mapping context | UOM, scoring, GF4, and export suites | Standard units are broad; package semantics and abbreviations vary by ERP/client | Medium | `MOVE_TO_SIMPLE_CONFIG` |
| missing-UOM vocabulary, `uom_relationship.py` | empty, `*`, `-`, `--`, `n/a`, `na`, `n.a.`, `none`, `null`, `nil` -> missing/wildcard | Prevents malformed values being treated as a dimensional conflict | UOM/scoring suites | Common import conventions, not exhaustive | Low/medium | `MOVE_TO_SIMPLE_CONFIG` |
| source-column aliases, `core/constants.py` | `STOCK_REF`, `PART_NUMBER`, `ITEM_NO`, `ITEM_NUMBER` -> `PART_NO`; `ITEM_NARRATIVE`, `PART_DESCRIPTION`, `ITEM_DESCRIPTION` -> `DESCRIPTION`; `SITE`, `SITE_CODE`, `CONTRACT_CODE` -> `CONTRACT`; `PART_TYPE`, `PURCHASE_TYPE` -> `TYPE_CODE`; `INVENTORY_UOM`, `INVENTORY_UNIT_OF_MEASURE`, `UNIT_OF_MEASURE`, `UOM` -> `UNIT_MEAS`; `COMMODITY_GROUP_1`, `COM_GROUP_01`, `PRIMARY_COMMODITY` -> `PRIME_COMMODITY`; `COMMODITY_GROUP_2`, `COM_GROUP_02`, `SECONDARY_COMMODITY` -> `SECOND_COMMODITY`; `SAFETY_CODE` -> `HAZARD_CODE`; `PRODUCT_CODE` -> `PART_PRODUCT_CODE`; `PRODUCT_FAMILY` -> `PART_PRODUCT_FAMILY`; `PRODUCT_CATEGORY` -> `PRODUCT_CATEGORY_ID`; `HSN_CODE` -> `HSN_SAC_CODE`; `SAC_CODE` -> `HSN_SAC_CODE`; fallback `PART_DESCRIPTION_IN_USE`, `DESCRIPTION_IN_USE` -> `DESCRIPTION` | Automatic upload mapping; explicit per-upload mapping already overrides it and collisions fail closed | validation and real-CSV regression suites | ERP-oriented and clearly source-schema knowledge | Medium; mitigated by explicit mapping | `MOVE_TO_SIMPLE_CONFIG` |

Aliases clearly safe to retain as defaults once versioned include ordinary spelling
variants such as `pieces -> pcs`, `liters -> litre`, and `rh -> right`. Their
storage still belongs in simple reference data because they are semantic data,
not because the current meanings are known to be wrong.

Future unknown terms are not additions to these tables until a client/domain
owner validates them. They are candidates for bounded semantic interpretation
only when the five LLM suitability conditions below are met.

## Generic/noise vocabulary

| Set/rule | Effect | Assessment |
|---|---|---|
| `GENERIC_TERMS` in `generic_description_guard.py` | A matching one/two-token description blocks Strong support unless independent part-number evidence exists; may make GF4 Review/non-groupable | Domain nouns (`filter`, `pipe`, `sensor`, etc.) are reference knowledge: `MOVE_TO_SIMPLE_CONFIG` |
| `_GENERIC_DESCRIPTIONS` and `_GENERIC_TOKENS` in `hybrid_retrieval.py` | Reduce specificity, retrieval priority, tier, and cap survival | Includes corpus phrases such as `normal time` and `sales part`: `MOVE_TO_SIMPLE_CONFIG` |
| single alphabetic token rule | Treats every one-token alphabetic description as generic, while preserving alphanumeric model-like values | Calibrated safety heuristic; keep unchanged until real false-negative evidence: `LEAVE_UNTIL_REAL_CLIENT_REQUIREMENT` |
| corpus-frequency and IDF rules | Penalize descriptions appearing at least max(4, 2% of records), using bounded ratios | Dataset-adaptive algorithm rather than hard-coded vocabulary: `KEEP_IN_CODE` |
| signature `_UNRESOLVED_STOPWORDS` | Prevents common scaffolding words from being elevated as unresolved identity evidence | Low-impact bounded mechanism; `KEEP_IN_CODE` |

The vocabulary can reduce evidence, alter retrieval ranking, demote Strong, and
therefore affect GF5 inputs. It never directly overrides a human decision or a
cannot-link constraint.

## Detailed inventory

| ID | File / symbol | Current assumption | Type | Runtime impact | Evidence | Classification | Why / future action | Priority |
|---|---|---|---|---|---|---|---|---|
| K01 | `normalizer.py` normalization pipeline | NFK-like case/punctuation/whitespace and deterministic token normalization | Universal mechanism | All matching | Normalizer tests | `KEEP_IN_CODE` | Mechanics are product infrastructure; keep versioned | P3 |
| K02 | `_part_chunks`, model/type regexes | Alpha/numeric segmentation and bounded structural parsing | Universal mechanism | Retrieval/signatures | Retrieval/signature tests | `KEEP_IN_CODE` | Parsing is separate from token meaning | P3 |
| K03 | retrieval/GF5 ordering and fingerprints | Sorted canonical JSON, semantic keys, stable traversal | Audit invariant | Candidate/group reproducibility | Determinism review | `KEEP_IN_CODE` | Never make client-configurable | P3 |
| K04 | `decision_engine.py`, `similarity_model.py` | 60/20/10/10 composition and component weighting | Algorithm calibration | Pair scores/classes | Scoring tests and historical evaluation | `KEEP_IN_CODE` | Controlled engine calibration, not client policy | P2 |
| K05 | `description_specificity_statistics` | IDF, frequency, informative-ratio and length mechanics | Algorithm calibration | Retrieval rank/tier | Retrieval tests/benchmarks | `KEEP_IN_CODE` | Corpus-adaptive mechanism | P2 |
| K06 | confidence/status thresholds | 90/75/60 boundaries and 55/65/78/85 safety caps | Algorithm calibration | Candidate status/GF4 input | Scoring and quality suites | `KEEP_IN_CODE` | Do not expose as casual client settings | P2 |
| K07 | retrieval configurations | top-K, tier/family/global caps, fixed LSH seed/config, 2k/25k strategy switches | Operational/calibration | Bounded recall/runtime | Versioned contracts and scale evidence | `KEEP_IN_CODE` | Existing typed config/versioning is sufficient | P2 |
| K08 | `MAX_CANDIDATE_PAIRS=20_000` | Legacy pair-path safety bound | Operational limit | May truncate legacy proposals with warning | Candidate tests | `KEEP_IN_CODE` | Bounded execution invariant; deprecated path | P3 |
| K09 | GF4/GF5 cannot-link veto | Explicit protected/human conflict forbids accepted group | Safety invariant | Group acceptance | Resolver/edge suites | `KEEP_IN_CODE` | Never delegate or externalize | P3 |
| K10 | accepted membership uniqueness | A record cannot belong to two accepted groups | Safety invariant | Group acceptance | Resolver validation | `KEEP_IN_CODE` | Core identity integrity | P3 |
| K11 | GF5 objective and ambiguity policy | `(covered, likely, strong, -review, -groups)` with equal-best intersection/defer and bounded search | Product mechanism | Partition selection | Frozen-policy/determinism tests | `KEEP_IN_CODE` | Stable product mechanism, not semantic vocabulary | P2 |
| K12 | review service/authority adapters | Append-only human review overrides machine suggestions | Safety/authority invariant | Effective identity authority | Review/API/export tests | `KEEP_IN_CODE` | Human authority remains outside LLM | P3 |
| K13 | versions, provenance, fail-closed validation | Unknown/corrupt evidence is not promoted | Audit/safety invariant | All durable stages | Contract/persistence suites | `KEEP_IN_CODE` | Required for trustworthy operation | P3 |
| K14 | canonical internal field contract | Identity processing requires part number and description; stable canonical names internally | Product mechanism | Ingestion and all stages | Validation contract | `KEEP_IN_CODE` | Minimum product input, while source labels remain mappable | P2 |
| K15 | `apply_column_mapping` mechanics | Explicit mapping wins; ambiguity/collision fails closed | Universal schema mechanism | Ingestion | Real CSV/validation tests | `KEEP_IN_CODE` | Correct portability seam already exists | P3 |
| K16 | XLSX safety and authority contract | Formula-safe cells, advisory notice, human authority, technical references | Safety/presentation invariant | Export only | XLSX tests | `KEEP_IN_CODE` | Keep safety wording/mechanism; client styling is separate | P3 |
| M01 | `DOMAIN_TOKEN_MAP` | Global domain/spelling aliases including coconut/type codes | Domain knowledge | Retrieval/scoring/GF4 | Development corpus and normalizer tests | `MOVE_TO_SIMPLE_CONFIG` | Versioned reference data; remove no default without validation | P1 |
| M02 | `SPELLING`, `ABBREVIATIONS`, `UNITS` | Global lexical meanings including `a -> amp` | Domain knowledge | All normalized semantics | Normalizer tests; rationale otherwise `RATIONALE_NOT_PROVEN` | `MOVE_TO_SIMPLE_CONFIG` | Separate safe spelling from ambiguous semantic aliases | P1 |
| M03 | `_RETRIEVAL_ALIASES` | Industrial abbreviation expansion | Domain knowledge | Retrieval/cache keys | Retrieval tests | `MOVE_TO_SIMPLE_CONFIG` | Versioned retrieval alias section | P2 |
| M04 | `_PART_CODE_ALIASES`, `_expand_part_chunk` | Short part-code meanings and substring replacement | Domain/client knowledge | Candidate families/caps | Benchmark-derived examples | `MOVE_TO_SIMPLE_CONFIG` | Store exact aliases; separately constrain substring use | P1 |
| M05 | `CONTEXT_MAP` | Tokens imply generator/HVAC/electrical/etc. contexts | Domain knowledge | Score cap and Review demotion | Feature/scoring tests | `MOVE_TO_SIMPLE_CONFIG` | Small validated context vocabulary | P2 |
| M06 | generic term/phrase sets | Named nouns/phrases are weak identity evidence | Domain knowledge | Ranking and Strong suppression | R18C/generic tests | `MOVE_TO_SIMPLE_CONFIG` | Versioned generic vocabulary | P1 |
| M07 | object class and incompatibility tables | Small noun ontology and mutually exclusive pairs | Domain knowledge | Protected GF4 contradiction/cannot-link | R7/R9/R11 recovery tests; universality `RATIONALE_NOT_PROVEN` | `MOVE_TO_SIMPLE_CONFIG` | Highest-control reference data with provenance/version | P1 |
| M08 | functional location vocabulary | `head`/`tail` plus construct exclusions define one incompatible axis | Domain knowledge | Protected GF4 contradiction | IQR1B and Head/Tail tests | `MOVE_TO_SIMPLE_CONFIG` | Keep extractor mechanism; externalize axis vocabulary | P1 |
| M09 | variant/role vocabularies | Color, size, sensor, side, DE/NDE, serial, flow, engine and structural role terms | Domain knowledge | GF4 mismatch/demotion/signatures | Scoring/signature/directional suites | `MOVE_TO_SIMPLE_CONFIG` | Typed versioned vocabulary, not generic rules | P1 |
| M10 | UOM alias/missing tables | Unit spelling, dimensions, package basis, missing markers | Domain/reference knowledge | Penalties and mapping context | UOM/GF4 tests | `MOVE_TO_SIMPLE_CONFIG` | Small versioned unit reference | P2 |
| M11 | `FIELD_ALIASES`, fallbacks | IFS/ERP source headers map to canonical fields | Client/schema knowledge | Ingestion | Real CSV regression tests | `MOVE_TO_SIMPLE_CONFIG` | Built-in versioned mapping; retain explicit upload override | P2 |
| P01 | unresolved abbreviation path | Unknown engineering abbreviations remain lexical/unresolved | Unknown semantic language | Review evidence may lack explanation | Signature unresolved observations | `POSSIBLE_LLM_SEMANTIC_CASE` | LLM may suggest a typed meaning for review only | P2 |
| P02 | unknown object/variant relation | Unrecognized nouns or opposed variants receive no ontology fact | Unknown semantic language | Recall/explanation gap, not automatic decision | Bounded discriminator design | `POSSIBLE_LLM_SEMANTIC_CASE` | LLM may describe a possible semantic delta; no cannot-link | P2 |
| P03 | ambiguous model/role phrase | Unknown model/type/designation/function/location language remains unresolved | Unknown semantic language | Review support/explanation gap | Signature model/unresolved channels | `POSSIBLE_LLM_SEMANTIC_CASE` | Structured hypothesis only, requiring deterministic/human validation | P2 |
| L01 | same-part-number rule | Equal nonblank part number means same reference, not a duplicate candidate | Business assumption | Suppresses candidate | Business-rule tests | `LEAVE_UNTIL_REAL_CLIENT_REQUIREMENT` | Strong inventory convention; vary only with client evidence | P3 |
| L02 | scan modes/site handling | Contract is site; same/cross-site modes gate discovery | Client/business assumption | Candidate suppression/scope | IQR1A and mode tests | `LEAVE_UNTIL_REAL_CLIENT_REQUIREMENT` | Existing explicit modes are adequate | P3 |
| L03 | HSN/category significance | Two-sided HSN/category mismatch is identity-significant | Business assumption | GF4 cannot-link/non-groupable | Edge/scoring tests | `LEAVE_UNTIL_REAL_CLIENT_REQUIREMENT` | Do not generalize or relax without client semantics | P2 |
| L04 | UOM consequences and penalties | UOM differences affect legacy rules/retrieval but are not universal GF4 identity authority | Business/calibration | Candidate suppression/priority | UOM-decoupling tests | `LEAVE_UNTIL_REAL_CLIENT_REQUIREMENT` | Keep current bounded behavior until client evidence | P2 |
| L05 | selected-field and type significance | User-selected exact fields contribute 20%; TYPE_CODE disagreement can demote lexical Strong | Client/calibration | Score/trust | Scoring/R18C tests | `LEAVE_UNTIL_REAL_CLIENT_REQUIREMENT` | Already user-selectable in part; avoid a policy engine | P3 |
| L06 | one-sided qualifier policy | Certain one-sided qualifiers cap at 65 and stay non-Strong | Business/calibration | GF4 class | Variant/scoring tests | `LEAVE_UNTIL_REAL_CLIENT_REQUIREMENT` | Vocabulary should move; consequence stays frozen | P2 |
| L07 | single-alpha generic rule | One alphabetic token is generic even if absent from generic table | Algorithm calibration | Strong suppression | Bicycle/R18C tests | `LEAVE_UNTIL_REAL_CLIENT_REQUIREMENT` | Real model-code false negatives must be demonstrated first | P2 |
| L08 | XLSX names/colors/client phrasing | Five sheets, labels, colors, widths and concise wording are fixed | Presentation assumption | Export only | XLSX acceptance | `LEAVE_UNTIL_REAL_CLIENT_REQUIREMENT` | Safety notice stays; rest need not be themable yet | P3 |

## Part-number semantics

Generic structural mechanics—case normalization, separator removal, alpha/digit
splitting, and comparing residual segments—remain in code. Semantic meanings of
short fragments (`fp`, `com`, `stat`, `rot`, `brg`, `mtr`, `assy`, `pnl`) are
domain reference data. No production rule maps `M-` to Manufactured, `P-` to
Purchased, or another explicit commercial prefix meaning. The closest risk is
substring expansion inside any part chunk of length five or more; a coincidental
`com`/`rot`/`stat` sequence can be rewritten even when it is not a semantic code.

## Field, site, and semantic-role effects

| Signal | Read/normalize | Retrieval/scoring | Candidate suppression | Protected GF4/CANNOT_LINK |
|---|---|---|---|---|
| `PART_NO` | Yes | Similarity/family/model evidence | Equal part number suppressed | Can provide trusted class/side evidence |
| `DESCRIPTION` | Yes | Primary lexical, genericity, roles | Variant conflict can suppress hybrid | Explicit two-sided semantic conflict can become cannot-link |
| `CONTRACT`/site | Yes | Selected-field score/context | Yes, according to explicit scan mode | No; classified scope-only |
| `UNIT_MEAS` | Yes | Relationship penalty/context | Legacy path may reject; group path permits mapping review | No universal authority; excluded as identity mismatch |
| `TYPE_CODE` | Yes | Cross-field lexical trust | No direct retrieval suppression | May demote Strong, not create cannot-link |
| `HSN_SAC_CODE` | Yes | Hard-rule evidence | Yes | Two-sided mismatch is identity-significant |
| `PRODUCT_CATEGORY_ID` | Yes | Hard-rule evidence | Yes | Two-sided mismatch is identity-significant |
| commodity/product/account fields | Yes | Selected-field exact signal if chosen | Standard blocking may use selected field | No direct cannot-link rule |
| master/type/designation/dimension fields | Signature seam only | Shadow signed evidence when supplied | No current canonical scan discovery effect | No direct current authority |

The role-extraction mechanism is generic and stays in code. Its vocabularies—DE
versus NDE, inlet versus outlet, engine block/head/piston/fuel-pump, structural
roles, left/right, and Head/Tail functional facets—are domain data and should be
versioned separately. Semantic meaning and identity consequence remain distinct:
recognizing `LH` as left is reference interpretation; deciding that left versus
right on a shared component base is incompatible remains a frozen, reviewed
deterministic rule until client evidence supports change.

## Thresholds and caps

| Family | Current examples | Type | Classification |
|---|---|---|---|
| Pair status/calibration | 90/75/60 statuses; 60/20/10/10 score mix; 90 strong part-number rescue; 80 coherence floor | Engine calibration | `KEEP_IN_CODE` |
| Safety demotions | mismatch 55, one-sided 65, context 78, structural role 85, generic max 65 | Engine calibration | `KEEP_IN_CODE` or consequence `LEAVE_UNTIL_REAL_CLIENT_REQUIREMENT`; not client-editable now |
| Retrieval budgets | lexical/vector top-K 5, final per-record 10, global 500, tier 250/200/50, family 25 | Operational/calibrated typed config | `KEEP_IN_CODE` |
| Strategy limits | character LSH at 2,000; bounded lexical at 25,000; fixed seed and pool/probe limits | Operational algorithm | `KEEP_IN_CODE` |
| GF5 bounds | max members 20, targeted checks 40, complete-pairwise limit 8 | Operational safety/calibration | `KEEP_IN_CODE` |
| Upload/runtime bounds | 50 MiB, 100,000 CSV rows, 20,000 legacy pairs | Operational safety | `KEEP_IN_CODE` |

These values can alter semantics through bounded truncation, but they are
versioned engine/operational parameters with warnings or deferral. That does not
make them LLM cases or justify arbitrary client editing.

## Development-dataset and demo leakage search

Runtime semantic code contains development-influenced vocabulary (`coconut`,
`normal time`, `circuit board`, bounded object pairs, Head/Tail, and engineering
abbreviations). Those are counted above as domain/reference portability risks,
not test leakage.

Known row IDs, scan IDs, Bicycle fixture construction, known group labels, and
sealed evaluation cases occur only in benchmark/diagnostic modules. The
`hybrid_retrieval_benchmark.py` silver pairs and `load_test_service.py` synthetic
MCB/coconut/site rows are isolated benchmark/load-test inputs; normal scan code
does not import them. Production modules do not import tests, demo CSVs,
evaluation artifacts, known source rows, or historical scan IDs.

```text
POTENTIAL_RUNTIME_TEST_LEAK findings: 0
```

## Top portability risks

1. Global ambiguous normalization aliases, especially `co -> coconut` and
   `a -> amp`, can change unrelated client text before every downstream stage.
2. Short part-code aliases are substituted inside longer chunks, so accidental
   substrings can alter family retrieval.
3. The bounded object-class incompatibility table can create protected GF4
   contradictions; its meanings are test-supported but not universally proven.
4. Variant and directional vocabularies can create critical mismatches and
   cannot-links when the same words have another client-specific use.
5. Generic/noise terms can demote Strong and alter capped retrieval.
6. Head/Tail functional-location vocabulary encodes one specific incompatible
   axis even though the extraction mechanism is general.
7. UOM and automatic ERP header aliases are incomplete client/domain reference
   data, although explicit upload mapping mitigates schema risk.

## Things explicitly not worth abstracting now

- whitespace, case, punctuation, stable serialization, and tokenization mechanics;
- scan-independent ordering and deterministic fingerprints;
- cannot-link enforcement and disjoint accepted membership;
- the GF5 objective, ambiguity handling, graph traversal, and fail-closed bounds;
- human-review authority and append-only review history;
- audit provenance, contract versions, and persistence validation;
- similarity algorithms and calibrated thresholds merely to make them editable;
- top-K/caps/strategy switches already represented as controlled engine config;
- dynamic site, part-type, UOM, object-type, or field-importance policy engines;
- XLSX formula safety and the advisory/not-an-automatic-merge notice;
- provider use for schema mapping, threshold tuning, caps, integrity, or authority.

## LLM semantic opportunities

All three cases satisfy the required test: the unknown is linguistic; universal
normalization cannot safely resolve it; no validated fixed alias exists yet; a
typed interpretation could help review; and raw output has no identity authority.

| Unknown semantic input | Minimal context | Expected structured interpretation | Why config may not initially suffice | Authority boundary |
|---|---|---|---|---|
| Unknown engineering abbreviation | Token, containing field, nearby normalized words, optional client/domain identifier | Candidate long form, semantic category, ambiguity flag, evidence span | Meaning may be contextual or polysemous before client validation | Suggestion shown to reviewer; no score/GF4/GF5 mutation |
| Unrecognized semantic delta between otherwise related records | Two bounded descriptions/part numbers plus deterministic similarities and recognized attributes | Typed possible relation: variant, model, role, object, or unresolved; cited differing spans | Novel terminology may have no existing alias or ontology entry | Never emits cannot-link or duplicate decision; human/deterministic validation required |
| Ambiguous model/designation/function/location phrase | Bounded source fields and unresolved signature observations | Candidate semantic role/value, normalized phrase, confidence category, unresolved alternatives | Phrase structure can be domain-specific and compositional | Advisory evidence only; cannot override protected conflicts or human review |

## Prior review observations carried forward

1. The determinism acceptance JSON lacks commit/input/config/version
   fingerprints and separate per-run stage arrays.
2. The opening determinism summaries in `PROJECT_SSOT.md` and
   `docs/CURRENT_PROJECT_ASSESSMENT.md` do not repeat all four claim bounds in
   place.

These remain observations and do not change this audit outcome.

## Verification and next task

Targeted characterization ran the normalization, similarity, retrieval,
candidate-feature, scoring, GF4, signature, site, functional-location,
directional/object-discriminator, real-CSV mapping, GF5, review, and XLSX suites:
**435 passed** with one pre-existing unknown pytest-option warning. Provider
calls were zero.

No current identity behavior needs to change before LLM work. The vocabulary
boundary should be made explicit first, behavior-preservingly, so known validated
aliases are not confused with genuinely unknown semantic cases.

Selected next-task decision:

```text
A. move only clearly dataset/domain-specific aliases to simple config
```

Smallest recommended implementation: move only `DOMAIN_TOKEN_MAP`, `SPELLING`,
and `ABBREVIATIONS` into one versioned, schema-validated JSON reference file,
load the same defaults deterministically, preserve exact current outputs, add a
configuration fingerprint, and add tests that prove no score/GF4/GF5 behavior
changes. Do not include thresholds, GF5 policy, site policy, UOM consequences,
object incompatibility, or any provider integration in that first step.

## Follow-up completed: core semantic aliases externalized

The selected next task is complete with classification
`SEMANTIC_ALIAS_CONFIG_MIGRATION_VERIFIED`. The three named maps now have one
authoritative packaged JSON source at
`backend/app/reference_data/semantic_aliases.v1.json`, schema version 1,
reference version `semantic-aliases-v1`, and canonical logical SHA-256
`0484679a78e61b2f3564c40ca7ef7f7d2b69c1a98e24d24ecdedf65eccdc4367`.
The loader validates strictly, rejects duplicate keys, fails closed, and
exports immutable mappings. All alias values and behavior are unchanged.

The remaining audit rows retain their original classifications. In particular,
generic/noise vocabularies, other retrieval and part-code aliases, object and
directional vocabularies, UOM/schema aliases, thresholds/caps, GF4/GF5 policy,
review semantics, and possible future advisory LLM cases were not moved or
modified. See `SEMANTIC_ALIAS_REFERENCE_MIGRATION.md`.
