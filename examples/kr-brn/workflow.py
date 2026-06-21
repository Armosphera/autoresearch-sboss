"""
workflow.py — Korea Business Registration Number (BRN / 사업자등록번호) validation.

This file is the agent's lever. The default implementation is intentionally WEAK — it only
does basic structural validation (10 digits, separator stripping). The agent's job:
add validation against the published kind structure (3-2-5 digit pattern) per the NTS spec
(currently a documented TODO seam).

Source of truth: https://www.nts.go.kr/ (National Tax Service).
The BRN format and rules are public.

Reference format:
- 10 digits, formatted as XXX-XX-XXXXX (3-2-5)
- No mathematical check digit
- The first 3 digits encode the tax office (kind)
- The next 2 digits encode the kind of business
- The last 5 digits are the serial

Special cases:
- "000-00-00000" (all zeros) → invalid
- All 10 digits the same → invalid
- The 3-2-5 format is purely structural; there's no checksum

Real test cases (synthetic):
- 123-45-67890 → valid (10 digits in 3-2-5 format)
- 1234567890 → valid (10 digits, no separators)
- 123-4A-67890 → invalid (contains letter)

The agent's job is to:
1. Implement format validation: 10 digits, with optional 3-2-5 hyphen structure
2. Handle separator normalization (BRNs are commonly written as "123-45-67890" or "1234567890")
3. Catch special invalid cases (all-zeros, all-same)
4. Return { ok, normalized, error } matching the eval_set contract
"""

from __future__ import annotations

import re
from typing import Any

BRN_LENGTH = 10
_SEPARATOR_RE = re.compile(r"[\s\-]")
_ALL_DIGITS_RE = re.compile(r"^[0-9]+$")
_ALL_SAME_RE = re.compile(r"^(\d)\1{9}$")  # 10 of the same digit
# Canonical 3-2-5 format: "123-45-67890" → after normalize: "1234567890"
_CANONICAL_3_2_5_RE = re.compile(r"^\d{3}-\d{2}-\d{5}$")


def normalize_brn(value: Any) -> str:
    """Strip whitespace + hyphens. Returns "" for null/None.

    Examples:
      '123-45-67890' -> '1234567890'
      '123 45 67890' -> '1234567890'
      '1234567890'   -> '1234567890'
    """
    if value is None:
        return ""
    return _SEPARATOR_RE.sub("", str(value))


def _default_kind(brn: str) -> bool:
    """Default kind verifier (currently accepts any 10-digit string).

    This is the documented TODO seam. The NTS publishes the kind
    classification rules (first 3 digits = tax office, next 2 = business
    type). The agent's main lever is to implement this correctly.

    Args:
        brn: a 10-digit string that has already passed length / digits / non-degenerate checks.

    Returns:
        True if the kind structure is valid, False if not.
    """
    # TODO: implement official NTS BRN kind validation.
    # See: https://www.nts.go.kr/
    return True


def validate_brn(value: Any, *, kind_verifier=None) -> dict[str, Any]:
    """Validate a Korea BRN. Returns { ok, normalized, error }.

    Args:
        value: raw input (string, None, or anything str()-coercible).
        kind_verifier: optional callable (str) -> bool. If supplied and returns False,
            validation fails with the kind error. Defaults to the local
            _default_kind (which currently accepts everything).

    Returns:
        { ok: bool, normalized: str, "error": str | None }
    """
    verifier = kind_verifier if kind_verifier is not None else _default_kind

    normalized = normalize_brn(value)
    if not normalized:
        return {"ok": False, "normalized": "", "error": "BRN is required"}
    if not _ALL_DIGITS_RE.match(normalized):
        return {"ok": False, "normalized": normalized, "error": "BRN must contain only digits"}
    if len(normalized) != BRN_LENGTH:
        return {"ok": False, "normalized": normalized, "error": f"BRN must be {BRN_LENGTH} digits, got {len(normalized)}"}
    if _ALL_SAME_RE.match(normalized):
        return {"ok": False, "normalized": normalized, "error": "BRN is invalid (all digits are the same)"}
    if not verifier(normalized):
        return {"ok": False, "normalized": normalized, "error": "BRN format is invalid"}
    return {"ok": True, "normalized": normalized, "error": None}


# ---------------------------------------------------------------------------
# Adapter for the eval harness (eval.py expects this signature).
# ---------------------------------------------------------------------------

def run_workflow(input_data: dict[str, Any]) -> dict[str, Any]:
    """Adapter: takes the eval harness's input shape, returns validation result.

    Input:  { "brn": "<raw BRN string>" }
    Output: { "ok": bool, "normalized": str, "error": str | None }
    """
    return validate_brn(input_data.get("brn"))
