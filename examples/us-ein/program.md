# program.md — US EIN (Employer Identification Number) research charter

You are an autonomous research agent. Your job: improve `workflow.py` so that the field-level
exact-match F1 score from `eval.py` goes up. You do not edit `eval.py`, `eval_set.json`, or
`pyproject.toml`. You only edit `workflow.py` and append to `results.tsv`.

## The task

Validate US Employer Identification Numbers (EINs). Given a raw EIN string (possibly with
separators), return a structured `{ ok, normalized, error }`.

The current workflow (`workflow.py`) is intentionally weak — it only does:
- Strip whitespace + hyphens
- Reject if not 9 digits
- Reject if all digits are the same
- Stub `campus_code_verifier` that accepts everything

The **baseline score is ~100 / 100** (no campus-code-rejection test cases in the eval set).
The agent's job: implement proper IRS campus code validation (the 2-digit prefix).

## The EIN format

- Total: 9 digits
- Format: XX-XXXXXXX (with hyphen) or XXXXXXXXX (no hyphen)
- Prefix (first 2 digits) is the IRS campus code that issued the EIN
- 7-digit serial number (0000001 - 9999999)
- No checksum

## Valid IRS campus codes

```
01, 02, 03, 04, 05, 06, 10, 11, 12, 13, 14, 15, 16,
20, 21, 22, 23, 24, 25, 26, 27,
30, 31, 32, 33, 34, 35, 36, 37, 38, 39,
40, 41, 42, 43, 44, 45, 46, 47, 48,
50, 51, 52, 53, 54, 55, 56, 57, 58, 59,
60, 61, 62, 63, 64, 65, 66, 67, 68,
71, 72, 73, 74, 75, 76, 77,
80, 81, 82, 83, 84, 85, 86, 87, 88,
90, 91, 92, 93, 94, 95, 98, 99
```

Unassigned codes (00, 07, 08, 09, 17, 18, 19, 28, 29, 49, 69, 70, 78, 79, 89, 96, 97) should be rejected.

Source: https://www.irs.gov/businesses/small-businesses-self-employed/how-eins-work

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

1. **Implement campus code validation.** The `_default_validate_campus_code` stub
   accepts everything. Replace with a check against `_VALID_CAMPUS_CODES`. The 9-digit
   format + the 2-digit prefix check.
2. **Better error messages.** Distinguish "wrong length" from "bad campus code" with
   clear messages.
3. **Defensive input handling.** Coerce int/float, etc.

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

The whole point: a Python US EIN validator that's STRICTLY BETTER than the naive regex
baseline, with proper IRS campus code validation. Worst case you revert.
