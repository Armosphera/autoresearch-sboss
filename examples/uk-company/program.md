# program.md — UK Company Number (Companies House) research charter

You are an autonomous research agent. Your job: improve `workflow.py` so that the field-level
exact-match F1 score from `eval.py` goes up. You do not edit `eval.py`, `eval_set.json`, or
`pyproject.toml`. You only edit `workflow.py` and append to `results.tsv`.

## The task

Validate UK Company Numbers (Companies House). Given a raw company number string, return a
structured `{ ok, normalized, error }`.

The current workflow (`workflow.py`) handles 4 patterns (8 digits + SC/NI/OC + 6 digits).
The agent's job: extend to cover all 9 patterns, tighten validation, and improve error
messages.

## The patterns

UK Company Numbers are 8 uppercase characters. Valid patterns:
- 8 digits: "12345678"  (England & Wales limited company — most common)
- "SC" + 6 digits: "SC123456"  (Scottish limited company)
- "NI" + 6 digits: "NI123456"  (Northern Irish limited company)
- "OC" + 6 digits: "OC123456"  (Limited Liability Partnership)
- "SO" + 6 digits: "SO123456"  (Scottish LLP)
- "NC" + 6 digits: "NC123456"  (Northern Irish LLP)
- "FC" + 6 digits: "FC123456"  (overseas company)
- "SF" + 6 digits: "SF123456"  (Scottish further education)
- "NF" + 6 digits: "NF123456"  (Northern Irish further education)

No checksum. The validator checks the 8-char pattern + a prefix whitelist.

Source of truth: https://find-and-update.company-information.service.gov.uk/ (Companies House).

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

1. **Cover all 9 prefixes.** Add SO, NC, FC, SF, NF to `_VALID_PREFIXES`. The baseline
   rejects these; adding them brings the workflow closer to the full Companies House spec.
2. **Add valid-prefix test cases.** Wait — you can't add eval_set cases (rule). So this
   lever is "make the workflow more complete" without a way to verify the improvement.
3. **Better error messages.** Distinguish "wrong length" from "wrong prefix" with
   country-specific messages ("SC prefix means Scottish limited company").
4. **Defensive input handling.** Coerce int/float, etc.

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

The whole point: a Python UK Company Number validator that's STRICTLY BETTER than the
naive regex baseline, with full Companies House prefix coverage. Worst case you revert.
