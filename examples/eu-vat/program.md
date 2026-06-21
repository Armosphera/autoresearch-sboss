# program.md — EU VAT (VAT identification number) research charter

You are an autonomous research agent. Your job: improve `workflow.py` so that the field-level
exact-match F1 score from `eval.py` goes up. You do not edit `eval.py`, `eval_set.json`, or
`pyproject.toml`. You only edit `workflow.py` and append to `results.tsv`.

## The task

Validate EU VAT identification numbers (VATINs). Given a raw VAT string (possibly with
separators, mixed case, etc.), return a structured `{ ok, normalized, error }` result.

The current workflow (`workflow.py`) is intentionally weak — it only does:
- Uppercase + strip whitespace/dots/hyphens
- 2-letter country code + 8-12 alphanumeric body check
- Membership in the EU country code list
- Stub `check_digit_verifier` that accepts everything

The **baseline score is ~50-60 / 100** (depending on eval_set). The agent's job is to push
it to 100 by implementing real per-country format + checksum validation.

## Per-country reference

Source of truth: https://ec.europa.eu/taxation_customs/vies/ and individual country tax
authority documentation. Public algorithms:

- **AT** (Austria): `ATU` + 8 digits. Checksum: weighted sum mod 11.
- **BE** (Belgium): `BE0` + 9 digits. Last 2 digits = `97 - (first 8 mod 97)`.
- **DE** (Germany): `DE` + 9 digits. First 8 = sequential, 9th = ISO 7064 mod 11-10.
- **ES** (Spain): `ES` + 9 chars (letter or digit). Format depends on company type
  (Spanish national ID, passport + sequence, etc.).
- **FR** (France): `FR` + 2 chars + 9 digits. Checksum: `(siren * 3 + 12) mod 97 = XX`.
- **GB** (UK): `GB` + 9 digits (VAT) or `GB` + 12 digits (branch traders).
  Note: post-Brexit, UK uses different rules; for VIES purposes, treat as `GD`/`HA`.
- **IT** (Italy): `IT` + 11 digits. First 7 = sequential, 8-10 = office code, 11 = check.
- **NL** (Netherlands): `NL` + 9 digits + `B` + 2 digits (BTW number with B suffix).
- **PL** (Poland): `PL` + 10 digits. Last = NIP, 10th = mod-11 checksum.
- **PT** (Portugal): `PT` + 9 digits. 9th = mod-11 checksum.

## The loop

```
1. Read results.tsv — find the current best score.
2. Read workflow.py — understand the current state.
3. Make ONE focused change to workflow.py (a hypothesis).
4. Run: python3 eval.py
5. Read the new score from stdout.
6. If new_score > best_score:
       git add workflow.py && git commit -m "score: N.NN — <one-line hypothesis>"
   Else:
       git checkout workflow.py
7. Append the experiment to results.tsv.
8. Repeat.
```

## Rules of engagement

- **One hypothesis per experiment.** Don't bundle 5 unrelated changes into one commit.
- **Read first, edit second.** Always re-read workflow.py before editing.
- **Keep it boring.** Small, reversible changes. No sweeping rewrites.
- **Respect the time budget.** Default 60s per experiment (env `EXPERIMENT_BUDGET_SEC`).
- **Don't touch the eval set.** `eval_set.json` is the ground truth. Editing it is cheating.
- **Don't touch the score function.** `eval.py` is the judge. Editing it is cheating.
- **Log everything.** Every experiment, keep or revert, goes in `results.tsv`.

## What to try (in rough priority order)

1. **Per-country exact length check.** Tighten `8 <= len(body) <= 12` to per-country exact
   lengths. Should be ~10-20 lines. This is the easiest first-move win.
2. **Per-country format check.** Some countries allow letters in the body (ES, NL). Others
   are digit-only. Update the digit check per country.
3. **Per-country checksum.** Implement the checksum for at least one country (start with
   DE — most common, well-documented algorithm). Add the others incrementally.
4. **Better error messages.** Distinguish "wrong country" from "wrong length" from
   "wrong checksum" with country-specific messages.
5. **Special case handling.** GB post-Brexit, branch traders (GB+12), Spain's
   nationality letters, etc.

## When to stop

- Score = 100.0 → declare victory, write a one-paragraph summary in `results.tsv`.
- 20 experiments in a row without a keep → consider rewriting `program.md`.
- Same file edited 5 times with no improvement → step back, re-read `workflow.py`.

## Logging format for results.tsv

Tab-separated:
`timestamp\tcommit\tstatus\tscore\tbudget_sec\tdescription`

Commit hash on revert is `-`. Description is one short line — what you changed and why.

## Environment

- `LLM_ENDPOINT_URL` (optional): OpenAI-compatible chat completions endpoint.
- `LLM_API_KEY` (optional): bearer token for the endpoint.
- `LLM_MODEL` (optional): model name. Default `mock-validator-v1` (deterministic regex).
- `EXPERIMENT_BUDGET_SEC` (optional): wall-clock budget. Default `60`.

If `LLM_ENDPOINT_URL` is unset, the harness uses a deterministic mock that uses regex
against the document. For real research, set the env vars.

## Have fun

The whole point: a Python EU VAT validator that's STRICTLY BETTER than the naive regex
baseline, with per-country format + checksum validation. Worst case you revert.
