"""
eval.py — fixed eval harness for the sa-tin example.

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
        raise ValueError(f"eval_set.json must be a JSON array, got {type(data).__name__}")
    for i, item in enumerate(data):
        if "input" not in item or "expected" not in item:
            raise ValueError(f"eval item {i} missing 'input' or 'expected'")
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
    per_field = {f: (1.0 if _eq(expected.get(f), predicted.get(f)) else 0.0) for f in EVAL_FIELDS}
    per_field["overall"] = sum(per_field.values()) / len(EVAL_FIELDS)
    return per_field


def run_eval(eval_set: list[dict], budget_sec: float) -> tuple[float, dict]:
    deadline = time.monotonic() + budget_sec
    per_item_scores = []
    per_field_totals = {f: 0.0 for f in EVAL_FIELDS}
    errors = 0

    for i, item in enumerate(eval_set):
        if time.monotonic() > deadline:
            raise TimeoutError(f"Eval exceeded budget of {budget_sec}s after {i} items")

        try:
            predicted = workflow.run_workflow(item["input"])
        except Exception:  # noqa: BLE001
            errors += 1
            predicted = {}

        s = score_outputs(item["expected"], predicted)
        per_item_scores.append(s["overall"])
        for f in EVAL_FIELDS:
            per_field_totals[f] += s[f]

    n = len(eval_set)
    overall = sum(per_item_scores) / n if n else 0.0
    per_field_avg = {f: (v / n if n else 0.0) for f, v in per_field_totals.items()}
    return overall, {"per_field": per_field_avg, "errors": errors, "n_items": n}


def main() -> int:
    budget = float(os.environ.get("EVAL_BUDGET_SEC", "60"))
    eval_set_path = Path(os.environ.get("EVAL_SET", DEFAULT_EVAL_SET))
    eval_set = load_eval_set(eval_set_path)

    started = time.monotonic()
    overall, stats = run_eval(eval_set, budget)
    elapsed = time.monotonic() - started

    print(f"autoresearch-sboss eval [scripts example]")
    print(f"  eval_set:     {eval_set_path}")
    print(f"  budget_sec:   {budget}")
    print()
    print(f"score: {overall * 100:.4f}  elapsed: {elapsed:.2f}s  n_items: {stats['n_items']}  errors: {stats['errors']}")
    pf = stats["per_field"]
    print("per_field_pct: " + "  ".join(f"{f}={pf[f] * 100:.1f}" for f in EVAL_FIELDS))
    return 0 if overall >= 1.0 - 1e-9 else 1


if __name__ == "__main__":
    sys.exit(main())
