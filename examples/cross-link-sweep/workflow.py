"""workflow.py — cross-link sweep across 22 examples/*/program.md files in armosphera/autoresearch-sboss.

AGENT-EDITABLE. The agent improves this strategy. eval.py scores the result.

Strategy v1 (baseline):
  1. List all 22 examples/*/program.md via GitHub Contents API.
  2. For each, fetch current content from default branch.
  3. If content references `SamStep74` or `samstep74`, prepare a replacement that:
     - swaps github.com/SamStep74/ -> github.com/Armosphera/
     - swaps github.com/samstep74/ -> github.com/Armosphera/
     - swaps SamStep74/A1-AI-Core -> Armosphera/A1-AI-Core
     - preserves everything else (commit SHAs, prose, etc.)
  4. PUT via GitHub Contents API as a single commit per file.
  5. Run `python eval.py` to verify.

After eval.py prints `score: 22 / 22`, append `keep 22.0000 keep` to results.tsv.
Otherwise `git revert` (or in our case: revert via the API) and try again.
"""

from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).parent
sys.path.insert(0, str(REPO_ROOT))

REPO = "Armosphera/autoresearch-sboss"
DEFAULT_REF = "main"

# 22 examples/*/program.md files, derived from `gh api .../git/trees/main?recursive=1`.
# The agent must NOT change this list — it's the canonical corpus (matches eval_set.json).
EXAMPLE_PROGRAM_MD = [
    "examples/chart-of-accounts-am/program.md",
    "examples/chart-of-accounts-ru/program.md",
    "examples/chat-client/program.md",
    "examples/einvoice-am/program.md",
    "examples/hhvh/program.md",
    "examples/model-catalog/program.md",
    "examples/model-policy/program.md",
    "examples/open-notebook/program.md",
    "examples/payroll-am/program.md",
    "examples/payroll-ru/program.md",
    "examples/phone-am/program.md",
    "examples/phone-ru/program.md",
    "examples/product-research/program.md",
    "examples/regions-am/program.md",
    "examples/regions-ru/program.md",
    "examples/ru-einvoice/program.md",
    "examples/ru-identifiers/program.md",
    "examples/settings-store/program.md",
    "examples/supplemental-sources/program.md",
    "examples/vat-return-form/program.md",
    "examples/vat-return/program.md",
    "examples/vat-ru/program.md",
]


def get_token() -> str:
    tok = (
        os.environ.get("GH_TOKEN_ARMOSPHERA")
        or (Path("/tmp/gh_token").read_text().strip() if Path("/tmp/gh_token").exists() else None)
    )
    if not tok:
        r = subprocess.run(["gh", "auth", "token", "--user", "Armosphera"], capture_output=True, text=True)
        tok = r.stdout.strip()
    return tok


TOKEN = get_token()


def gh(method: str, url: str, body: dict | None = None) -> tuple[int, dict]:
    data = json.dumps(body).encode() if body else None
    request = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"token {TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(request, timeout=20) as resp:
            return resp.status, json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")


def fetch(path: str, ref: str = DEFAULT_REF) -> tuple[str | None, str | None]:
    """Fetch (content, sha) for a file in the target repo."""
    status, data = gh("GET", f"https://api.github.com/repos/{REPO}/contents/{path}?ref={ref}")
    if status != 200:
        return None, None
    try:
        content = base64.b64decode(data["content"]).decode("utf-8")
    except Exception:
        return None, None
    return content, data.get("sha")


def replace_refs(content: str) -> str:
    """Apply the canonical SamStep74/samstep74 -> Armosphera replacements."""
    new = content
    new = new.replace("github.com/SamStep74/", "github.com/Armosphera/")
    new = new.replace("github.com/samstep74/", "github.com/Armosphera/")
    new = new.replace("SamStep74/A1-AI-Core", "Armosphera/A1-AI-Core")
    new = new.replace("samstep74/A1-AI-Core", "Armosphera/A1-AI-Core")
    return new


def commit(path: str, content: str, sha: str, message: str) -> tuple[int, dict]:
    body = {
        "message": message,
        "content": base64.b64encode(content.encode()).decode(),
        "branch": DEFAULT_REF,
        "sha": sha,
    }
    return gh("PUT", f"https://api.github.com/repos/{REPO}/contents/{path}", body)


def run_one_iteration(commit_each_file: bool = True, dry_run: bool = False) -> dict:
    """Run one sweep. Returns a result dict: {updates, errors, score_pre, score_post}."""
    updates = []
    errors = []

    for path in EXAMPLE_PROGRAM_MD:
        content, sha = fetch(path)
        if content is None:
            errors.append((path, "fetch_failed"))
            continue
        new = replace_refs(content)
        if new == content:
            updates.append((path, "noop_already_clean"))
            continue
        if dry_run:
            updates.append((path, "dry_run_no_commit"))
            continue
        message = f"chore: re-point SamStep74/A1-AI-Core ref to Armosphera/A1-AI-Core mirror in {path}"
        status, result = commit(path, new, sha, message)
        if status in (200, 201):
            updates.append((path, f"committed:{result['commit']['sha'][:12]}"))
        else:
            errors.append((path, f"commit_failed:{status}:{result.get('message')}"))

    return {"updates": updates, "errors": errors}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Cross-link sweep workflow")
    parser.add_argument("--dry-run", action="store_true", help="Don't commit")
    parser.add_argument("--verify", action="store_true", help="Just verify (no edits)")
    args = parser.parse_args()

    t0 = time.time()
    if args.verify:
        result = {"updates": [], "errors": [], "verified": True}
        for path in EXAMPLE_PROGRAM_MD:
            content, _ = fetch(path)
            status = "clean" if content and "SamStep74" not in content and "samstep74" not in content else "dirty"
            result["updates"].append((path, status))
    else:
        result = run_one_iteration(commit_each_file=True, dry_run=args.dry_run)
    elapsed = time.time() - t0

    print(f"=== workflow.py: cross-link sweep ===")
    print(f"elapsed: {elapsed:.2f}s")
    print(f"updates: {len(result['updates'])}, errors: {len(result['errors'])}")
    for path, status in result["updates"]:
        print(f"  ✓ {path}: {status}")
    for path, err in result["errors"]:
        print(f"  ✗ {path}: {err}")


if __name__ == "__main__":
    main()