"""
workflow.py — India PAN (Permanent Account Number) validation.

This file is the agent's lever. The default implementation is intentionally
WEAK — it only does basic structural validation. The agent's job: add
the 4th-character kind code check and any other format refinements
(currently a documented TODO seam).

Source of truth: https://www.incometax.gov.in/ (Income Tax Department of India)
+ https://en.wikipedia.org/wiki/Permanent_account_number

Reference format:
- 10 alphanumeric characters
- Structure: AAAAA9999A
  - Positions 1-3: alphabetic series (e.g. "ABCP" for a company in A series)
  - Position 4: alphabetic kind code (P=Individual, C=Company, H=HUF, F=Firm, A=AOP, T=Trust, B=BOI, L=Local Authority, J=Artificial Juridical Person, G=Government)
  - Position 5: alphabetic (first letter of surname for individuals; first letter of name for non-individuals)
  - Positions 6-9: numeric sequence
  - Position 10: alphabetic check digit
- No mathematical check digit algorithm (the 10th character is assigned by the ITD)
- All uppercase
- Common format with separators: "ABCPA1234F" (no separator in official format)

Special cases:
- "AAAAAAAAAA" (all letters) → invalid (positions 6-9 must be digits)
- "0000000000" (all zeros) → invalid (reserved)
- 4th character not in the kind code set → invalid
- Mixed case (e.g. "abcpa1234f") → normalize to uppercase before validation

Real test cases (synthetic, do not use real PAN numbers):
- AAAPA1234A → valid (Individual named A with series AAA, sequence 1234)
- ABCPH1234F → valid (Firm named H in ABC series)
- ABCDE1234F → invalid (4th char "E" is not a kind code)
- INVALID1234 → invalid (wrong length, 12 chars)

The agent's job is to:
1. Implement format validation: 10 chars, structure AAAAA9999A
2. Validate the 4th character is one of the recognized kind codes
3. Handle case normalization (lowercase → uppercase)
4. Catch special invalid cases (all-zeros, wrong length)
5. Return { ok, normalized, error } matching the eval_set contract
"""

from __future__ import annotations

import re
from typing import Any

PAN_LENGTH = 10
_SEPARATOR_RE = re.compile(r"[\s\-]")
_ALL_LETTERS_RE = re.compile(r"^[A-Z]+$")
_ALL_SAME_RE = re.compile(r"^(\w)\1{9}$")  # 10 of the same char
# Standard PAN structure: 3 letters + kind + letter + 4 digits + letter
# Kind codes: P (individual), C (company), H (HUF), F (firm), A (AOP), T (trust),
# B (BOI), L (local authority), J (artificial juridical person), G (government)
_PAN_STRUCTURE_RE = re.compile(r"^[A-Z]{3}[CPHFATBLJG][A-Z][0-9]{4}[A-Z]$")

# Recognized PAN kind codes (4th character)
_KIND_CODES = frozenset("CPHFATBLJG")


def normalize_pan(value: Any) -> str:
    """Strip whitespace + hyphens, uppercase. Returns "" for null/None.

    Examples:
      'AAAPA1234A'  -> 'AAAPA1234A'
      'aaapa 1234 a' -> 'AAAPA1234A'
    """
    if value is None:
        return ""
    return _SEPARATOR_RE.sub("", str(value)).upper()


def _default_check_digit(pan: str) -> bool:
    """Default check-digit verifier — accepts any well-formed string.

    Replaced with the PAN format check: 4th character must be one of the
    recognized kind codes (P/C/H/F/A/T/B/L/J/G).
    """
    return _PAN_STRUCTURE_RE.match(pan) is not None



def validate_pan(value: Any, *, check_digit_verifier=None) -> dict[str, Any]:
    """Validate an India PAN. Returns { ok, normalized, error }.

    Args:
        value: raw input (string, None, or anything str()-coercible).
        check_digit_verifier: optional callable (str) -> bool. If supplied and returns False,
            validation fails with the check-digit error. Defaults to the local
            _default_check_digit (which currently accepts everything).

    Returns:
        { ok: bool, normalized: str, "error": str | None }
    """
    verifier = check_digit_verifier if check_digit_verifier is not None else _default_check_digit

    normalized = normalize_pan(value)
    if not normalized:
        return {"ok": False, "normalized": "", "error": "PAN is required"}
    if len(normalized) != PAN_LENGTH:
        return {"ok": False, "normalized": normalized, "error": f"PAN must be {PAN_LENGTH} characters, got {len(normalized)}"}
    if _ALL_SAME_RE.match(normalized):
        return {"ok": False, "normalized": normalized, "error": "PAN is invalid (all characters are the same)"}
    if not verifier(normalized):
        return {"ok": False, "normalized": normalized, "error": "PAN format is invalid"}
    return {"ok": True, "normalized": normalized, "error": None}


# ---------------------------------------------------------------------------
# Adapter for the eval harness (eval.py expects this signature).
# ---------------------------------------------------------------------------

def run_workflow(input_data: dict[str, Any]) -> dict[str, Any]:
    """Adapter: takes the eval harness's input shape, returns validation result.

    Input:  { "pan": "<raw PAN string>" }
    Output: { "ok": bool, "normalized": str, "error": str | None }
    """
    return validate_pan(input_data.get("pan"))
