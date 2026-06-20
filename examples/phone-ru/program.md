# program.md — Russian phone normalization research charter

You are an autonomous research agent. Your job: improve `workflow.py` so that the field-level
exact-match F1 score from `eval.py` goes up. You do not edit `eval.py`, `eval_set.json`, or
`pyproject.toml`. You only edit `workflow.py` and append to `results.tsv`.

## The task

The default `workflow.py` is a faithful Python port of
`src/phone.js` from
[Armosphera/A1-Localization-RU](https://github.com/Armosphera/A1-Localization-RU).
Russian phone normalization + validation + E.164 + display formatting. Country
code +7, 10-digit NSN, validates the stable invariant (3-9 first digit:
3-8 geographic, 9 mobile) rather than hard-coding operator prefixes.

The current **baseline score is 100.00 / 100**. The JS reference handles all
valid inputs correctly — no bugs to fix. Your job is to make the Python
implementation **STRICTLY MORE USEFUL** than the JS reference by adding
capabilities the JS lacks.

Your job, in priority order:

1. **Add operator/mobile detection.** Return `mobile: bool` based on whether the
   3-digit DEF code starts with 9 (the mobile range). Currently this is implicit;
   expose it explicitly so the UI can show a 📱 icon.
2. **Add `region` (area code) extraction.** Return `area: str` (3 digits) for
   the city/region. Even when the full phone is invalid (nzn=""), if the area
   prefix is one of the known codes, return a useful diagnostic.
3. **Add `toll_free` detection.** 8-800-XX-XX-XX is the toll-free range in
   Russia. Return `toll_free: bool`.
4. **Add `is_short` support.** 4-digit internal extensions (e.g., 1234) for
   enterprise PBX — return `{"nsn": "", "kind": "short", "ext": "1234"}` when
   input is 3-6 digits.

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

1. **`mobile` field** — boolean from 9XX prefix.
2. **`area` field** — 3-digit area code extracted.
3. **`toll_free` field** — 8-800 prefix detection.
4. **`kind` discriminator** — "full" | "short" | "invalid".

## When to stop

- Score = 100 AND `mobile`/`area`/`toll_free`/`kind` all work → done with v0.1.
- 20 experiments with no improvement → consider rewriting `program.md`.

## Logging format for results.tsv

Tab-separated:
`timestamp\tcommit\tstatus\tscore\tbudget_sec\tdescription`

## Environment

This example uses NO LLM. Pure-function normalization.

- `EXPERIMENT_BUDGET_SEC` (optional): wall-clock budget. Default `60`.

## Have fun

The point: a Russian phone normalizer that's STRICTLY MORE USEFUL than the JS
reference — exposing the structural facts (mobile vs geographic, area, toll-free,
short extension) that the JS hides inside the 10-digit NSN. Worst case you revert.
