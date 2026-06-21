# program.md — India GSTIN research charter

You are an autonomous research agent. Your job: improve `workflow.py` so the field-level
exact-match F1 score from `eval.py` goes up. You do not edit `eval.py`, `eval_set.json`, or
`pyproject.toml`. You only edit `workflow.py` and append to `results.tsv`.

## The task

Validate India GST Identification Numbers (GSTINs). Given a raw 15-character GSTIN
string (possibly with separators), return a structured `{ ok, normalized, error }`.

## Source of truth

- **Public GSTIN spec**: https://www.gst.gov.in/ (Government of India GST portal)
- **Format reference**: state code (2 digits, 01-37 + 96 + 97) + PAN-style (10 chars:
  5 letters + 4 digits + 1 letter) + entity code (1 digit) + 'Z' + check (1 digit)
- **No checksum** — the 15th character is a check digit but the algorithm is not
  publicly published; we use format validation only.

## The loop

Same as the other examples — see the top-level `program.md` or one of the existing
examples (e.g. `examples/cpf/program.md`).

## Have fun

The whole point: a Python India GSTIN validator that's STRICTLY BETTER than a naive
regex baseline. Worst case you revert.
