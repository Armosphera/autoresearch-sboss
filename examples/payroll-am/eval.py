"""
eval.py — fixed eval harness for the payroll-am example.

DO NOT MODIFY. The agent edits workflow.py. This file is the judge.

Runs compute_payroll() over the eval set, computes field-level exact-match F1 over
{gross, incomeTax, pension, stampDuty, healthInsurance, totalWithholdings, net}.
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

EVAL_FIELDS = ("gross", "incomeTax", "pension", "stampDuty", "healthInsurance", "totalWithholdings", "net")
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
    return int(a) == int(b)


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
            predicted = {f: None for f in EVAL_FIELDS}

        s = score_outputs(item["expected"], predicted)
        per_item_scores.append(s["overall"])
        for f in EVAL_FIELDS:
            per_field_totals[f] += s[f]

    n = len(eval_set)
    overall = (sum(per_item_scores) / n) * 100.0 if n else 0.0
    per_field_pct = {f: (per_field_totals[f] / n) * 100.0 if n else 0.0 for f in EVAL_FIELDS}
    return overall, {"n_items": n, "errors": errors, "per_field_pct": per_field_pct}


def main() -> int:
    budget_sec = float(os.environ.get("EXPERIMENT_BUDGET_SEC", "60"))
    eval_path = Path(os.environ.get("EVAL_SET_PATH", str(DEFAULT_EVAL_SET)))

    print("autoresearch-sboss eval [payroll-am example]")
    print(f"  eval_set:     {eval_path}")
    print(f"  budget_sec:   {budget_sec}")
    print(f"  llm_endpoint: {os.environ.get('LLM_ENDPOINT_URL', '(no LLM — pure function)')}")
    print()

    eval_set = load_eval_set(eval_path)

    t0 = time.monotonic()
    try:
        overall, stats = run_eval(eval_set, budget_sec)
    except TimeoutError as exc:
        elapsed = time.monotonic() - t0
        print(f"status: TIMEOUT  elapsed: {elapsed:.2f}s  reason: {exc}")
        return 1
    except Exception as exc:  # noqa: BLE001
        elapsed = time.monotonic() - t0
        print(f"status: ERROR    elapsed: {elapsed:.2f}s  reason: {exc!r}")
        return 1

    elapsed = time.monotonic() - t0
    print(f"score: {overall:.4f}  elapsed: {elapsed:.2f}s  n_items: {stats['n_items']}  errors: {stats['errors']}")
    print(f"per_field_pct: " + "  ".join(f"{f}={stats['per_field_pct'][f]:.1f}" for f in EVAL_FIELDS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
