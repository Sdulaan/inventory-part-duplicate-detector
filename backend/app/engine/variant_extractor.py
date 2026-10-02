import re

from app.engine.normalizer import normalize_description


FILTER_FUNCTION = {"air", "fuel", "oil", "water", "hydraulic"}
COLOR = {"red", "blue", "green", "black", "white", "yellow"}
SIZE_PHRASES = {
    "extra small": "extra small",
    "xs": "extra small",
    "small": "small",
    "medium": "medium",
    "large": "large",
    "xl": "extra large",
    "extra large": "extra large",
}
SENSOR_TYPE = {"temperature", "pressure", "flow", "level"}
SIDE_MAP = {
    "left": "left",
    "lh": "left",
    "right": "right",
    "rh": "right",
    "front": "front",
    "rear": "rear",
}
CONNECTIVITY = {"wired", "wireless"}
ENVIRONMENT = {"indoor", "outdoor"}
OPERATION_MODE = {"manual", "automatic"}
PLACEMENT = {"internal", "external"}
HIERARCHY = {"primary", "secondary"}
SIGNAL_TYPE = {"analog", "digital"}
STRUCTURAL_ROLE_MAP = {
    "top": "top",
    "comp": "component",
    "component": "component",
    "assy": "assembly",
    "assembly": "assembly",
    "sub": "subassembly",
    "subassembly": "subassembly",
    "base": "base",
    "module": "module",
    "kit": "kit",
    "rotor": "rotor",
    "stator": "stator",
}

VARIANT_GROUP_LABELS = {
    "FILTER_FUNCTION": "critical function",
    "COLOR": "color",
    "SIZE": "size",
    "TYPE_OR_GRADE": "type",
    "ELECTRICAL_RATING": "ampere rating",
    "DIMENSION": "dimension",
    "SENSOR_TYPE": "sensor type",
    "SIDE": "side",
    "CONNECTIVITY": "connectivity",
    "ENVIRONMENT": "environment",
    "OPERATION_MODE": "operation mode",
    "PLACEMENT": "placement",
    "HIERARCHY": "hierarchy",
    "SIGNAL_TYPE": "signal type",
}

IDENTITY_ROLE_GROUP_LABELS = {
    "END_POSITION": "bearing end position",
    "SERIALIZATION_ROLE": "serialization role",
    "FLOW_ROLE": "flow role",
    "ENGINE_COMPONENT_ROLE": "engine component role",
}

ONE_SIDED_QUALIFIER_GROUPS = {
    "CONNECTIVITY",
    "ENVIRONMENT",
    "OPERATION_MODE",
    "PLACEMENT",
    "HIERARCHY",
    "SIGNAL_TYPE",
    # A sized SKU (jumpsuit M) and an unsized record are not confirmed as one item.
    "SIZE",
}
ORDINAL_WORDS = {
    "first": "1",
    "second": "2",
    "third": "3",
    "fourth": "4",
    "fifth": "5",
    "sixth": "6",
    "seventh": "7",
    "eighth": "8",
    "ninth": "9",
    "tenth": "10",
}


def _words(text: str) -> set[str]:
    return set(text.split())


SIZE_CODES = {
    "xxs": "extra extra small",
    "xs": "extra small",
    "s": "small",
    "m": "medium",
    "l": "large",
    "xl": "extra large",
    "xxl": "extra extra large",
    "xxxl": "extra extra extra large",
    "2xl": "extra extra large",
    "3xl": "extra extra extra large",
    "4xl": "4x large",
    "5xl": "5x large",
    "onesize": "one size",
    "onesz": "one size",
    "os": "one size",
}
# A single letter after one of these words is a type/series code ("TYPE S"),
# not a garment size.
_SIZE_CODE_BLOCKERS = {"type", "grade", "class", "series", "model"}


# Size ranges written without the slash in some catalogues (ML = M/L).
_SIZE_RANGE_ALIASES = {"ml": "m/l", "sm": "s/m", "xss": "xs/s", "lxl": "l/xl"}


def _size_code_value(token: str) -> str | None:
    """A size code, or a size range written with "/" (M/L, XS/S)."""
    token = token.strip().casefold()
    token = _SIZE_RANGE_ALIASES.get(token, token)
    if token in SIZE_CODES:
        return SIZE_CODES[token]
    parts = token.split("/")
    if len(parts) == 2 and all(part in SIZE_CODES for part in parts):
        return "/".join(SIZE_CODES[part] for part in parts)
    return None


def _find_size_codes(raw: str) -> list[str]:
    """Size codes when marked as sizes: "(S)", "size M", or the last word.

    The last word counts only after a non-numeric word, so "Nova jumpsuit
    black/stripe m" and "tights black (9000) l" are sizes, while "cable 5 m"
    (metres) and "oil 10 l" (litres) and "pipe clamp type s" are not.
    """
    codes = "|".join(sorted(SIZE_CODES, key=len, reverse=True))
    found = [
        SIZE_CODES[code.casefold()]
        for code in re.findall(rf"\(\s*({codes})\s*\)", raw, flags=re.IGNORECASE)
    ]
    found += [
        SIZE_CODES[code.casefold()]
        for code in re.findall(rf"\b(?:size|sz)\s*:?\s*({codes})\b", raw, flags=re.IGNORECASE)
    ]
    words = raw.strip().split()
    if len(words) >= 2:
        last = re.sub(r"^[-/]+", "", words[-1])
        previous = words[-2].casefold().strip("-/")
        value = _size_code_value(last)
        if (
            value
            and not re.fullmatch(r"\d+(?:[.,]\d+)?", previous)
            and previous not in _SIZE_CODE_BLOCKERS
        ):
            found.append(value)
    # A size glued on with "-" or "/" ("HOODIE-L") keeps the earlier rule.
    marked = re.search(rf"[-/]\s*({codes})\s*$", raw.strip(), flags=re.IGNORECASE)
    if marked and not found:
        found.append(SIZE_CODES[marked.group(1).casefold()])
    return found


_WRITTEN_NUMBER = re.compile(r"\d+(?:[.,]\d+)?(?:/\d+(?:[.,]\d+)?)?")


def _written_number(value: str) -> str:
    return str(int(value)) if value.isdigit() else value


def _find_numeric_variant(raw: str, normalized: str) -> tuple[list[str], list[str]]:
    """Return the ordered numbers, as written, and the text around them.

    Two descriptions with the same surrounding text but different numbers
    (40x60 vs 60x60, 10' vs 20', M10 vs M12) describe different items.
    """
    numbers = _WRITTEN_NUMBER.findall(raw)
    if not numbers:
        return [], []
    base = re.sub(r"\d+", "#", normalized).strip()
    if not re.search(r"[a-z]", base):
        return [], []
    return [" ".join(_written_number(number) for number in numbers)], [base]


def _find_size(normalized: str, raw: str = "") -> list[str]:
    found = _find_size_codes(raw)
    protected = normalized
    words = raw.strip().split()
    if found and words:
        # The trailing size code was already read as one value ("xs/s"); do
        # not read its parts again as separate sizes.
        tail = normalize_description(words[-1])
        if tail and protected.endswith(tail):
            protected = protected[: -len(tail)]
    for phrase in ("extra small", "extra large"):
        if re.search(rf"\b{re.escape(phrase)}\b", protected):
            found.append(SIZE_PHRASES[phrase])
            protected = re.sub(rf"\b{re.escape(phrase)}\b", " ", protected)
    for token in ("xs", "xl", "small", "medium", "large"):
        if re.search(rf"\b{re.escape(token)}\b", protected):
            found.append(SIZE_PHRASES[token])
    return sorted(set(found))


def _find_type_or_grade(normalized: str) -> list[str]:
    matches = re.findall(r"\b(?:type|grade)\s+[a-z0-9]+\b", normalized)
    return sorted(set(matches))


def _find_electrical(raw: str, normalized: str) -> list[str]:
    values = set()
    for match in re.findall(r"\b(\d+(?:\.\d+)?)\s*a\b", raw, flags=re.IGNORECASE):
        values.add(f"{match.upper()}A")
    for match in re.findall(r"\b(\d+(?:\.\d+)?)\s*amp\b", normalized):
        values.add(f"{match.upper()}A")
    for match in re.findall(r"\b(\d+(?:\.\d+)?)\s*v\b", raw, flags=re.IGNORECASE):
        values.add(f"{match.upper()}V")
    for match in re.findall(r"\b(\d+(?:\.\d+)?)\s*volt\b", normalized):
        values.add(f"{match.upper()}V")
    return sorted(values)


def _find_dimensions(raw: str, normalized: str) -> list[str]:
    values = set()
    for source in (raw, normalized):
        for match in re.findall(r"\b(\d+(?:\.\d+)?)\s*mm\b", source, flags=re.IGNORECASE):
            values.add(f"{match.upper()}MM")
    return sorted(values)


def _find_trailing_variant(description) -> tuple[list[str], list[str]]:
    raw = "" if description is None else str(description).strip().lower()
    numeric = re.match(r"^(.*?\S)[\s_-]+(\d+)(?:st|nd|rd|th)?$", raw)
    if numeric:
        base = normalize_description(numeric.group(1))
        return [str(int(numeric.group(2)))], [base] if base else []

    normalized = normalize_description(description)
    words = normalized.split()
    if len(words) >= 2 and words[-1] in ORDINAL_WORDS:
        return [ORDINAL_WORDS[words[-1]]], [" ".join(words[:-1])]
    return [], []


def _find_structural_roles(normalized: str) -> list[str]:
    words = normalized.split()
    roles = set()
    if "subassembly" in words or (
        "sub" in words and ({"assembly", "assy"} & set(words))
    ):
        roles.add("subassembly")
    for word in words:
        role = STRUCTURAL_ROLE_MAP.get(word)
        if role and not (role == "assembly" and "subassembly" in roles):
            roles.add(role)
    return sorted(roles)


def _find_sides(normalized: str) -> list[str]:
    return sorted({SIDE_MAP[word] for word in normalized.split() if word in SIDE_MAP})


def _find_end_positions(normalized: str) -> list[str]:
    """Extract explicit DE/NDE placement without substring or one-sided inference."""
    values = set()
    protected = normalized
    if re.search(r"\bnon drive end\b", protected):
        values.add("non-drive-end")
        protected = re.sub(r"\bnon drive end\b", " ", protected)
    if re.search(r"\bdrive end\b", protected):
        values.add("drive-end")
    words = set(normalized.split())
    if "nde" in words:
        values.add("non-drive-end")
    if "de" in words:
        values.add("drive-end")
    return sorted(values)


def _find_serialization_roles(normalized: str) -> list[str]:
    values = set()
    protected = normalized
    if re.search(r"\bnon serial\b", protected):
        values.add("non-serial")
        protected = re.sub(r"\bnon serial\b", " ", protected)
    if re.search(r"\bserial\b", protected):
        values.add("serial")
    return sorted(values)


def _find_flow_roles(normalized: str) -> list[str]:
    words = set(normalized.split())
    return sorted(words & {"inlet", "outlet"})


def _find_engine_component_roles(normalized: str) -> list[str]:
    """Recognize only explicit component roles within an engine description."""
    words = set(normalized.split())
    if "engine" not in words:
        return []
    roles = set()
    if "block" in words:
        roles.add("block")
    if "head" in words:
        roles.add("head")
    if words & {"piston", "pistons"}:
        roles.add("pistons")
    if "fuel" in words and "pump" in words:
        roles.add("fuel-pump")
    return sorted(roles)


def extract_variant_attributes(description) -> dict[str, list[str]]:
    raw = "" if description is None else str(description).lower()
    normalized = normalize_description(description)
    words = _words(normalized)
    trailing_suffix, trailing_base = _find_trailing_variant(description)
    numeric_values, numeric_base = _find_numeric_variant(raw, normalized)
    return {
        "FILTER_FUNCTION": sorted(words & FILTER_FUNCTION),
        "COLOR": sorted(words & COLOR),
        "SIZE": _find_size(normalized, raw),
        "TYPE_OR_GRADE": _find_type_or_grade(normalized),
        "ELECTRICAL_RATING": _find_electrical(raw, normalized),
        "DIMENSION": _find_dimensions(raw, normalized),
        "SENSOR_TYPE": sorted(words & SENSOR_TYPE),
        "SIDE": _find_sides(normalized),
        "CONNECTIVITY": sorted(words & CONNECTIVITY),
        "ENVIRONMENT": sorted(words & ENVIRONMENT),
        "OPERATION_MODE": sorted(words & OPERATION_MODE),
        "PLACEMENT": sorted(words & PLACEMENT),
        "HIERARCHY": sorted(words & HIERARCHY),
        "SIGNAL_TYPE": sorted(words & SIGNAL_TYPE),
        "END_POSITION": _find_end_positions(normalized),
        "SERIALIZATION_ROLE": _find_serialization_roles(normalized),
        "FLOW_ROLE": _find_flow_roles(normalized),
        "ENGINE_COMPONENT_ROLE": _find_engine_component_roles(normalized),
        "STRUCTURAL_ROLE": _find_structural_roles(normalized),
        "TRAILING_VARIANT_SUFFIX": trailing_suffix,
        "TRAILING_VARIANT_BASE": trailing_base,
        "NUMERIC_VARIANT_VALUES": numeric_values,
        "NUMERIC_VARIANT_BASE": numeric_base,
    }


def find_critical_mismatches(attributes_a: dict, attributes_b: dict) -> list[dict]:
    mismatches = []
    for group, label in VARIANT_GROUP_LABELS.items():
        values_a = set(attributes_a.get(group, []))
        values_b = set(attributes_b.get(group, []))
        if values_a and values_b and values_a != values_b:
            mismatches.append({
                "group": group,
                "label": label,
                "values_a": sorted(values_a),
                "values_b": sorted(values_b),
            })
    suffix_a = set(attributes_a.get("TRAILING_VARIANT_SUFFIX", []))
    suffix_b = set(attributes_b.get("TRAILING_VARIANT_SUFFIX", []))
    base_a = set(attributes_a.get("TRAILING_VARIANT_BASE", []))
    base_b = set(attributes_b.get("TRAILING_VARIANT_BASE", []))
    if suffix_a and suffix_b and suffix_a != suffix_b and base_a == base_b and base_a:
        mismatches.append({
            "group": "TRAILING_VARIANT_SUFFIX",
            "label": "trailing variant suffix",
            "values_a": sorted(suffix_a),
            "values_b": sorted(suffix_b),
        })
    if not mismatches:
        numeric = _numeric_variant_mismatch(attributes_a, attributes_b)
        if numeric:
            mismatches.append(numeric)
    return mismatches


def _numeric_variant_numbers(
    attributes_a: dict, attributes_b: dict
) -> tuple[list[str], list[str]] | None:
    """Numbers of two descriptions whose surrounding wording is identical."""
    base_a = attributes_a.get("NUMERIC_VARIANT_BASE", [])
    base_b = attributes_b.get("NUMERIC_VARIANT_BASE", [])
    values_a = attributes_a.get("NUMERIC_VARIANT_VALUES", [])
    values_b = attributes_b.get("NUMERIC_VARIANT_VALUES", [])
    if not (base_a and base_a == base_b and values_a and values_b):
        return None
    return values_a[0].split(), values_b[0].split()


def _numeric_variant_mismatch(attributes_a: dict, attributes_b: dict) -> dict | None:
    """Same wording, different numbers: report only the numbers that differ."""
    numbers = _numeric_variant_numbers(attributes_a, attributes_b)
    if numbers is None:
        return None
    numbers_a, numbers_b = numbers
    if sorted(numbers_a) == sorted(numbers_b):
        return None  # same numbers in another order: see find_reordered_numbers
    differing = [(a, b) for a, b in zip(numbers_a, numbers_b) if a != b]
    if len(numbers_a) != len(numbers_b) or not differing:
        differing = [(" x ".join(numbers_a), " x ".join(numbers_b))]
    return {
        "group": "NUMERIC_VARIANT",
        "label": "number (size, length or rating)",
        "values_a": [a for a, _b in differing],
        "values_b": [b for _a, b in differing],
    }


def find_reordered_numbers(attributes_a: dict, attributes_b: dict) -> dict | None:
    """Same wording and numbers in a different order, e.g. 20x30 vs 30x20.

    This may be one item written two ways, so it is borderline, not a conflict.
    """
    numbers = _numeric_variant_numbers(attributes_a, attributes_b)
    if numbers is None:
        return None
    numbers_a, numbers_b = numbers
    if numbers_a == numbers_b or sorted(numbers_a) != sorted(numbers_b):
        return None
    return {
        "group": "REORDERED_NUMBERS",
        "label": "number order",
        "values_a": [" x ".join(numbers_a)],
        "values_b": [" x ".join(numbers_b)],
    }


def find_identity_role_mismatches(attributes_a: dict, attributes_b: dict) -> list[dict]:
    """Return explicit two-sided identity-role conflicts for deterministic scoring."""
    mismatches = []
    for group, label in IDENTITY_ROLE_GROUP_LABELS.items():
        values_a = set(attributes_a.get(group, []))
        values_b = set(attributes_b.get(group, []))
        if values_a and values_b and values_a != values_b:
            mismatches.append({
                "group": group,
                "label": label,
                "values_a": sorted(values_a),
                "values_b": sorted(values_b),
            })
    return mismatches


def find_one_sided_qualifier(attributes_a: dict, attributes_b: dict) -> dict | None:
    """Find a defining qualifier present on only one side of a candidate pair."""
    for group in sorted(ONE_SIDED_QUALIFIER_GROUPS):
        values_a = set(attributes_a.get(group, []))
        values_b = set(attributes_b.get(group, []))
        if bool(values_a) != bool(values_b):
            return {
                "group": group,
                "label": VARIANT_GROUP_LABELS[group],
                "values_a": sorted(values_a),
                "values_b": sorted(values_b),
            }
    return None


def find_structural_role_mismatch(attributes_a: dict, attributes_b: dict) -> dict | None:
    """Return softer evidence when assembly roles differ between descriptions."""
    values_a = set(attributes_a.get("STRUCTURAL_ROLE", []))
    values_b = set(attributes_b.get("STRUCTURAL_ROLE", []))
    if values_a and values_b and values_a != values_b:
        return {
            "group": "STRUCTURAL_ROLE",
            "label": "structural role",
            "values_a": sorted(values_a),
            "values_b": sorted(values_b),
        }
    return None
