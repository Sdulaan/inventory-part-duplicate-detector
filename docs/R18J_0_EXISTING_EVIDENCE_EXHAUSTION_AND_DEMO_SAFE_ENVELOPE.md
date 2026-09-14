# R18J-0 existing-evidence exhaustion and demo-safe envelope

## Productization follow-through

The authorized follow-through is complete with classification
`DEMO_SAFE_PRODUCTIZATION_READY_FOR_REHEARSAL`. Because R18J-0 found no safe
source-visible discriminator, no detector correction was made. Instead, the
UI and exports now apply a deterministic advisory presentation mapping:
unreviewed groups are `Potential Same-Identity Group` / `Requires Human Review`,
and human Confirm, Reject, or Defer states become the visible authority. The
bounded XLSX uses `Summary`, `Candidate Groups`, and `Group Data` and makes the
authority split explicit without changing membership. Curated walkthrough data
must be labelled; real data remains unvalidated candidate output. No unsupported
accuracy/probability/confidence claim was added, runtime and GF5 remain
unchanged, provider calls are 0, and `NEXT = FINAL_DEMO_REHEARSAL`.

Classification: `R18J_0_NO_SAFE_SOURCE_VISIBLE_DISCRIMINATOR`

Next: `DEMO_SAFE_PRODUCTIZATION_WITHOUT_ACCURACY_OVERCLAIM`

## Baseline and scope

R18J-0 began from commit
`547abb4695095b6c6dca71303e297350d4095ec7` on `llm-assisted-mvp`.
The protected `deterministic-demo-v1` tag remained at
`d510cf3c18b3a8448d0f79be3e59c398efb32eae`. This task reconciles and
analyzes existing human evidence only. Runtime detector, GF4, R18C, GF5, GF6,
persistence, API, UI, XLSX, and presentation behavior are unchanged. No new
human workbook was created, no provider was called, and provider calls were 0.

## Evidence exhausted and claim limits

The deterministic analysis read all authorized existing sources:

| Source | Human evidence | Use in R18J-0 |
|---|---:|---|
| R18 Senior pair reference | 316 judgments | direct pair labels; all rows reconciled |
| R18 Evaluation panel | 300 memberships | subset marker, never double-counted |
| R18G Development group review | 48 judgments | unambiguous two-member Strong pairs mapped |
| R18G targeted partition review | 2 groups / 9 assignments | within-partition SAME and cross-partition DIFFERENT pairs mapped where currently Strong |
| R18G consumed holdout | 16 judgments | unambiguous two-member Strong pairs mapped diagnostically |
| R18I diagnostic cases | 6 failed + 2 accepted Likely | joined as duplicate observations, not new labels |

All 316 R18 rows, 48 Development groups, two targeted groups, 16 consumed
holdout groups, and eight R18I cases were reconciled before selecting pairs that
map unambiguously to the frozen post-R18C/current Strong state. Multi-member
group judgments without an explicit partition were not invented as pair
labels. Development evidence is not independent validation, the consumed
holdout is diagnostic only, and no old human label is called production truth.

## Unified Strong-pair matrix

There are 67 source observations and 53 canonical Strong pairs after stable
member-reference deduplication:

| Reconciled human result | Canonical pairs |
|---|---:|
| SAME | 40 |
| DIFFERENT | 10 |
| conflicting labels across review rounds | 3 |
| **Total** | **53** |

The three conflicts are material evidence against fitting a certainty rule:

| Pair | Earlier/later judgments | Interpretation |
|---|---|---|
| JD-SERIAL / JD-SERIAL-2 | R18 SAME; consumed holdout DIFFERENT | later judgment explicitly depends on business serial conventions absent from input |
| NE01-MODEL-S / NE01-MODEL-X | R18 SAME; Development group DIFFERENT | same Senior evidence supports opposite conclusions in different review contexts |
| HP-FIFO / HP-FIFO-02 | R18 SAME; consumed holdout DIFFERENT | generic description and suffix meaning remain ambiguous |

Conflicting pairs remain `CONFLICTING_HUMAN_LABELS` and are excluded from both
SAME-harm and DIFFERENT-catch counts. Neither observation is overwritten.

The ignored unified CSV includes all available source fields, Senior labels and
comments, canonical fingerprint, score components, GF4/provenance/R18C state,
LexicalTrustAssessment and technical evidence, residuals, signature
completeness, UOM/type/site comparisons, and group/status context. Unavailable
master-description and dimension/quality values remain empty rather than being
invented.

## DIFFERENT Strong source-visibility breakdown

| Causal availability | All DIFFERENT Strong | Meaning |
|---|---:|---|
| `SOURCE_VISIBLE_ACTIONABLE` | 1 | current technical extraction exposes a conflict |
| `PARTIALLY_ACTIONABLE` | 6 | surface residual is visible, but its identity meaning is not established |
| `EXTERNAL_KNOWLEDGE_DOMINANT` | 2 | business/domain convention supplies the distinction |
| `UNRESOLVED` | 1 | no deterministic source-visible decision basis is established |
| **Total** | **10** | |

The source-visible-only analysis therefore contains one DIFFERENT case. Its
technical-attribute-conflict candidate also selects three known SAME Strong
controls, so it is not a safe correction. The all-case analysis likewise finds
no zero-harm repeated signal.

## Candidate discriminator evaluation

Eighteen transparent single-feature or small 2-condition families were tested.
Twelve are `CONTRADICTED_BY_POSITIVE_CONTROLS`; six are `NOT_ACTIONABLE`. There
are zero `REPEATED_GENERAL_SIGNAL`, zero `PROMISING_BUT_TOO_SMALL`, and zero
holdout-only candidates worth a targeted check.

| Candidate family | DIFFERENT caught / 10 | SAME harmed / 40 | Development D/S harm | Holdout D/S harm | Source-visible caught | Decision |
|---|---:|---:|---:|---:|---:|---|
| part-number residual divergence | 10 | 40 | 3 / 8 | 4 / 2 | 1 | contradicted |
| unresolved residual divergence | 10 | 39 | 3 / 8 | 4 / 2 | 1 | contradicted |
| identity-signature incomplete | 10 | 37 | 3 / 8 | 4 / 2 | 1 | contradicted |
| exact description + part residual | 9 | 35 | 3 / 8 | 4 / 2 | 0 | contradicted |
| copied/description dominance | 9 | 34 | 3 / 8 | 4 / 2 | 0 | contradicted |
| lexical/unresolved weakest path | 8 | 29 | 3 / 7 | 4 / 2 | 0 | contradicted |
| numeric residual divergence | 6 | 14 | 1 / 1 | 4 / 1 | 0 | contradicted |
| description dominance + numeric residual | 6 | 13 | 1 / 1 | 4 / 1 | 0 | contradicted |
| description-only evidence | 5 | 20 | 2 / 3 | 2 / 0 | 0 | contradicted |
| alphabetic residual divergence | 4 | 29 | 2 / 7 | 0 / 1 | 1 | contradicted |
| technical-attribute conflict | 1 | 3 | 0 / 0 | 0 / 0 | 1 | contradicted |

Part-type conflict, UOM conflict, model/type conflict, recognized
object/function conflict, independent non-description support missing, and
cross-site-only support catch no DIFFERENT Strong pair. They are non-actionable
in this evidence. Full confidence composition and support counts are preserved
in the candidate CSV. The ten unconflicted DIFFERENT cases comprise one HIGH,
eight MEDIUM, and one LOW judgment; no candidate obtains safe separation by
confidence band.

These results also protect the two accepted holdout Likely controls, the R18C
SAME Strong population and named positive controls, Development SAME pairs,
exact/generic safety behavior, Bicycle deferral, and Head/Tail cannot-link.
Because this task is shadow analysis only, Bicycle and Head/Tail behavior is
unchanged by construction.

## Overfit and leave-source-out interpretation

Residual and description candidates recur across R18, Development, and the
consumed holdout, but they recur far more broadly among SAME controls. Their
failure is not merely insufficient sample size; the sign is non-specific.
Conversely, the only source-visible technical conflict appears in one R18 pair
and is contradicted by three SAME pairs. Removing any one source family cannot
turn either pattern into a repeated, zero-harm signal. No threshold is selected
from the six holdout failures, and no identifier, noun, group ID, or exact part
number is used as a rule.

## R18I reassessment

The four case-level `STATUS_PROMOTION_ERROR` cases remain unsuitable for
confident presentation, but existing wider evidence does not prove a safe
Strong-trust correction:

| R18I case | Wider-evidence result |
|---|---|
| NAS-REPL1 / NAS-REPL2 | visible numeric residual is shared by numerous SAME controls; genuinely ambiguous |
| HP-FIFO / HP-FIFO-02 | directly conflicts with the earlier R18 SAME judgment; no stable deterministic label |
| YINPPART / YINPPART2 | numeric/copied-description pattern is contradicted by SAME controls |
| RDEW IP1 / RDEW IP5 | same numeric/copied-description ambiguity; no independent source-visible contradiction |

The two external-domain R18I cases are `INPUT_INFORMATION_LIMIT`:

- JD-SERIAL / JD-SERIAL-2 requires the client's serial-tracking convention and
  also has conflicting SAME/Different Senior judgments.
- MT-ENG S1 / MT-ENG S2 requires knowledge that S1/S2 encode distinct mounting
  positions; the visible suffixes alone do not prove that meaning.

Neither is counted as evidence for a lexical runtime correction.

## Decision

`R18J_0_NO_SAFE_SOURCE_VISIBLE_DISCRIMINATOR`.

No runtime correction is justified. No candidate merits
`R18J_1_TINY_TARGETED_HUMAN_CHECK`, so a <=12-pair check is **not needed** and
is not requested. The remaining issue is presentation honesty, not an
authorized attempt to fit more deterministic logic from exhausted,
non-independent evidence. Any future runtime correction still requires a new
independent human-labelled holdout before quality graduation.

## Demo-safe operating envelope

The product may be demonstrated only under this contract:

- the system is advisory;
- nothing auto-merges or silently changes the inventory;
- human review is authoritative;
- candidates are shown as hypotheses requiring review;
- no unsupported precision, accuracy, or confidence percentage is stated.

Use these presentation labels:

- **Potential Same-Identity Group**
- **System-Suggested Candidate Group**
- **Requires Human Review**

Do not present `LIKELY_DUPLICATE_GROUP` as confirmed duplicate truth. The
existing internal status may remain technically unchanged, but the next
productization task should soften its UI/XLSX wording for the demo without
changing grouping semantics.

A curated dataset is allowed only when explicitly marked **DEMONSTRATION /
WALKTHROUGH EXAMPLES**. Client rows may instead be shown as system-generated
candidates requiring review, with no implication that the selection is an
unbiased validation set or representative accuracy sample.

Temporary XLSX posture:

1. Section A — human-reviewed or confirmed decisions, if available.
2. Section B — system-suggested candidate groups, explicitly **Requires
   Review**.
3. Section C — rejected, deferred, and conflict context where useful.

This posture is a recommendation only. XLSX-vNext, Group Confidence Index,
R19A, and Identity Context Projection remain unauthorized and unimplemented.

## Artifacts and verification

Ignored deterministic artifacts under
`artifacts/gf12_a2_human_identity_review/`:

- `r18j0_unified_strong_human_evidence.csv`
- `r18j0_candidate_discriminator_evaluation.csv`
- `r18j0_positive_control_impact.csv`
- `r18j0_summary.json`

The focused tests cover source reconciliation, order-independent canonical pair
fingerprinting, matching and conflicting-label deduplication, deterministic
source-visibility classification, deterministic candidate evaluation,
positive-control accounting, holdout-overfit detection, demo-safe routing, and
absence of runtime mutation/provider integration.
