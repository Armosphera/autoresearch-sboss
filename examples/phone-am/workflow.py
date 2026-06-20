"""
workflow.py — Armenian phone number normalization, validation, formatting.

Faithful Python port of src/armeniaPhone.js from A1-Localization-AM.
Armenia (country code +374) uses an 8-digit National Significant Number (NSN).
We normalize the many shapes users type (+374…, 00374…, domestic 0…, bare,
with spaces/punctuation) down to the canonical 8-digit NSN, then validate
and format. Validates the STABLE invariant (8-digit NSN, not starting with 0)
rather than hard-coding operator prefixes.

Source of truth (JS, MIT): https://github.com/Armosphera/A1-Localization-AM
Corresponding JS file:   src/armeniaPhone.js
JS test contract:         test/armenia-phone.test.js
"""

from __future__ import annotations

import re
from typing import Any

COUNTRY_CODE = "374"
NSN_LENGTH = 8

# 8-digit NSN, must start with 1-9 (not 0)
_NSN_RE = re.compile(r"^[1-9]\d{7}$")


def normalize_nsn(value: Any) -> str:
    """Normalize any common phone-input shape to the 8-digit NSN, or "" if invalid."""
    s = re.sub(r"\D", "", str("" if value is None else value))
    if s.startswith("00374"):
        s = s[5:]
    elif len(s) == 11 and s.startswith("374"):
        s = s[3:]
    elif len(s) == 9 and s.startswith("0"):
        s = s[1:]
    return s if _NSN_RE.match(s) else ""


def is_valid_armenian_phone(value: Any) -> bool:
    return normalize_nsn(value) != ""


def e164(value: Any) -> str | None:
    nsn = normalize_nsn(value)
    return f"+374{nsn}" if nsn else None


def format_phone(value: Any) -> str | None:
    nsn = normalize_nsn(value)
    return f"+374 {nsn[:2]} {nsn[2:]}" if nsn else None


# ---------------------------------------------------------------------------
# Adapter for the eval harness.
# ---------------------------------------------------------------------------

def run_workflow(input_data: dict[str, Any]) -> dict[str, Any]:
    """Adapter for eval.py. Takes {"phone": "<raw phone string>"}.

    Output:
      {
        "nsn":       str,   # 8-digit NSN or "" if invalid
        "valid":     bool,  # True iff nsn is non-empty
        "e164":      str|None,  # "+374XXXXXXXX" or None
        "formatted": str|None,  # "+374 XX XXXXXX" or None
      }
    """
    phone = input_data.get("phone") if isinstance(input_data, dict) else input_data
    nsn = normalize_nsn(phone)
    return {
        "nsn": nsn,
        "valid": nsn != "",
        "e164": e164(phone),
        "formatted": format_phone(phone),
    }
