# program.md — Armenian regions lookup research charter

You are an autonomous research agent. Your job: improve `workflow.py` so that the field-level
exact-match F1 score from `eval.py` goes up. You do not edit `eval.py`, `eval_set.json`, or
`pyproject.toml`. You only edit `workflow.py` and append to `results.tsv`.

## The task

The default `workflow.py` is a faithful Python port of `src/armeniaRegions.js` from
[A1-Localization-AM](https://github.com/Armosphera/A1-Localization-AM). It looks up
Armenian administrative regions (marzes) by ISO 3166-2:AM code, Armenian name, or
English name — case-insensitive, whitespace-trimmed. Armenia has 11 divisions: 10
provinces plus the capital Yerevan.

The current **baseline score is 100.00 / 100**. The JS reference handles all the input
shapes correctly — no bugs to fix. Your job is to make the Python implementation
**STRICTLY MORE USEFUL** than the JS reference by adding capabilities the JS lacks.

Your job, in priority order:

1. **City-to-region reverse lookup.** Add `find_region_by_city(city_name)` that returns
   the region whose `cities[]` list contains the given city. Useful for
   "what marz is Gyumri in?" The JS doesn't have this — it only has
   `citiesForRegion(code)`.

2. **Fuzzy name matching.** Currently `find_region` requires exact (case-insensitive)
   match. Add fuzzy match: handle missing diacritics, common transliteration variants
   (e.g., "Yerevan" / "Erewan", "Vanadzor" / "Vanadzor"). Return null if no good match.

3. **Distance to Yerevan.** Add `distance_from_yerevan(region_code)` returning approximate
   km (useful for shipping/logistics calculations). Could be a hardcoded table or use
   great-circle formula with region centroid coordinates.

4. **Adjacency lookup.** Add `adjacent_regions(region_code)` returning the list of
   neighboring marzes by their codes. Useful for "find regions bordering this one".

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

1. **City-to-region.** Add `find_region_by_city(city)` that returns the region whose
   `cities[]` contains the city.
2. **Fuzzy name match.** Handle "Yerevan" vs "Erewan" (transliteration variants).
3. **Distance to Yerevan.** Hardcoded table for now: Yerevan=0, Aragatsotn=50, Ararat=40, etc.
4. **Adjacency lookup.** Hardcoded: Aragatsotn↔Ararat↔Armavir↔Kotayk↔Lori↔Shirak↔Tavush↔Gegharkunik↔Vayots Dzor↔Syunik.

## When to stop

- Score = 100 AND find_region_by_city works → done with v0.1.
- 20 experiments with no improvement → consider rewriting `program.md`.

## Logging format for results.tsv

Tab-separated:
`timestamp\tcommit\tstatus\tscore\tbudget_sec\tdescription`

## Environment

This example uses NO LLM. Pure-function lookup.

- `EXPERIMENT_BUDGET_SEC` (optional): wall-clock budget. Default `60`.

## Have fun

The point: a Python regions lookup that's STRICTLY MORE USEFUL than the JS reference —
with reverse lookups (city → region), fuzzy matching, and (optionally) distance /
adjacency data. Worst case you revert.
