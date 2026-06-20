# program.md — Armenian payroll rules research charter

You are an autonomous research agent. Your job: improve `workflow.py` so that the field-level
exact-match F1 score from `eval.py` goes up. You do not edit `eval.py`, `eval_set.json`, or
`pyproject.toml`. You only edit `workflow.py` and append to `results.tsv`.

## The task

The default `workflow.py` is a faithful Python port of `src/armeniaPayroll.js` from
[A1-Localization-AM](https://github.com/Armosphera/A1-Localization-AM). It computes an
employee's gross → net under 2026 Armenian rules: 4 withholdings off the SAME gross —
income tax (flat 20%), pension (tiered 5% / 10%−25k capped at 87,500), stamp duty (flat
1,000/mo 2026 revision), and health insurance (banded 0 / 4,800 / 10,800).

The current **baseline score is 100.00 / 100**. The JS reference is mathematically clean
for valid gross inputs — no bugs to fix. Your job is to make the Python implementation
**STRICTLY MORE USEFUL** than the JS reference by adding capabilities the JS lacks.

Your job, in priority order:

1. **Input validation warnings.** Detect: negative gross, non-finite (NaN/Infinity),
   unreasonably large salaries (e.g., > 100M AMD), and gross that looks like a typo
   (e.g., 1 dram, 100 dram). Return a `warnings` field (list of strings, empty for clean).
   The JS silently treats invalid inputs as 0 — silent failure is dangerous in payroll.

2. **Net effective rate.** Return `effectiveRate: totalWithholdings / gross` (rounded
   to 4 decimal places). A CFO looking at a pay stub wants to see "33.5% effective tax
   burden" at a glance.

3. **Annual projection.** Add `compute_annual_payroll(monthly_gross, months=12)` that
   returns `{annualGross, annualIncomeTax, annualPension, annualStampDuty,
   annualHealthInsurance, annualNet}`. Useful for budget planning.

4. **Employer-side contributions.** Armenia employers also pay a 5% social contribution
   (different from the employee pension) and other employer-side taxes. Add
   `employerContributions(gross)` returning `{socialContribution, totalEmployerCost}`.

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
- **Don't break existing tests.** Baseline 100.00 must stay 100.00 — your additions must
  be backwards-compatible.

## What to try (in rough priority order)

1. **Add `warnings` field.** Returns `[]` for clean gross (positive, < 100M), or a list
   like `["negative_gross", "unrealistic_salary:100000000"]` for suspect inputs.
2. **Add `effectiveRate` field.** `totalWithholdings / gross * 100`, rounded.
3. **Annual projection function.** `compute_annual_payroll(monthly_gross)`.
4. **Employer-side contributions.** Armenia social contribution (5% up to cap).
5. **Comparison mode.** Given multiple gross salaries, return the cheapest-vs-most-expensive
   net comparison.

## When to stop

- Score = 100 AND `warnings` works AND `effectiveRate` works → done with v0.1.
- 20 experiments with no improvement → consider rewriting `program.md`.

## Logging format for results.tsv

Tab-separated:
`timestamp\tcommit\tstatus\tscore\tbudget_sec\tdescription`

## Environment

This example uses NO LLM. Pure-function computation.

- `EXPERIMENT_BUDGET_SEC` (optional): wall-clock budget. Default `60`.

## Have fun

The point: a Python payroll engine that's STRICTLY MORE USEFUL than the JS reference —
with input warnings, effective rate, and (optionally) annual + employer-side views.
Worst case you revert.
