"""
workflow.py — HHVH (Armenian taxpayer id) validation, Python port + extension hooks.

This file is the agent's lever. The default implementation is a faithful Python port of
src/localization.js::validateHvhh() from A1-Localization-AM (the official SBOSS Armenian
localization module). The agent's job is to extend it: most importantly, implement the
official Armenian HHVH check-digit algorithm (currently a documented TODO seam in the JS).

Source of truth (JS, MIT): https://github.com/Armosphera/A1-Localization-AM
Corresponding JS function: src/localization.js :: validateHvhh()
JS test contract:          test/localization.test.js
"""

from __future__ import annotations

import re
from typing import Any

HVHH_LENGTH = 8

# Match the JS regex /[\s.\-]/g — strip ASCII whitespace, dot, hyphen.
_SEPARATOR_RE = re.compile(r"[\s.\-]")
_ALL_DIGITS_RE = re.compile(r"^[0-9]+$")
_ALL_SAME_RE = re.compile(r"^(\d)\1{7}$")


def normalize_hvhh(value: Any) -> str:
    """Strip common separators (spaces, dots, hyphens). Returns "" for null/None."""
    if value is None:
        return ""
    return _SEPARATOR_RE.sub("", str(value))


def _default_check_digit(hvhh: str) -> bool:
    """Default check-digit verifier (currently accepts any non-degenerate 8-digit string).

    This is the documented TODO seam from src/localization.js. The Armenian State Revenue
    Committee publishes the official HHVH check-digit algorithm; implementing it here is
    the agent's main lever for improving validation accuracy.

    Args:
        hvhh: an 8-digit string that has already passed length / digits / non-degenerate checks.

    Returns:
        True if the check digit is valid, False if not.
    """
    # TODO: implement official Armenian HHVH check-digit algorithm.
    # See: https://www.petekamutner.am/ (Armenian tax authority)
    return True


def validate_hvhh(value: Any, *, check_digit_verifier=None) -> dict[str, Any]:
    """Validate an HHVH. Mirrors src/localization.js::validateHvhh().

    Args:
        value: raw input (string, None, or anything str()-coercible).
        check_digit_verifier: optional callable (str) -> bool. If supplied and returns False,
            validation fails with the check-digit error. Defaults to the local _default_check_digit.

    Returns:
        { ok: bool, normalized: str, error: str | None }
    """
    verifier = check_digit_verifier if check_digit_verifier is not None else _default_check_digit

    normalized = normalize_hvhh(value)
    if not normalized:
        return {"ok": False, "normalized": "", "error": "ՀՎՀՀ-ն պարտադիր է"}
    if not _ALL_DIGITS_RE.match(normalized):
        return {"ok": False, "normalized": normalized, "error": "ՀՎՀՀ-ն պետք է պարունակի միայն թվանշաններ"}
    if len(normalized) != HVHH_LENGTH:
        return {"ok": False, "normalized": normalized, "error": f"ՀՎՀՀ-ն պետք է լինի {HVHH_LENGTH} նիշ"}
    if _ALL_SAME_RE.match(normalized):
        return {"ok": False, "normalized": normalized, "error": "ՀՎՀՀ-ն անվավեր է"}
    if not verifier(normalized):
        return {"ok": False, "normalized": normalized, "error": "ՀՎՀՀ-ի ստուգիչ նիշը սխալ է"}
    return {"ok": True, "normalized": normalized, "error": None}


# ---------------------------------------------------------------------------
# Adapter for the eval harness (eval.py expects this signature).
# ---------------------------------------------------------------------------

def run_workflow(input_data: dict[str, Any]) -> dict[str, Any]:
    """Adapter: takes the eval harness's input shape, returns validation result.

    Input:  { "hvhh": "<raw HHVH string>" }
    Output: { "ok": bool, "normalized": str, "error": str | None }
    """
    return validate_hvhh(input_data.get("hvhh"))
