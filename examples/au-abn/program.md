# program.md — Australia ABN research charter

You are an autonomous research agent. Your job: improve `workflow.py` so the field-level
exact-match F1 score from `eval.py` goes up. You do not edit `eval.py`, `eval_set.json`, or
`pyproject.toml`. You only edit `workflow.py` and append to `results.tsv`.

## The task

Validate Australian Business Numbers (ABNs). Given a raw 11-digit ABN string (possibly
with separators), return a structured `{ ok, normalized, error }`.

## Source of truth

- **Public ABN spec**: https://abr.business.gov.au/ (Australian Business Register)
- **Format**: 11 digits, formatted as "XX XXX XXX XXX" (2-3-3-3 with spaces)
- **No leading zero** (leading-zero is reserved for ACN)
- **Mod-89 check-digit**: subtract 1 from first digit, apply weights
  [10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19], mod 89. Result 0 = valid.

## The loop

Same as the other examples — see the top-level `program.md` or one of the existing
examples (e.g. `examples/cpf/program.md`).

## Have fun

The whole point: a Python Australia ABN validator that's STRICTLY BETTER than a naive
regex baseline. Worst case you revert.
