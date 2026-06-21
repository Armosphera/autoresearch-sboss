# program.md — Japan My Number research charter

You are an autonomous research agent. Your job: improve `workflow.py` so the field-level
exact-match F1 score from `eval.py` goes up. You do not edit `eval.py`, `eval_set.json`, or
`pyproject.toml`. You only edit `workflow.py` and append to `results.tsv`.

## The task

Validate Japan My Numbers (個人番号 / マイナンバー). Given a raw 12-digit string (possibly
with separators), return a structured `{ ok, normalized, error }`.

## Source of truth

- **Public My Number spec**: https://www.soumu.go.jp/ (Ministry of Internal Affairs)
- **Format**: 12 digits, formatted as "XXXXXX XXXXXX" (6+6 with space)
- **Check algorithm**: mod 11 with weights [6, 5, 4, 3, 2, 7, 6, 5, 4, 3, 2, 1]

## The loop

Same as the other examples — see the top-level `program.md` or one of the existing
examples (e.g. `examples/cpf/program.md`).

## Have fun

The whole point: a Python Japan My Number validator that's STRICTLY BETTER than a naive
regex baseline. Worst case you revert.
