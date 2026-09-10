# Demo-safe productization

## Final rehearsal result

The productization passed its exact final rehearsal as
`FINAL_DEMO_REHEARSAL_GO`. A provider-none live 17-row synthetic scan completed
in 713 ms, all review authority states persisted correctly, the reviewed CSV
contained only the confirmed set, and the XLSX opened with correct counts,
linkage, and safe wording. Focused backend tests (76), frontend tests (153), and
the production build passed. The live walkthrough is primary; a pre-completed
synthetic result and known-good XLSX are fallbacks. Runtime detector/GF5
semantics remain unchanged and no quality or production-readiness claim is
created.

Classification: `DEMO_SAFE_PRODUCTIZATION_READY_FOR_REHEARSAL`

Next: `FINAL_DEMO_REHEARSAL`

## Decision and boundary

Existing human evidence did not identify a source-visible discriminator that
could safely correct the detector without harming known same-identity controls.
An algorithm correction was therefore not justified. This change productizes
the current result as an advisory candidate-discovery workflow while preserving
the detector, GF4 evidence classes, R18C lexical trust, GF5 membership and
partition policy, GF6 statuses, candidate generation, signatures, thresholds,
cannot-link rules, and append-only human-review semantics.

The product contract is:

```text
System suggests -> Human reviews -> Human decision becomes authoritative
```

The application never represents an unreviewed system group as a confirmed
duplicate. It does not automatically merge, delete, or change records in IFS.

## Safe terminology

| Internal or review state | Client-facing presentation |
|---|---|
| `LIKELY_DUPLICATE_GROUP` | Potential Same-Identity Group; Requires Human Review; Stronger deterministic evidence / Stronger Evidence |
| `POSSIBLE_DUPLICATE_GROUP_REVIEW` | Potential Same-Identity Group; Requires Human Review; Needs additional review / Review Evidence |
| `CONFIRM_ALL_AS_ONE`, `CONFIRM_SELECTED` | Human Confirmed Same-Identity Group |
| `SPLIT_PARTITIONS` | Human Reviewed - Split into Identity Sets |
| `KEEP_ALL_SEPARATE` | Human Rejected Candidate |
| `UNSURE` | Review Deferred |

Evidence tiers describe deterministic evidence strength only. They are not
probabilities, accuracy measures, or confidence percentages. No Group
Confidence Index was added.

## Product surfaces

The group-first results page now presents advisory candidate groups, explicit
human authority, safe loading and empty states, evidence-tier filters, review
actions, and clearly separated system and reviewed exports. Deterministic
explanations are headed "Why the system suggested this group." The legacy pair
diagnostics remain an advanced diagnostic surface and are not the business
result or review authority.

The system CSV retains its internal compatibility fields and adds deterministic
display fields for candidate label, review requirement, and evidence tier. The
reviewed CSV remains limited to current human-confirmed identity sets.

## XLSX authority model

The existing group export is revised, not replaced by XLSX-vNext:

- `Summary` states the report purpose, advisory limitation, human authority,
  workflow, and counts separated into system suggestions, confirmations,
  rejections, and deferred/unreviewed candidates.
- `Candidate Groups` contains one readable row per candidate with candidate and
  canonical IDs, review state, evidence tier, member count, sites, reason,
  human decision, and human comment.
- `Group Data` preserves all source member fields and links every member to the
  same unchanged candidate group.

Spreadsheet-formula escaping, deterministic ordering, immutable membership,
and the authoritative reviewed-export boundary remain intact. The workbook
contains no unsupported accuracy, probability, or confidence percentage.

## Demo data and claim policy

Two truthful modes are supported:

- Mode A uses clearly labelled `DEMONSTRATION / WALKTHROUGH EXAMPLES` to show
  upload, discovery, evidence, review, and export. It is not unbiased validation.
- Mode B shows client or real data only as system-generated candidates requiring
  human review. It is not presented as validated or representative performance.

Use a prepared result as the primary demo path. A small live scan is optional
and demonstrates workflow only. The consumed holdout is engineering evidence,
not a marketing metric or independent proof.

## Verification

- Backend full suite: 1,851 passed, 15 skipped.
- Frontend tests: 153 passed using Node's no-isolation test mode required by the
  local Windows sandbox.
- Frontend production build: passed with Vite 8.0.16.
- Export smoke coverage: group page contracts, review decisions, CSV export,
  XLSX generation/open, required sheets, advisory notice, authority separation,
  formula safety, deterministic membership, and zero provider calls passed.
- Provider calls: 0.

No LLM advisory, semantic enrichment, Group Confidence Index, XLSX-vNext,
Identity Context Projection, deployment, IAM/tenancy, IFS integration, GF11
performance work, resolver correction, or new Senior review was started.
