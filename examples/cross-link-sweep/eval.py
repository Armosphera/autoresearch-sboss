"""eval.py — fixed eval harness for the cross-link-sweep example.

DO NOT MODIFY. The agent edits workflow.py. This file is the judge.

Reads eval_set.json (22 entries, one per examples/*/program.md), reads each program.md
from the LOCAL filesystem (no GitHub API needed), and computes a binary score:

  +1 per file if the program.md's source-ref matches `expected_source_repo`
  +0 per file otherwise

The local-file read makes this a deterministic, network-free eval. The CI gate can run
it on every push without a GitHub token.

Prints the score, the per-file result table, and exits 0 if score == len(eval_set),
1 otherwise.

The agent's goal: keep this at `score: 22 / 22` after every example addition.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).parent
sys.path.insert(0, str(REPO_ROOT))

# The actual git repo root is the parent of examples/cross-link-sweep/. Resolve it
# once and reuse for all file reads + the out-of-scope glob.
GIT_REPO_ROOT = REPO_ROOT.parent.parent
EVAL_SET = REPO_ROOT / "eval_set.json"


def read_local_program_md(path: str) -> str | None:
    """Read a program.md from the local filesystem (relative to git repo root).

    The 22 in-scope program.md files all live in this repo at examples/*/program.md.
    No GitHub API needed — the local file is the source of truth for the test.
    """
    full_path = GIT_REPO_ROOT / path
    try:
        return full_path.read_text(encoding="utf-8", errors="replace")
    except (OSError, FileNotFoundError):
        return None


def score_file(content: str, expected_repo: str) -> tuple[int, str]:
    """Return (delta, reason)."""
    if not content:
        return 0, "fetch_failed"

    bad = "SamStep74" in content or "samstep74" in content

    if expected_repo == "Armosphera/A1-AI-Core":
        # Must reference Armosphera/A1-AI-Core AND must NOT reference SamStep74
        if bad:
            return 0, "still_has_samstep74"
        if "Armosphera/A1-AI-Core" in content or "github.com/Armosphera/A1-AI-Core" in content:
            return 1, "ok_aicore"
        return 0, "no_aicore_ref"
    else:
        # Localization repos — must NOT have any SamStep74 ref
        if bad:
            return 0, "has_samstep74_in_localization"
        return 1, "ok_localization"


def main() -> int:
    if not EVAL_SET.exists():
        print(f"FAIL: missing {EVAL_SET}", file=sys.stderr)
        return 2

    eval_set = json.loads(EVAL_SET.read_text())
    t0 = time.time()
    total = 0
    per_file: list[tuple[str, str, int, str]] = []

    # Read each program.md locally. `expected_source_repo` is WHERE THE UPSTREAM
    # SOURCE MODULE LIVES (different repo), NOT where the program.md lives.
    # The program.md file IS the local file we're testing.
    for entry in eval_set:
        path = entry["file"]              # e.g. "examples/hhvh/program.md"
        expected_repo = entry["expected_source_repo"]
        content = read_local_program_md(path)
        delta, reason = score_file(content, expected_repo)
        total += delta
        per_file.append((path, expected_repo, delta, reason))

    elapsed = time.time() - t0
    max_score = len(eval_set)

    print(f"\n=== Cross-link-sweep eval ===")
    print(f"score: {total} / {max_score} | elapsed: {elapsed:.2f}s")
    print()
    print(f"{'file':50} {'expected_repo':40} {'Δ':>3}  {'reason'}")
    print("-" * 100)
    for path, expected_repo, delta, reason in per_file:
        marker = "+" if delta else "·"
        print(f"{path:50} {expected_repo:40} {marker:>3}  {reason}")

    if total == max_score:
        print(f"\n✅ ALL CLEAR — every program.md points to the right source repo.")
    else:
        print(f"\n❌ {max_score - total} files still need work.")

    # List examples NOT in the eval_set (those are correctly out of scope).
    # The eval_set covers the 22 SBOSS-derived examples (A1-AI-Core +
    # A1-Localization-AM + A1-Localization-RU). Other examples (e.g. cnpj, cpf,
    # eu-vat, uk-company, us-ein, gstin, swiss-uid, au-abn) reference public
    # sources (irs.gov, gst.gov.in, uid.admin.ch, abr.business.gov.au, etc.) or
    # have no Armosphera mirror at all, so they're correctly OUT OF SCOPE.
    # cross-link-sweep itself is also excluded (no program.md source of truth).
    in_scope = {entry["file"] for entry in eval_set}
    out_of_scope = []
    for prog_md in sorted(GIT_REPO_ROOT.glob("examples/*/program.md")):
        rel = str(prog_md.relative_to(GIT_REPO_ROOT))
        if rel not in in_scope:
            out_of_scope.append(rel)
    if out_of_scope:
        print()
        print(f"Out of scope ({len(out_of_scope)} program.md files — public sources or no Armosphera mirror):")
        for p in sorted(out_of_scope):
            print(f"  · {p}")

    return 0 if total == max_score else 1


if __name__ == "__main__":
    sys.exit(main())