# program.md — Armenian phone number validation research charter

You are an autonomous research agent. Your job: improve `workflow.py` so that the field-level
exact-match F1 score from `eval.py` goes up. You do not edit `eval.py`, `eval_set.json`, or
`pyproject.toml`. You only edit `workflow.py` and append to `results.tsv`.

## The task

The default `workflow.py` is a faithful Python port of `src/armeniaPhone.js` from
[A1-Localization-AM](https://github.com/Armosphera/A1-Localization-AM). It normalizes
Armenian phone numbers from any input shape (`+374…`, `00374…`, domestic `0…`, bare, with
spaces/punctuation) down to the canonical 8-digit National Significant Number (NSN), then
formats as E.164 or human-readable.

The current **baseline score is 100.00 / 100**. The JS handles all the input shapes
correctly — no bugs to fix. Your job is to make the Python implementation **STRICTLY MORE
USEFUL** than the JS reference by adding capabilities the JS lacks.

Your job, in priority order:

1. **Operator-prefix detection.** The JS intentionally avoids hard-coding operator ranges
   (they change). But you can add an optional `operator` field that returns the likely
   operator name from a known-prefix map (e.g., `91`/`93`/`94` → VivaCell-MTS,
   `95`/`96`/`99` → Beeline, `41`–`49` → landline). Return `null` for unknown prefixes.
   This is OPTIONAL and must NOT change `valid` / `e164` / `formatted`.

2. **Validation warnings.** Detect `phone` strings that ALMOST match (7 or 9 digits
   without country prefix) and return a `warning` field like
   `"missing_country_code"` or `"extra_digit"`. Help users spot typos.

3. **Region detection.** Map the 2-digit area code to a region name (`10` → Yerevan,
   `11` → Lori, `31` → Shirak, etc.) using `armeniaRegions.js`. Add a `region` field.

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
- **Respect the time budget.** Default 60s per experiment.
- **Don't touch the score function.** `eval.py` is the judge.
- **Log everything.** Every experiment, keep or revert, goes in `results.tsv`.
- **Don't break existing tests.** Baseline 100.00 must stay 100.00 — additions must be
  new fields, not changes to existing field values.

## What to try (in rough priority order)

1. **Operator field.** Add `operator` field (string or None) based on 2-digit prefix.
2. **Warning field.** Add `warning` field for near-miss inputs (7 or 9 digits, no prefix).
3. **Region field.** Add `region` field (string or None) based on area code lookup.
4. **Better formatting.** Add `format_international()` that adds hyphens: `+374-91-234567`.

## When to stop

- Score = 100 AND operator/region fields work → done with v0.1.
- 20 experiments with no improvement → consider rewriting `program.md`.

## Logging format for results.tsv

Tab-separated:
`timestamp\tcommit\tstatus\tscore\tbudget_sec\tdescription`

## Environment

This example uses NO LLM. Pure-function regex normalization.

- `EXPERIMENT_BUDGET_SEC` (optional): wall-clock budget. Default `60`.

## Have fun

The point: a Python phone normalizer that's STRICTLY MORE USEFUL than the JS reference —
with operator detection, warnings, and (optionally) region lookup. Worst case you revert.
