"""Load the packaged, versioned semantic-alias reference exactly once."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping


SCHEMA_VERSION = 1
REFERENCE_PATH = Path(__file__).with_name("semantic_aliases.v1.json")
_REQUIRED_KEYS = frozenset(
    {
        "schema_version",
        "reference_version",
        "domain_token_map",
        "spelling",
        "abbreviations",
    }
)
_MAP_KEYS = ("domain_token_map", "spelling", "abbreviations")


class SemanticAliasReferenceError(RuntimeError):
    """Raised when the packaged semantic-alias reference is unusable."""


@dataclass(frozen=True)
class SemanticAliasReference:
    schema_version: int
    reference_version: str
    domain_token_map: Mapping[str, str]
    spelling: Mapping[str, str]
    abbreviations: Mapping[str, str]
    fingerprint: str


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SemanticAliasReferenceError(
                f"Semantic alias reference contains duplicate JSON key: {key!r}"
            )
        result[key] = value
    return result


def _canonical_payload(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def load_semantic_alias_reference(
    path: Path = REFERENCE_PATH,
) -> SemanticAliasReference:
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise SemanticAliasReferenceError(
            f"Cannot read semantic alias reference {path}: {exc}"
        ) from exc

    try:
        payload = json.loads(raw, object_pairs_hook=_reject_duplicate_keys)
    except SemanticAliasReferenceError:
        raise
    except json.JSONDecodeError as exc:
        raise SemanticAliasReferenceError(
            f"Invalid JSON in semantic alias reference {path}: {exc}"
        ) from exc

    if not isinstance(payload, dict):
        raise SemanticAliasReferenceError(
            "Semantic alias reference must be a JSON object"
        )
    actual_keys = frozenset(payload)
    if actual_keys != _REQUIRED_KEYS:
        missing = sorted(_REQUIRED_KEYS - actual_keys)
        unexpected = sorted(actual_keys - _REQUIRED_KEYS)
        raise SemanticAliasReferenceError(
            "Semantic alias reference has invalid top-level keys: "
            f"missing={missing}, unexpected={unexpected}"
        )
    if type(payload["schema_version"]) is not int:
        raise SemanticAliasReferenceError("schema_version must be an integer")
    if payload["schema_version"] != SCHEMA_VERSION:
        raise SemanticAliasReferenceError(
            f"Unsupported semantic alias schema_version: {payload['schema_version']!r}"
        )
    reference_version = payload["reference_version"]
    if not isinstance(reference_version, str) or not reference_version.strip():
        raise SemanticAliasReferenceError(
            "reference_version must be a non-empty string"
        )

    validated_maps: dict[str, Mapping[str, str]] = {}
    for section in _MAP_KEYS:
        aliases = payload[section]
        if not isinstance(aliases, dict):
            raise SemanticAliasReferenceError(f"{section} must be a JSON object")
        for key, value in aliases.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise SemanticAliasReferenceError(
                    f"{section} keys and values must be strings"
                )
        validated_maps[section] = MappingProxyType(dict(aliases))

    fingerprint = hashlib.sha256(_canonical_payload(payload)).hexdigest()
    return SemanticAliasReference(
        schema_version=payload["schema_version"],
        reference_version=reference_version,
        domain_token_map=validated_maps["domain_token_map"],
        spelling=validated_maps["spelling"],
        abbreviations=validated_maps["abbreviations"],
        fingerprint=fingerprint,
    )


SEMANTIC_ALIAS_REFERENCE = load_semantic_alias_reference()
DOMAIN_TOKEN_MAP = SEMANTIC_ALIAS_REFERENCE.domain_token_map
SPELLING = SEMANTIC_ALIAS_REFERENCE.spelling
ABBREVIATIONS = SEMANTIC_ALIAS_REFERENCE.abbreviations
SEMANTIC_ALIAS_REFERENCE_VERSION = SEMANTIC_ALIAS_REFERENCE.reference_version
SEMANTIC_ALIAS_REFERENCE_FINGERPRINT = SEMANTIC_ALIAS_REFERENCE.fingerprint
