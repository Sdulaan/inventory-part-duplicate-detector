# Packaged deterministic semantic alias reference

## Result

Classification: `SEMANTIC_ALIAS_CONFIG_MIGRATION_VERIFIED`.

The three dataset/domain-specific maps formerly defined in Python are now one
packaged deterministic semantic alias reference:

```text
backend/app/reference_data/semantic_aliases.v1.json
```

This changes the location of existing knowledge, not its meaning. No alias was
added, removed, corrected, trimmed, lowercased, broadened, or reinterpreted.
In particular, the existing ambiguous aliases `co -> coconut` and `a -> amp`
remain unchanged.

## Reference contract

| Property | Value |
|---|---|
| schema version | `1` |
| reference version | `semantic-aliases-v1` |
| `domain_token_map` entries | 19 |
| `spelling` entries | 2 |
| `abbreviations` entries | 11 |
| canonical SHA-256 | `0484679a78e61b2f3564c40ca7ef7f7d2b69c1a98e24d24ecdedf65eccdc4367` |

The fingerprint is SHA-256 over the logical object serialized as UTF-8 JSON
with exact-key sorting, no ASCII coercion, and canonical compact separators.
It includes `schema_version`, `reference_version`, and all three maps. It does
not depend on path, timestamps, indentation, or JSON member order.

The migration snapshot also recorded exact per-map fingerprints:

| Map | SHA-256 |
|---|---|
| `domain_token_map` | `31c667bddf0bf2f4a787fa29b218660ad0ebda56acf1a14116f68dc0fb9abfca` |
| `spelling` | `53ee0647e9d9da2ea1953590c79c683dfd274c50a9d29ae9f9fcb9ac8f0ea553` |
| `abbreviations` | `2f4070f67e9917d37ed9d5ea788e1b22545c1ef80fdf6f38efe207ae778499da` |

## Loading and safety

`app.reference_data.semantic_aliases` locates the adjacent packaged JSON,
loads and validates it once during module import, and exposes the established
`DOMAIN_TOKEN_MAP`, `SPELLING`, and `ABBREVIATIONS` names as read-only
`MappingProxyType` views. A scan therefore cannot mutate shared aliases and
alter a later scan.

The loader fails closed with `SemanticAliasReferenceError` for an unreadable
or missing file, malformed UTF-8/JSON, duplicate JSON keys, missing or
unexpected top-level keys, unsupported or non-integer schema versions, empty
or non-string reference versions, wrong section types, and non-string alias
values. There is no hard-coded runtime fallback and no second authoritative
Python copy.

The backend Dockerfile copies the complete `app` tree into the image, so the
reference is included by the existing container/runtime packaging path. Local
execution likewise imports it from the backend application package. No
packaging change was needed.

## Behavior and performance evidence

The migration test fixes all three entry counts, each pre-migration map
fingerprint, the combined reference fingerprint, and selected risky sentinel
entries. Existing normalization fixtures retain exact outputs. Candidate
discovery, scoring, GF4, GF5, group membership, evidence, determinism, review,
and XLSX suites pass without provider access.

The committed corrected 5,327-row S0-S10 acceptance artifact remains the
comparison baseline: 158 groups (45 Stronger Evidence and 113 Review Evidence),
27 conflicts, 40 deferred work units, 4,982 unassigned records, and 171,251
GF5 partition explorations. A fresh protected-workbook run was intentionally
not used because that local workbook is out of bounds; bounded deterministic
end-to-end fixtures provide post-migration equivalence evidence.

A local characterization measured one-process initial module import, file
load, validation, and fingerprinting at about 44.7 ms. Once loaded, 100,000
read-only map lookups took about 7.7 ms. Runtime normalization uses the same
in-memory lookups and existing caches, so there is no per-record file I/O.
These figures characterize one development machine, not an SLO.

## Preserved boundary

This is not a full semantic registry, client policy engine, dynamic ontology,
or AI knowledge base. Generic/noise vocabulary, other retrieval and part-code
aliases, object incompatibilities, directional/variant/function vocabularies,
UOM and column aliases, site and part-type rules, thresholds, caps, GF4/GF5
policy, review semantics, and XLSX behavior remain where they were.

The future boundary remains:

```text
Known approved alias -> deterministic reference lookup
Unknown semantic term -> future optional semantic interpretation
Identity consequence -> existing deterministic and human authority
```

No LLM or provider call is involved in loading or using the reference.
