"""
workflow.py — Russian VAT (НДС) — 2026 rates + settlement math.

Faithful Python port of src/vat.js from A1-Localization-RU.

2026 налоговая реформа: base rate 20% → 22% (effective 2026-01-01, ФНС
«Налоги 2026»). Reduced 10% (food/children/medical), 0% (export).
УСН payers may use special 5%/7%. Year-keyed so prior/future years can be
added without breaking callers.

Source of truth (JS, MIT): https://github.com/Armosphera/A1-Localization-RU
Corresponding JS file:   src/vat.js
"""

from __future__ import annotations

import math
from typing import Any


# ===========================================================================
# Inlined money helper — keep self-contained per the framework's 3-file pattern.
# ===========================================================================

def _round_rub(value) -> float:
    """Mirror of money.js roundRub: round to whole kopecks (2 decimals),
    half-toward-+inf (matches JS Math.round)."""
    n = float(value) if isinstance(value, (int, float)) or value is not None else 0.0
    if n != n or n in (float("inf"), float("-inf")):
        return 0.0
    if n >= 0:
        return math.floor(n * 100 + 0.5 + 1e-9) / 100
    return -math.floor(-n * 100 + 0.5 + 1e-9) / 100


# ===========================================================================
# Rates — 2026 налоговая реформа + back-dated 2025.
# ===========================================================================

VAT_RATES: dict[int, dict] = {
    2026: {"standard": 22, "reduced": 10, "zero": 0, "usnLow": 5, "usnHigh": 7},
    2025: {"standard": 20, "reduced": 10, "zero": 0},  # pre-reform, for back-dated docs
}

CURRENT_YEAR = 2026


def rates_for(year: int = CURRENT_YEAR) -> dict:
    return VAT_RATES.get(year, VAT_RATES[CURRENT_YEAR])


def vat_from_net(net: float, rate_percent: float) -> float:
    """VAT added on top of a net (tax-exclusive) amount."""
    n = float(net or 0)
    r = float(rate_percent or 0)
    return _round_rub((n * r) / 100)


def vat_from_gross(gross: float, rate_percent: float) -> float:
    """VAT contained within a gross (tax-inclusive) amount — settlement rate r/(100+r),
    e.g. 22/122, 10/110."""
    g = float(gross or 0)
    r = float(rate_percent or 0)
    if r <= 0:
        return 0.0
    return _round_rub((g * r) / (100 + r))


def net_from_gross(gross: float, rate_percent: float) -> float:
    return _round_rub((float(gross or 0)) - vat_from_gross(gross, rate_percent))


def is_valid_vat_rate(rate_percent: float, opts: dict = None) -> bool:
    """Allowed rate? УСН regime adds the special 5%/7% rates (2026)."""
    o = opts or {}
    r = float(rate_percent or 0)
    allowed = [0, 5, 7, 10, 22] if o.get("regime") == "usn" else [0, 10, 22]
    return r in allowed


# ===========================================================================
# Autoresearch eval entry point
# ===========================================================================
# eval_set items look like:
#   { "input": {operation, ...args}, "expected": {"result": <value>} }
# Per-case field set: {result} only (operation dispatch + polymorphic return).

def run_workflow(input: dict) -> dict:
    o = input or {}
    op = o.get("operation")
    if op == "ratesFor":
        return {"result": rates_for(o.get("year", CURRENT_YEAR))}
    if op == "vatFromNet":
        return {"result": vat_from_net(o.get("net"), o.get("ratePercent"))}
    if op == "vatFromGross":
        return {"result": vat_from_gross(o.get("gross"), o.get("ratePercent"))}
    if op == "netFromGross":
        return {"result": net_from_gross(o.get("gross"), o.get("ratePercent"))}
    if op == "isValidVatRate":
        return {"result": is_valid_vat_rate(o.get("ratePercent"), o.get("opts") or {})}
    return {"result": None}
