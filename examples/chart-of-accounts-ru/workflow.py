"""
workflow.py — Russian chart of accounts (План счетов бухгалтерского учёта).

Faithful Python port of src/chartOfAccounts.js from A1-Localization-RU.

Российский План счетов бухгалтерского учёта финансово-хозяйственной
деятельности организаций — Приказ Минфина РФ № 94н от 31.10.2000.

Unlike the AM chart (where the leading digit encodes the class), in 94н the
РАЗДЕЛ (section) is determined by the account NUMBER RANGE. The нормальное
сальдо (normal balance) follows each account's ХАРАКТЕР (character):
  активный (active)          → debit
  пассивный (passive)        → credit
  активно-пассивный (a/p)    → null (both sides)

Pure data + lookups, no I/O, no deps. Data loaded from data.json (73 accounts)
+ sections.json (9 sections) at import time.

Source of truth (JS, MIT): https://github.com/Armosphera/A1-Localization-RU
Corresponding JS file:   src/chartOfAccounts.js
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).parent

with (DATA_DIR / "data.json").open() as _f:
    _ACCOUNTS: tuple[dict, ...] = tuple(json.load(_f))
with (DATA_DIR / "sections.json").open() as _f:
    _SECTIONS: tuple[dict, ...] = tuple(json.load(_f))

# Lookup index: code → account
_BY_CODE: dict[str, dict] = {a["code"]: a for a in _ACCOUNTS}

# Nature → normal balance
_NATURE_TO_BALANCE: dict[str, str | None] = {
    "active": "debit",
    "passive": "credit",
    "active-passive": None,
}


def _as_code(code: Any) -> str:
    """Normalize any input to a trimmed string ("" for null/undefined/objects)."""
    if code is None:
        return ""
    if isinstance(code, (dict, list)):
        return ""
    return str(code).strip()


def _numeric_code(s: str) -> float:
    """Numeric value used for range matching (NaN for non-numeric input)."""
    if not re.match(r"^\d+$", s):
        return float("nan")
    return float(s)


def account_by_code(code: Any) -> dict | None:
    s = _as_code(code)
    if not s:
        return None
    return _BY_CODE.get(s)


def accounts_by_section(section_id: Any) -> list[dict]:
    sid = _as_code(section_id)
    if not sid:
        return []
    return [a for a in _ACCOUNTS if a["section"] == sid]


def accounts_by_nature(nature: Any) -> list[dict]:
    n = _as_code(nature)
    if not n:
        return []
    return [a for a in _ACCOUNTS if a["nature"] == n]


def section_of(code: Any) -> dict | None:
    """Section by NUMBER RANGE. Three-digit codes (001–011) are забалансовые счета;
    two-digit codes (01–99) fall into one of the eight balance-sheet sections."""
    s = _as_code(code)
    n = _numeric_code(s)
    if n != n:  # NaN
        return None
    if len(s) == 3:
        off = next((sec for sec in _SECTIONS if sec["id"] == "offBalance"), None)
        if off is None:
            return None
        return off if off["range"][0] <= n <= off["range"][1] else None
    for sec in _SECTIONS:
        if sec["id"] == "offBalance":
            continue
        if sec["range"][0] <= n <= sec["range"][1]:
            return sec
    return None


def normal_balance(code: Any) -> str | None:
    a = account_by_code(code)
    if a is None:
        return None
    return _NATURE_TO_BALANCE.get(a["nature"])


def is_valid_account_code(code: Any) -> bool:
    return account_by_code(code) is not None


# ===========================================================================
# Autoresearch eval entry point
# ===========================================================================
# eval_set items look like:
#   { "input": {"code": "..."}, "expected": {found, code, ru, section, nature, normalBalance} }

def run_workflow(input: dict) -> dict:
    code = (input or {}).get("code")
    a = account_by_code(code)
    if a is None:
        return {"found": False, "code": None, "ru": None, "section": None, "nature": None, "normalBalance": None}
    return {
        "found": True,
        "code": a.get("code"),
        "ru": a.get("ru"),
        "section": a.get("section"),
        "nature": a.get("nature"),
        "normalBalance": normal_balance(code),
    }
