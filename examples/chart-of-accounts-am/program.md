# program.md — Armenian chart of accounts research charter

You are an autonomous research agent. Your job: improve `workflow.py` so that the field-level
exact-match F1 score from `eval.py` goes up. You do not edit `eval.py`, `eval_set.json`, or
`data.json`. You only edit `workflow.py` and append to `results.tsv`.

## The task

The default `workflow.py` ports `src/armeniaChartOfAccounts.js` from
[A1-Localization-AM](https://github.com/Armosphera/A1-Localization-AM). It loads the
official RA chart of accounts (623 accounts across 9 classes, per Ministry of Finance
order arlis.am/hy/acts/75961) and provides three lookup functions:

- `accountByCode(code)` → returns the full account record or `None`
- `accountClass(code)` → returns class metadata (digit / hy / en / type / normalBalance)
- `normalBalance(code)` → `"debit"` / `"credit"` / `None`

Plus a new `validateCode(code)` wrapper that returns a structured result with an explicit
error code when the lookup fails (`empty_code` / `non_numeric_code` / `invalid_length_code`
/ `unknown_code`).

The 20 eval cases split evenly:
- **10 known codes** (one per class 1-9, plus the 4-digit sub-account `1111`): expect
  `ok=true`, `hy`/`class`/`type` filled in.
- **10 invalid/unknown codes** (empty, non-numeric, wrong length, well-formed but
  unknown): expect `ok=false`, `error` filled in, `hy`/`class`/`type` null.

**Baseline score should be 100.00.** The JS reference is data-only and the Python
implementation should match it byte-for-byte for known codes + add the structured
validation wrapper for invalid ones.

Your job is to make the Python implementation **STRICTLY MORE USEFUL** than the JS:

1. **Search by Armenian name keyword.** Add `search_by_name(query, lang="hy")` that returns
   a list of matching accounts. Useful for "find all accounts related to VAT".

2. **Code → parent class navigation.** Add `parent_class(code)` and
   `sub_accounts(parent_code)` that walk the chart hierarchy. Useful for UI dropdowns.

3. **Type metadata.** Add `accounts_by_type("asset")` returning all 110 asset accounts
   (the JS already has this; the eval just doesn't test it yet).

4. **Deprecated / inactive flags.** If you have access to a newer version of the chart
   that deprecates some accounts, add a `deprecated` field. (Out of scope for this
   baseline — skip unless you have a source.)

## The loop

```
1. Read results.tsv — find the current best score.
2. Read workflow.py — understand the current state.
3. Make ONE focused change to workflow.py (a hypothesis).
4. Run: uv run eval.py   (or: python3 eval.py)
5. Read the new score from stdout.
6. If new_score > best_score:
       git add workflow.py eval_set.json && git commit -m "score: N.NNN — <one-line hypothesis>"
   Else:
       git checkout workflow.py eval_set.json
7. Append the experiment to results.tsv.
8. Repeat.
```

## Rules of engagement

- **One hypothesis per experiment.** Don't bundle 5 unrelated changes into one commit.
- **Read first, edit second.** Always re-read workflow.py before editing.
- **Keep it boring.** Small, reversible changes. No sweeping rewrites.
- **Respect the time budget.** Default 60s per experiment.
- **Don't touch the score function.** `eval.py` is the judge.
- **Log everything.** Every experiment, keep or revert, goes in `results.tsv`.
- **Don't break existing tests.** Baseline 100.00 must stay 100.00.
- **Don't edit data.json.** It's the immutable source of truth (mirrors the JS reference).

## What to try (in rough priority order)

1. **Search by name.** Use simple substring match (case-insensitive). Update eval_set.json
   to test queries like `query: "ԱԱՀ"` → expected = [accounts with "ԱԱՀ" in name].
2. **Sub-accounts.** Given a 3-digit parent code (e.g., `111`), return all 4-digit children
   (e.g., `1111`, `1112`, `1113`, ...).
3. **Type counts.** Return `{asset: 110, equity: 43, liability: 88, ...}` — useful for
   accounting dashboards.
4. **Validate + suggest.** Given a malformed code like `999`, suggest the closest valid
   code by first-digit (e.g., `99X` → `911`).

## When to stop

- Score = 100 AND search_by_name works → done with v0.1.
- 20 experiments with no improvement → consider rewriting `program.md`.

## Logging format for results.tsv

Tab-separated:
`timestamp\tcommit\tstatus\tscore\tbudget_sec\tdescription`

## Environment

This example uses NO LLM. Pure lookup + validation.

- `EXPERIMENT_BUDGET_SEC` (optional): wall-clock budget. Default `60`.

## Have fun

The point: a Python chart-of-accounts lookup that's STRICTLY MORE USEFUL than the JS
reference — with structured validation, search, and (optionally) hierarchy navigation.
Worst case you revert.
