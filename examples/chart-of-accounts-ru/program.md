# program.md — Russian chart of accounts research charter

You are an autonomous research agent. Your job: improve `workflow.py` so that the field-level
exact-match F1 score from `eval.py` goes up. You do not edit `eval.py`, `eval_set.json`, or
`pyproject.toml`. You only edit `workflow.py` and append to `results.tsv`.

## The task

The default `workflow.py` is a faithful Python port of
`src/chartOfAccounts.js` from
[Armosphera/A1-Localization-RU](https://github.com/Armosphera/A1-Localization-RU).
Russian chart of accounts (План счетов) per Приказ Минфина РФ № 94н от 31.10.2000.

**73 accounts** in 9 sections (8 balance-sheet sections I-VIII + off-balance),
loaded from `data.json` + `sections.json`. Unlike the AM chart (where the
leading digit encodes the class), in 94н the **section is determined by the
account NUMBER RANGE** (e.g. 01–09 is section I, 10–19 is section II).
Off-balance accounts use 3-digit codes (001–011), balance-sheet accounts use
2-digit codes (01–99).

The current **baseline score is 100.00 / 100** — the JS reference is correct.
Your job is to make the Python implementation **STRICTLY MORE USEFUL** than the
JS reference by adding capabilities the JS lacks.

Your job, in priority order:

1. **Add `subAccounts` (sub-account validation).** Russian chart supports
   3-level codes like "01.01" (sub-account of account 01). Validate format
   and lookup.
2. **Add `sectionOf` (section by code) exposed via run_workflow.** Currently
   only `accountByCode` is exposed; add a second operation to return the
   section for a given code.
3. **Add `accountsBySection` + `accountsByNature` exposed via run_workflow.**
   Surface the filter operations.
4. **Add `nature_summary` rollup.** Return a count of active / passive /
   active-passive accounts per section.
5. **Add `subAccountOf(parentCode, subCode)` validator.** Verifies that
   `subCode` is a valid sub-account format of `parentCode` (3 digits + dot
   + 2 digits).

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

1. **`subAccounts` (3-level codes).** Validate "01.01" against the chart.
2. **`sectionOf` via run_workflow.** Second operation in the dispatcher.
3. **`accountsBySection` / `accountsByNature` via run_workflow.** Third +
   fourth operations.
4. **`nature_summary` rollup.** Per-section count of active/passive/a-p.
5. **`subAccountOf` validator.** Format check + parent lookup.

## When to stop

- Score = 100 AND sub-accounts + sectionOf + accountsBySection all work → done with v0.1.
- 20 experiments with no improvement → consider rewriting `program.md`.

## Logging format for results.tsv

Tab-separated:
`timestamp\tcommit\tstatus\tscore\tbudget_sec\tdescription`

## Environment

This example uses NO LLM. Pure-function lookup with data file.

- `EXPERIMENT_BUDGET_SEC` (optional): wall-clock budget. Default `60`.

## Have fun

The point: a Russian chart-of-accounts lookup that's STRICTLY MORE USEFUL than
the JS reference — supporting sub-accounts, surface-level section filtering,
and per-section nature rollups. Worst case you revert.
