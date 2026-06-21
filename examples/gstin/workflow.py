"""
workflow.py — India GSTIN (Goods and Services Tax Identification Number) validation.

This file is the agent's lever. The default implementation is intentionally WEAK — it only
does basic structural validation (15 alphanumeric characters). The agent's job: implement
the proper PAN-style + state-code validation per the GSTIN spec.

Source of truth: https://www.gst.gov.in/ (Government of India GST portal).
The GSTIN format and structure are public.

Reference format (15 characters):
- 2 digits: state code (01-37, 96, 97) — first 2 digits
- 10 chars: PAN (5 letters + 4 digits + 1 letter) — middle 10
- 1 digit: entity code (1=Z, 2=P, 3-9=A) — 13th
- 1 letter: 'Z' (default for the check digit position) — 14th
- 1 digit: check digit — 15th

Total: 15 alphanumeric characters. No checksum.
Real test cases:
- 22AAAAA0000A1Z5 (valid canonical example)
- 27AAACI9466C1Z5 (valid)

Special cases:
- "000000000000000" (all zeros) → invalid (reserved)

The agent's job is to:
1. Normalize (uppercase, strip whitespace)
2. Check 15 alphanumeric characters
3. (Optional) Validate state code range (01-37, 96, 97)
4. (Optional) Validate PAN-style middle (5 letters + 4 digits + 1 letter)
5. Return { ok, normalized, error } matching the eval_set contract
"""

from __future__ import annotations

import re
from typing import Any

GSTIN_LENGTH = 15
_SEPARATOR_RE = re.compile(r"[\s.\-/]")  # strip whitespace, dot, dash, slash
_ALNUM_RE = re.compile(r"^[A-Z0-9]+$")
_ALL_SAME_RE = re.compile(r"^(\w)\1{14}$")  # 15 of the same char

# Indian state codes (first 2 digits of GSTIN)
_VALID_STATE_CODES = frozenset({
    "01", "02", "03", "04", "05", "06", "07", "08", "09", "10",
    "11", "12", "13", "14", "15", "16", "17", "18", "19", "20",
    "21", "22", "23", "24", "25", "26", "27", "28", "29", "30",
    "31", "32", "33", "34", "35", "36", "37",
    "96",  # Other Territory
    "97",  # Other Territory
})


def normalize_gstin(value: Any) -> str:
    """Strip whitespace + common separators, uppercase. Returns "" for null/None.

    Examples:
      '22AAAAA0000A1Z5' -> '22AAAAA0000A1Z5'
      '22 aaaaa 0000 a1z5' -> '22AAAAA0000A1Z5'
    """
    if value is None:
        return ""
    return _SEPARATOR_RE.sub("", str(value)).upper()


def _default_validate_state_code(state: str) -> bool:
    """Default state-code check — accepts any 2 digits.

    Replaced with a check against India's valid state code list.
    GSTINs are issued by Indian states; the 2-digit prefix is the state code.
    """
    return state in _VALID_STATE_CODES



def validate_gstin(value: Any, *, state_code_verifier=None) -> dict[str, Any]:
    """Validate an India GSTIN. Returns { ok, normalized, error }.

    Args:
        value: raw input (string, None, or anything str()-coercible).
        state_code_verifier: optional callable (str) -> bool. If supplied and returns False,
            validation fails with the state-code error.

    Returns:
        { ok: bool, normalized: str, error: str | None }
    """
    verifier = state_code_verifier if state_code_verifier is not None else _default_validate_state_code

    normalized = normalize_gstin(value)
    if not normalized:
        return {"ok": False, "normalized": "", "error": "GSTIN is required"}
    if not _ALNUM_RE.match(normalized):
        return {"ok": False, "normalized": normalized, "error": "GSTIN must be alphanumeric"}
    if len(normalized) != GSTIN_LENGTH:
        return {"ok": False, "normalized": normalized, "error": f"GSTIN must be {GSTIN_LENGTH} characters, got {len(normalized)}"}
    if _ALL_SAME_RE.match(normalized):
        return {"ok": False, "normalized": normalized, "error": "GSTIN is invalid (all characters are the same)"}
    state = normalized[:2]
    if not verifier(state):
        return {"ok": False, "normalized": normalized, "error": f"GSTIN has an unassigned state code: {state}"}
    return {"ok": True, "normalized": normalized, "error": None}


# ---------------------------------------------------------------------------
# Adapter for the eval harness (eval.py expects this signature).
# ---------------------------------------------------------------------------

def run_workflow(input_data: dict[str, Any]) -> dict[str, Any]:
    """Adapter: takes the eval harness's input shape, returns validation result.

    Input:  { "gstin": "<raw GSTIN string>" }
    Output: { "ok": bool, "normalized": str, "error": str | None }
    """
    return validate_gstin(input_data.get("gstin"))
