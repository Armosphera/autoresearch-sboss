# program.md — HHVH (Armenian taxpayer id) validation research charter

You are an autonomous research agent. Your job: improve `workflow.py` so that the field-level
exact-match F1 score from `eval.py` goes up. You do not edit `eval.py`, `eval_set.json`, or
`pyproject.toml`. You only edit `workflow.py` and append to `results.tsv`.

## The task

The default `workflow.py` is a faithful Python port of `src/localization.js::validateHvhh()`
from [A1-Localization-AM](https://github.com/Armosphera/A1-Localization-AM). The current
**baseline score is 96.67 / 100** — see `results.tsv`. The single failing case is input
`"00123-456"` (7 digits typed with a hyphen separator). The JS reference silently inflates
this to `"00123456"` and accepts it as a valid HHVH. The eval set expects rejection, treating
this as a UX bug (a user typing a separator probably mistyped the length, not the format).

Your job is to make the score **STRICTLY BETTER than the JS reference**. Targets, in order:

1. **Fix the pre-normalization length check.** Detect when the raw input (before stripping
   separators) has the wrong digit count, even if the normalized form has 8 digits. This
   alone brings the baseline to 100. Commit and continue.

2. **Implement the official Armenian HHVH check-digit algorithm** in `_default_check_digit()`.
   The JS has this as a TODO seam: `// The official check-digit algorithm is not publicly
   published`. Research it (Armenian State Revenue Committee / ՀՀ ՊԵԿ). When you have the
   algorithm, wire it in. Generate a small test set of REAL HHVH numbers (any Armenian
   company's tax id, e.g. from public e-invoices on `e-invoicing.taxservice.am` or
   `https://www.petekamutner.am/`) and add them to `eval_set.json` as new ground-truth
   check-digit cases.

3. **Harden input normalization.** Currently we strip ASCII whitespace, dot, hyphen. What
   about Unicode whitespace (NBSP, Armenian space U+0531)? Latin digit look-alikes? Add cases.

4. **Handle the `value is a number` case.** Right now we coerce via `str()`. What if `value`
   is `12345678` (int)? What about `12345678.0` (float with trailing zero)?

## The loop

```
1. Read results.tsv — find the current best score.
2. Read workflow.py — understand the current state.
3. Make ONE focused change to workflow.py (a hypothesis).
4. Run: uv run eval.py
5. Read the new score from stdout.
6. If new_score > best_score:
       git add workflow.py eval_set.json && git commit -m "score: N.NNN — <one-line hypothesis>"
   Else:
       git checkout workflow.py eval_set.json
7. Append the experiment to results.tsv.
8. Repeat.
```

You MAY modify `eval_set.json` ONLY to add new ground-truth check-digit cases that prove your
implementation is correct. Do not delete or weaken existing cases. Adding cases that the JS would
fail but your workflow.py passes is the whole point — that's what "strictly better" means.

## Rules of engagement

- **One hypothesis per experiment.** Don't bundle 5 unrelated changes into one commit.
- **Read first, edit second.** Always re-read workflow.py before editing.
- **Keep it boring.** Small, reversible changes. No sweeping rewrites.
- **Respect the time budget.** Default 60s per experiment. If eval.py runs over budget, revert.
- **Don't touch the score function.** `eval.py` is the judge. Editing it is cheating.
- **Log everything.** Every experiment, keep or revert, goes in `results.tsv`.

## What to try (in rough priority order)

1. **Research the official check-digit algorithm.** Start with the Armenian State Revenue
   Committee website, e-invoice specs, and any open implementations on GitHub. Implement it
   in `_default_check_digit()`. Add real-world HHVH examples to `eval_set.json`.
2. **Unicode whitespace + Latin look-alikes.** Strip NBSP (U+00A0), figure space (U+2007),
   narrow no-break space (U+202F), and zero-width space (U+200B). Reject Latin digit
   look-alikes (e.g., superscript digits).
3. **Numeric coercion.** Handle `value=12345678` (int), `value=12345678.0` (float with trailing
   zero), `value=12_345_678` (Python int with underscore).
4. **Better error reporting.** Add `error_code` field (machine-readable) alongside `error`
   (human-readable). Don't break the existing string — just add the field.

## When to stop

- Score = 100 AND you've implemented and validated the official check-digit algorithm → done.
- 20 experiments with no improvement → consider rewriting `program.md`.
- Same file edited 5 times with no improvement → step back, re-read workflow.py.

## Logging format for results.tsv

Same as the top-level README. Tab-separated:
`timestamp\tcommit\tstatus\tscore\tbudget_sec\tdescription`

## Environment

This example uses NO LLM. It's a pure-function optimization. No `LLM_*` env vars needed.

- `EXPERIMENT_BUDGET_SEC` (optional): wall-clock budget. Default `60`.

## Have fun

The point is that tomorrow morning you wake up to a Python validator that's STRICTLY BETTER
than the JS reference — including the check-digit algorithm the JS author left as a TODO.
Worst case you revert.
