# program.md — Russian identifier validator research charter

You are an autonomous research agent. Your job: improve `workflow.py` so that the field-level
exact-match F1 score from `eval.py` goes up. You do not edit `eval.py`, `eval_set.json`, or
`pyproject.toml`. You only edit `workflow.py` and append to `results.tsv`.

## The task

The default `workflow.py` is a faithful Python port of `src/inn.js` from
[A1-Localization-RU](https://github.com/Armosphera/A1-Localization-RU). It validates five
Russian business identifier types:

- **ИНН** (10 digits = legal entity, 12 digits = individual) — weighted sum, mod 11, mod 10
- **КПП** (9 chars, regex only) — 4 digits + 2 [0-9A-Z] + 3 digits
- **ОГРН** (13 digits) — Horner mod 11
- **ОГРНИП** (15 digits) — Horner mod 13
- **СНИЛС** (11 digits) — weighted sum, mod 101

The current **baseline score is 85.00 / 100**. Three failing cases (`#7`, `#18`, `#19`) are
identifiers with whitespace or hyphen separators (`"112-233-445 95"`, `"7707-0838-93"`,
`"10277-0013-2195"`) that the JS reference's dispatcher rejects because separator stripping
is only applied inside `_validate_snils` — not in the dispatcher or other validators.

Your job is to make the score **STRICTLY BETTER than the JS reference**. Targets, in order:

1. **Add separator stripping in the dispatcher** (matching the SNILS-level handling).
   Strip `\s` and `-` BEFORE shape detection so `"7707-0838-93"` becomes `"7707083893"` and
   routes to INN validation. This alone brings the baseline to 100.

2. **Harden the dispatcher.** Right now we dispatch by length and content. Edge cases to
   handle: a 9-digit string that's NOT КПП-shaped (e.g., `"123456789"`), a 10-character
   string with letters (e.g., `"770708389A"`), input that's `None` or `12345` (int).

3. **Improve error messages.** The current "unknown identifier shape" message leaks the
   length and has_letters boolean. Make it more descriptive for users.

4. **Add more identifier types** (optional). After hitting 100, you could add:
   - ОГРНИП variant for individual entrepreneurs (already there)
   - КПП with leading zeros (rare but valid)
   - ИНН for foreign organizations (10 digits, special range)

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

1. **Separator stripping.** Apply `.replace(r"[\s-]", "")` to INN, OGRN, OGRNIP, and KPP
   validation, matching the SNILS pattern. Confirm cases #18 and #19 pass.
2. **Better "unknown shape" error.** Add specific errors for each length mismatch instead of
   the catch-all. E.g., "ИНН should be 10 or 12 digits, got 9" vs "ОГРН should be 13 digits, got 9".
3. **Numeric input handling.** `validate_identifier(12345678)` should work — currently relies
   on `str()` coercion, which produces `"12345678"`. Add explicit int/float handling.
4. **Whitespace around КПП reason code.** `"7707 AB001"` (space in middle) — reject or accept?
   Probably reject; the JS does.

## When to stop

- Score = 100 AND you've added separator stripping AND improved dispatcher edge cases → done.
- 20 experiments with no improvement → consider rewriting `program.md`.
- Same file edited 5 times with no improvement → step back, re-read workflow.py.

## Logging format for results.tsv

Same as the top-level README. Tab-separated:
`timestamp\tcommit\tstatus\tscore\tbudget_sec\tdescription`

## Environment

This example uses NO LLM. Pure-function optimization.

- `EXPERIMENT_BUDGET_SEC` (optional): wall-clock budget. Default `60`.

## Have fun

The point: a Python validator that's STRICTLY BETTER than the JS reference, with documented
edge-case coverage. Worst case you revert.
