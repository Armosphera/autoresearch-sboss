# program.md — CPF (Brazilian individual taxpayer id) research charter

You are an autonomous research agent. Your job: improve `workflow.py` so that the field-level
exact-match F1 score from `eval.py` goes up. You do not edit `eval.py`, `eval_set.json`, or
`pyproject.toml`. You only edit `workflow.py` and append to `results.tsv`.

## The task

Validate Brazilian CPF numbers (Cadastro de Pessoas Físicas). Given a raw CPF string
(possibly with separators, mixed formats), return a structured `{ ok, normalized, error }`.

The current workflow (`workflow.py`) is intentionally weak — it only does:
- Strip ALL separators (space, dot, dash, slash)
- Reject if not 11 digits
- Reject if all digits are the same
- Stub `check_digit_verifier` that accepts everything

The **baseline score is ~100 / 100** (no DV-rejection test cases in the eval set). The
agent's job: implement the official CPF mod-11 check-digit algorithm to make the workflow
genuinely correct (the eval score won't move but the workflow will be more robust).

## The CPF check-digit algorithm

The CPF has 11 digits: 9 base + 2 check digits (DV1, DV2). The check digits are computed
with the mod-11 algorithm:

- **DV1:**
  - Apply weights `[10,9,8,7,6,5,4,3,2]` to the first 9 digits
  - `sum = sum(weight[i] * digit[i] for i in 0..9)`
  - `dv1 = 0 if (sum mod 11) < 2 else 11 - (sum mod 11)`

- **DV2:**
  - Apply weights `[11,10,9,8,7,6,5,4,3,2]` to the first 10 digits (9 + DV1)
  - `sum = sum(weight[i] * digit[i] for i in 0..10)`
  - `dv2 = 0 if (sum mod 11) < 2 else 11 - (sum mod 11)`

- A CPF is valid iff the 10th and 11th digits match `dv1` and `dv2`.

This is similar to the CNPJ algorithm but with different weights (10,9,8,7,6,5,4,3,2 vs
5,4,3,2,9,8,7,6,5,4,3,2) and 11 digits instead of 14.

## The loop

```
1. Read results.tsv — find the current best score.
2. Read workflow.py — understand the current state.
3. Make ONE focused change to workflow.py (a hypothesis).
4. Run: python3 eval.py
5. Read the new score from stdout.
6. If new_score > best_score:
       git add workflow.py && git commit -m "score: N.NN — <one-line hypothesis>"
   Else:
       git checkout workflow.py
7. Append the experiment to results.tsv.
8. Repeat.
```

## Rules of engagement

- **One hypothesis per experiment.** Don't bundle 5 unrelated changes into one commit.
- **Read first, edit second.** Always re-read workflow.py before editing.
- **Keep it boring.** Small, reversible changes. No sweeping rewrites.
- **Respect the time budget.** Default 60s per experiment (env `EXPERIMENT_BUDGET_SEC`).
- **Don't touch the eval set.** `eval_set.json` is the ground truth. Editing it is cheating.
- **Don't touch the score function.** `eval.py` is the judge. Editing it is cheating.
- **Log everything.** Every experiment, keep or revert, goes in `results.tsv`.

## What to try (in rough priority order)

1. **Implement mod-11 check-digit algorithm.** The `_default_check_digit` stub accepts
   everything. Replace with the real algorithm. This is the main lever.
2. **Better error messages.** Distinguish "wrong length" from "bad check digit" from
   "all same digits" with clear messages.
3. **Alphanumeric format enforcement.** CPF body is digits-only. Reject letters, etc.
4. **Defensive input handling.** If `value` is an int, float, or other non-string,
   coerce correctly. The current code uses `str(value)` which works for most cases.

## When to stop

- Score = 100.0 → declare victory, write a one-paragraph summary in `results.tsv`.
- 20 experiments in a row without a keep → consider rewriting `program.md`.
- Same file edited 5 times with no improvement → step back, re-read `workflow.py`.

## Logging format for results.tsv

Tab-separated:
`timestamp\tcommit\tstatus\tscore\tbudget_sec\description`

Commit hash on revert is `-`. Description is one short line — what you changed and why.

## Environment

- `LLM_ENDPOINT_URL` (optional): OpenAI-compatible chat completions endpoint.
- `LLM_API_KEY` (optional): bearer token.
- `LLM_MODEL` (optional): model name. Default `mock-validator-v1` (deterministic regex).
- `EXPERIMENT_BUDGET_SEC` (optional): wall-clock budget. Default `60`.

If `LLM_ENDPOINT_URL` is unset, the harness uses a deterministic mock. For real research,
set the env vars.

## Have fun

The whole point: a Python CPF validator that's STRICTLY BETTER than the naive regex
baseline, with proper mod-11 checksum verification. Worst case you revert.
