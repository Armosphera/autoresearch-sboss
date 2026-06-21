"""
workflow.py — UK Company Number (Companies House) validation.

This file is the agent's lever. The default implementation handles the 4 most common
patterns (8 digits + SC/NI/OC + 6 digits). The agent's job: extend to the remaining
prefixes (SO/NC/FC/SF/NF), tighten the validation, and add proper error messages.

Source of truth: https://find-and-update.company-information.service.gov.uk/ (Companies House).

Reference patterns (8 uppercase characters):
- 8 digits: "12345678"  (England & Wales limited company — most common)
- "SC" + 6 digits: "SC123456"  (Scottish limited company)
- "NI" + 6 digits: "NI123456"  (Northern Irish limited company)
- "OC" + 6 digits: "OC123456"  (Limited Liability Partnership)
- "SO" + 6 digits: "SO123456"  (Scottish LLP)
- "NC" + 6 digits: "NC123456"  (Northern Irish LLP)
- "FC" + 6 digits: "FC123456"  (overseas company)
- "SF" + 6 digits: "SF123456"  (Scottish further education)
- "NF" + 6 digits: "NF123456"  (Northern Irish further education)

No checksum. The validator checks the 8-char pattern + a prefix whitelist.

Normalization: trim leading/trailing whitespace, uppercase. No internal separator stripping
(UK company numbers don't have separators in the wild).
"""

from __future__ import annotations

import re
from typing import Any

# Valid 2-letter prefixes for UK company numbers (England & Wales, Scotland, NI, etc.)
_VALID_PREFIXES = frozenset({
    "SC",  # Scottish limited company
    "NI",  # Northern Irish limited company
    "OC",  # Limited Liability Partnership
    "SO",  # Scottish LLP
    "NC",  # Northern Irish LLP
    "FC",  # overseas company
    "SF",  # Scottish further education
    "NF",  # Northern Irish further education
})

UK_COMPANY_LENGTH = 8
_ALL_DIGITS_RE = re.compile(r"^[0-9]+$")
_PREFIXED_RE = re.compile(r"^([A-Z]{2})([0-9]{6})$")


def normalize_uk_company(value: Any) -> str:
    """Trim whitespace, uppercase. No internal separator stripping.

    Returns: "" for null/None.
    """
    if value is None:
        return ""
    return str(value).strip().upper()


def _is_valid_uk_company(value: str) -> bool:
    """Default validity check — 8 digits OR a valid prefix + 6 digits.

    The agent's job: extend this to cover all 9 patterns (currently handles 4):
    - 8 digits
    - SC + 6 digits
    - NI + 6 digits
    - OC + 6 digits
    (missing: SO, NC, FC, SF, NF)
    """
    if len(value) != UK_COMPANY_LENGTH:
        return False
    if _ALL_DIGITS_RE.match(value):
        return True
    m = _PREFIXED_RE.match(value)
    if not m:
        return False
    prefix = m.group(1)
    return prefix in _VALID_PREFIXES


def validate_uk_company(value: Any) -> dict[str, Any]:
    """Validate a UK Company Number. Returns { ok, normalized, error }.

    Args:
        value: raw input (string, None, or anything str()-coercible).

    Returns:
        { ok: bool, normalized: str, error: str | None }
    """
    normalized = normalize_uk_company(value)
    if not normalized:
        return {"ok": False, "normalized": "", "error": "UK Company Number is required"}
    if len(normalized) != UK_COMPANY_LENGTH:
        return {
            "ok": False,
            "normalized": normalized,
            "error": f"UK Company Number must be {UK_COMPANY_LENGTH} characters, got {len(normalized)}",
        }
    if not _is_valid_uk_company(normalized):
        return {
            "ok": False,
            "normalized": normalized,
            "error": "UK Company Number has an invalid format (must be 8 digits or SC/NI/OC/SO/NC/FC/SF/NF + 6 digits)",
        }
    return {"ok": True, "normalized": normalized, "error": None}


# ---------------------------------------------------------------------------
# Adapter for the eval harness (eval.py expects this signature).
# ---------------------------------------------------------------------------

def run_workflow(input_data: dict[str, Any]) -> dict[str, Any]:
    """Adapter: takes the eval harness's input shape, returns validation result.

    Input:  { "uk_company": "<raw UK Company Number string>" }
    Output: { "ok": bool, "normalized": str, "error": str | None }
    """
    return validate_uk_company(input_data.get("uk_company"))
