# program.md — Israel ID research charter

You are an autonomous research agent. Your job: improve `workflow.py` so the field-level
exact-match F1 score from `eval.py` goes up. You do not edit `eval.py`, `eval_set.json`, or
`pyproject.toml`. You only edit `workflow.py` and append to `results.tsv`.

## The task

Validate Israel ID numbers (Teudat Zehut / תעודת זהות). Given a raw 9-digit string
(possibly with separators), return a structured `{ ok, normalized, error }`.

## Source of truth

- **Israeli government**: https://www.gov.il/
- **Format**: 9 digits (zero-padded)
- **Check algorithm**: modified Luhn with weights [1, 2, 1, 2, ...], for products ≥ 10 subtract 9

## The loop

Same as the other examples — see the top-level `program.md` or one of the existing
examples (e.g. `examples/cpf/program.md`).

## Have fun

The whole point: a Python Israel ID validator that's STRICTLY BETTER than a naive
regex baseline. Worst case you revert.
