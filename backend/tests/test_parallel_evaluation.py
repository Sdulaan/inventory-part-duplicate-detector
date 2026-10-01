from itertools import combinations

from app.engine.identity_evidence_evaluator import DeterministicIdentityContext
from app.services import parallel_evaluation
from app.services.parallel_evaluation import evaluate_canonical_pairs

from test_identity_evidence import prepare_discovery, row


def test_parallel_evaluation_returns_the_sequential_results_in_order(db, monkeypatch):
    records = [
        row("A1", "Viola x will. Mix 6-Pack"),
        row("A2", "Viola x will. Mix 6-Pack"),
        row("B1", "Filtmatta 40x60cm 100st/bunt"),
        row("B2", "Filtmatta 60x60cm 100st/bunt"),
        row("C1", "MOTOR BEARING 6205"),
        row("C2", "MOTOR BEARING SKF 6205"),
    ]
    _scan, catalog = prepare_discovery(db, records, [])[:2]
    records_by_id = {record.record_id: record for record in catalog.records}
    pairs = list(combinations(sorted(records_by_id), 2))
    context = DeterministicIdentityContext("SAME_SITE_DUPLICATE", ("CONTRACT", "UNIT_MEAS"))

    sequential = evaluate_canonical_pairs(records_by_id, context, pairs, workers=1)
    monkeypatch.setattr(parallel_evaluation, "PARALLEL_MIN_PAIRS", 0)
    parallel = evaluate_canonical_pairs(records_by_id, context, pairs, workers=2)

    assert parallel == sequential
    assert [(item.record_id_1, item.record_id_2) for item in parallel] == pairs



def test_broken_worker_pool_falls_back_to_sequential_results(db, monkeypatch):
    from concurrent.futures.process import BrokenProcessPool

    records = [row(f"P{index}", f"Hex bolt M{index} zinc") for index in range(4)]
    _scan, catalog = prepare_discovery(db, records, [])[:2]
    records_by_id = {record.record_id: record for record in catalog.records}
    pairs = list(combinations(sorted(records_by_id), 2))
    context = DeterministicIdentityContext("SAME_SITE_DUPLICATE", ("CONTRACT", "UNIT_MEAS"))
    expected = evaluate_canonical_pairs(records_by_id, context, pairs, workers=1)

    def broken_pool(*_args, **_kwargs):
        raise BrokenProcessPool("a worker process died")

    monkeypatch.setattr(parallel_evaluation, "PARALLEL_MIN_PAIRS", 0)
    monkeypatch.setattr(parallel_evaluation, "_evaluate_in_pool", broken_pool)
    assert evaluate_canonical_pairs(records_by_id, context, pairs, workers=4) == expected
