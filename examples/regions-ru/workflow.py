"""
workflow.py — Russian federal subjects (субъекты Российской Федерации) lookup.

Faithful Python port of src/regions.js from A1-Localization-RU.

Russian federal subjects, keyed on the ISO 3166-2:RU codes. Pure data + lookups,
no I/O. The data set is loaded from the sibling data.json (83 entries: 2 cities of
federal significance, 21 republics, 9 krais, 46 oblasts, 1 autonomous oblast,
4 autonomous okrugs).

Why the ISO 3166-2:RU standard set (and ONLY it): ISO codes are stable, neutral,
internationally-recognized identifiers. Encoding exactly this set gives downstream
systems a fixed, machine-checkable key space and deliberately avoids the
territorial-claim ambiguity that arises from subjects not recognized in the
international standard.

Subdivision `type` uses the Russian constitutional vocabulary:
  город федерального значения | республика | край | область |
  автономная область | автономный округ

Mirrors the AM sibling (regions-am) — same exported names and shapes, but keyed
on ISO 3166-2:RU instead of ISO 3166-2:AM.

Source of truth (JS, MIT): https://github.com/Armosphera/A1-Localization-RU
Corresponding JS file:   src/regions.js
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATA_PATH = Path(__file__).parent / "data.json"

# Load once at import time (immutable data).
with DATA_PATH.open() as _f:
    _REGIONS = tuple(json.load(_f))

# Lookup index: uppercase code → region.
_BY_CODE: dict[str, dict] = {r["code"]: r for r in _REGIONS}

# Name index: lowercased ru / en name → region.
_BY_NAME: dict[str, dict] = {}
for _r in _REGIONS:
    _BY_NAME[_r["ru"].lower()] = _r
    _BY_NAME[_r["en"].lower()] = _r


def _normalize_code(code: Any) -> str | None:
    if not isinstance(code, str):
        return None
    s = code.strip().upper()
    return s if s else None


def region_by_code(code: Any) -> dict | None:
    c = _normalize_code(code)
    if c is None:
        return None
    return _BY_CODE.get(c)


def is_valid_region_code(code: Any) -> bool:
    return region_by_code(code) is not None


def find_region(query: Any) -> dict | None:
    """Resolve by ISO code OR exact ru/en name (all case-insensitive, trimmed).
    Returns the region dict or None."""
    if not isinstance(query, str):
        return None
    q = query.strip()
    if not q:
        return None
    by_code = _BY_CODE.get(q.upper())
    if by_code is not None:
        return by_code
    return _BY_NAME.get(q.lower())


def cities_for_region(code: Any) -> list[str]:
    """Returns a COPY of the region's cities (centre first), or [] on miss.
    Mutating the returned list does not affect the frozen REGIONS data."""
    r = region_by_code(code)
    return list(r["cities"]) if r is not None else []


# ===========================================================================
# Autoresearch eval entry point
# ===========================================================================
# eval_set items look like:
#   { "input": {"query": "..."}, "expected": {found, code, ru, en, center} }
# For invalid queries: expected = {found: false}

def run_workflow(input: dict) -> dict:
    q = (input or {}).get("query")
    r = find_region(q)
    if r is None:
        return {"found": False, "code": None, "ru": None, "en": None, "center": None}
    return {
        "found": True,
        "code": r.get("code"),
        "ru": r.get("ru"),
        "en": r.get("en"),
        "center": r.get("center"),
    }
