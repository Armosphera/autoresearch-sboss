# program.md — Russian federal subjects research charter

You are an autonomous research agent. Your job: improve `workflow.py` so that the field-level
exact-match F1 score from `eval.py` goes up. You do not edit `eval.py`, `eval_set.json`, or
`pyproject.toml`. You only edit `workflow.py` and append to `results.tsv`.

## The task

The default `workflow.py` is a faithful Python port of
`src/regions.js` from
[Armosphera/A1-Localization-RU](https://github.com/Armosphera/A1-Localization-RU).
Russian federal subjects (субъекты Российской Федерации), keyed on the
ISO 3166-2:RU codes. **83 entries** loaded from `data.json`:
2 cities of federal significance (Москва, Санкт-Петербург), 21 republics,
9 krais, 46 oblasts, 1 autonomous oblast, 4 autonomous okrugs.

Uses the standard ISO 3166-2:RU set (and ONLY it) to avoid territorial-claim
ambiguity. Pure data + lookups, no I/O.

The current **baseline score is 100.00 / 100** — the JS reference handles all
valid queries correctly. Your job is to make the Python implementation
**STRICTLY MORE USEFUL** than the JS reference by adding capabilities the JS lacks.

Your job, in priority order:

1. **Add `type` discriminator.** Return `type: "город федерального значения" | "республика" | ...`
   so the UI can colour-code by subdivision kind.
2. **Add `cities` field.** Return the full list of cities for the region (currently
   the data is in `data.json` but `find_region()` doesn't surface it).
3. **Add `citiesForRegion()` exposed via run_workflow.** Currently only
   `find_region` is exposed; add a second operation to return just the cities list.
4. **Add federal-district grouping.** Group 83 subjects by federal district
   (8 districts: Central, Northwestern, Southern, North Caucasian, Volga, Ural,
   Siberian, Far Eastern). Useful for tax-rate lookup.
5. **Add `regionByFederalDistrict(district)` reverse lookup.** Returns the list
   of regions in a given federal district.

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

1. **`type` field** — subdivision kind discriminator.
2. **`cities` field** — return the list from data.json.
3. **`citiesForRegion()` via run_workflow** — second operation in the dispatcher.
4. **Federal-district grouping** — 8 districts, mapping from code to district.
5. **`regionByFederalDistrict(district)`** — reverse lookup.

## When to stop

- Score = 100 AND `type` + `cities` + federal-district grouping all work → done with v0.1.
- 20 experiments with no improvement → consider rewriting `program.md`.

## Logging format for results.tsv

Tab-separated:
`timestamp\tcommit\tstatus\tscore\tbudget_sec\tdescription`

## Environment

This example uses NO LLM. Pure-function lookup with data file.

- `EXPERIMENT_BUDGET_SEC` (optional): wall-clock budget. Default `60`.

## Have fun

The point: a Russian federal-subjects lookup that's STRICTLY MORE USEFUL than
the JS reference — exposing type, cities, and federal-district grouping that
the JS hides inside the frozen REGIONS data. Worst case you revert.
