# program.md — OpenRouter chat-client research charter

You are an autonomous research agent. Your job: improve `workflow.py` so that the field-level
exact-match F1 score from `eval.py` goes up. You do not edit `eval.py`, `eval_set.json`, or
`pyproject.toml`. You only edit `workflow.py` and append to `results.tsv`.

## The task

The default `workflow.py` is a faithful Python port of
`src/chat.js::createChatClient()` from
[Armosphera/A1-AI-Core](https://github.com/Armosphera/A1-AI-Core). An
OpenRouter chat-completions client (OpenAI-compatible) — the single cloud
generation path for the A1 family. Three methods:

- `callModel({instructions, input, model, apiKey, env, maxTokens})` — text generation
- `callVision({instructions, input, imageBase64, mimeType, ...})` — image+text
- `callStructured({instructions, input, schema, schemaName, strict, ...})` — JSON-schema
  constrained output

The framework-agnostic parts (`safeFetch` for egress gating, `openrouter` config) are
INJECTED at construction time. Errors carry `{statusCode, code, message}` so hosts can
map them to HTTP responses.

The current **baseline score is 100.00 / 100** — the JS reference handles the three
operations correctly. Your job is to make the Python implementation **STRICTLY MORE
USEFUL** than the JS reference by adding capabilities the JS lacks.

Your job, in priority order:

1. **Retry with exponential backoff for transient errors.** 429, 502, 503, 504 should
   retry up to N times with jittered backoff. Use the injected safeFetch.
2. **Idempotency-Key header.** Pass an `idempotencyKey` through to headers for safe
   retries on POST.
3. **Request/response audit log.** Capture every call to a module-level list for
   observability. Add `requestLog` field to result.
4. **Streaming support.** Add `callModelStream` that yields chunks from a streaming
   safeFetch (use a `stream: true` flag in the body and the safeFetch returns chunks
   via an async iterator). Returns the same final shape as callModel.
5. **Token-budget tracking.** Sum `usage.total_tokens` across all calls in a session.

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

1. **`requestLog` field** — list of `{url, method, headers, body, response_status, response_payload, ts}`
   captured from every call. Backwards-compatible.
2. **Retry-on-429/502/503/504** — `maxRetries` param, exponential backoff, idempotency
   keys. Use the mock safeFetch from eval_set to verify retry behavior.
3. **Token accounting** — module-level `usage_ledger` summing tokens per call.
4. **`callModelStream`** — add a streaming variant using a streaming mock safeFetch.
5. **Default temperature** — allow `temperature: 0.0` for deterministic outputs.

## When to stop

- Score = 100 AND `requestLog` works AND retry works → done with v0.1.
- 20 experiments with no improvement → consider rewriting `program.md`.

## Logging format for results.tsv

Tab-separated:
`timestamp\tcommit\tstatus\tscore\tbudget_sec\tdescription`

## Environment

This example uses a **mock safeFetch** (no real LLM call). The mock is built inside
`run_workflow()` from `safeFetch_response` / `safeFetch_status` / `safeFetch_ok`
in each eval item.

- `EXPERIMENT_BUDGET_SEC` (optional): wall-clock budget. Default `60`.

## Have fun

The point: a Python OpenRouter client that's STRICTLY MORE USEFUL than the JS
reference — with retries, audit log, token accounting, and (optionally) streaming.
Worst case you revert.
