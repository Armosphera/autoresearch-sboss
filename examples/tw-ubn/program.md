# program.md — Taiwan UBN research charter

You are an autonomous research agent. Your job: improve `workflow.py` so the field-level
exact-match F1 score from `eval.py` goes up. You do not edit `eval.py`, `eval_set.json`, or
`pyproject.toml`. You only edit `workflow.py` and append to `results.tsv`.

## The task

Validate Taiwan UBN numbers (Unified Business Number / 統一編號). Given a raw 8-digit string
(possibly with separators), return a structured `{ ok, normalized, error }`.

## Source of truth

- **Ministry of Economic Affairs**: https://www.moea.gov.tw/
- **Format**: 8 digits, first digit must be non-zero
- **No public check-digit algorithm** — the 8-digit number is assigned by the government

## The loop

Same as the other examples — see the top-level `program.md` or one of the existing
examples (e.g. `examples/cpf/program.md`).

## Have fun

The whole point: a Python Taiwan UBN validator that's STRICTLY BETTER than a naive
regex baseline. Worst case you revert.
