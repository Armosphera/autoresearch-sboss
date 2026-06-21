#!/usr/bin/env python3
"""run_evals.py — run all sub-examples evals and print a summary table.

The Karpathy autoresearch pattern: each example is a fixed-target workflow that
the agent iterates on. The CI gate uses bash to assert every example scores
100. This tool is the local equivalent — it runs every example's eval.py,
captures the score, and prints a summary table.

Usage:
    python scripts/run_evals.py              # run all examples
    python scripts/run_evals.py ar-cuit       # run a single example
    python scripts/run_evals.py --strict      # exit 1 if any < 100
    python scripts/run_evals.py --json        # machine-readable output

Exit codes:
    0 — all examples at 100/100 (or 22/22 for cross-link-sweep)
    1 — one or more examples below threshold (with --strict)
    2 — one or more examples errored out
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = REPO_ROOT / "examples"

SCORE_RE = re.compile(r"^score:\s+(\S+)\s+elapsed:")
INFRA_SCORE_RE = re.compile(r"^score:\s+(\S+)$")
# cross-link-sweep outputs "score: 22 / 22 | elapsed: ..." (no decimal)
INFRA_FRAC_RE = re.compile(r"^score:\s+(\d+)\s*/\s*(\d+)\s*\|")
ERROR_RE = re.compile(r"^Error|Traceback|File \"<frozen")


def run_one(example_dir: Path, timeout: float = 60.0) -> dict:
    """Run one example's eval.py and capture the result."""
    name = example_dir.name
    eval_script = example_dir / "eval.py"
    if not eval_script.exists():
        return {"name": name, "score": None, "status": "skip", "error": "no eval.py"}
    try:
        result = subprocess.run(
            ["python3", str(eval_script)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=example_dir,
        )
    except subprocess.TimeoutExpired:
        return {"name": name, "score": None, "status": "timeout", "error": f"timeout after {timeout}s"}
    if result.returncode != 0:
        return {
            "name": name,
            "score": None,
            "status": "error",
            "error": (result.stderr or "")[:200],
        }
    # Parse the score line. Supports three formats:
    #   "score: 100.0000  elapsed: ..."      (most examples)
    #   "score: 0.8888"                       (some examples)
    #   "score: 22 / 22 | elapsed: ..."       (cross-link-sweep infra)
    score = None
    score_max = None
    for line in (result.stdout or "").splitlines():
        m = SCORE_RE.match(line) or INFRA_SCORE_RE.match(line)
        if m:
            try:
                score = float(m.group(1))
            except ValueError:
                pass
            break
        m = INFRA_FRAC_RE.match(line)
        if m:
            try:
                score = float(m.group(1))
                score_max = float(m.group(2))
            except ValueError:
                pass
            break
    return {
        "name": name,
        "score": score,
        "status": "ok" if score is not None else "parse-error",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Run autoresearch-sboss sub-example evals")
    ap.add_argument("examples", nargs="*", help="Specific examples to run (default: all)")
    ap.add_argument("--strict", action="store_true", help="Exit 1 if any example is below 100")
    ap.add_argument("--json", action="store_true", help="JSON output instead of table")
    ap.add_argument("--timeout", type=float, default=60.0, help="Per-example timeout (default 60s)")
    args = ap.parse_args()

    if args.examples:
        targets = [EXAMPLES_DIR / name for name in args.examples]
    else:
        targets = sorted(p for p in EXAMPLES_DIR.iterdir() if p.is_dir())

    results = []
    for example_dir in targets:
        if not example_dir.exists():
            results.append({"name": example_dir.name, "score": None, "status": "missing", "error": "dir not found"})
            continue
        r = run_one(example_dir, timeout=args.timeout)
        results.append(r)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        # Pretty table
        name_w = max(len(r["name"]) for r in results) if results else 10
        print(f"{'example'.ljust(name_w)}  {'score'.rjust(10)}  status")
        print(f"{'-' * name_w}  {'-' * 10}  {'-' * 10}")
        for r in results:
            score_str = f"{r['score']:>10.4f}" if r["score"] is not None else "       N/A"
            status_str = r["status"]
            if r["status"] != "ok" and "error" in r:
                status_str = f"{status_str} ({r['error'][:40]})"
            print(f"{r['name'].ljust(name_w)}  {score_str}  {status_str}")

    # Exit code logic
    n_below = sum(1 for r in results if r["score"] is not None and r["score"] < 100 and r["status"] == "ok")
    # cross-link-sweep is the one exception — it scores "22" (out of 22)
    n_error = sum(1 for r in results if r["status"] in ("error", "timeout", "parse-error", "missing"))
    if n_error:
        return 2
    if args.strict and n_below:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
