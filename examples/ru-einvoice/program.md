# program.md — Russian e-invoice (счёт-фактура / УПД) research charter

You are an autonomous research agent. Your job: improve `workflow.py` so that the field-level
exact-match F1 score from `eval.py` goes up. You do not edit `eval.py`, `eval_set.json`, or
`pyproject.toml`. You only edit `workflow.py` and append to `results.tsv`.

## The task

The default `workflow.py` is a faithful Python port of
`src/einvoice.js` from
[Armosphera/A1-Localization-RU](https://github.com/Armosphera/A1-Localization-RU).
Structural compliance gate for a Russian e-invoice (счёт-фактура / УПД) before mapping
to the official ФНС XSD `ON_NSCHFDOPPR` (format 5.03, Приказ ФНС № ЕД-7-26/970@) and
submission through an оператор ЭДО with a КЭП signature.

The 2026 налоговая реформа raised the base rate 20% → 22%. Allowed issuance rates:
0% (export/exempt), 10% (reduced: food/children/medical), 22% (base). Settlement
rates 10/110, 22/122 are NOT issuance rates and are not in the allowed set.

Catches ~19 distinct error codes covering: number, date (missing/format/calendar),
currency code, seller (name/INN/KPP), buyer (name/INN/KPP), and per-line
(description/quantity/net/VAT rate/VAT amount/VAT mismatch/total/total mismatch).

The current **baseline score is 100.00 / 100** — the JS reference handles all
inputs correctly. Your job is to make the Python implementation **STRICTLY MORE
USEFUL** than the JS reference by adding capabilities the JS lacks.

Your job, in priority order:

1. **Add `severity` field per finding.** Currently every error is `"error"` (blocks
   submission). Distinguish:
   - `"error"` — blocks submission (missing field, invalid format, etc.)
   - `"warning"` — should fix but doesn't block (e.g., vatAmount within 5% of expected)
   - `"info"` — informational (e.g., 0% rate on a domestic sale — likely export)
2. **Add `summary` field.** One-line human-readable summary for UI toasts:
   `"3 errors: MISSING_NUMBER, INVALID_SELLER_INN, LINE_VAT_MISMATCH (lines[2].vatAmount)"`.
3. **УСН (USN) regime support.** Add a `regime: "osn"|"usn"` option. When `usn`,
   allowed rates become [0, 5, 7, 10, 22] (УСН доходы 5%/7% in 2026).
4. **Cross-line consistency.** Add checks that span multiple lines:
   - All line rates sum correctly to header total rate
   - Sum of line totals = TotalAmount

## The loop

```
1. Read results.tsv — find the current best score.
2. Read workflow.py — understand the current state.
3. Make ONE focused change to workflow.py (a hypothesis).
4. Run: python3 eval.py
5. Read the new score from stdout.
6. If new_score > best_score:
       git add workflow.py && git commit -m "score: N.NNN — <one-line hypothesis>"
   Else:
       git checkout workflow.py
7. Append the experiment to results.tsv.
8. Repeat.
```

## Rules of engagement

- **One hypothesis per experiment.** Don't bundle 5 unrelated changes into one commit.
- **Read first, edit second.** Always re-read workflow.py before editing.
- **Keep it boring.** Small, reversible changes. No sweeping rewrites.
- **Respect the time budget.** Default 60s per experiment.
- **Don't touch the score function.** `eval.py` is the judge.
- **Log everything.** Every experiment, keep or revert, goes in `results.tsv`.
- **Don't break existing tests.** Baseline 100.00 must stay 100.00.

## What to try (in rough priority order)

1. **Add `severity` field.** Default to "error" for all current codes; add
   warning-level checks (rate within 5% tolerance but not exact match).
2. **Add `summary` field.** Deterministic short string.
3. **УСН regime.** `regime="usn"` → allowed rates = [0, 5, 7, 10, 22].
4. **Cross-line consistency.** Sum line totals = TotalAmount.
5. **Round-trip with `build_e_invoice_xml`.** Verify that an invoice that
   validates can be round-tripped through the XML builder without loss.

## When to stop

- Score = 100 AND `severity` works AND `summary` works AND УСН regime works → done with v0.1.
- 20 experiments with no improvement → consider rewriting `program.md`.

## Logging format for results.tsv

Tab-separated:
`timestamp\tcommit\tstatus\tscore\tbudget_sec\tdescription`

## Environment

This example uses NO LLM. Pure-function validation.

- `EXPERIMENT_BUDGET_SEC` (optional): wall-clock budget. Default `60`.

## Have fun

The point: a Russian e-invoice validator that's STRICTLY MORE USEFUL than the JS
reference — with severity, summary, УСН regime, and (optionally) cross-line checks.
Worst case you revert.
