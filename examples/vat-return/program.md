# program.md — Armenian VAT return computation research charter

You are an autonomous research agent. Your job: improve `workflow.py` so that the field-level
exact-match F1 score from `eval.py` goes up. You do not edit `eval.py`, `eval_set.json`, or
`pyproject.toml`. You only edit `workflow.py` and append to `results.tsv`.

## The task

The default `workflow.py` is a faithful Python port of
`src/vatReturn.js::computeVatReturn()` from
[A1-Localization-AM](https://github.com/Armosphera/A1-Localization-AM). It implements
Armenia's standard VAT logic per decree N 298-Ն (arlis.am/hy/acts/136996):

- **Output VAT** = sum of VAT charged on sales (20% standard, 16.67% imputed, 0% zero-rated,
  exempt = 0)
- **Input VAT** = sum of VAT paid on recoverable purchases (recoverable by default)
- **Net** = output VAT − input VAT
- **Payable** to SRC = max(0, net) — Armenia doesn't auto-refund; a positive net is payable
- **CreditCarried** = max(0, -net) — Armenia carries negative balances forward

The current **baseline score is 100.00 / 100**. The JS reference is mathematically clean
for valid inputs — there are no bugs to fix. Your job is to make the Python implementation
**STRICTLY MORE USEFUL** than the JS reference by adding capabilities the JS lacks.

Your job is to add value, in this order:

1. **Input validation warnings.** The JS silently accepts negative `netAmount`,
   implausible `vatRate` (e.g., 200), and `vatAmount` that wildly disagrees with
   `vatRate`. Detect these and return a `warnings` field (list of strings, empty
   for clean inputs). This is what makes the difference between "calculation engine"
   and "audit-ready filing tool".

2. **Audit trail.** Return an `audit` field listing how each input line was classified
   (e.g., `{"index": 0, "kind": "sale", "net": 100000, "vat": 20000, "rate": 20,
   "bucket": "standard"}`). A finance auditor can then trace any number back to the
   source line.

3. **Multi-period aggregation.** Add `compute_vat_return_annual(periods)` that sums
   multiple `compute_vat_return` outputs. Returns `{year, outputVat, inputVat, net,
   payable, creditCarried}`. Useful for annual reconciliation.

4. **`vatReturnForm` port.** Port the second function in `src/vatReturn.js` that maps
   period data onto the official SRC form lines (7/9/12/13/16/17/18/21/23). Returns the
   form structure with `source` and `lineDefinitions` metadata.

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
- **Respect the time budget.** Default 60s per experiment. If eval.py runs over budget, revert.
- **Don't touch the score function.** `eval.py` is the judge. Editing it is cheating.
- **Log everything.** Every experiment, keep or revert, goes in `results.tsv`.
- **Don't break existing tests.** Baseline 100.00 must stay 100.00 — your additions must
  be backwards-compatible (add fields, don't rename or change types).

## What to try (in rough priority order)

1. **Add `warnings` field** to `run_workflow()`. Returns `[]` for clean inputs, or a list
   like `["negative_net:line:0", "vat_rate_invalid:line:2:rate=200"]` for suspect inputs.
   Update `eval_set.json` to add expected warnings for cases you construct.
2. **Add `audit` field.** Per-line classification log.
3. **Defensive defaults.** What if `sales` is `None`? Currently JS treats as `[]`. Should
   Python be stricter?
4. **Currency normalization.** All amounts assumed AMD. Add explicit `currency` field; warn
   if non-AMD input.

## When to stop

- Score = 100 AND `warnings` works AND `audit` works → done with v0.1.
- 20 experiments with no improvement → consider rewriting `program.md`.
- Same file edited 5 times with no improvement → step back, re-read workflow.py.

## Logging format for results.tsv

Tab-separated:
`timestamp\tcommit\tstatus\tscore\tbudget_sec\tdescription`

## Environment

This example uses NO LLM. Pure-function computation.

- `EXPERIMENT_BUDGET_SEC` (optional): wall-clock budget. Default `60`.

## Have fun

The point: a Python VAT computation that's STRICTLY MORE USEFUL than the JS reference —
audit-ready, with warnings and traceability, ready for a finance team to file with
confidence. Worst case you revert.
