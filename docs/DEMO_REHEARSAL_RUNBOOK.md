# Final demo rehearsal runbook

Status: authorized after `DEMO_SAFE_PRODUCTIZATION_READY_FOR_REHEARSAL`.

## Before the rehearsal

- Use the prepared, pre-completed result as the primary path.
- Optionally prepare a small live CSV for workflow demonstration; do not depend
  on a long full-real scan.
- Label curated data `DEMONSTRATION / WALKTHROUGH EXAMPLES`.
- Treat real/client rows as unvalidated candidates requiring human review.
- Have one naming/format variation, one rejected variant or protected conflict,
  one ambiguous candidate, and—only if safe to explain—one cross-site example.
- Confirm the reviewed export contains only current human-confirmed identity sets.

## Twelve-step flow

1. Explain the inventory identity problem and the cost of manual search.
2. Upload the walkthrough CSV or open the prepared result.
3. Show the System-Suggested Candidate Groups summary.
4. Open one candidate and explain its persisted deterministic evidence.
5. Point out `Potential Same-Identity Group` and `Requires Human Review`.
6. Confirm one candidate and show `Human Confirmed Same-Identity Group`.
7. Reject one candidate and show `Human Rejected Candidate`.
8. Defer or leave one candidate for review and show `Review Deferred` or
   `Requires Human Review`.
9. Export the system-suggestions XLSX.
10. Open `Summary` and `Candidate Groups`, then briefly show linked members in
    `Group Data`.
11. Show that system evidence and human decisions occupy separate columns and
    that reviewed CSV output is limited to human-confirmed sets.
12. State the next-phase roadmap without claiming validated accuracy,
    probability, confidence, automatic merge safety, or production readiness.

Recommended spoken line:

> The system is narrowing thousands of inventory rows into reviewable
> same-identity candidates. It does not make the final merge decision—the
> reviewer does.

## Presenter checklist

- [ ] Prepared result loads and candidate groups render.
- [ ] Unreviewed candidates say `Requires Human Review`.
- [ ] Confirm, Reject, and Defer controls save and display the human authority.
- [ ] No screen calls an unreviewed candidate a confirmed duplicate.
- [ ] No percentage is described as accuracy, probability, or confidence.
- [ ] XLSX downloads and opens with `Summary`, `Candidate Groups`, and `Group Data`.
- [ ] Summary notice says suggestions are not automatic merge instructions.
- [ ] Candidate rows show evidence tier separately from human decision/comment.
- [ ] Reviewed CSV excludes rejected, deferred, unreviewed, and superseded states.
- [ ] No claim treats curated examples or the consumed holdout as unbiased proof.

If any authority label or export boundary is wrong, stop the demonstration and
classify it as a presentation or workflow defect; do not explain it away as an
accuracy result.
