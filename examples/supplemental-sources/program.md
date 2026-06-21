# program.md — Supplemental sources policy research charter

You are an autonomous research agent. Your job: improve `workflow.py` so that the field-level
exact-match F1 score from `eval.py` goes up. You do not edit `eval.py`, `eval_set.json`, or
`pyproject.toml`. You only edit `workflow.py` and append to `results.tsv`.

## The task

The default `workflow.py` is a faithful Python port of
`src/supplemental.js` from
[Armosphera/A1-AI-Core](https://github.com/Armosphera/A1-AI-Core).
Advisory-only "supplemental sources" policy — e.g. Open Notebook hits shown
BESIDE a product's authoritative citations. Pure (no I/O).

The cap / dedupe key / ordering / excerpt length are the product-tunable knobs.
**Supplemental sources are advisory** — a consuming product MUST keep them out
of any authoritative-citation gate (they never satisfy a required citation).

The current **baseline score is 100.00 / 100** — the JS reference handles all
input shapes correctly. Your job is to make the Python implementation
**STRICTLY MORE USEFUL** than the JS reference by adding capabilities the JS lacks.

Your job, in priority order:

1. **Add `snippet` field with sentence-boundary truncation.** Currently excerpts
   are sliced at exactly 280 chars; add a variant that truncates at the nearest
   sentence boundary (`.` `!` `?`) within 280 chars.
2. **Add `origin_tag` field.** Currently `origin` is hardcoded to "open-notebook";
   allow callers to override (e.g. "arxiv", "wikipedia", "internal-kb").
3. **Add `groupedByOrigin` rollup.** Group results by origin, with per-group
   count + top-scored excerpt.
4. **Add `isAdvisory` predicate.** A function `(row) => bool` to check whether
   a row should be treated as advisory (instead of authoritative).
5. **Add `redactPII` option.** Strip emails/phone numbers from excerpts
   (e.g. `john@example.com` → `[email]`).

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

1. **`snippet` (sentence-boundary)** — friendlier truncation.
2. **`origin_tag`** — caller-overridable origin.
3. **`groupedByOrigin` rollup** — per-origin summary.
4. **`isAdvisory` predicate** — first-class advisory check.
5. **`redactPII`** — privacy-safe excerpts.

## When to stop

- Score = 100 AND `snippet` (sentence-boundary) + `origin_tag` work → done with v0.1.
- 20 experiments with no improvement → consider rewriting `program.md`.

## Logging format for results.tsv

Tab-separated:
`timestamp\tcommit\tstatus\tscore\tbudget_sec\tdescription`

## Environment

This example uses NO LLM. Pure function.

- `EXPERIMENT_BUDGET_SEC` (optional): wall-clock budget. Default `60`.

## Have fun

The point: a Python supplemental-sources policy that's STRICTLY MORE USEFUL
than the JS reference — with sentence-boundary truncation, custom origin
tags, per-origin rollups, and (optionally) PII redaction. Worst case you
revert.
