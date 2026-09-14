import re
from functools import lru_cache
from typing import Any

from app.reference_data.semantic_aliases import DOMAIN_TOKEN_MAP


def _tokenize(text: Any) -> list[str]:
    if text is None:
        return []
    value = str(text).strip().lower()
    if value in {"", "nan", "none"}:
        return []
    value = re.sub(r"[^a-z0-9]+", " ", value)
    tokens = []
    for token in value.split():
        if token in DOMAIN_TOKEN_MAP:
            tokens.append(token)
        else:
            tokens.extend(re.sub(r"(?<=[a-z])(?=\d)|(?<=\d)(?=[a-z])", " ", token).split())
    return tokens


@lru_cache(maxsize=100_000)
def expand_domain_tokens(text: Any) -> str:
    words = []
    for token in _tokenize(text):
        replacement = DOMAIN_TOKEN_MAP.get(token, token)
        words.extend(replacement.split())
    if "coconut" in words:
        expanded = []
        index = 0
        while index < len(words):
            if (
                words[index].isdigit()
                and index > 0
                and words[index - 1] == "coconut"
            ):
                expanded.extend(["type", words[index]])
            else:
                expanded.append(words[index])
            index += 1
        words = expanded
    return " ".join(words)


@lru_cache(maxsize=100_000)
def normalize_description_with_dictionary(text: Any) -> str:
    return expand_domain_tokens(text)


@lru_cache(maxsize=100_000)
def normalize_part_no_with_dictionary(part_no: Any) -> str:
    return expand_domain_tokens(part_no)
