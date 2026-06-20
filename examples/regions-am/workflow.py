"""
workflow.py — Armenian administrative-region (marz) dictionary, Python port.

Faithful Python port of src/armeniaRegions.js from A1-Localization-AM.
Armenia has 11 administrative divisions: 10 provinces (marzes) plus the capital
Yerevan. Keyed on official ISO 3166-2:AM codes so addresses, SRC e-invoices,
shipping, and analytics share stable identifiers.

  regionByCode(code)   — exact match on ISO code (case-insensitive, whitespace-trimmed)
  isValidRegionCode(code) — bool wrapper around regionByCode
  findRegion(query)    — match by code, Armenian name, or English name
  citiesForRegion(code) — returns the marz center first, then other major cities

Source of truth (JS, MIT): https://github.com/Armosphera/A1-Localization-AM
Corresponding JS file:   src/armeniaRegions.js
JS test contract:         test/armenia-regions.test.js
"""

from __future__ import annotations

from typing import Any

REGIONS = [
    {"code": "AM-ER", "hy": "Երևան", "en": "Yerevan", "center": "Երևան", "cities": ["Երևան"]},
    {"code": "AM-AG", "hy": "Արագածոտն", "en": "Aragatsotn", "center": "Աշտարակ", "cities": ["Աշտարակ", "Ապարան", "Թալին"]},
    {"code": "AM-AR", "hy": "Արարատ", "en": "Ararat", "center": "Արտաշատ", "cities": ["Արտաշատ", "Մասիս", "Արարատ", "Վեդի"]},
    {"code": "AM-AV", "hy": "Արմավիր", "en": "Armavir", "center": "Արմավիր", "cities": ["Արմավիր", "Վաղարշապատ", "Մեծամոր"]},
    {"code": "AM-GR", "hy": "Գեղարքունիք", "en": "Gegharkunik", "center": "Գավառ", "cities": ["Գավառ", "Սևան", "Մարտունի", "Վարդենիս", "Ճամբարակ"]},
    {"code": "AM-KT", "hy": "Կոտայք", "en": "Kotayk", "center": "Հրազդան", "cities": ["Հրազդան", "Աբովյան", "Չարենցավան", "Եղվարդ", "Ծաղկաձոր"]},
    {"code": "AM-LO", "hy": "Լոռի", "en": "Lori", "center": "Վանաձոր", "cities": ["Վանաձոր", "Ալավերդի", "Սպիտակ", "Ստեփանավան", "Թումանյան"]},
    {"code": "AM-SH", "hy": "Շիրակ", "en": "Shirak", "center": "Գյումրի", "cities": ["Գյումրի", "Արթիկ", "Մարալիկ"]},
    {"code": "AM-SU", "hy": "Սյունիք", "en": "Syunik", "center": "Կապան", "cities": ["Կապան", "Գորիս", "Սիսիան", "Մեղրի", "Քաջարան"]},
    {"code": "AM-TV", "hy": "Տավուշ", "en": "Tavush", "center": "Իջևան", "cities": ["Իջևան", "Դիլիջան", "Բերդ", "Նոյեմբերյան"]},
    {"code": "AM-VD", "hy": "Վայոց Ձոր", "en": "Vayots Dzor", "center": "Եղեգնաձոր", "cities": ["Եղեգնաձոր", "Վայք", "Ջերմուկ"]},
]

REGION_CODES = [r["code"] for r in REGIONS]

_BY_CODE = {r["code"]: r for r in REGIONS}


def region_by_code(code: Any) -> dict | None:
    if not code or not isinstance(code, str):
        return None
    return _BY_CODE.get(code.strip().upper()) or None


def is_valid_region_code(code: Any) -> bool:
    return region_by_code(code) is not None


def find_region(query: Any) -> dict | None:
    if not query or not isinstance(query, str):
        return None
    q = query.strip().lower()
    if not q:
        return None
    by_code = region_by_code(query)
    if by_code:
        return by_code
    for r in REGIONS:
        if r["hy"].lower() == q or r["en"].lower() == q:
            return r
    return None


def cities_for_region(code: Any) -> list[str]:
    region = region_by_code(code)
    return list(region["cities"]) if region else []


# ---------------------------------------------------------------------------
# Adapter for the eval harness.
# ---------------------------------------------------------------------------

def run_workflow(input_data: dict[str, Any]) -> dict[str, Any]:
    """Adapter for eval.py. Takes {"query": "<search string>"}.

    Output:
      {
        "found":  bool,           # True iff a region matched
        "code":   str | None,     # ISO 3166-2:AM code (e.g., "AM-ER")
        "hy":     str | None,     # Armenian name
        "en":     str | None,     # English name
        "center": str | None,     # Marz center city (Armenian)
      }
    """
    query = input_data.get("query") if isinstance(input_data, dict) else input_data
    region = find_region(query)
    if region is None:
        return {"found": False, "code": None, "hy": None, "en": None, "center": None}
    return {
        "found":  True,
        "code":   region["code"],
        "hy":     region["hy"],
        "en":     region["en"],
        "center": region["center"],
    }
