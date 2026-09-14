# Ambiguous global alias portability review

## Outcome

Classification:
`AMBIGUOUS_ALIAS_REVIEW_RECOMMENDS_DISABLE_PENDING_VALIDATION`.

This is a read-only review of exactly two current mappings:

```text
co -> coconut
a  -> amp
```

No alias, reference version, schema, normalizer, retrieval rule, score, GF4/GF5
rule, test expectation, or provider behavior changed.

## Compact decision table

| Alias | Current mapping | Strongest evidence | Client validated? | Runtime impact | Recommendation |
|---|---|---|---|---|---|
| `co` | `coconut` | `DEVELOPMENT_DATA_DERIVED`: the historical 5,327-row CSV has three selected descriptions `CO SO MRP`, while the only coconut tests exercise `CO1`/`C01`, not standalone `co` | No evidence found | Changes three real selected descriptions; no bounded proposal/GF4/GF5 difference | `DISABLE_PENDING_VALIDATION` |
| `a` | `amp` | `DEVELOPMENT_DATA_DERIVED`: 46 selected descriptions change, including article, Type A, part/revision-like, and A1 contexts; one bounded Strong edge/group becomes Review when suppressed | No evidence found | Changes normalization, scores, one GF4 tier, and one GF5 presentation tier in the bounded diagnostic | `MOVE_TO_CONTEXTUAL_CONFIG` |

## Evidence provenance register

Every evidentiary statement used for the recommendations is classified here.

| Evidence | Provenance | What it establishes |
|---|---|---|
| Commit `4494d54`, `Add domain synonym normalization for ERP part matching` | `DOCUMENTED_ASSUMPTION` | Introduced `co -> coconut` with no rationale beyond the broad commit subject |
| Commit `07c9a6e`, `Initial production-oriented duplicate detector` | `DOCUMENTED_ASSUMPTION` | Introduced `a -> amp` with no field/client qualification |
| Coconut candidate/scoring fixtures using `DEC CO1`, `DEC C01`, and `Dec Coco 1` | `TEST_DERIVED` | Current intended coconut-family behavior passes, but `CO1` and `C01` are separate exact aliases; the fixtures do not validate standalone `co` |
| Normalizer fixture `MCB30A -> miniature circuit breaker 30 amp` | `TEST_DERIVED` | `a` supports a known numeric-electrical development case; passing the test is not validation that every `A` means amp |
| Historical 5,327-row CSV blob from commit `f6889ef` | `DEVELOPMENT_DATA_DERIVED` | Supplies the occurrence and suppression measurements below; it is project data, not client approval or a representative validation sample |
| Existing hard-coded-assumption audit | `DOCUMENTED_ASSUMPTION` | Previously identified both aliases as high portability risks |
| 128-record isolated suppression runs | `TEST_DERIVED` | Measures mechanical downstream authority without changing persisted configuration |
| Repository Senior-review reports and artifacts | `HUMAN_REVIEW_EVIDENCE` | Human identity judgments exist, but no reviewed item explicitly validates either alias meaning |
| Client approval for either mapping | `UNVERIFIED` | No explicit client validation was found |
| Independent domain-expert approval for either mapping | `UNVERIFIED` | No explicit domain-expert validation of these mappings was found |

There is therefore no `CLIENT_VALIDATED` or `DOMAIN_EXPERT_VALIDATED` evidence
for either alias. The presence of code, tests, or historical data is not
reclassified as approval.

## Exact runtime path

Both values are loaded once from
`backend/app/reference_data/semantic_aliases.v1.json` by
`app.reference_data.semantic_aliases`. Strict schema validation and immutable
mapping views do not qualify or contextualize the values.

### `co -> coconut`

`DOMAIN_TOKEN_MAP` is imported by `app.engine.domain_dictionary`.
`expand_domain_tokens` lowercases input, replaces non-ASCII-alphanumeric
punctuation with spaces, and considers resulting tokens. If a complete token is
already a key, it is retained for lookup; otherwise boundaries between letters
and digits are split. Replacement is a dictionary lookup on each resulting
whole token, not arbitrary substring replacement.

The domain lookup is used directly for part-number normalization and runs last
for description normalization, after spelling and abbreviation expansion.
Consequences include:

- case-insensitive `CO` becomes `coconut`;
- whitespace-, hyphen-, and slash-delimited `co` becomes `coconut`;
- a pure alphabetic larger word containing `co` is not changed merely because
  it contains those letters;
- an alphanumeric token not itself present in the map can split at a
  letter/digit boundary and expose `co` as a token;
- `co1` and `co2` do not use standalone `co`; they are separate exact map keys
  that become `type 1` and `type 2`;
- after expansion, `coconut` followed by a numeric token triggers the existing
  coconut-specific `type` insertion. Thus an exposed `co` can cascade beyond a
  one-token synonym.

Normalized descriptions and part numbers feed canonical records, legacy and
hybrid candidate discovery, similarity/scoring, explanations, deterministic
GF4 evidence, and therefore the evidence graph supplied to GF5. The alias has
potential authority at every one of those stages even where a particular
bounded corpus produces no final difference.

### `a -> amp`

`ABBREVIATIONS` is imported by `app.engine.normalizer`.
`normalize_description` lowercases input, first splits letter/digit boundaries,
then replaces punctuation with spaces, applies spelling, and finally performs a
whole-token abbreviation lookup. The resulting words then pass through domain
token expansion.

Consequences include:

- standalone case-insensitive `A` becomes `amp`;
- hyphen- and slash-separated `A` becomes a standalone token and is replaced;
- pure alphabetic larger words are not changed merely for containing `a`;
- digit-adjacent forms such as `30A`, `A1`, and the `A` segment of `A320` are
  split before lookup and therefore can become `30 amp`, `amp 1`, and
  `amp 320`;
- `amp` has no further domain-map expansion, but numeric-before-`amp` text can
  be recognized as an electrical measurement by technical-token extraction;
- part-number normalization bypasses `ABBREVIATIONS`, so `A` in `PART_NO` is
  not changed by this alias. Description-derived retrieval, scoring, GF4, and
  GF5 inputs are affected.

## Historical 5,327-row occurrence analysis

The workbook was not opened. The analysis read the exact historical CSV from
the local Git object at `f6889ef:data/List_20260709_093045.csv`. Samples below
are deliberately concise.

### `co`

Across all source fields there are 10 raw exact-token occurrences in four rows:
nine uppercase `CO` occurrences across `Part Description in Use`, `Part
Description`, and `Master Part Description`, plus one title-case `Co` in `Part
Type`. The selected runtime description contains `CO` in three rows, always in
the phrase `CO SO MRP`; no selected part number is changed. Suppression changes
exactly those three normalized descriptions from `coconut so mrp` to
`co so mrp`.

One additional observed exact token is hyphen-delimited in `Co-Product` in the
Part Type field. That field is not the selected description/part-number path in
this run, but it demonstrates portability risk if generic normalization is
reused for broader source observations.

There are 33,990 raw occurrences of the letters `co` embedded in alphanumeric
strings across the wide dataset. This number is not an affected-row count:
larger alphabetic words are protected by whole-token matching. Only punctuation
or letter/digit splitting can expose an embedded segment as a token.

### `a`

Across all source fields there are 5,535 raw exact-token occurrences in 5,326
rows: 5,532 uppercase `A` and three lowercase `a`. Most are outside the selected
description path, including `Part Status` in 5,326 rows and `ABC Class` in 95.
Other exact occurrences include 27 each in `Part No`, `Part Description in Use`,
`Part Description`, and `Master Part Description`; four slash-delimited
Inventory UoM occurrences; and one each in Site and Site Description.

The active runtime mapping changes 46 selected descriptions: 20 space/other
whole-token cases, seven hyphen-delimited whole-token cases, and 19 tokens
exposed by letter/digit splitting. The 27 Part No exact tokens do not change
because that path does not use `ABBREVIATIONS`.

Concise observed contexts include `First bottle for a water`, `Pencil Type A`,
`RH INV CARBON STICK A`, `AK INV PART A`, `Article Stock A1`, and `PART 06-A`.
These establish collision with article, type/class, part/revision-like, and
alphanumeric designation uses; they do not establish the intended alternative
meaning of every occurrence.

There are 148,167 raw embedded-letter occurrences across the wide dataset.
Again, pure alphabetic embeddings are not replaced. The material exposure is
the 19 selected descriptions where letter/digit splitting creates the exact
token `a`.

## Isolated semantic-impact diagnostic

The diagnostic corpus contains 128 actual CSV records: all 49 rows whose
selected description changes for either alias plus stable immediate-neighbor
controls. It ran the normal candidate, GF4, GF5, and G2-v2 path in disposable
in-memory databases with providers configured as none. Suppression was a
process-local mapping substitution restored after each run; no packaged or
persistent reference changed.

| Metric | Current | Without `co` | Without `a` |
|---|---:|---:|---:|
| Candidate proposals | 84 | 84 | 84 |
| Strong GF4 edges | 3 | 3 | 2 |
| Review GF4 edges | 17 | 17 | 18 |
| Cannot-link GF4 edges | 9 | 9 | 9 |
| Non-groupable GF4 edges | 55 | 55 | 55 |
| Accepted GF5 groups | 14 | 14 | 14 |
| Stronger Evidence groups | 2 | 2 | 1 |
| Review Evidence groups | 12 | 12 | 13 |
| Conflicts | 6 | 6 | 6 |
| Deferred | 1 | 1 | 1 |
| Provider calls | 0 | 0 | 0 |

Suppressing `co` changes normalized text but no proposal, GF4 class, group
membership/status, conflict, or deferral in this bounded corpus.

Suppressing `a` leaves proposals and group membership unchanged but changes the
`RH INV PENCIL A` / `RH PENCIL` relationship from Strong (92.32) to Review
(87.32). Its same two-member group consequently moves from Stronger Evidence to
Review Evidence. Cannot-links, conflicts, and deferrals remain unchanged. This
proves that the global one-character alias currently contributes identity
evidence authority; it does not prove which tier is correct.

## False-expansion and validation assessment

### `co -> coconut`

- `DEVELOPMENT_DATA_DERIVED`: all three active real occurrences are `CO SO MRP`,
  not a source-visible coconut phrase.
- `TEST_DERIVED`: current coconut fixtures depend on `co1`/`c01` and `coco`, not
  standalone `co`.
- `DOCUMENTED_ASSUMPTION`: the mapping originated under a broad ERP synonym
  commit with no narrower rationale.
- `UNVERIFIED`: no client or domain-expert approval exists in repository
  evidence.
- `PORTABILITY_RISK_HYPOTHESIS`: outside this repository `CO` could represent a
  company, material, geography, status, or code. These possibilities are not
  proof and do not determine the observed rows' meaning.

Recommendation: `DISABLE_PENDING_VALIDATION` with high confidence. Confidence
applies to removing global semantic authority pending validation, not to any
claim about what the three observed `CO` values actually mean.

LLM suitability: potentially suitable only as a future bounded advisory case
for unresolved `CO` with field and nearby-token context. An LLM must not write
the deterministic alias or determine identity. A later client-approved meaning
belongs in scoped deterministic reference data.

### `a -> amp`

- `TEST_DERIVED`: `MCB30A` demonstrates a credible numeric-electrical use.
- `DEVELOPMENT_DATA_DERIVED`: 46 selected descriptions also include visibly
  non-amperage grammatical, type, part/revision, and designation contexts.
- `TEST_DERIVED`: suppression changes one Strong edge/group to Review in the
  bounded real-data diagnostic.
- `UNVERIFIED`: no client or domain-expert evidence approves universal `A` to
  amp expansion.
- `PORTABILITY_RISK_HYPOTHESIS`: grade, phase, revision, type, class, side, or
  arbitrary code are possible meanings in other inventories. They are risk
  hypotheses, not proof of any particular observed record.

Recommendation: `MOVE_TO_CONTEXTUAL_CONFIG` with high confidence. A future
rule should require evidence such as numeric adjacency plus electrical context
or an explicit client/field scope; its exact contract must be designed and
tested separately.

LLM suitability: not a good primary LLM case. Known structural amperage forms
are better handled deterministically, while a single-character unknown has too
little standalone context. An optional LLM could later offer a bounded advisory
interpretation only after deterministic contextual rules leave the meaning
unresolved.

## Verification and next task

Provider-free reference, normalizer, candidate, scoring, GF4, resolver-contract,
GF5 policy, group-first orchestration, and determinism coverage passed:
**118 passed** with the existing unknown pytest-option warning. The two isolated
suppression diagnostics made no filesystem or persistent-reference change and
recorded zero provider calls.

No semantic change was authorized or applied. The evidence justifies a separate
bounded change task, not an unreviewed edit during this audit.

Smallest next task: create semantic-reference v2 removing only standalone
`co -> coconut` from global authority, retain `co1`, `co2`, `c01`, `c02`, and
`coco` unchanged, and verify the three affected real descriptions plus full
normalization/candidate/GF4/GF5 regression coverage. Contextualizing `a` should
remain a separate later task.
