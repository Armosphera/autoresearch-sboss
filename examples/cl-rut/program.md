# program.md — Chile RUT research charter

You are an autonomous research agent. Your job: improve `workflow.py` so the field-level
exact-match F1 score from `eval.py` goes up. You do not edit `eval.py`, `eval_set.json`, or
`pyproject.toml`. You only edit `workflow.py` and append to `results.tsv`.

## The task

Validate Chile RUT numbers (Rol Único Tributario). Given a raw 7-8 digit body + check
character (0-9 or K) string (possibly with separators), return a structured
`{ ok, normalized, error }`.

## Source of truth

- **SII spec**: https://www.sii.cl/ (Servicio de Impuestos Internos)
- **Format**: 7-8 digit body + check character (0-9 or K), formatted as "XXXXXXXX-X"
- **Check algorithm**: mod 11 with weights [2, 3, 4, 5, 6, 7, 2, 3] applied right-to-left

## The loop

Same as the other examples — see the top-level `program.md` or one of the existing
examples (e.g. `examples/cpf/program.md`).

## Have fun

The whole point: a Python Chile RUT validator that's STRICTLY BETTER than a naive
regex baseline. Worst case you revert.
