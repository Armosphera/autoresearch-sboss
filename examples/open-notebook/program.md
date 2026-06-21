# program.md — Open Notebook connector research charter

You are an autonomous research agent. Your job: improve `workflow.py` so that the field-level
exact-match F1 score from `eval.py` goes up. You do not edit `eval.py`, `eval_set.json`, or
`pyproject.toml`. You only edit `workflow.py` and append to `results.tsv`.

## The task

The default `workflow.py` is a faithful Python port of
`src/open-notebook.js` from
[Armosphera/A1-AI-Core](https://github.com/Armosphera/A1-AI-Core).
Open Notebook (lfnovo/open-notebook) — opt-in AI source that sits BESIDE a
product's local RAG. We connect to a self-hosted instance over its REST API;
we never bundle its Python/SurrealDB runtime.

Framework-agnostic: the egress-gated fetch is INJECTED. The connector is:
- opt-in — only runs when `settings.openNotebook.enabled + baseUrl` are set
- egress-gated — calls go through the injected safeFetch
- non-throwing — any failure returns `[]` so the host retrieval flow is never broken

Returned rows match the common RAG result shape so callers can merge sources.

The current **baseline score is 100.00 / 100** — the JS reference handles all
shapes correctly. Your job is to make the Python implementation **STRICTLY
MORE USEFUL** than the JS reference by adding capabilities the JS lacks.

Your job, in priority order:

1. **Add `summary` field per result.** One-line human-readable summary
   (e.g. `"Open Notebook: 3 results (top: 'Doc A' score 0.92)"`).
2. **Add `cache` layer** with TTL — avoid repeated network calls for the same
   query within a configurable TTL window.
3. **Add `mergeWithLocalRAG`** — combine open-notebook results with a local
   RAG result list, deduped by sourceUrl, sorted by score.
4. **Add `searchWithRetry`** — exponential backoff for transient HTTP errors
   (429, 502, 503, 504) with idempotency-key header.
5. **Add `groupByNotebook`** — group results by their source notebook (parse
   from the title prefix or a `notebook` field).

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

1. **`summary` field** — per-result short string.
2. **`cache` with TTL** — per-query caching.
3. **`mergeWithLocalRAG`** — combined retrieval.
4. **`searchWithRetry`** — exponential backoff.
5. **`groupByNotebook`** — source-notebook grouping.

## When to stop

- Score = 100 AND `summary` works AND caching works → done with v0.1.
- 20 experiments with no improvement → consider rewriting `program.md`.

## Logging format for results.tsv

Tab-separated:
`timestamp\tcommit\tstatus\tscore\tbudget_sec\tdescription`

## Environment

This example uses a **mock safeFetch** (no real Open Notebook call). The mock
is built inside `run_workflow()` from `safeFetchResponse` / `safeFetchStatus`
/ `safeFetchOk` / `safeFetchThrows` in each eval item.

- `EXPERIMENT_BUDGET_SEC` (optional): wall-clock budget. Default `60`.

## Have fun

The point: a Python Open Notebook connector that's STRICTLY MORE USEFUL than
the JS reference — with summaries, caching, RAG-merge, and (optionally)
retry-with-backoff. Worst case you revert.
