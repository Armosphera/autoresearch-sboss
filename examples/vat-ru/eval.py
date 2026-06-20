"""
eval.py — fixed eval harness for the vat-ru example.

DO NOT MODIFY. The agent edits workflow.py. This file is the judge.

Per-case field set: each item's `expected` has {result: <value>}.
For ratesFor: result is a dict. For vatFromNet/Gross/NetFromGross: number.
For isValidVatRate: bool. Per-case score uses JSON equality for dicts, == for
numbers and bools.
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
    fields = list(expected.keys())
    per_field = {f: (1.0 if _eq(expected.get(f), predicted.get(f)) else 0.0) for f in fields}
    per_field["overall"] = sum(per_field.values()) / len(fields) if fields else 1.0
    return per_field


def run_eval(eval_set: list[dict], budget_sec: float) -> tuple[float, dict]:
    deadline = time.monotonic() + budget_sec
    per_item_scores = []
    per_field_totals: dict[str, float] = {}
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
        for f in item["expected"]:
            per_field_totals[f] = per_field_totals.get(f, 0.0) + s[f]

    n = len(eval_set)
    overall = (sum(per_item_scores) / n) * 100.0 if n else 0.0
    per_field_pct = {f: (v / n) * 100.0 for f, v in per_field_totals.items()}
    return overall, {"n_items": n, "errors": errors, "per_field_pct": per_field_pct}


def main() -> int:
    budget_sec = float(os.environ.get("EXPERIMENT_BUDGET_SEC", "60"))
    eval_path = Path(os.environ.get("EVAL_SET_PATH", str(DEFAULT_EVAL_SET)))

    print("autoresearch-sboss eval [vat-ru example]")
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
    pf = stats["per_field_pct"]
    print(f"per_field_pct: " + "  ".join(f"{f}={pf[f]:.1f}" for f in sorted(pf)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
