"""
workflow.py — Saudi Arabia TIN (Tax Identification Number) validation.

This file is the agent's lever. The default implementation is intentionally WEAK — it only
does basic structural validation. The agent's job: add the kind-prefix validation and any
other refinements (currently a documented TODO seam).

Source of truth: https://zatca.gov.sa/ (Zakat, Tax and Customs Authority).
The TIN format is public.

Reference format:
- 10 digits, no separators
- First digit indicates the taxpayer kind:
  - 3 → VAT-payer (registered for VAT)
  - 4 → non-VAT-payer (registered but not for VAT)
  - 5+ → reserved / not used (currently)
- Digits 2-10 are the serial
- No public check-digit algorithm (the digits are assigned by ZATCA)

Special cases:
- "0000000000" (all zeros) → invalid
- All 10 digits the same → invalid
- First digit not 3 or 4 → invalid (no public TIN prefix)

Real test cases (synthetic, do not use real TINs):
- 3001234567 → valid (VAT-payer)
- 4001234567 → valid (non-VAT-payer)
- 5001234567 → invalid (first digit 5, no public prefix)
- 2001234567 → invalid (first digit 2, no public prefix)

The agent's job is to:
1. Implement format validation: 10 digits, first digit in {3, 4}
2. Catch special invalid cases (all-zeros, all-same)
3. Return { ok, normalized, error } matching the eval_set contract
"""

from __future__ import annotations

import re
from typing import Any

TIN_LENGTH = 10
_SEPARATOR_RE = re.compile(r"[\s\-]")
_ALL_DIGITS_RE = re.compile(r"^[0-9]+$")
_ALL_SAME_RE = re.compile(r"^(\d)\1{9}$")  # 10 of the same digit

# Recognized first digits (3 = VAT-payer, 4 = non-VAT-payer per ZATCA)
_RECOGNIZED_PREFIXES = frozenset("34")


def normalize_tin(value: Any) -> str:
    """Strip whitespace + hyphens, returns "" for null/None.

    Examples:
      '3001234567'  -> '3001234567'
      '300 123 4567' -> '3001234567'
      '300-123-4567' -> '3001234567'
    """
    if value is None:
        return ""
    return _SEPARATOR_RE.sub("", str(value))


def _default_kind(tin: str) -> bool:
    """Default kind verifier — accepts any 10-digit string.

    Replaced with the ZATCA TIN kind prefix check: first digit must be
    3 (VAT-payer) or 4 (non-VAT-payer).
    """
    return tin[0] in _RECOGNIZED_PREFIXES



def validate_tin(value: Any, *, kind_verifier=None) -> dict[str, Any]:
    """Validate a Saudi Arabia TIN. Returns { ok, normalized, error }.

    Args:
        value: raw input (string, None, or anything str()-coercible).
        kind_verifier: optional callable (str) -> bool. If supplied and returns False,
            validation fails with the kind error. Defaults to the local
            _default_kind (which currently accepts everything).

    Returns:
        { ok: bool, normalized: str, "error": str | None }
    """
    verifier = kind_verifier if kind_verifier is not None else _default_kind

    normalized = normalize_tin(value)
    if not normalized:
        return {"ok": False, "normalized": "", "error": "TIN is required"}
    if not _ALL_DIGITS_RE.match(normalized):
        return {"ok": False, "normalized": normalized, "error": "TIN must contain only digits"}
    if len(normalized) != TIN_LENGTH:
        return {"ok": False, "normalized": normalized, "error": f"TIN must be {TIN_LENGTH} digits, got {len(normalized)}"}
    if _ALL_SAME_RE.match(normalized):
        return {"ok": False, "normalized": normalized, "error": "TIN is invalid (all digits are the same)"}
    if not verifier(normalized):
        return {"ok": False, "normalized": normalized, "error": "TIN kind prefix is invalid"}
    return {"ok": True, "normalized": normalized, "error": None}


# ---------------------------------------------------------------------------
# Adapter for the eval harness (eval.py expects this signature).
# ---------------------------------------------------------------------------

def run_workflow(input_data: dict[str, Any]) -> dict[str, Any]:
    """Adapter: takes the eval harness's input shape, returns validation result.

    Input:  { "tin": "<raw TIN string>" }
    Output: { "ok": bool, "normalized": str, "error": str | None }
    """
    return validate_tin(input_data.get("tin"))
