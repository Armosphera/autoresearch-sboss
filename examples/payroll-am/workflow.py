"""
workflow.py — Armenian payroll rules engine, Python port + extension hooks.

Computes gross → net under current (2026) RA rules. Four employee withholdings,
all computed independently off the SAME gross:
  1. Personal income tax (եկամտային հարկ): flat 20% (since 1 Jan 2023).
  2. Mandatory funded pension (կուտակային վճար): tiered 5% / 10%−25k, capped 87,500.
  3. Stamp duty / military payment (դրոշմանիշային վճար): flat 1,000/mo (2026 revision).
  4. Universal health-insurance premium: 0 / 4,800 / 10,800 by gross bands (Dec-2025 law).

Source of truth (JS, MIT): https://github.com/Armosphera/A1-Localization-AM
Corresponding JS file:   src/armeniaPayroll.js
JS test contract:         test/armenia-payroll.test.js
"""

from __future__ import annotations

import math
from typing import Any

INCOME_TAX_RATE = 20  # flat %, since 1 Jan 2023

PENSION_LOW_CEIL = 500000
PENSION_CAP_THRESHOLD = 1125000
PENSION_CAP = 87500

# 2026 revision: flat 1,000/mo (was previously tiered 1,500/3,000/5,500/8,500).
STAMP_DUTY_2026 = 1000

# Health insurance bands (Dec-2025 law):
HEALTH_INSURANCE_MIN_GROSS = 200001
HEALTH_INSURANCE_LOW_CEIL = 500000
HEALTH_INSURANCE_LOW = 4800   # 10,800 - 6,000 state reimbursement
HEALTH_INSURANCE_FULL = 10800


def round_amd(amount: Any) -> int:
    """Match JS Math.round() (half toward +∞). Whole dram via localization kernel."""
    n = float(amount) if amount is not None else 0.0
    if not math.isfinite(n):
        return 0
    if n >= 0:
        return math.floor(n + 0.5)
    return -math.floor(-n + 0.5)


def income_tax(gross: Any) -> int:
    g = round_amd(gross)
    return 0 if g <= 0 else round_amd((g * INCOME_TAX_RATE) / 100)


def pension(gross: Any) -> int:
    g = round_amd(gross)
    if g <= 0:
        return 0
    if g <= PENSION_LOW_CEIL:
        return round_amd(g * 0.05)
    if g <= PENSION_CAP_THRESHOLD:
        return round_amd(g * 0.10 - 25000)
    return PENSION_CAP


def stamp_duty(gross: Any) -> int:
    g = round_amd(gross)
    return 0 if g <= 0 else STAMP_DUTY_2026


def health_insurance(gross: Any) -> int:
    g = round_amd(gross)
    if g < HEALTH_INSURANCE_MIN_GROSS:
        return 0
    return HEALTH_INSURANCE_LOW if g <= HEALTH_INSURANCE_LOW_CEIL else HEALTH_INSURANCE_FULL


def compute_payroll(gross_input: Any) -> dict[str, int]:
    """Faithful port of computePayroll() from src/armeniaPayroll.js.

    Args:
        gross_input: gross monthly salary in AMD (int, float, or numeric string-coercible)

    Returns:
        {gross, incomeTax, pension, stampDuty, healthInsurance, totalWithholdings, net}
    """
    gross = round_amd(gross_input)
    tax = income_tax(gross)
    pen = pension(gross)
    stamp = stamp_duty(gross)
    health = health_insurance(gross)
    total = tax + pen + stamp + health
    return {
        "gross": gross,
        "incomeTax": tax,
        "pension": pen,
        "stampDuty": stamp,
        "healthInsurance": health,
        "totalWithholdings": total,
        "net": gross - total,
    }


# ---------------------------------------------------------------------------
# Adapter for the eval harness.
# ---------------------------------------------------------------------------

def run_workflow(input_data: dict[str, Any]) -> dict[str, Any]:
    """Adapter for eval.py. Takes {"gross": <amount>}, returns compute_payroll output."""
    return compute_payroll(input_data.get("gross"))
