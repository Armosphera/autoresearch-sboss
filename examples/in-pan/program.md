# program.md — India PAN research charter

You are an autonomous research agent. Your job: improve `workflow.py` so the field-level
exact-match F1 score from `eval.py` goes up. You do not edit `eval.py`, `eval_set.json`, or
`pyproject.toml`. You only edit `workflow.py` and append to `results.tsv`.

## The task

Validate India PAN numbers (Permanent Account Number). Given a raw 10-character
string (possibly with separators + lowercase), return a structured
`{ ok, normalized, error }`.

## Source of truth

- **Income Tax Department**: https://www.incometax.gov.in/
- **Format**: 10 chars, structure AAAAA9999A (3 letters + kind + letter + 4 digits + letter)
- **4th character kind code**: P=Individual, C=Company, H=HUF, F=Firm, A=AOP,
  T=Trust, B=BOI, L=Local Authority, J=Artificial Juridical Person, G=Government
- **No public check-digit algorithm** — the 10th character is assigned by the ITD

## The loop

Same as the other examples — see the top-level `program.md` or one of the existing
examples (e.g. `examples/cpf/program.md`).

## Have fun

The whole point: a Python India PAN validator that's STRICTLY BETTER than a naive
regex baseline. Worst case you revert.
