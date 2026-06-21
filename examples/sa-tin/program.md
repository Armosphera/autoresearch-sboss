# program.md — Saudi Arabia TIN research charter

You are an autonomous research agent. Your job: improve `workflow.py` so the field-level
exact-match F1 score from `eval.py` goes up. You do not edit `eval.py`, `eval_set.json`, or
`pyproject.toml`. You only edit `workflow.py` and append to `results.tsv`.

## The task

Validate Saudi Arabia TIN numbers (Tax Identification Number). Given a raw 10-digit string
(possibly with separators), return a structured `{ ok, normalized, error }`.

## Source of truth

- **ZATCA**: https://zatca.gov.sa/ (Zakat, Tax and Customs Authority)
- **Format**: 10 digits
- **First digit kind prefix**: 3 = VAT-payer, 4 = non-VAT-payer
- **No public check-digit algorithm** — the digits are assigned by ZATCA

## The loop

Same as the other examples — see the top-level `program.md` or one of the existing
examples (e.g. `examples/cpf/program.md`).

## Have fun

The whole point: a Python Saudi Arabia TIN validator that's STRICTLY BETTER than a naive
regex baseline. Worst case you revert.
