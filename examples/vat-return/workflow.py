"""
workflow.py — Armenian VAT return computation, Python port + extension hooks.

Default implementation is a faithful Python port of src/vatReturn.js::computeVatReturn()
from A1-Localization-AM (the official SBOSS Armenian localization module).
The agent's job is to make this STRICTLY MORE USEFUL than the JS reference: add input
validation, audit trail, and (optionally) multi-period aggregation.

Source of truth (JS, MIT): https://github.com/Armosphera/A1-Localization-AM
Corresponding JS file:   src/vatReturn.js
JS test contract:         test/vat-return.test.js
"""

from __future__ import annotations

import math
from typing import Any

# Armenia VAT rates per decree N 298-Ն (arlis.am/hy/acts/136996)
STANDARD_VAT_RATE = 20
IMPUTED_VAT_RATE = 16.67  # 20/120; form line 9


def round_amd(amount: Any) -> int:
    """Match JS Math.round() (half toward +∞). Pure whole-dram amounts per localization kernel."""
    n = float(amount) if amount is not None else 0.0
    if not math.isfinite(n):
        return 0
    # JS Math.round: half rounds toward +∞ (0.5→1, -0.5→0). Python's round() is banker's
    # rounding. Reproduce JS exactly so the port matches.
    if n >= 0:
        return math.floor(n + 0.5)
    return -math.floor(-n + 0.5)


def _line_vat(line: dict[str, Any]) -> dict[str, int]:
    """Per-line: round net, compute or take-provided vat."""
    net = round_amd(line.get("netAmount"))
    rate = line.get("vatRate")
    rate = float(rate) if isinstance(rate, (int, float)) and not isinstance(rate, bool) else 0
    provided_vat = line.get("vatAmount")
    if provided_vat is not None:
        vat = round_amd(provided_vat)
    else:
        vat = round_amd((net * rate) / 100)
    return {"net": net, "vat": vat}


def compute_vat_return(payload: dict[str, Any] | None = None) -> dict[str, int]:
    """Faithful port of computeVatReturn() from src/vatReturn.js.

    Args:
        payload: {"sales": [...], "purchases": [...]} — see program.md for line shape.

    Returns:
        {outputVat, inputVat, taxableSales, taxablePurchases, net, payable, creditCarried}
    """
    payload = payload or {}
    sales = payload.get("sales") or []
    purchases = payload.get("purchases") or []

    output_vat = 0
    taxable_sales = 0
    for s in sales:
        v = _line_vat(s)
        output_vat += v["vat"]
        taxable_sales += v["net"]

    input_vat = 0
    taxable_purchases = 0
    for p in purchases:
        v = _line_vat(p)
        taxable_purchases += v["net"]
        # recoverable by default; only skip when explicitly false
        if p.get("recoverable") is not False:
            input_vat += v["vat"]

    net = output_vat - input_vat
    return {
        "outputVat": output_vat,
        "inputVat": input_vat,
        "taxableSales": taxable_sales,
        "taxablePurchases": taxable_purchases,
        "net": net,
        "payable": max(0, net),
        "creditCarried": max(0, -net),
    }


# ---------------------------------------------------------------------------
# Adapter for the eval harness.
# ---------------------------------------------------------------------------

def run_workflow(input_data: dict[str, Any]) -> dict[str, Any]:
    """Adapter for eval.py. Takes {sales, purchases}, returns compute_vat_return output."""
    return compute_vat_return(input_data)
