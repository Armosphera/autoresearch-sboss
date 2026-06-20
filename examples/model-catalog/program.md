# program.md — OpenRouter model catalog research charter

You are an autonomous research agent. Your job: improve `workflow.py` so that the field-level
exact-match F1 score from `eval.py` goes up. You do not edit `eval.py`, `eval_set.json`, or
`pyproject.toml`. You only edit `workflow.py` and append to `results.tsv`.

## The task

The default `workflow.py` is a faithful Python port of
`src/model-catalog.js` from
[samstep74/A1-AI-Core](https://github.com/samstep74/A1-AI-Core).
Live OpenRouter model catalog. Framework-agnostic: the egress gate (`isEgressAllowed`),
the fetch implementation (`safeFetch`), and the OpenRouter endpoint/attribution
config are all INJECTED via `run_workflow` input.

`list_models()` returns `{ online, source: "live"|"fallback", reason?, models }`
and **NEVER throws** — when egress is blocked or the call fails it degrades to
the bundled `FALLBACK_MODELS` (5 entries: Claude 3.5 Sonnet, GPT-4o, GPT-4o mini,
Gemini Flash 1.5, Llama 3.1 70B) so the onboarding menu always renders.

The current **baseline score is 100.00 / 100** — the JS reference handles all
input shapes correctly. Your job is to make the Python implementation
**STRICTLY MORE USEFUL** than the JS reference by adding capabilities the JS lacks.

Your job, in priority order:

1. **Add `cached` field** to the result. After a successful live fetch, cache
   the response (with a TTL) so subsequent calls within the TTL return from
   cache without a network request.
2. **Add `stale_at` / `fetched_at` timestamps** so callers can show
   "last refreshed 5 min ago" in the UI.
3. **Add `filterByContext(minContext)`** — return only models with
   `contextLength >= minContext`. Useful for "I need a 1M context model" filter.
4. **Add `filterByModality(text|image|audio)`** — filter by supported input
   modalities (parse from `architecture.modality` in the OpenRouter response).
5. **Add `searchModels(query)`** — fuzzy search by name/id substring (case-
   insensitive). Returns matching models.

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

1. **`cached` + timestamps** — TTL-based cache for the live response.
2. **`filterByContext`** — min context length filter.
3. **`filterByModality`** — input modality filter.
4. **`searchModels`** — fuzzy name/id search.
5. **`compareModels(id1, id2)`** — side-by-side compare (context, pricing).

## When to stop

- Score = 100 AND `cached` works AND filtering works → done with v0.1.
- 20 experiments with no improvement → consider rewriting `program.md`.

## Logging format for results.tsv

Tab-separated:
`timestamp\tcommit\tstatus\tscore\tbudget_sec\tdescription`

## Environment

This example uses a **mock safeFetch** (no real OpenRouter call). The mock
is built inside `run_workflow()` from `safeFetchResponse` / `safeFetchStatus`
/ `safeFetchOk` / `safeFetchThrows` in each eval item.

- `EXPERIMENT_BUDGET_SEC` (optional): wall-clock budget. Default `60`.

## Have fun

The point: a Python OpenRouter catalog that's STRICTLY MORE USEFUL than the
JS reference — with caching, filtering, fuzzy search, and (optionally)
side-by-side compare. Worst case you revert.
