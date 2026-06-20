"""
workflow.py — Russian phone number normalization, validation, formatting.

Faithful Python port of src/phone.js from A1-Localization-RU.
Russia (country code +7) uses a 10-digit National Significant Number (NSN):
3-digit area/operator code (DEF/ABC) + 7-digit subscriber number. Domestic
trunk prefix is 8 (the legacy "8 (495) ..." form). We normalize the many
shapes users type (+7…, 8…, bare, with spaces/punctuation) down to the
canonical 10-digit NSN, then validate and format. Validates the STABLE
invariant (10-digit NSN starting 3-9: 3-8 geographic, 9 mobile) rather
than hard-coding the ever-changing list of operator prefixes.

Source of truth (JS, MIT): https://github.com/Armosphera/A1-Localization-RU
Corresponding JS file:   src/phone.js
"""

from __future__ import annotations

import re
from typing import Any

COUNTRY_CODE = "7"
NSN_LENGTH = 10

# 10-digit NSN, must start 3-9 (geographic 3-8, mobile 9).
# Russian NSNs never start with 0/1/2.
_NSN_RE = re.compile(r"^[3-9]\d{9}$")


def normalize_nsn(value: Any) -> str:
    """Normalize any common phone-input shape to the 10-digit NSN, or "" if invalid."""
    digits = re.sub(r"\D", "", str("" if value is None else value))
    nsn = ""
    if len(digits) == 11 and digits[0] == "8":
        nsn = digits[1:]  # domestic trunk form 8XXXXXXXXXX
    elif len(digits) == 11 and digits[0] == "7":
        nsn = digits[1:]  # E.164 form without + 7XXXXXXXXXX
    elif len(digits) == NSN_LENGTH:
        nsn = digits       # already bare NSN
    return nsn if _NSN_RE.match(nsn) else ""


def is_valid_russian_phone(value: Any) -> bool:
    return normalize_nsn(value) != ""


def e164(value: Any) -> str | None:
    nsn = normalize_nsn(value)
    return f"+{COUNTRY_CODE}{nsn}" if nsn else None


def format_phone(value: Any) -> str | None:
    nsn = normalize_nsn(value)
    if not nsn:
        return None
    area = nsn[0:3]
    block = nsn[3:6]
    pair1 = nsn[6:8]
    pair2 = nsn[8:10]
    return f"+{COUNTRY_CODE} ({area}) {block}-{pair1}-{pair2}"


# ===========================================================================
# Autoresearch eval entry point
# ===========================================================================
# eval_set items look like:
#   { "input": {"value": "..."}, "expected": {"nsn": "...", "valid": bool, "e164": "..."|null, "formatted": "..."|null} }
# All 4 functions are evaluated for every case (mirrors the phone-am pattern).

def run_workflow(input: dict) -> dict:
    value = input.get("value")
    return {
        "nsn": normalize_nsn(value),
        "valid": is_valid_russian_phone(value),
        "e164": e164(value),
        "formatted": format_phone(value),
    }
