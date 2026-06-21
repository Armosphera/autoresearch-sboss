# program.md — Singapore UEN research charter

You are an autonomous research agent. Your job: improve `workflow.py` so the field-level
exact-match F1 score from `eval.py` goes up. You do not edit `eval.py`, `eval_set.json`, or
`pyproject.toml`. You only edit `workflow.py` and append to `results.tsv`.

## The task

Validate Singapore UEN numbers (Unique Entity Number). Given a raw 9-10 character string
(possibly with separators), return a structured `{ ok, normalized, error }`.

## Source of truth

- **ACRA spec**: https://www.acra.gov.sg/ (Accounting and Corporate Regulatory Authority)
- **Format**: 9 digits + 1 check letter (most common), or 10 digits (foreign companies)
- **No mathematical check digit** — the check letter is ACRA-internal, not public

## The loop

Same as the other examples — see the top-level `program.md` or one of the existing
examples (e.g. `examples/cpf/program.md`).

## Have fun

The whole point: a Python Singapore UEN validator that's STRICTLY BETTER than a naive
regex baseline. Worst case you revert.
