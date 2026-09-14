import hashlib
import json
from pathlib import Path

import pytest

from app.engine.domain_dictionary import DOMAIN_TOKEN_MAP
from app.engine.normalizer import ABBREVIATIONS, SPELLING
from app.reference_data.semantic_aliases import (
    SEMANTIC_ALIAS_REFERENCE,
    SEMANTIC_ALIAS_REFERENCE_FINGERPRINT,
    SemanticAliasReferenceError,
    load_semantic_alias_reference,
)


EXPECTED_FINGERPRINT = "0484679a78e61b2f3564c40ca7ef7f7d2b69c1a98e24d24ecdedf65eccdc4367"
EXPECTED_MAP_FINGERPRINTS = {
    "domain_token_map": "31c667bddf0bf2f4a787fa29b218660ad0ebda56acf1a14116f68dc0fb9abfca",
    "spelling": "53ee0647e9d9da2ea1953590c79c683dfd274c50a9d29ae9f9fcb9ac8f0ea553",
    "abbreviations": "2f4070f67e9917d37ed9d5ea788e1b22545c1ef80fdf6f38efe207ae778499da",
}


def _map_fingerprint(value) -> str:
    canonical = json.dumps(
        dict(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _valid_payload() -> dict:
    return {
        "schema_version": 1,
        "reference_version": "test-reference-v1",
        "domain_token_map": {"x": "example"},
        "spelling": {"mispelt": "misspelled"},
        "abbreviations": {"abbr": "abbreviation"},
    }


def _write_payload(path: Path, payload: object) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_packaged_reference_exactly_matches_migration_snapshot():
    assert len(DOMAIN_TOKEN_MAP) == 19
    assert len(SPELLING) == 2
    assert len(ABBREVIATIONS) == 11
    assert _map_fingerprint(DOMAIN_TOKEN_MAP) == EXPECTED_MAP_FINGERPRINTS["domain_token_map"]
    assert _map_fingerprint(SPELLING) == EXPECTED_MAP_FINGERPRINTS["spelling"]
    assert _map_fingerprint(ABBREVIATIONS) == EXPECTED_MAP_FINGERPRINTS["abbreviations"]
    assert SEMANTIC_ALIAS_REFERENCE_FINGERPRINT == EXPECTED_FINGERPRINT
    assert SEMANTIC_ALIAS_REFERENCE.schema_version == 1
    assert SEMANTIC_ALIAS_REFERENCE.reference_version == "semantic-aliases-v1"
    assert DOMAIN_TOKEN_MAP["co"] == "coconut"
    assert ABBREVIATIONS["a"] == "amp"
    assert SPELLING["decicatted"] == "desiccated"


@pytest.mark.parametrize("aliases", [DOMAIN_TOKEN_MAP, SPELLING, ABBREVIATIONS])
def test_runtime_alias_maps_are_immutable(aliases):
    with pytest.raises(TypeError):
        aliases["new"] = "value"


def test_missing_reference_fails_closed(tmp_path):
    with pytest.raises(SemanticAliasReferenceError, match="Cannot read"):
        load_semantic_alias_reference(tmp_path / "missing.json")


def test_invalid_json_fails_closed(tmp_path):
    path = tmp_path / "invalid.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(SemanticAliasReferenceError, match="Invalid JSON"):
        load_semantic_alias_reference(path)


def test_duplicate_key_fails_closed(tmp_path):
    path = tmp_path / "duplicate.json"
    path.write_text(
        '{"schema_version":1,"reference_version":"v1",'
        '"domain_token_map":{"x":"one","x":"two"},'
        '"spelling":{},"abbreviations":{}}',
        encoding="utf-8",
    )
    with pytest.raises(SemanticAliasReferenceError, match="duplicate JSON key"):
        load_semantic_alias_reference(path)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda p: p.pop("schema_version"), "missing=.*schema_version"),
        (lambda p: p.pop("spelling"), "missing=.*spelling"),
        (lambda p: p.update({"unexpected": {}}), "unexpected=.*unexpected"),
        (lambda p: p.update({"schema_version": 2}), "Unsupported"),
        (lambda p: p.update({"domain_token_map": []}), "domain_token_map must"),
        (lambda p: p.update({"abbreviations": {"x": 1}}), "keys and values"),
        (lambda p: p.update({"reference_version": 1}), "non-empty string"),
        (lambda p: p.update({"reference_version": "  "}), "non-empty string"),
    ],
)
def test_malformed_reference_fails_closed(tmp_path, mutation, message):
    payload = _valid_payload()
    mutation(payload)
    path = _write_payload(tmp_path / "reference.json", payload)
    with pytest.raises(SemanticAliasReferenceError, match=message):
        load_semantic_alias_reference(path)


def test_reference_fingerprint_is_logical_and_order_independent(tmp_path):
    payload = _valid_payload()
    first = load_semantic_alias_reference(_write_payload(tmp_path / "first.json", payload))
    reordered = dict(reversed(list(payload.items())))
    second = load_semantic_alias_reference(
        _write_payload(tmp_path / "second.json", reordered)
    )
    assert first.fingerprint == second.fingerprint
