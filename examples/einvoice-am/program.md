# program.md — Armenian e-invoice validator research charter

You are an autonomous research agent. Your job: improve `workflow.py` so that the field-level
exact-match F1 score from `eval.py` goes up. You do not edit `eval.py`, `eval_set.json`, or
`pyproject.toml`. You only edit `workflow.py` and append to `results.tsv`.

## The task

The default `workflow.py` is a faithful Python port of
`src/einvoice.js::validateEInvoice()` from
[A1-Localization-AM](https://github.com/Armosphera/A1-Localization-AM). Structural
compliance gate for an e-invoice before mapping to the official SRC XSD and submission.
Catches 16 distinct error codes covering transaction type, dates, supplier/buyer
identification, line items, and amount/rate consistency.

The current **baseline score is 100.00 / 100**. The JS reference handles all valid
inputs correctly — no bugs to fix. Your job is to make the Python implementation
**STRICTLY MORE USEFUL** than the JS reference by adding capabilities the JS lacks.

Your job, in priority order:

1. **Add `severity` field per finding.** Currently every error is `"error"` (blocks
   submission). Distinguish:
   - `"error"` — blocks submission (missing field, invalid format, etc.)
   - `"warning"` — should fix but doesn't block (e.g., vatAmount within 5% of expected)
   - `"info"` — informational (e.g., zero-rate line on a typically-VAT'd invoice)

2. **Add `summary` field.** One-line human-readable summary for UI toasts:
   `"2 errors: MISSING_TRANSACTION_TYPE, INVALID_BUYER_HVHH (buyer.hvhh)"`.

3. **Strict mode option.** Currently vatAmount mismatch tolerance is 1 dram. Add a
   `strict: bool` parameter that makes tolerance 0 (exact match required).

4. **Cross-line checks.** Add checks that span multiple lines:
   - All line rates sum correctly to header total rate
   - Sum of line totals = sum of net + vat + excise + env-fee

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

1. **Add `severity` field.** Default to "error" for all current codes; you can also add
   new warning-level checks (rate within 5% tolerance but not exact match).
2. **Add `summary` field.** Deterministic short string.
3. **Strict mode.** `strict=True` → vatAmount mismatch tolerance = 0.
4. **Cross-line consistency.** Sum line totals = header total.

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

The point: a Python e-invoice validator that's STRICTLY MORE USEFUL than the JS
reference — with severity, summary, strict mode, and (optionally) cross-line checks.
Worst case you revert.
