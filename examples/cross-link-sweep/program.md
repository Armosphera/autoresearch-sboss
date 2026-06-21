# program.md — cross-account link sweep research charter

You are an autonomous research agent. Your job: improve `workflow.py` so the **business score**
from `eval.py` goes up. You do not edit `eval.py`, `eval_set.json`, or `pyproject.toml`.
You only edit `workflow.py` and append to `results.tsv`.

## The task

The `autoresearch-sboss` repo references the shared `A1-AI-Core` engine by GitHub URL in 22
`examples/*/program.md` files. Originally these pointed at `SamStep74/A1-AI-Core`; we have
mirrored the engine to `Armosphera/A1-AI-Core` so all downstream consumers under the
Armosphera org can resolve without crossing org boundaries.

**Baseline score: 0 / 22** — all 22 program.md files still reference the old path.
**Target score: 22 / 22** — every example whose upstream module lives in
`Armosphera/A1-AI-Core/src/*.js` has its `program.md` pointing at the Armosphera mirror.

The eval set is fixed: it tells you which of the 22 examples SHOULD be re-pointed (those
whose source module is in `A1-AI-Core`) and which should NOT (those sourced from
`A1-Localization-AM` / `A1-Localization-RU` — those were already on `Armosphera/` and need
no change).

## The rules

1. **Touch only `workflow.py`.** That file generates the replacement commits. Do not hand-edit
   individual `program.md` files in `examples/*/` — let `workflow.py` do it via the GitHub
   Contents API.
2. **One-pass atomicity.** Each `keep` produces a single commit per file. The agent measures
   score, decides keep/revert, appends to `results.tsv`, repeats.
3. **No false positives.** Replacing in a file whose source is NOT in `A1-AI-Core` is a
   **revert** — even if the resulting `program.md` is "fine", it's outside the eval contract.
4. **Preserve commit SHAs.** If a `program.md` already references a commit SHA from
   `SamStep74/A1-AI-Core`, the replacement must use the **identical SHA on the Armosphera
   mirror**. Use the GitHub Contents API to look up the file at the target repo's default
   branch and copy the SHA verbatim.

## The eval contract

`eval.py` reads `eval_set.json` and computes a score:

- For each entry, the entry specifies `file` (path under `examples/`), `source_module`
  (e.g. `src/model-policy.js`), and `expected_source_repo` (`Armosphera/A1-AI-Core` or
  `Armosphera/A1-Localization-AM` or `Armosphera/A1-Localization-RU`).
- Score increments when:
  - For `expected_source_repo = Armosphera/A1-AI-Core`: the `program.md` contains
    `github.com/Armosphera/A1-AI-Core` and contains NO `github.com/SamStep74/A1-AI-Core`.
  - For `expected_source_repo = Armosphera/A1-Localization-*`: the `program.md` does not
    contain `SamStep74` / `samstep74` at all (already correct).
- Max score: 22 / 22.
- Min score: 0 / 22 (current state of `main`).

## The loop

```
1. Read results.tsv — find the current best score.
2. Read workflow.py — understand the current strategy.
3. Edit workflow.py: pick the next file to fix, run the GitHub Contents API replacement,
   verify the new content via the API.
4. Run `python eval.py` — get the new score.
5. If new > best: commit workflow.py + the new program.md, append `keep` to results.tsv.
   If new ≤ best: `git revert`, append `revert` to results.tsv.
```

## Time budget

Default 60 s per iteration (`CROSS_LINK_BUDGET_S` env var, capped at 600 s).
The GitHub Contents API is rate-limited at 5000 req/h — keep batches ≤ 100 per run.

## Files

- `workflow.py` — agent-editable. Strategy + per-file replacement.
- `eval.py` — fixed. Computes the score.
- `eval_set.json` — fixed. 22 entries, one per `examples/*/program.md`.
- `results.tsv` — append-only ledger: `iteration | score | action | elapsed_s`.