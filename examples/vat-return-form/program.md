# program.md — VAT return form validator research charter

You are an autonomous research agent. Your job: improve `workflow.py` so that the field-level
exact-match F1 score from `eval.py` goes up. You do not edit `eval.py`, `eval_set.json`, or
`pyproject.toml`. You only edit `workflow.py` and append to `results.tsv`.

## The task

The default `workflow.py` is a faithful Python port of
`src/vatReturn.js::validateVatReturnForm()` from
[A1-Localization-AM](https://github.com/Armosphera/A1-Localization-AM). It validates an
assembled VAT-return form against the official SRC form rules per decree N 298-Ն.
Detects 10 distinct error codes: `FORM_MISSING_LINE`, `FORM_NON_NUMERIC_AMOUNT`,
`FORM_NON_INTEGER_AMOUNT`, `FORM_NEGATIVE_AMOUNT`, `FORM_16_BASE_MISMATCH`,
`FORM_16_VAT_MISMATCH`, `FORM_21_VAT_MISMATCH`, `FORM_23_NET_MISMATCH`,
`FORM_7_RATE_MISMATCH`, `FORM_9_RATE_MISMATCH`.

The current **baseline score is 100.00 / 100**. The JS reference handles all 10 error
codes correctly — no bugs to fix. Your job is to make the Python implementation
**STRICTLY MORE USEFUL** than the JS reference by adding capabilities the JS lacks.

Your job, in priority order:

1. **Add `severity` field per finding.** The JS treats every finding as `error`. Add
   `severity` (`"error"` / `"warning"` / `"info"`) per finding. Errors block filing;
   warnings are advisory; info is FYI. Candidates for warnings: rate-band mismatch
   within tighter tolerance (e.g., 0.1% instead of 1%), amounts very close to zero.
2. **Add `summary` field.** One-line human-readable summary: e.g.,
   `"2 errors: FORM_16_BASE_MISMATCH (line 16.base), FORM_NEGATIVE_AMOUNT (line 7.base)"`.
   Useful for UI toast notifications.
3. **Stricter checks.** Reject: zero line totals (suspicious), lines 7/9 vatAmount = 0
   with non-zero base, recoverable > 50% of output (suspicious credit pattern).
4. **Better numeric tolerance.** Currently the rate band is ~1% + 2 dram. For large
   amounts (>10M), 1% can hide real errors. Use 0.5% for amounts > 10M.

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

## What to try (in rough priority order)

1. **Add `severity` per finding.** Default to `"error"`; tag specific findings as
   `"warning"` (rate-band mismatch within 0.5% but not 1%, near-zero amounts).
2. **Add `summary` field.** A short, deterministic, human-readable string.
3. **Stricter checks.** Reject: amount exactly 0 on a line that's supposed to have
   transactions (e.g., line 7 with base=0 implies no sales — probably an error).
4. **Tighter rate band.** 0.5% + 1 dram for amounts > 10M.

## When to stop

- Score = 100 AND `severity` works AND `summary` works → done with v0.1.
- 20 experiments with no improvement → consider rewriting `program.md`.

## Logging format for results.tsv

Tab-separated:
`timestamp\tcommit\tstatus\tscore\tbudget_sec\tdescription`

## Environment

This example uses NO LLM. Pure-function validation.

- `EXPERIMENT_BUDGET_SEC` (optional): wall-clock budget. Default `60`.

## Have fun

The point: a Python VAT form validator that's STRICTLY MORE USEFUL than the JS
reference — with severity, summary, and (optionally) stricter checks. Worst case you
revert.
