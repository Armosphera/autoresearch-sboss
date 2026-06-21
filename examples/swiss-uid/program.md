# program.md — Swiss UID (Unternehmens-Identifikationsnummer) research charter

You are an autonomous research agent. Your job: improve `workflow.py` so the field-level
exact-match F1 score from `eval.py` goes up. You do not edit `eval.py`, `eval_set.json`, or
`pyproject.toml`. You only edit `workflow.py` and append to `results.tsv`.

## The task

Validate Swiss UIDs (Unternehmens-Identifikationsnummer). Given a raw 12-character
"CHE-XXX.XXX.XXX" or "CH-XXX.XXX.XXX" string, return `{ ok, normalized, error }`.

## Source of truth

- **Public UID spec**: https://www.uid.admin.ch/ (Swiss Federal Statistical Office)
- **Format**: 3 letters (CHE/CH/CDF) + 9 digits = 12 chars
- **No checksum** — sequence number, not a verified sum

## The loop

Same as the other examples — see the top-level `program.md` or one of the existing
examples (e.g. `examples/cpf/program.md`).

## Have fun

The whole point: a Python Swiss UID validator that's STRICTLY BETTER than a naive
regex baseline. Worst case you revert.
