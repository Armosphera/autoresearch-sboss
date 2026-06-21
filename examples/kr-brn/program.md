# program.md — Korea BRN research charter

You are an autonomous research agent. Your job: improve `workflow.py` so the field-level
exact-match F1 score from `eval.py` goes up. You do not edit `eval.py`, `eval_set.json`, or
`pyproject.toml`. You only edit `workflow.py` and append to `results.tsv`.

## The task

Validate Korea Business Registration Numbers (BRN / 사업자등록번호). Given a raw 10-digit
string (possibly with 3-2-5 hyphen separators), return a structured `{ ok, normalized, error }`.

## Source of truth

- **NTS spec**: https://www.nts.go.kr/ (National Tax Service)
- **Format**: 10 digits, formatted as XXX-XX-XXXXX (3-2-5)
- **No mathematical check digit** — the first 3 digits encode the tax office kind, the
  next 2 encode the business type, the last 5 are the serial

## The loop

Same as the other examples — see the top-level `program.md` or one of the existing
examples (e.g. `examples/cpf/program.md`).

## Have fun

The whole point: a Python Korea BRN validator that's STRICTLY BETTER than a naive
regex baseline. Worst case you revert.
