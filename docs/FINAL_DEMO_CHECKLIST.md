# Final advisory demo checklist

Classification: `FINAL_DEMO_REHEARSAL_GO`

## Before presenting

- [ ] Branch is `llm-assisted-mvp` and the rehearsal commit is checked out.
- [ ] Use only `data/llm_assisted_mvp_demo.csv`, labelled
  `DEMONSTRATION / WALKTHROUGH EXAMPLES`.
- [ ] Start the backend with `GROUP_LLM_PROVIDER=none`,
  `LLM_DEMO_ENABLED=false`, and `LLM_PROVIDER=none`; do not load `.env`.
- [ ] Start Vite at `http://127.0.0.1:5173`.
- [ ] Confirm `/health`, `/ready`, and `/api/llm/status`; LLM must be disabled
  and provider must be `none`.
- [ ] Keep the pre-completed local synthetic database and known-good XLSX ready.

## Flow checks

- [ ] Validate 17 rows, then run the bounded current-product scan.
- [ ] Show four System-Suggested Candidate Groups and the G2_V2 projection.
- [ ] Open at least three examples and show supporting evidence, cautions, and
  why human review is required.
- [ ] Confirm the three-record motor candidate.
- [ ] Reject one two-record candidate.
- [ ] Defer one candidate and leave one candidate unreviewed.
- [ ] Confirm the four visible authority states: Human Confirmed, Human
  Rejected, Review Deferred, and Requires Human Review.
- [ ] Export XLSX and begin on `Overview`; state the advisory and human-authority
  message before showing candidate details.
- [ ] In `Review Groups`, show one two-member block and the three-member motor
  block; point out that group fields span the block while member fields remain
  distinct.
- [ ] Use `Group Index` for the concise candidate list and `Detailed Data` for
  flat filtering/sorting.
- [ ] Show that canonical IDs and stable references remain available only on
  the final `Technical Reference` support sheet.
- [ ] Confirm Reviewed CSV contains only the three confirmed motor records.

## Truthfulness checks

- [ ] Say: “This is a candidate-discovery and review workflow, not an automatic
  merge engine.”
- [ ] Do not claim benchmark accuracy, production readiness, probability, or
  confidence percentages.
- [ ] Do not describe an unreviewed candidate as a confirmed or likely duplicate.
- [ ] State that no record is automatically merged, deleted, changed, or written
  back to IFS.
- [ ] Describe Stronger deterministic evidence as a categorical evidence tier,
  not probability or proof.

## Recovery checks

- [ ] If a live scan slows or fails, open pre-completed scan 1 from the local
  synthetic rehearsal database.
- [ ] If export fails, open the known-good rehearsal XLSX.
- [ ] If refresh occurs, reopen `/scans/1`; the persisted result remains ready.
- [ ] If the presentation machine cannot open XLSX, show Candidate Groups in
  the application and use the reviewed CSV; never invent workbook results.
- [ ] Never repair the database, change identity logic, enable a provider, or
  claim same-scan resume during the demo.

Suggested future tag: `advisory-demo-ready-v1`. Do not create or move it without
explicit architect approval.

Post-rehearsal XLSX status: `DEMO_XLSX_CLIENT_UX_POLISH_READY`. Reference commit
subject: `Polish client XLSX review experience`.
