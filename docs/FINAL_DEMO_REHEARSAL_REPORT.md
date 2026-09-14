# Final advisory demo rehearsal report

## Post-rehearsal determinism gate

The later `DETERMINISM_CACHE_AND_GF5_ORDERING_VERIFIED` correction restores the
qualified deterministic claim. Three fresh 5,327-row scans with different scan
IDs and cold/warm cache states produced identical semantic candidate and group
results. Scan-local IDs and timestamps may differ. The product remains advisory,
human review remains authoritative, and this is not an accuracy or automatic-
merge claim. See `DETERMINISM_CACHE_AND_GF5_ORDERING_FIX.md`.

Classification: `FINAL_DEMO_REHEARSAL_GO`

Rehearsal baseline: `6ec74d42a24797de19dafcf312f08b7c958aa299` on
`llm-assisted-mvp`.

## Result

The exact non-Docker demo path completed end to end against a disposable local
SQLite database with both LLM providers disabled. The live 17-row scan was
fast and repeatable enough to be the primary path. A pre-completed local
synthetic database and a known-good XLSX are retained as fallbacks.

This rehearsal proves workflow, presentation, review authority, and export
reliability. It is not an accuracy benchmark, production-readiness
certification, automatic merge demonstration, or probability/confidence claim.

## Dataset and result

- Dataset: `data/llm_assisted_mvp_demo.csv`
- Required label: `DEMONSTRATION / WALKTHROUGH EXAMPLES`
- SHA-256: `af23e6ad6855a545cbb7258da95ff1bc4fca9fa8a149042838ed689d15cddebd`
- Records: 17
- Authority: `G2_V2`
- Candidate groups: 4 (one Stronger Evidence, three Review Evidence)
- Other outcomes: three conflicts, zero deferred work units, eight unassigned
  records

The dataset exercises a three-member motor naming/format variation, ambiguous
two-member candidates, and protected variants/conflicts. These examples
demonstrate behavior only and are not validation evidence.

## Timed flow

| Step | Result | Approximate time |
|---|---|---:|
| Backend/frontend health round trip | PASS | 341 ms |
| Vite ready | PASS | 452 ms |
| CSV validation | PASS, 17 records | 41 ms |
| Upload plus synchronous scan | PASS, scan 1 completed | 713 ms |
| Summary plus four group details | PASS | 196 ms |
| Confirm motor candidate | PASS, event persisted/current | 88 ms |
| Reject filter candidate | PASS, event persisted/current | 84 ms |
| Defer sensor candidate | PASS, event persisted/current | 79 ms |
| Browser route refresh | PASS, result still ready | 1,055 ms |
| XLSX export | PASS | 93 ms |
| XLSX open and structural inspection | PASS | 613 ms |
| Restart and reopen pre-completed result | PASS | 249 ms |

One seal candidate was deliberately left unreviewed. The UI/API state after
review was exactly one `Human Confirmed Same-Identity Group`, one `Human
Rejected Candidate`, one `Review Deferred`, and one `Requires Human Review`.
The reviewed CSV contained only the three confirmed motor records. Source CSV
SHA-256 remained unchanged before and after the rehearsal.

## Explanation and wording verification

All four group details were opened. At least three examples contained a safe
headline, two or more supporting points, caution points, and explicit review
guidance. The visible vocabulary is:

- `Potential Same-Identity Group`
- `Requires Human Review`
- `Stronger deterministic evidence`
- `Needs additional review`
- `Human Confirmed Same-Identity Group`
- `Human Rejected Candidate`
- `Review Deferred`

No primary-path or workbook text used Confirmed Duplicate, Likely Duplicate,
High-Confidence Duplicate, AI Confirmed, Guaranteed Match, or an unsupported
accuracy/precision/confidence/probability percentage.

## XLSX verification

Known-good workbook:
`artifacts/demo_rehearsal/DEMONSTRATION_WALKTHROUGH_EXAMPLES_system_groups.xlsx`

SHA-256:
`77ca8d60156e913c2c7011a33adc66363d8a85ac5ccd7aa3ec56d7ecfa5b3057`

- `Summary` states advisory purpose, required human review, human authority,
  four system suggestions, one confirmation, one rejection, and two
  deferred/unreviewed candidates.
- `Candidate Groups` has all nine required group-level columns and one row per
  candidate. Every unreviewed row says `Requires Human Review`.
- `Group Data` has nine readable source-member rows linked to four candidate
  IDs with group sizes 2, 2, 2, and 3.
- Workbook formula-cell count is zero and no banned wording was found.
- Membership and system status remain distinct from the human decision.

## Verification runs

- Focused backend presentation/review/XLSX/demo tests: 76 passed.
- Frontend tests: 153 passed.
- Frontend production build: PASS with Vite 8.0.16; 42 modules transformed.
- Live HTTP application and browser-route smoke: PASS.
- Provider calls: 0.

Runtime detector, GF4/GF5/GF6 behavior, candidate membership, thresholds,
cannot-links, signatures, and `GF5_PARTITION_POLICY_V1` were unchanged.

## Five-to-seven-minute spoken script

**0:00–0:45 — Business problem.** Inventory lists often contain different
codes and descriptions for records that may refer to one physical item. Manual
search across thousands of rows is slow, and identical words alone are not
enough to establish identity.

**0:45–1:30 — Start the walkthrough.** “These are DEMONSTRATION / WALKTHROUGH
EXAMPLES. I will validate 17 synthetic rows and run the deterministic current
product.” Show that the result is G2_V2 and that records become reviewable
candidate groups rather than automatic merge instructions.

**1:30–2:30 — Candidate generation.** Show the four System-Suggested Candidate
Groups and say: “The system narrows a large inventory list into reviewable
same-identity candidates. It does not automatically merge or change inventory
records; the reviewer makes the authoritative decision.”

**2:30–3:30 — Evidence and safeguards.** Open the motor group and two other
examples. Show “Why the system suggested this group,” supporting evidence,
cautions, sites, and `Requires Human Review`. Explain that protected
contradictions stay outside accepted membership and that an evidence tier is
not probability or proof.

**3:30–4:45 — Human authority.** Confirm the motor group, reject one candidate,
and defer another. Point out that the human state dominates the system
suggestion and that one remaining candidate still requires review. “This is a
candidate-discovery and review workflow, not an automatic merge engine.”

**4:45–5:45 — Client deliverable.** Export XLSX. In `Summary`, show the advisory
notice and separated system/human counts. In `Candidate Groups`, show evidence
tier beside human decision/comment. In `Group Data`, show the original readable
member rows and stable candidate linkage. Show that Reviewed CSV contains only
the human-confirmed set.

**5:45–6:30 — Close and roadmap.** State that the current demo path is
deterministic, performs no IFS writeback, and keeps the reviewer authoritative.
Future work—human validation, optional advisory enrichment, deployment,
identity context, and integration—requires separate authorization and must not
be inferred from this workflow demonstration.

## Prepared Q&A

**Why not auto-merge?** Identity decisions can depend on business context not
fully represented in source fields. The system reduces the search space and
explains why records look related, but the reviewer remains final authority.

**What happens with genuine variants?** Deterministic evidence can protect
known contradictions or surface ambiguity. The reviewer can reject, defer,
confirm a subset, or split a multi-member candidate; no variant is forcibly
merged.

**What happens across sites?** Different sites do not automatically mean
different identities, but site is contextual information rather than proof of
sameness.

**Can the system be wrong?** Yes. It produces candidates, not confirmed truth.
That is why explanations, caution evidence, and human review are required.

**What does Stronger deterministic evidence mean?** The candidate met the
system's stronger categorical evidence rules. It is not a percentage,
probability, accuracy statement, or human confirmation.

**Does this demo use an LLM?** The current demo path is deterministic. LLM use
is reserved for a future advisory layer, not authority for identity grouping.

**What gets written back to IFS?** Nothing. This demo produces review states
and exports only; it does not merge, delete, change, or write records to IFS.

## Failure recovery

Backend startup, frontend startup, validation/upload, refresh, and XLSX open
were rehearsed. The moved local fallback database was restarted and scan 1
reopened with all three decisions plus the unreviewed state intact. Three
malformed command-line validation attempts failed safely
with HTTP 400 before the correctly formatted request passed; no scan or source
mutation resulted.

- Backend unavailable: restart with the provider-none command in
  `docs/DEMO_REHEARSAL_RUNBOOK.md`, then check `/health` and `/ready`.
- Frontend unavailable: restart Vite and reload the same persisted scan route.
- Upload failure: correct mapping/input and validate again; do not edit the
  database.
- Slow scan: open pre-completed scan 1 in the local synthetic fallback database.
- Export failure: retry once, then use the hash-verified known-good XLSX.
- Browser refresh: reopen `/scans/1`; persisted state was verified after refresh.
- Workbook unavailable: show the in-app Candidate Groups and reviewed CSV, and
  state that workbook opening is unavailable; do not invent results.

Local pre-completed database:
`artifacts/demo_rehearsal/DEMONSTRATION_WALKTHROUGH_EXAMPLES.sqlite3` (Git
ignored, synthetic only). Its SHA-256 is
`176960c173aabf08d3758e8236383bf168659605a0310e5397e658f36cace4d0`.

## Recommended demo path

Use the bounded 17-row live synthetic scan as primary. Keep pre-completed scan 1
openable from the local synthetic database in a second browser tab and the
known-good XLSX ready locally. If any live step becomes unreliable, switch to
the pre-completed result without claiming that the fallback is a fresh run.

No tag was created or moved. `advisory-demo-ready-v1` is only a suggested future
tag and requires explicit architect approval.

## Authorized XLSX presentation re-rehearsal

The bounded post-freeze correction is
`DEMO_XLSX_CLIENT_UX_POLISH_READY`. The export now opens on `Overview`; the
primary `Review Groups` sheet presents one candidate as a visually bounded
member block; `Group Index` provides a concise one-row index; `Detailed Data`
remains flat/filterable; and `Technical Reference` retains canonical IDs and
stable source references outside the primary review flow.

Microsoft Excel opened and rendered all five sheets from the reviewed synthetic
fallback. Inspection covered two-member blocks, the three-member motor block,
all four authority states, long wrapped content, and technical traceability.
The reviewed fixture exported in 1,268 ms. The locally available Scan 34 export
completed in 5,689 ms and retained exactly 158 groups, 341 member rows, 51
Stronger Evidence groups, 107 Review Evidence groups, and 158 unreviewed states.
Focused XLSX/package tests passed 22/22; the broader bounded backend export and
safety suite passed 127/127; provider calls remained zero. Detector, GF5,
membership, and review authority are unchanged. The demo remains authorized
under the same advisory claim boundary after the containing commit,
`Polish client XLSX review experience`.
