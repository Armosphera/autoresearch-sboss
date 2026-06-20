# program.md — Russian VAT research charter

You are an autonomous research agent. Your job: improve `workflow.py` so that the field-level
exact-match F1 score from `eval.py` goes up. You do not edit `eval.py`, `eval_set.json`, or
`pyproject.toml`. You only edit `workflow.py` and append to `results.tsv`.

## The task

The default `workflow.py` is a faithful Python port of
`src/vat.js` from
[Armosphera/A1-Localization-RU](https://github.com/Armosphera/A1-Localization-RU).
Russian VAT (НДС) — 2026 rates + settlement math.

**2026 налоговая реформа:** base rate 20% → 22% (effective 2026-01-01).
Reduced 10% (food/children/medical), 0% (export). УСН payers may use
special 5%/7% rates. Year-keyed so prior/future years can be added without
breaking callers.

5 functions: `ratesFor` / `vatFromNet` / `vatFromGross` / `netFromGross` /
`isValidVatRate`.

The current **baseline score is 100.00 / 100** — the JS reference is
correct. Your job is to make the Python implementation **STRICTLY MORE
USEFUL** than the JS reference by adding capabilities the JS lacks.

Your job, in priority order:

1. **Add `audit` field per call.** Trace which rate table + which regime was
   used; show the settlement rate (e.g. 22/122 for 22% base); show
   effective tax rate as percentage.
2. **Add `summary` field.** One-line human-readable summary for UI toasts:
   `"10,000 ₽ net × 22% = 12,200 ₽ gross (НДС 2,200 ₽)"`.
3. **Add `vatSummary` for batches.** `summarizeVat([{net, rate}, ...])` returns
   rollup by rate + grand total.
4. **Add year-keyed validators.** `isValidRateForYear(rate, year, opts)`
   to support back-dated documents.
5. **Add `reverseVat` (gross → net+VAT split).** Returns `{net, vat, total}`
   for a gross amount.

## The loop

```
1. Read results.tsv — find the current best score.
2. Read workflow.py — understand the current state.
3. Make ONE focused change to workflow.py (a hypothesis).
4. Run: python3 eval.py
5. Read the new score from stdout.
6. If new_score > best_score:
       git add workflow.py && git commit -m "score: N.NNN — <one-line hypothesis>"
   Else:
       git checkout workflow.py
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

1. **`audit` field** — per-call trace.
2. **`summary` field** — short string summary.
3. **`summarizeVat` (batch rollup).** Per-rate totals + grand total.
4. **`isValidRateForYear`** — year-aware validator.
5. **`reverseVat`** — gross → net+VAT split.

## When to stop

- Score = 100 AND `audit` + `summary` + `summarizeVat` all work → done with v0.1.
- 20 experiments with no improvement → consider rewriting `program.md`.

## Logging format for results.tsv

Tab-separated:
`timestamp\tcommit\tstatus\tscore\tbudget_sec\tdescription`

## Environment

This example uses NO LLM. Pure-function fiscal math.

- `EXPERIMENT_BUDGET_SEC` (optional): wall-clock budget. Default `60`.

## Have fun

The point: a Russian VAT engine that's STRICTLY MORE USEFUL than the JS
reference — with audit traces, batch rollup, and (optionally) year-keyed
validators. Worst case you revert.
