# program.md — Product research primitives research charter

You are an autonomous research agent. Your job: improve `workflow.py` so that the field-level
exact-match F1 score from `eval.py` goes up. You do not edit `eval.py`, `eval_set.json`, or
`pyproject.toml`. You only edit `workflow.py` and append to `results.tsv`.

## The task

The default `workflow.py` is a faithful Python port of
`src/product-research.js` from
[samstep74/A1-AI-Core](https://github.com/samstep74/A1-AI-Core).
**Karpathy-style product research primitives for A1 products.**

Pure helpers (no I/O, no shells, no model calls). Hosts use these to render a
narrow agent program, compare fixed-budget eval results, and record experiment
rows in a stable TSV format.

Public surface (8 ops):
- `normalizeProductResearchConfig` — validate + normalize product config
- `renderProductResearchProgram` — render the markdown program the agent follows
- `decideExperimentStatus` — keep / discard / crash based on metric + complexity
- `metricDelta` — direction-aware metric delta
- `extractMetricFromText` — regex parse metric from eval output
- `formatExperimentHeader` / `formatExperimentResult` / `parseExperimentTsv` — TSV I/O

The current **baseline score is 100.00 / 100** — the JS reference handles all
shapes correctly. Your job is to make the Python implementation **STRICTLY
MORE USEFUL** than the JS reference by adding capabilities the JS lacks.

Your job, in priority order:

1. **Add `validateConfig` method.** Return `{ok, errors: [{path, code, message}]}` for
   the config (instead of raising TypeError). Friendlier for UIs.
2. **Add `experimentSummary`** — given a list of TSV rows, return rollup: `{total,
   kept, discarded, crashed, bestMetric, worstMetric, meanDelta}`.
3. **Add `progressVsBudget`** — given rows + timeBudgetMinutes, return how much
   of the budget has been consumed by the kept experiments.
4. **Add `detectRegression`** — given current and last-kept metric, return
   whether the new one is a regression and by how much.
5. **Add `renderProgramAsYaml`** — YAML version of the program for tools that
   prefer structured config over markdown.

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

1. **`validateConfig`** — return errors instead of raising.
2. **`experimentSummary`** — TSV rollup.
3. **`progressVsBudget`** — budget consumption.
4. **`detectRegression`** — single-call regression check.
5. **`renderProgramAsYaml`** — alternate output format.

## When to stop

- Score = 100 AND `validateConfig` works AND `experimentSummary` works → done with v0.1.
- 20 experiments with no improvement → consider rewriting `program.md`.

## Logging format for results.tsv

Tab-separated:
`timestamp\tcommit\tstatus\tscore\tbudget_sec\tdescription`

## Environment

This example uses NO LLM. Pure function.

- `EXPERIMENT_BUDGET_SEC` (optional): wall-clock budget. Default `60`.

## Have fun

The point: a Python product-research primitives module that's STRICTLY MORE
USEFUL than the JS reference — with friendly validation, experiment rollups,
budget tracking, and (optionally) YAML output. Worst case you revert.
