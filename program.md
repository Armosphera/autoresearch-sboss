# program.md — autonomous research charter for autoresearch-sboss

You are an autonomous research agent. Your job: tune the SBOSS workflow in `workflow.py` so that
the business score from `eval.py` improves. You do not edit `eval.py`, `eval_set.json`, or
`pyproject.toml`. You only edit `workflow.py` and append to `results.tsv`.

## The task

Optimize the SBOSS invoice-field-extraction workflow. Given noisy invoice text, extract
`vendor_name`, `invoice_date`, `total_amount`, `currency`, and `tax_id` as structured JSON.

The current workflow (`workflow.py`) defines:
- `WORKFLOW_CONFIG` — prompt template + LLM parameters (the agent can tune these)
- `run_workflow(input, config)` — the actual extraction logic (the agent can rewrite this body)

The metric (printed by `eval.py`) is **field-level exact-match F1**, scaled 0–100. Higher is better.

## The loop

```
1. Read results.tsv — find the current best score.
2. Read workflow.py — understand the current state.
3. Make ONE focused change to workflow.py (a hypothesis).
4. Run: uv run eval.py
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
- **Read first, edit second.** Always re-read workflow.py before editing — context may have shifted.
- **Keep it boring.** Small, reversible changes. No sweeping rewrites.
- **Respect the time budget.** Default 60s per experiment (env `EXPERIMENT_BUDGET_SEC`).
  If eval.py runs over budget, the score is invalid — revert.
- **Don't touch the eval set.** `eval_set.json` is the ground truth. Editing it is cheating.
- **Don't touch the score function.** `eval.py` is the judge. Editing it is cheating.
- **Log everything.** Every experiment, keep or revert, goes in `results.tsv`.

## What to try (in rough priority order)

1. **Prompt template wording.** The default template is verbose. Tighten it. Remove contradictions.
2. **Few-shot examples.** Add 1-3 worked examples to `WORKFLOW_CONFIG["examples"]`. Quality > quantity.
3. **Output format hints.** Explicitly request JSON. Specify the schema. Mention "no prose".
4. **Field ordering.** Reorder the schema fields. Sometimes extraction accuracy depends on order.
5. **LLM parameters.** Lower temperature for deterministic extraction. Bump `max_tokens` if truncating.
6. **run_workflow() body.** Swap the mock LLM for a real call. Pre-process the document text.
   Post-process the LLM output. Add retries. Anything is fair game — this is the agent's lever.
7. **Caching.** Hash `(prompt, document)` to skip repeat calls during eval.

## When to stop

- Score plateau: 20 experiments in a row without a keep → consider rewriting `program.md`.
- Perfect score: 100.0 → declare victory, write a one-paragraph summary in `results.tsv` end.
- Stuck: same file edited 5 times with no improvement → step back, re-read `workflow.py`, try a
  different lever.

## Logging format for results.tsv

```
timestamp	commit	status	score	budget_sec	description
2026-06-20T12:34:56Z	abc1234	keep	82.50	58.2	tightened system prompt
2026-06-20T12:36:01Z	-	revert	-	59.4	added 2 few-shot examples (no help)
```

Commit hash on revert is `-`. Description is one short line — what you changed and why.

## Environment

- `LLM_ENDPOINT_URL` (optional): OpenAI-compatible chat completions endpoint.
- `LLM_API_KEY` (optional): bearer token for the endpoint.
- `LLM_MODEL` (optional): model name. Default `mock-extractor-v1` (deterministic, no API).
- `EXPERIMENT_BUDGET_SEC` (optional): wall-clock budget. Default `60`.

If `LLM_ENDPOINT_URL` is unset, the harness uses a deterministic mock extractor that uses regex
against the document. This is fine for proving the loop works; for real research, set the env vars.

## Have fun

The whole point of this is that you wake up tomorrow to a log of experiments and (hopefully)
a better workflow than you had yesterday. Don't ask me — try things. Worst case you revert.
