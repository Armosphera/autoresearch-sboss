#!/usr/bin/env python3
"""new_example.py — generate a new autoresearch-sboss example scaffold.

Usage:
    python scripts/new_example.py <name> [--input-key <key>]

Creates examples/<name>/ with the 5-file template:
- eval.py        (fixed harness, do not modify)
- workflow.py    (agent's lever, TODO seam)
- program.md     (research charter)
- eval_set.json  (default 3-case starter, you add more)
- results.tsv    (empty log)

The <name> follows the existing convention (kebab-case):
  - ar-cuit, cl-rut, sg-uen (country-tld-style: ISO 3166-1 alpha-2 + abbrev)
  - mx-rfc, jp-mynumber (short name + abbrev)
  - hhvh, cnpj, cpf (lowercase abbrev)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = REPO_ROOT / "examples"


def render_eval_py(name: str) -> str:
    """Render the fixed eval.py harness, adapted for <name>."""
    return f'''"""
eval.py — fixed eval harness for the {name} example.

DO NOT MODIFY. The agent edits workflow.py. This file is the judge.

Runs run_workflow() (from workflow.py) over the eval set in eval_set.json, computes
a field-level exact-match F1 score, prints the result, and exits 0/1.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).parent
sys.path.insert(0, str(REPO_ROOT))

import workflow  # noqa: E402

EVAL_FIELDS = ("ok", "normalized", "error")
DEFAULT_EVAL_SET = REPO_ROOT / "eval_set.json"


def load_eval_set(path: Path) -> list[dict]:
    with path.open() as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"eval_set.json must be a JSON array, got {{type(data).__name__}}")
    for i, item in enumerate(data):
        if "input" not in item or "expected" not in item:
            raise ValueError(f"eval item {{i}} missing 'input' or 'expected'")
    return data


def _eq(a, b) -> bool:
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    if isinstance(a, bool) or isinstance(b, bool):
        return bool(a) == bool(b)
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a == b
    if isinstance(a, dict) and isinstance(b, dict):
        return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    if isinstance(a, list) and isinstance(b, list):
        return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    return str(a) == str(b)


def score_outputs(expected: dict, predicted: dict) -> dict[str, float]:
    per_field = {{f: (1.0 if _eq(expected.get(f), predicted.get(f)) else 0.0) for f in EVAL_FIELDS}}
    per_field["overall"] = sum(per_field.values()) / len(EVAL_FIELDS)
    return per_field


def run_eval(eval_set: list[dict], budget_sec: float) -> tuple[float, dict]:
    deadline = time.monotonic() + budget_sec
    per_item_scores = []
    per_field_totals = {{f: 0.0 for f in EVAL_FIELDS}}
    errors = 0

    for i, item in enumerate(eval_set):
        if time.monotonic() > deadline:
            raise TimeoutError(f"Eval exceeded budget of {{budget_sec}}s after {{i}} items")

        try:
            predicted = workflow.run_workflow(item["input"])
        except Exception:  # noqa: BLE001
            errors += 1
            predicted = {{}}

        s = score_outputs(item["expected"], predicted)
        per_item_scores.append(s["overall"])
        for f in EVAL_FIELDS:
            per_field_totals[f] += s[f]

    n = len(eval_set)
    overall = sum(per_item_scores) / n if n else 0.0
    per_field_avg = {{f: (v / n if n else 0.0) for f, v in per_field_totals.items()}}
    return overall, {{"per_field": per_field_avg, "errors": errors, "n_items": n}}


def main() -> int:
    budget = float(os.environ.get("EVAL_BUDGET_SEC", "60"))
    eval_set_path = Path(os.environ.get("EVAL_SET", DEFAULT_EVAL_SET))
    eval_set = load_eval_set(eval_set_path)

    started = time.monotonic()
    overall, stats = run_eval(eval_set, budget)
    elapsed = time.monotonic() - started

    print(f"autoresearch-sboss eval [{Path(__file__).parent.name} example]")
    print(f"  eval_set:     {{eval_set_path}}")
    print(f"  budget_sec:   {{budget}}")
    print()
    print(f"score: {{overall * 100:.4f}}  elapsed: {{elapsed:.2f}}s  n_items: {{stats['n_items']}}  errors: {{stats['errors']}}")
    pf = stats["per_field"]
    print("per_field_pct: " + "  ".join(f"{{f}}={{pf[f] * 100:.1f}}" for f in EVAL_FIELDS))
    return 0 if overall >= 1.0 - 1e-9 else 1


if __name__ == "__main__":
    sys.exit(main())
'''


def render_workflow_py(name: str, input_key: str) -> str:
    """Render the workflow.py template with a TODO seam for the agent."""
    return f'''"""
workflow.py — {name} validation.

This file is the agent's lever. The default implementation is intentionally WEAK — it only
does basic structural validation. The agent's job: add the proper format checks and
check-digit algorithm per the upstream spec (currently a documented TODO seam).

## Source of truth
TODO: link to the official spec (e.g. the tax authority's published format).

## The task
Given a raw input string (possibly with separators), return a structured
{{ ok, normalized, error }} per the eval_set contract.

## Current behavior
Structure-only validation: rejects empty, rejects non-{input_key}, rejects wrong length,
rejects all-same, otherwise accepts. The check-digit verifier is a TODO seam that
returns True. The agent's job: implement the real check.
"""

from __future__ import annotations

import re
from typing import Any


def normalize(value: Any) -> str:
    """Strip whitespace + common separators. Returns "" for null/None.

    Customize the separator regex below for the target format.
    """
    if value is None:
        return ""
    return re.sub(r"[\\s.\\-/]", "", str(value)).upper()


def _default_check_digit(normalized: str) -> bool:
    """Default check-digit verifier (currently accepts everything that passes structure).

    TODO: implement the real check-digit algorithm.
    """
    return True


def validate(value: Any, *, check_digit_verifier=None) -> dict[str, Any]:
    """Validate. Returns {{ ok, normalized, error }}.

    Args:
        value: raw input (string, None, or anything str()-coercible).
        check_digit_verifier: optional callable (str) -> bool. If supplied and
            returns False, validation fails with a check-digit error.
    """
    verifier = check_digit_verifier if check_digit_verifier is not None else _default_check_digit

    normalized = normalize(value)
    if not normalized:
        return {{"ok": False, "normalized": "", "error": "value is required"}}
    # TODO: add your length / character-class / check-digit rules here
    if not verifier(normalized):
        return {{"ok": False, "normalized": normalized, "error": "value check digit is invalid"}}
    return {{"ok": True, "normalized": normalized, "error": None}}


def run_workflow(input_data: dict[str, Any]) -> dict[str, Any]:
    """Adapter for the eval harness (eval.py expects this signature)."""
    return validate(input_data.get("{input_key}"))
'''


def render_program_md(name: str) -> str:
    return f'''# program.md — {name} research charter

You are an autonomous research agent. Your job: improve `workflow.py` so the field-level
exact-match F1 score from `eval.py` goes up. You do not edit `eval.py`, `eval_set.json`, or
`pyproject.toml`. You only edit `workflow.py` and append to `results.tsv`.

## The task

TODO: describe the target format in one paragraph (country, length, separator rules,
check-digit algorithm if any).

## Source of truth

TODO: link to the official spec.

## The loop

Same as the other examples — see the top-level `program.md` or one of the existing
examples (e.g. `examples/cpf/program.md`).

## Have fun

The whole point: a Python validator for {name} that's STRICTLY BETTER than a naive
regex baseline. Worst case you revert.
'''


def render_eval_set_json(name: str, input_key: str) -> str:
    return f'''[
  {{ "input": {{ "{input_key}": "TODO_VALUE" }}, "expected": {{ "ok": true, "normalized": "TODO_NORMALIZED", "error": null }} }},
  {{ "input": {{ "{input_key}": "" }}, "expected": {{ "ok": false, "normalized": "", "error": "value is required" }} }},
  {{ "input": {{ "{input_key}": "TODO_INVALID" }}, "expected": {{ "ok": false, "normalized": "TODO_INVALID_NORMALIZED", "error": "TODO_REASON" }} }}
]
'''


def render_results_tsv() -> str:
    return "timestamp\\tcommit\\tstatus\\tscore\\tbudget_sec\\tdescription\\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Create a new autoresearch-sboss example scaffold")
    ap.add_argument("name", help="Kebab-case name (e.g. ar-cuit, mx-rfc)")
    ap.add_argument("--input-key", default="value", help="Input field name (default: value)")
    args = ap.parse_args()

    target = EXAMPLES_DIR / args.name
    if target.exists():
        print(f"Error: {target} already exists", file=sys.stderr)
        return 1

    target.mkdir(parents=True)
    (target / "eval.py").write_text(render_eval_py(args.name))
    (target / "workflow.py").write_text(render_workflow_py(args.name, args.input_key))
    (target / "program.md").write_text(render_program_md(args.name))
    (target / "eval_set.json").write_text(render_eval_set_json(args.name, args.input_key))
    (target / "results.tsv").write_text(render_results_tsv())

    print(f"Created {target}/ with 5-file template")
    print(f"  Next: edit {target}/workflow.py and add real test cases to eval_set.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
