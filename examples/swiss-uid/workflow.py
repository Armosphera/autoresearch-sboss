"""
workflow.py — Swiss UID (Unternehmens-Identifikationsnummer) validation.

This file is the agent's lever. The default implementation handles the most common form
(CHE + 9 digits). The agent's job: extend to alternative prefixes and tighten the format.

Source of truth: https://www.uid.admin.ch/ (Swiss Federal Statistical Office).

Reference format (most common):
- CHE + 9 digits (3 + 9 = 12 chars, with optional dots: "CHE-123.456.789")

Alternative prefixes for non-standard entities (foundations, associations):
- CH + 9 digits (3 + 9 = 11 chars: "CH-123.456.789")
- CDF (foundations, 5+9 chars: "CDF-12345.678.90")
- etc.

No checksum. The Swiss UID is a sequence number; there's no mod-11 or weighted-sum
verification. Validation is purely structural.

Source: https://www.uid.admin.ch/

The agent's job:
1. Normalize (strip whitespace, dots, dashes; uppercase)
2. Check the prefix is "CHE" or another valid prefix
3. Check 9 digits (for the standard CHE form) or other valid lengths
4. Return { ok, normalized, error } matching the eval_set contract
"""

from __future__ import annotations

import re
from typing import Any

SWISS_UID_LENGTH = 12  # "CHE" + 9 digits
_SEPARATOR_RE = re.compile(r"[\s.\-/]")  # strip whitespace, dot, dash, slash
_ALNUM_RE = re.compile(r"^[A-Z0-9]+$")
_ALL_SAME_RE = re.compile(r"^(\w)\1{11}$")  # 12 of the same char

# Valid Swiss UID prefixes (for-profit vs other entity types)
_VALID_PREFIXES = frozenset({
    "CHE",  # companies (CHE-XXX.XXX.XXX, 9 digits)
    "CH",   # alternative for-profit (CH-XXX.XXX.XXX)
    "CDF",  # foundations
})


def normalize_swiss_uid(value: Any) -> str:
    """Strip whitespace + common separators, uppercase. Returns "" for null/None.

    Examples:
      'CHE-123.456.789' -> 'CHE123456789'
      'che 123 456 789'  -> 'CHE123456789'
      'CHE123456789'     -> 'CHE123456789'
    """
    if value is None:
        return ""
    return _SEPARATOR_RE.sub("", str(value)).upper()


def _default_validate_prefix(value: str) -> bool:
    """Default prefix check (currently accepts any 12-char alphanumeric starting with CHE/CH/CDF)."""
    # Extract the leading non-digit sequence (the prefix)
    prefix = ""
    for c in value:
        if c.isalpha():
            prefix += c
        else:
            break
    return prefix in _VALID_PREFIXES


def validate_swiss_uid(value: Any) -> dict[str, Any]:
    """Validate a Swiss UID. Returns { ok, normalized, error }.

    Args:
        value: raw input (string, None, or anything str()-coercible).

    Returns:
        { ok: bool, normalized: str, error: str | None }
    """
    normalized = normalize_swiss_uid(value)
    if not normalized:
        return {"ok": False, "normalized": "", "error": "Swiss UID is required"}
    if not _ALNUM_RE.match(normalized):
        return {"ok": False, "normalized": normalized, "error": "Swiss UID must be alphanumeric"}
    if len(normalized) != SWISS_UID_LENGTH:
        return {
            "ok": False,
            "normalized": normalized,
            "error": f"Swiss UID must be {SWISS_UID_LENGTH} characters, got {len(normalized)}",
        }
    if _ALL_SAME_RE.match(normalized):
        return {"ok": False, "normalized": normalized, "error": "Swiss UID is invalid (all characters are the same)"}
    if not _default_validate_prefix(normalized):
        return {
            "ok": False,
            "normalized": normalized,
            "error": "Swiss UID has an unrecognized prefix (expected CHE, CH, or CDF)",
        }
    return {"ok": True, "normalized": normalized, "error": None}


# ---------------------------------------------------------------------------
# Adapter for the eval harness (eval.py expects this signature).
# ---------------------------------------------------------------------------

def run_workflow(input_data: dict[str, Any]) -> dict[str, Any]:
    """Adapter: takes the eval harness's input shape, returns validation result.

    Input:  { "swiss_uid": "<raw Swiss UID string>" }
    Output: { "ok": bool, "normalized": str, "error": str | None }
    """
    return validate_swiss_uid(input_data.get("swiss_uid"))
