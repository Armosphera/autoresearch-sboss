# program.md — A1 model policy resolver research charter

You are an autonomous research agent. Your job: improve `workflow.py` so that the field-level
exact-match F1 score from `eval.py` goes up. You do not edit `eval.py`, `eval_set.json`, or
`pyproject.toml`. You only edit `workflow.py` and append to `results.tsv`.

## The task

The default `workflow.py` is a faithful Python port of
`src/model-policy.js::resolveModelForRequest()` from
[@a1/ai](https://github.com/Armosphera/A1-AI-Core) (the official SBOSS AI provider core).
The JS returns ONLY the resolved model id — no provenance. Your job is to make the Python
implementation **strictly more useful** by adding traceability and (later) richer
routing logic.

The current **baseline score is 50.00 / 100**. The `resolved_model` field matches the JS in
all 20 cases. The `source` field is missing everywhere (workflow.py returns `None` for
source — the JS doesn't compute it). The agent's first move: implement the `source` field
to track which precedence rule fired.

Your job is to make the score STRICTLY BETTER than the JS reference. Targets, in order:

1. **Add `source` tracking** (`"module"` | `"aspect"` | `"default"` | `"auto"`). This alone
   brings the baseline to 100.

2. **Add `chain` field** (optional): ordered list of all precedence rules considered with
   their outcomes. Useful for debugging "why did this model get picked?" in production.

3. **Cost-aware routing** (advanced): integrate OpenRouter's pricing data from
   `FALLBACK_MODELS` / live `model-catalog.js`. When multiple models could resolve, prefer
   the cheaper one if cost < some threshold; otherwise prefer the configured one. Add
   `cost_estimate_usd` to output.

4. **LLM-based scoring** (advanced): when `source` would be `"auto"` (nothing matched),
   call an LLM with the request context to pick the best model from the fallback list.
   Use `LLM_ENDPOINT_URL` / `LLM_API_KEY` / `LLM_MODEL` env vars. This converts autoresearch
   into a self-improving model router.

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

## What to try (in rough priority order)

1. **Source tracking.** Compute which rule fired. Don't change `resolve_model()` — just
   modify `run_workflow()` to also return the source. Should be ~10 lines.
2. **Defensive input handling.** Right now `resolve_model` defaults policy/ctx to `{}`. What
   if `policy` is `None`? What if `policy` is a string? Add explicit type checks.
3. **Chain output.** Add a third field `chain` that lists the full precedence resolution
   history. Update eval_set.json to test it (after the agent adds it to workflow.py).
4. **Cost field.** Pull pricing from a hardcoded model catalog (or read it from
   `FALLBACK_MODELS` if available). Return estimated USD cost for the resolved model.

## When to stop

- Score = 100 AND `source` field works AND chain output works → done with v0.1.
- 20 experiments with no improvement → consider rewriting `program.md`.
- Same file edited 5 times with no improvement → step back, re-read workflow.py.

## Logging format for results.tsv

Same as the top-level README. Tab-separated:
`timestamp\tcommit\tstatus\tscore\tbudget_sec\tdescription`

## Environment

This example uses NO LLM by default. It's a pure-function optimization. For the LLM-based
scoring target (item #4 above), set:

- `LLM_ENDPOINT_URL` — OpenAI-compatible chat completions endpoint
- `LLM_API_KEY` — bearer token
- `LLM_MODEL` — model name (default `mock-router-v1` — deterministic mock)

- `EXPERIMENT_BUDGET_SEC` (optional): wall-clock budget. Default `60`.

## Have fun

The point: a Python model policy resolver that's STRICTLY BETTER than the JS reference,
with full traceability and (optionally) cost-aware / LLM-aware routing. Worst case you revert.
