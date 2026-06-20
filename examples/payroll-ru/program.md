# program.md — Russian payroll research charter

You are an autonomous research agent. Your job: improve `workflow.py` so that the field-level
exact-match F1 score from `eval.py` goes up. You do not edit `eval.py`, `eval_set.json`, or
`pyproject.toml`. You only edit `workflow.py` and append to `results.tsv`.

## The task

The default `workflow.py` is a faithful Python port of
`src/payroll.js` from
[Armosphera/A1-Localization-RU](https://github.com/Armosphera/A1-Localization-RU).
Russian payroll — НДФЛ (employee withholding) + страховые взносы (employer
contributions), 2026. Two tax engines:

- **НДФЛ** (employee withholding): 5-band progressive marginal scale on
  cumulative annual base (ст. 224 НК РФ). 2026 bands: 13% / 15% / 18% / 20% / 22%.
  Non-residents flat 30% (п. 3 ст. 224, default no deductions).
- **Страховые взносы** (employer unified): 30% within unified base limit
  (ЕПВБ = 2,979,000 in 2026), 15.1% above (ст. 425 НК РФ). МСП reduced tariff
  (ст. 427): 30% within 1.5×МРОТ monthly, 15% above.

Child standard deductions (ст. 218 НК РФ): 1st=1,400 / 2nd=2,800 / 3rd=6,000 /
disabled-child=12,000 (parent) or 6,000 (guardian). Stops once YTD income
exceeds 450,000.

The current **baseline score is 100.00 / 100** — the JS reference is correct.
Your job is to make the Python implementation **STRICTLY MORE USEFUL** than the
JS reference by adding capabilities the JS lacks.

Your job, in priority order:

1. **Add `audit` field per result.** Trace which band was used for НДФЛ, which
   insurance tier applied, and the effective tax rate. Useful for filing
   reviews and audit defense.
2. **Add `summary` field.** One-line human-readable summary for UI toasts:
   `"100,000 ₽ → 87,000 net (НДФЛ 13%, страх 30%)"`.
3. **Multi-employee batch.** `computeBatchPayroll([opts1, opts2, ...])` returns
   a list of per-employee results + a totals rollup.
4. **Year-keyed rates.** Add 2025 + 2027+ rate tables so back-dated and
   forward-dated documents compute correctly.

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

1. **`audit` field** — band/traces/effective rate per call.
2. **`summary` field** — short string summary.
3. **`computeBatchPayroll`** — multi-employee batch + totals.
4. **Year-keyed rates** — `year: 2025` / `2026` / `2027` parameter.
5. **МСП eligibility check** — `isSmeEligible(opts)` per ФЗ № 425-ФЗ.

## When to stop

- Score = 100 AND `audit` works AND `summary` works → done with v0.1.
- 20 experiments with no improvement → consider rewriting `program.md`.

## Logging format for results.tsv

Tab-separated:
`timestamp\tcommit\tstatus\tscore\tbudget_sec\tdescription`

## Environment

This example uses NO LLM. Pure-function fiscal engine.

- `EXPERIMENT_BUDGET_SEC` (optional): wall-clock budget. Default `60`.

## Have fun

The point: a Russian payroll engine that's STRICTLY MORE USEFUL than the JS
reference — with audit traces, batch processing, year-keyed rates, and
(optionally) МСП eligibility check. Worst case you revert.
