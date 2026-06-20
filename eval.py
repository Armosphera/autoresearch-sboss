"""
eval.py — fixed eval harness for autoresearch-sboss.

DO NOT MODIFY. The agent edits workflow.py. The judge is this file.

Runs the workflow defined in workflow.py over the eval set in eval_set.json, computes a
field-level exact-match F1 score (0-100, higher is better), prints the result to stdout in a
parseable format, and exits 0 on success / 1 on timeout or eval error.

Configurable via env vars:
    EXPERIMENT_BUDGET_SEC  — wall-clock budget, default 60
    EVAL_SET_PATH          — path to eval JSON, default eval_set.json
"""

from __future__ import annotations

import json
import os
import signal
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Load workflow module dynamically so the agent can edit it freely.
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent
sys.path.insert(0, str(REPO_ROOT))

import workflow  # noqa: E402  — the agent's lever


# ---------------------------------------------------------------------------
# Eval set
# ---------------------------------------------------------------------------

DEFAULT_EVAL_SET = REPO_ROOT / "eval_set.json"
EVAL_FIELDS = ("vendor_name", "invoice_date", "total_amount", "currency", "tax_id")


def load_eval_set(path: Path) -> list[dict]:
    with path.open() as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"eval_set.json must be a JSON array, got {type(data).__name__}")
    for i, item in enumerate(data):
        if "input" not in item or "expected" not in item:
            raise ValueError(f"eval item {i} missing 'input' or 'expected'")
    return data


# ---------------------------------------------------------------------------
# Scoring — field-level exact-match F1, scaled 0-100.
# ---------------------------------------------------------------------------

def score_field(expected: object, predicted: object) -> float:
    """1.0 if exact match (with light type coercion for numbers/dates), else 0.0."""
    if expected is None and predicted is None:
        return 1.0
    if expected is None or predicted is None:
        return 0.0
    # Numerics: compare with epsilon
    if isinstance(expected, (int, float)) and isinstance(predicted, (int, float)):
        return 1.0 if abs(float(expected) - float(predicted)) < 0.01 else 0.0
    # Strings: strip + lowercase compare
    if isinstance(expected, str) and isinstance(predicted, str):
        return 1.0 if expected.strip().lower() == predicted.strip().lower() else 0.0
    return 1.0 if expected == predicted else 0.0


def score_outputs(expected: dict, predicted: dict) -> dict[str, float]:
    """Return per-field score and overall (mean) score."""
    per_field = {f: score_field(expected.get(f), predicted.get(f)) for f in EVAL_FIELDS}
    per_field["overall"] = sum(per_field.values()) / len(EVAL_FIELDS)
    return per_field


def run_eval(eval_set: list[dict], budget_sec: float) -> tuple[float, dict]:
    """Run workflow on all eval items within the time budget. Returns (overall_score, stats)."""
    deadline = time.monotonic() + budget_sec
    per_item_scores: list[float] = []
    per_field_totals = {f: 0.0 for f in EVAL_FIELDS}
    errors = 0

    for i, item in enumerate(eval_set):
        if time.monotonic() > deadline:
            raise TimeoutError(f"Eval exceeded budget of {budget_sec}s after {i} items")

        try:
            predicted = workflow.run_workflow(item["input"], workflow.WORKFLOW_CONFIG)
        except Exception as exc:  # noqa: BLE001 — agent's workflow may raise; we want to know
            errors += 1
            predicted = {f: None for f in EVAL_FIELDS}

        s = score_outputs(item["expected"], predicted)
        per_item_scores.append(s["overall"])
        for f in EVAL_FIELDS:
            per_field_totals[f] += s[f]

    n = len(eval_set)
    overall = (sum(per_item_scores) / n) * 100.0 if n else 0.0
    per_field_pct = {f: (per_field_totals[f] / n) * 100.0 if n else 0.0 for f in EVAL_FIELDS}

    stats = {
        "n_items": n,
        "errors": errors,
        "per_field_pct": per_field_pct,
    }
    return overall, stats


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    budget_sec = float(os.environ.get("EXPERIMENT_BUDGET_SEC", "60"))
    eval_path = Path(os.environ.get("EVAL_SET_PATH", str(DEFAULT_EVAL_SET)))

    print(f"autoresearch-sboss eval")
    print(f"  eval_set:     {eval_path}")
    print(f"  budget_sec:   {budget_sec}")
    print(f"  workflow:     {workflow.WORKFLOW_CONFIG.get('name', '?')}")
    print(f"  llm_endpoint: {os.environ.get('LLM_ENDPOINT_URL', '(mock)')}")
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
