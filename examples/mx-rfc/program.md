# program.md — Mexico RFC research charter

You are an autonomous research agent. Your job: improve `workflow.py` so the field-level
exact-match F1 score from `eval.py` goes up. You do not edit `eval.py`, `eval_set.json`, or
`pyproject.toml`. You only edit `workflow.py` and append to `results.tsv`.

## The task

Validate Mexico RFCs (Registro Federal de Contribuyentes). Given a raw 12- or 13-character
RFC string (possibly with separators), return a structured `{ ok, normalized, error }`.

## Source of truth

- **Public SAT spec**: https://www.sat.gob.mx/ (Servicio de Administración Tributaria)
- **Format**: 4 letters + 6 digits (YYMMDD) + 2 alphanumeric (homoclave base) = 12 chars
- **13th char** (optional): the verification digit, computed from the first 12 via a
  weighted-sum modulo 11 algorithm. If the algorithm's check is 10, the 13th char is "A".
- **Weights**: [13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2] on the first 12 chars (A=10, B=11, ..., Z=35)

## The loop

Same as the other examples — see the top-level `program.md` or one of the existing
examples (e.g. `examples/cpf/program.md`).

## Have fun

The whole point: a Python Mexico RFC validator that's STRICTLY BETTER than a naive
regex baseline. Worst case you revert.
