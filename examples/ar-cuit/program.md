# program.md — Argentina CUIT/CUIL research charter

You are an autonomous research agent. Your job: improve `workflow.py` so the field-level
exact-match F1 score from `eval.py` goes up. You do not edit `eval.py`, `eval_set.json`, or
`pyproject.toml`. You only edit `workflow.py` and append to `results.tsv`.

## The task

Validate Argentina CUIT/CUIL numbers (tax id / labor id). Given a raw 11-digit string
(possibly with separators), return a structured `{ ok, normalized, error }`.

## Source of truth

- **AFIP spec**: https://www.afip.gob.ar/ (tax authority for legal entities)
- **ANSES spec**: https://www.anses.gob.ar/ (labor authority for individuals)
- **Format**: 11 digits, formatted as XX-XXXXXXXX-X (or no separators)
- **Check algorithm**: mod 11 with weights `[5, 4, 3, 2, 7, 6, 5, 4, 3, 2]`

## The loop

Same as the other examples — see the top-level `program.md` or one of the existing
examples (e.g. `examples/cpf/program.md`).

## Have fun

The whole point: a Python Argentina CUIT validator that's STRICTLY BETTER than a naive
regex baseline. Worst case you revert.
