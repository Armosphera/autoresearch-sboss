# autoresearch-sboss

**Autonomous keep-or-revert loop for SBOSS sovereign business workflows.**

This is the [Karpathy autoresearch](https://github.com/karpathy/autoresearch) pattern, adapted from
training tiny GPTs to optimizing SBOSS business workflows. Same loop. Different experiment.

> *One day, frontier business operations used to be tuned by meat computers in between eating,
> sleeping, and synchronizing once in a while using email threads in the ritual of "team meeting".
> That era is long gone. Operations are now the domain of autonomous swarms of AI agents running
> across sovereign compute. This repo is the story of how it began.* — `@samstep74`, June 2026

## What this is

The original autoresearch gives an AI agent a tiny GPT training environment and lets it experiment
overnight — edit `train.py`, train for 5 minutes, check `val_bpb`, keep or revert, repeat.

This repo gives an AI agent a **SBOSS workflow harness** and the same loop. The agent edits
`workflow.py` (a SBOSS workflow being tuned), runs `eval.py` within a fixed time budget, checks the
business score, and keeps or reverts via git. No GPU. No torch. Just Python + git + an LLM endpoint.

Pattern → business workflow. Same discipline.

## File layout

```
eval.py          — fixed: eval harness + scoring (do not modify)
workflow.py      — workflow config + run_workflow() (agent modifies this)
program.md       — agent instructions (human iterates on this)
eval_set.json    — fixed: 20 sample invoices with ground truth
results.tsv      — experiment log (commit after each keep)
pyproject.toml   — no external deps — pure stdlib + httpx (optional)
```

By design, each experiment runs for a fixed **time budget** (default 60s, env-overridable), regardless
of what the agent changes. The metric is the **business score** (default: field-level exact-match F1
on invoice extraction, higher is better). Workflows can be swapped by replacing `workflow.py` and
`eval_set.json` — the harness stays the same.

## Quick start

```bash
# 1. Install uv (if needed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Install dependencies
uv sync

# 3. Run one experiment manually to confirm the harness works (~5s with mock LLM)
uv run eval.py
```

If you see `score: 0.NNNN | elapsed: X.Xs`, the harness is working.

## Run all sub-examples

The repo ships with **38 reference examples** (37 SBOSS business workflow targets + 1
cross-link sweep). Use `scripts/run_evals.py` to run them all and print a summary table:

```bash
# Run every example, print a summary table
python scripts/run_evals.py

# Run a single example
python scripts/run_evals.py ar-cuit

# Run several
python scripts/run_evals.py ar-cuit cl-rut sg-uen kr-brn

# Strict mode — exit 1 if any example scores below 100
python scripts/run_evals.py --strict

# JSON output for downstream tools
python scripts/run_evals.py --json > results.json
```

The same logic powers the `sub-example evals` job in `.github/workflows/ci.yml`.

## Add a new example

`scripts/new_example.py` generates the 5-file template for a new target:

```bash
python scripts/new_example.py <name> [--input-key <key>]
# e.g.
python scripts/new_example.py ar-cuit --input-key cuit
```

This creates `examples/<name>/` with `eval.py`, `workflow.py`, `program.md`,
`eval_set.json`, `results.tsv`. The first run of `eval.py` will be a starter
score (typically 50-90); the agent's job is to improve it to 100 by editing
`workflow.py` per the `program.md` charter.

## Running the agent

Point Claude Code / Codex / Mavis / etc. at `program.md` and let it go (disable all permissions):

```
Hi, have a look at program.md and let's kick off a new experiment.
Let's do the setup first.
```

`program.md` is a super-lightweight "skill". The agent reads it, understands the task, edits
`workflow.py`, runs `eval.py`, decides to keep or revert, appends to `results.tsv`, and repeats.

Expect ~60 experiments/hour and ~500 experiments overnight. Reverts are the norm — keep rate
typically 5-15% depending on the workflow.

## Karpathy Eval Harness

This repo also exposes the shared A1 product-research runner, pinned to
`Armosphera/A1-AI-Core@f917e8a1fd72d48d6e227300a0c069c70ace6f1e`. The local shim uses that cached
clean clone by default. Set `A1_AI_CORE_CACHE_DIR` to choose the cache location, or set
`A1_AI_CORE_PATH` to an explicit checkout at the pinned commit.

```bash
npm run karpathy:list
npm run karpathy:program -- invoice-extractor-contract
npm run karpathy:run -- invoice-extractor-contract --best 100
node scripts/check-invoice-extractor-contract.mjs
```

The `invoice-extractor-contract` keeps the root invoice workflow on the deterministic mock path:
`workflow.py` is the editable surface, while `eval.py` and `eval_set.json` remain fixed guardrails.

## Design choices

- **One file to modify.** The agent only touches `workflow.py`. Diffs stay reviewable.
- **Fixed time budget.** Each experiment gets the same wall-clock time. Makes results comparable.
- **Pluggable LLM endpoint.** Default is a deterministic mock (no API key needed). Set
  `LLM_ENDPOINT_URL` + `LLM_API_KEY` to use OpenRouter, Ollama, or any OpenAI-compatible endpoint.
- **No GPU.** Pure Python. Runs on any Mac, any Linux box, any CI.
- **Self-contained.** Stdlib + optional `httpx`. No torch, no transformers, no numpy.

## Platform support

Anything that runs Python 3.10+. Tested on Mac Studio M2 Ultra (Metal). No GPU required.

## How to point this at a real SBOSS workflow

1. Replace `eval_set.json` with your real eval fixtures (e.g., production invoices + ground truth).
2. Replace `workflow.py`:
   - Update `WORKFLOW_CONFIG` with your prompt template + params.
   - Replace the mock LLM in `run_workflow()` with a call to your real LLM endpoint.
   - Set `LLM_ENDPOINT_URL`, `LLM_MODEL`, `LLM_API_KEY` env vars.
3. Update `program.md` with the new research charter (what to optimize, what the metric means).
4. Run `uv run eval.py` once to confirm the baseline.
5. Point an agent at `program.md` and let it run overnight.

The harness doesn't care what workflow you're tuning. It only cares about:
- A `run_workflow(input) -> output` function in `workflow.py`.
- A list of `{input, expected_output}` pairs in `eval_set.json`.
- A score function in `eval.py` (default: field-level exact-match F1).

Swap any of those and the loop keeps working.

## Examples

The `examples/` directory contains self-contained real-SBOSS workflow targets. Each one
follows the same 3-file pattern and can be iterated on independently.

| Example | What | Baseline | Source of truth |
|---|---|---|---|
| `examples/hhvh/` | **ՀՎՀՀ (Armenian taxpayer id) validation** | 96.67 / 100 | [Armosphera/A1-Localization-AM](https://github.com/Armosphera/A1-Localization-AM) `src/localization.js` |
| `examples/ru-identifiers/` | **5 Russian business id validators (ИНН / КПП / ОГРН / ОГРНИП / СНИЛС)** | 85.00 / 100 | [Armosphera/A1-Localization-RU](https://github.com/Armosphera/A1-Localization-RU) `src/inn.js` |
| `examples/model-policy/` | **A1 model policy resolver** (per-module / per-aspect precedence) | 50.00 / 100 | [Armosphera/A1-AI-Core](https://github.com/Armosphera/A1-AI-Core) `src/model-policy.js` |
| `examples/vat-return/` | **Armenian VAT return computation** (output − input = payable to SRC) | 100.00 / 100 | [Armosphera/A1-Localization-AM](https://github.com/Armosphera/A1-Localization-AM) `src/vatReturn.js` |
| `examples/payroll-am/` | **Armenian payroll rules engine** (4 employee withholdings → net) | 100.00 / 100 | [Armosphera/A1-Localization-AM](https://github.com/Armosphera/A1-Localization-AM) `src/armeniaPayroll.js` |
| `examples/chart-of-accounts-am/` | **Armenian chart of accounts** (623 accounts, 9 classes) | 100.00 / 100 | [Armosphera/A1-Localization-AM](https://github.com/Armosphera/A1-Localization-AM) `src/armeniaChartOfAccounts.js` |
| `examples/vat-return-form/` | **VAT return form validator** (10 error codes, cross-foot checks) | 100.00 / 100 | [Armosphera/A1-Localization-AM](https://github.com/Armosphera/A1-Localization-AM) `src/vatReturn.js` |
| `examples/phone-am/` | **Armenian phone normalization** (+374, 00374, 091234567, etc.) | 100.00 / 100 | [Armosphera/A1-Localization-AM](https://github.com/Armosphera/A1-Localization-AM) `src/armeniaPhone.js` |
| `examples/regions-am/` | **Armenian administrative regions** (11 marzes, ISO 3166-2:AM) | 100.00 / 100 | [Armosphera/A1-Localization-AM](https://github.com/Armosphera/A1-Localization-AM) `src/armeniaRegions.js` |
| `examples/einvoice-am/` | **Armenian e-invoice validator** (16 error codes, pre-SRC submission compliance gate) | 100.00 / 100 | [Armosphera/A1-Localization-AM](https://github.com/Armosphera/A1-Localization-AM) `src/einvoice.js` |
| `examples/chat-client/` | **OpenRouter chat-completions client** (callModel / callVision / callStructured, OpenAI-compatible, mockable safeFetch) | 100.00 / 100 | [Armosphera/A1-AI-Core](https://github.com/Armosphera/A1-AI-Core) `src/chat.js` |
| `examples/phone-ru/` | **Russian phone normalization** (+7, 8XXX, 10-digit NSN, 3-9 first-digit invariant) | 100.00 / 100 | [Armosphera/A1-Localization-RU](https://github.com/Armosphera/A1-Localization-RU) `src/phone.js` |
| `examples/ru-einvoice/` | **Russian e-invoice validator (счёт-фактура / УПД)** (19 error codes, 2026 tax reform base 22%, ИНН + КПП + rates [0, 10, 22]) | 100.00 / 100 | [Armosphera/A1-Localization-RU](https://github.com/Armosphera/A1-Localization-RU) `src/einvoice.js` |
| `examples/payroll-ru/` | **Russian payroll (НДФЛ + страх. взносы)** (5-band progressive 13/15/18/20/22%, unified 30% + МСП 1.5×МРОТ) | 100.00 / 100 | [Armosphera/A1-Localization-RU](https://github.com/Armosphera/A1-Localization-RU) `src/payroll.js` |
| `examples/regions-ru/` | **Russian federal subjects** (83 субъекта, ISO 3166-2:RU, 2 federal cities + 21 republics + 9 krais + 46 oblasts + 4 okrugs) | 100.00 / 100 | [Armosphera/A1-Localization-RU](https://github.com/Armosphera/A1-Localization-RU) `src/regions.js` |
| `examples/chart-of-accounts-ru/` | **Russian План счетов (94н)** (73 accounts, 8 sections + off-balance, section by number range not leading digit) | 100.00 / 100 | [Armosphera/A1-Localization-RU](https://github.com/Armosphera/A1-Localization-RU) `src/chartOfAccounts.js` |
| `examples/vat-ru/` | **Russian VAT engine (2026 reform)** (rates [0, 10, 22] + УСН [5, 7], year-keyed, gross↔net settlement math) | 100.00 / 100 | [Armosphera/A1-Localization-RU](https://github.com/Armosphera/A1-Localization-RU) `src/vat.js` |
| `examples/settings-store/` | **AI settings store** (file-backed JSON, 0600 perms, redactedForClient, resolveModelPolicy) | 100.00 / 100 | [Armosphera/A1-AI-Core](https://github.com/Armosphera/A1-AI-Core) `src/settings-store.js` |
| `examples/model-catalog/` | **OpenRouter model catalog** (injected safeFetch + isEgressAllowed, FALLBACK_MODELS, never throws) | 100.00 / 100 | [Armosphera/A1-AI-Core](https://github.com/Armosphera/A1-AI-Core) `src/model-catalog.js` |
| `examples/supplemental-sources/` | **Advisory source policy** (dedupe by sourceUrl‖title, score sort, cap 3, 280-char excerpt) | 100.00 / 100 | [Armosphera/A1-AI-Core](https://github.com/Armosphera/A1-AI-Core) `src/supplemental.js` |
| `examples/eu-vat/` | **EU VAT (VATIN) validator** (28 EU + GB/NO/CH, per-country length, allow letters in ES/NL/GB body) | 100.00 / 100 | [ec.europa.eu/taxation_customs/vies](https://ec.europa.eu/taxation_customs/vies/) |
| `examples/cnpj/` | **CNPJ (Brazilian taxpayer id)** (XX.XXX.XXX/XXXX-XX, mod-11 DV1+DV2 per Receita Federal) | 100.00 / 100 | [gov.br/receitafederal](https://www.gov.br/receitafederal/pt-br) |
| `examples/cpf/` | **CPF (Brazilian individual taxpayer id)** (XXX.XXX.XXX-XX, mod-11 DV1+DV2 per Receita Federal) | 100.00 / 100 | [gov.br/receitafederal](https://www.gov.br/receitafederal/pt-br) |
| `examples/uk-company/` | **UK Company Number (Companies House)** (8 digits, or SC/NI/OC/SO/NC/FC/SF/NF + 6 digits) | 100.00 / 100 | [find-and-update.company-information.service.gov.uk](https://find-and-update.company-information.service.gov.uk/) |
| `examples/us-ein/` | **US EIN (Employer Identification Number)** (XX-XXXXXXX, 9 digits, IRS campus code prefix) | 100.00 / 100 | [irs.gov/ein](https://www.irs.gov/businesses/small-businesses-self-employed/how-eins-work) |
| `examples/gstin/` | **India GSTIN** (15 alphanumeric, state code + PAN-style middle, default Z + check) | 100.00 / 100 | [gst.gov.in](https://www.gst.gov.in/) |
| `examples/swiss-uid/` | **Swiss UID (Unternehmens-Identifikationsnummer)** (CHE/CH/CDF + 9 digits) | 100.00 / 100 | [uid.admin.ch](https://www.uid.admin.ch/) |
| `examples/au-abn/` | **AU ABN (Australian Business Number)** (XX XXX XXX XXX, 11 digits, mod-89 check per ATO spec) | 100.00 / 100 | [abr.business.gov.au](https://abr.business.gov.au/) |
| `examples/mx-rfc/` | **Mexico RFC (Registro Federal de Contribuyentes)** (4 letters + 6 digits + 2-3 alphanumeric, SAT verification digit: mod 11 weighted sum [13..2], 0-9 maps to digit, 10 maps to 'A') | 100.00 / 100 | [sat.gob.mx](https://www.sat.gob.mx/) |
| `examples/jp-mynumber/` | **Japan My Number (個人番号)** (12 digits, mod-11 check with weights [6,5,4,3,2,7,6,5,4,3,2,1], cannot start with 0) | 100.00 / 100 | [soumu.go.jp](https://www.soumu.go.jp/) |
| `examples/ar-cuit/` | **Argentina CUIT/CUIL** (11 digits, AFIP mod-11 check with weights [5,4,3,2,7,6,5,4,3,2]) | 100.00 / 100 | [afip.gob.ar](https://www.afip.gob.ar/) |
| `examples/cl-rut/` | **Chile RUT (Rol Único Tributario)** (7-8 digits + check char 0-9/K, SII mod-11 with weights [2,3,4,5,6,7,2,3] applied right-to-left) | 100.00 / 100 | [sii.cl](https://www.sii.cl/) |
| `examples/sg-uen/` | **Singapore UEN (Unique Entity Number)** (9-10 alphanumeric, ACRA-internal check letter, no public checksum) | 100.00 / 100 | [acra.gov.sg](https://www.acra.gov.sg/) |
| `examples/in-pan/` | **India PAN (Permanent Account Number)** (10 chars, AAAAA9999A, 4th char is kind code P/C/H/F/A/T/B/L/J/G) | 100.00 / 100 | [incometax.gov.in](https://www.incometax.gov.in/) |
| `examples/il-id/` | **Israel ID (Teudat Zehut / תעודת זהות)** (9 digits, modified Luhn with weights [1,2,1,2,...]) | 100.00 / 100 | [gov.il](https://www.gov.il/) |
| `examples/sa-tin/` | **Saudi Arabia TIN (Tax Identification Number)** (10 digits, first digit 3 = VAT-payer or 4 = non-VAT-payer) | 100.00 / 100 | [zatca.gov.sa](https://zatca.gov.sa/) |
| `examples/tw-ubn/` | **Taiwan UBN (Unified Business Number / 統一編號)** (8 digits, first digit non-zero) | 100.00 / 100 | [moea.gov.tw](https://www.moea.gov.tw/) |
| `examples/kr-brn/` | **Korea Business Registration Number (사업자등록번호)** (10 digits in 3-2-5 format, no public check digit) | 100.00 / 100 | [nts.go.kr](https://www.nts.go.kr/) |
| `examples/open-notebook/` | **Open Notebook RAG connector** (opt-in, egress-gated, non-throwing, tolerates 4 response shapes) | 100.00 / 100 | [Armosphera/A1-AI-Core](https://github.com/Armosphera/A1-AI-Core) `src/open-notebook.js` |
| `examples/product-research/` | **Autoresearch primitives** (8 ops: normalizeConfig, renderProgram, decide, TSV I/O) — *the most meta example* | 100.00 / 100 | [Armosphera/A1-AI-Core](https://github.com/Armosphera/A1-AI-Core) `src/product-research.js` |

### `examples/hhvh/` — Armenian taxpayer id validation

A faithful Python port of `validateHvhh()` from A1-Localization-AM, plus a known-weakness
eval set that flags the JS reference's missing pre-normalization length check. The agent's
job: fix the bug to hit 100, then research and implement the official Armenian HHVH
check-digit algorithm (currently a TODO seam in the JS).

```bash
cd examples/hhvh
python3 eval.py             # baseline: 96.67
# then point an agent at program.md
```

### `examples/ru-identifiers/` — Russian business id validator suite

A unified Python validator that dispatches to 5 separate JS-ported validators: ИНН
(legal/individual, weighted mod 11), КПП (regex), ОГРН (Horner mod 11), ОГРНИП
(Horner mod 13), СНИЛС (weighted mod 101). Baseline 85.00 reflects the JS reference's
incomplete separator handling — only СНИЛС strips whitespace and hyphens; the dispatcher
and the other 4 validators don't. The agent's first move: add separator stripping in the
dispatcher to hit 100, then improve error messages and edge cases.

```bash
cd examples/ru-identifiers
python3 eval.py             # baseline: 85.00
# then point an agent at program.md
```

### `examples/model-policy/` — A1 model policy resolver

A faithful Python port of `resolveModelForRequest()` from `@a1/ai`, the SBOSS AI provider
core. The JS returns only the resolved model id — this baseline adds a `source` field
("module" / "aspect" / "default" / "auto") as the agent's first lever. Baseline 50.00 =
resolved_model matches JS everywhere (100%) + source missing everywhere (0%). After fixing
source → 100, the agent can add cost-aware or LLM-based routing using OpenRouter pricing
data from the fallback catalog.

```bash
cd examples/model-policy
python3 eval.py             # baseline: 50.00
# then point an agent at program.md
```

### `examples/vat-return/` — Armenian VAT return computation

A faithful Python port of `computeVatReturn()` from A1-Localization-AM. Implements
Armenia's VAT logic per decree N 298-Ն: output VAT (20% standard, 16.67% imputed, 0%
zero-rated) minus recoverable input VAT = net. Positive net is payable to SRC; negative
net is credit carried forward. **Baseline 100.00** — the JS is mathematically clean for
valid inputs, no bugs to fix. The agent's job: make it STRICTLY MORE USEFUL by adding
input-validation warnings (negative amounts, implausible rates, vatAmount/rate mismatch),
an audit trail (per-line classification), multi-period aggregation, and the second
`vatReturnForm()` function that maps onto official SRC form lines 7/9/12/13/16/17/18/21/23.

```bash
cd examples/vat-return
python3 eval.py             # baseline: 100.00
# then point an agent at program.md
```

### `examples/payroll-am/` — Armenian payroll rules engine

A faithful Python port of `computePayroll()` from A1-Localization-AM. Computes
gross → net under 2026 Armenian rules: 4 employee withholdings — income tax (flat 20%),
pension (tiered 5%/10%−25k, capped 87,500), stamp duty (flat 1,000/mo — 2026 revision
replaced the previous 1,500/3,000/5,500/8,500 tiers), and health insurance (banded
0 / 4,800 / 10,800 by Dec-2025 law). **Baseline 100.00** — no bugs to fix. Agent's job:
add warnings for negative / unrealistic gross, effective tax rate, annual projection,
employer-side social contributions (5% up to cap).

```bash
cd examples/payroll-am
python3 eval.py             # baseline: 100.00
# then point an agent at program.md
```

### `examples/chart-of-accounts-am/` — Armenian chart of accounts

A faithful Python port of `accountByCode` / `accountClass` / `normalBalance` from
A1-Localization-AM, backed by the full official RA chart (623 accounts across 9 classes
per Ministry of Finance order arlis.am/hy/acts/75961). Loads from `data.json` (3739 lines).
Adds a `validate_code()` wrapper that returns structured `{ok, normalized, error, account}`
— the JS silently returns `None` for malformed/unknown codes, the Python implementation
tells you WHY. **Baseline 100.00.** Agent's job: search by Armenian name, parent-class
navigation, sub-accounts list, deprecated flags.

```bash
cd examples/chart-of-accounts-am
python3 eval.py             # baseline: 100.00
# then point an agent at program.md
```

### `examples/vat-return-form/` — VAT return form validator

The sister function of `computeVatReturn()` in the same file. Validates an assembled VAT
return form against SRC decree N 298-Ն — catches 10 distinct error codes:
`FORM_MISSING_LINE`, `FORM_NON_NUMERIC_AMOUNT`, `FORM_NON_INTEGER_AMOUNT`,
`FORM_NEGATIVE_AMOUNT`, `FORM_16_BASE_MISMATCH` / `FORM_16_VAT_MISMATCH` (cross-foot),
`FORM_21_VAT_MISMATCH`, `FORM_23_NET_MISMATCH`, `FORM_7_RATE_MISMATCH` /
`FORM_9_RATE_MISMATCH` (plausibility bands). **Baseline 100.00.** Agent's job: add
`severity` field per finding (error/warning/info), `summary` field for UI toasts,
stricter checks (zero-amount lines that imply no transactions).

```bash
cd examples/vat-return-form
python3 eval.py             # baseline: 100.00
# then point an agent at program.md
```

### `examples/phone-am/` — Armenian phone normalization

A faithful Python port of `armeniaPhone.js` — the 4-function normalizer that takes
any input shape (`+37491234567`, `0037491234567`, `091234567`, `91234567`,
`+374 91 23 45 67`, `(091) 23-45-67`) down to the 8-digit National Significant Number,
then formats as E.164 (`+37491234567`) or human-readable (`+374 91 234567`). Validates
the stable invariant (8 digits, not starting with 0) rather than hard-coding operator
ranges. **Baseline 100.00** on first run. Agent's job: optional `operator` field
based on 2-digit prefix, `warning` field for near-miss inputs (typos), `region` field
via `armeniaRegions.js` lookup.

```bash
cd examples/phone-am
python3 eval.py             # baseline: 100.00
# then point an agent at program.md
```

### `examples/regions-am/` — Armenian administrative regions

A faithful Python port of `armeniaRegions.js` — 11 administrative divisions (10
provinces + Yerevan capital), keyed on official ISO 3166-2:AM codes (AM-ER through
AM-VD). 4 functions: `regionByCode`, `isValidRegionCode`, `findRegion` (matches by
code OR Armenian name OR English name, case-insensitive), `citiesForRegion`. Used
across A1 Suite for addresses, e-invoices, shipping. **Baseline 100.00** on first
run. Agent's job: add `find_region_by_city` (reverse lookup), fuzzy name matching
(transliteration variants), distance-to-Yerevan, adjacency lookup.

```bash
cd examples/regions-am
python3 eval.py             # baseline: 100.00
# then point an agent at program.md
```

### `examples/einvoice-am/` — Armenian e-invoice validator

Structural compliance gate for an e-invoice before mapping to the official SRC XSD
and submission. Port of `validateEInvoice()` from
[Armosphera/A1-Localization-AM](https://github.com/Armosphera/A1-Localization-AM)
`src/einvoice.js`. The most error-code-rich target in the suite (16 distinct codes
covering transaction type, dates, supplier/buyer identification, line items, and
amount/rate consistency). Validates HHVH on both supplier and buyer, requires
either HHVH or passport for buyer, supports excise + environmental-fee lines,
recognises 0% and 20% VAT rates for issued invoices. **Baseline 100.00** on first
run after a one-line test-data fix (an all-same-digit HHVH was getting rejected by
the new `isValidHvhh()` check). Agent's job: add per-finding `severity` (error /
warning / info), add `summary` line, add `strict` mode, add cross-line consistency
checks.

```bash
cd examples/einvoice-am
python3 eval.py             # baseline: 100.00
# then point an agent at program.md
```

### `examples/chat-client/` — OpenRouter chat-completions client

The first **LLM-shaped** target in the suite (the rest are pure-function
validators). Port of `createChatClient()` from
[Armosphera/A1-AI-Core](https://github.com/Armosphera/A1-AI-Core) `src/chat.js`.
OpenAI-compatible chat-completions client: 3 methods (`callModel`, `callVision`,
`callStructured`), typed `HttpError {statusCode, code, message}`, framework-
agnostic — the egress-gated `safeFetch` is INJECTED so the host product
enforces deny-until-listed. Mock `safeFetch` driven by `eval_set.json` makes
runs deterministic (no real LLM call). **Baseline 100.00** on first run.
Agent's job: add retry-with-backoff (429/502/503/504), `Idempotency-Key`
header, request/response audit log, streaming variant, token-budget tracking.

```bash
cd examples/chat-client
python3 eval.py             # baseline: 100.00
# then point an agent at program.md
```

### `examples/phone-ru/` — Russian phone normalization

Faithful Python port of `phone.js` from
[Armosphera/A1-Localization-RU](https://github.com/Armosphera/A1-Localization-RU).
Russia (country code +7) uses a 10-digit NSN: 3-digit area/operator (DEF/ABC)
+ 7-digit subscriber. Domestic trunk prefix is 8 (legacy "8 (495) ..." form).
Validates the **stable** invariant (3-9 first digit: 3-8 geographic, 9 mobile)
rather than hard-coding operator prefixes (which change frequently). **Baseline
100.00** on first run. Agent's job: add `mobile` / `area` / `toll_free` fields
+ `kind` discriminator (full / short / invalid).

```bash
cd examples/phone-ru
python3 eval.py             # baseline: 100.00
# then point an agent at program.md
```

### `examples/ru-einvoice/` — Russian e-invoice validator (счёт-фактура / УПД)

Structural compliance gate for a Russian e-invoice (счёт-фактура / УПД)
before mapping to the official ФНС XSD `ON_NSCHFDOPPR` (format 5.03, Приказ
ФНС № ЕД-7-26/970@) and submission through an оператор ЭДО with a КЭП
signature (63-ФЗ). Port of `einvoice.js` from
[Armosphera/A1-Localization-RU](https://github.com/Armosphera/A1-Localization-RU).
**2026 налоговая реформа:** base rate 20% → 22% (effective 2026-01-01).
Allowed issuance rates: 0% (export), 10% (reduced: food/children/medical),
22% (base). **~19 distinct error codes** covering number, date
(missing/format/calendar), currency, seller (name/ИНН/КПП), buyer
(name/ИНН/КПП), and per-line (description/quantity/net/VAT rate/VAT
amount/VAT mismatch/total/total mismatch). **Baseline 100.00** after a
test-data fix (the JS contract is `vatAmount = net*rate/100`, not
`quantity*unitPrice*rate/100`). Self-contained — inlined `validateInn`/
`isValidKpp`/`roundRub`/`ratesFor` from sibling JS files. Agent's job: add
`severity` + `summary` + УСН regime (`regime: "usn"` allows [0, 5, 7, 10, 22])
+ cross-line consistency.

```bash
cd examples/ru-einvoice
python3 eval.py             # baseline: 100.00
# then point an agent at program.md
```

### `examples/payroll-ru/` — Russian payroll (НДФЛ + страховые взносы)

Faithful Python port of `payroll.js` from
[Armosphera/A1-Localization-RU](https://github.com/Armosphera/A1-Localization-RU).
Russian payroll — НДФЛ (employee withholding) + страховые взносы (employer
contributions), 2026. **НДФЛ** (ст. 224 НК РФ): 5-band progressive marginal
scale on cumulative annual base (13%/15%/18%/20%/22%). Non-residents flat 30%.
**Страховые взносы** (ст. 425 НК РФ): unified 30% within ЕПВБ (=2,979,000
in 2026), 15.1% above. **МСП** reduced (ст. 427): 30% within 1.5×МРОТ monthly,
15% above. **Child standard deductions** (ст. 218 НК РФ): 1st/2nd/3rd +
disabled child. Cap at 450,000 YTD income. **Baseline 100.00** on first run.
Agent's job: add `audit` field (per-call trace), `summary` field, multi-
employee batch, year-keyed rates.

```bash
cd examples/payroll-ru
python3 eval.py             # baseline: 100.00
# then point an agent at program.md
```

### `examples/regions-ru/` — Russian federal subjects

Faithful Python port of `regions.js` from
[Armosphera/A1-Localization-RU](https://github.com/Armosphera/A1-Localization-RU).
**83 federal subjects** keyed on ISO 3166-2:RU: 2 cities of federal
significance (Москва, СПб), 21 republics, 9 krais, 46 oblasts, 1
autonomous oblast, 4 autonomous okrugs. Pure data + lookups in
`data.json`. **Baseline 100.00** on first run. Agent's job: add
`type` discriminator, `cities` field, federal-district grouping (8
districts), `regionByFederalDistrict` reverse lookup.

```bash
cd examples/regions-ru
python3 eval.py             # baseline: 100.00
# then point an agent at program.md
```

### `examples/chart-of-accounts-ru/` — Russian План счетов (94н)

Faithful Python port of `chartOfAccounts.js` from
[Armosphera/A1-Localization-RU](https://github.com/Armosphera/A1-Localization-RU).
Russian chart of accounts per Приказ Минфина РФ № 94н от 31.10.2000.
**73 accounts** in 9 sections (8 balance-sheet I-VIII + off-balance) +
`data.json` + `sections.json`. Section is determined by **number range**
(01-09=I, 10-19=II, ... 90-99=VIII), not by leading digit like the AM chart.
Off-balance accounts use 3-digit codes (001-011). ХАРАКТЕР (active/passive/
active-passive) maps to normal balance (debit/credit/null). **Baseline
100.00** on first run. Agent's job: sub-accounts (3-level codes like
"01.01"), `sectionOf` via run_workflow, per-section nature rollup.

```bash
cd examples/chart-of-accounts-ru
python3 eval.py             # baseline: 100.00
# then point an agent at program.md
```

### `examples/vat-ru/` — Russian VAT engine (2026 reform)

Faithful Python port of `vat.js` from
[Armosphera/A1-Localization-RU](https://github.com/Armosphera/A1-Localization-RU).
**2026 налоговая реформа:** base rate 20% → 22% (effective 2026-01-01).
Reduced 10% (food/children/medical), 0% (export), УСН 5%/7% for simplified
regime. Year-keyed (2025 back-dated at 20%, 2027+ defaults to 2026).
5 functions: ratesFor, vatFromNet, vatFromGross (settlement rate r/(100+r),
e.g. 22/122), netFromGross, isValidVatRate. **Baseline 100.00** on first
run. Agent's job: `audit` field (per-call trace), `summary` field, batch
rollup, year-aware validators.

```bash
cd examples/vat-ru
python3 eval.py             # baseline: 100.00
# then point an agent at program.md
```

### `examples/settings-store/` — AI settings store

Faithful Python port of `settings-store.js` from
[Armosphera/A1-AI-Core](https://github.com/Armosphera/A1-AI-Core).
Local file-backed AI settings (local-first): the single OpenRouter API key,
the per-aspect model policy, and the opt-in Open Notebook connector. Stored
as JSON with 0600 perms in a product-provided data dir. **5 ops:**
`getSettings`, `updateSettings`, `redactedForClient` (hides secrets for
browser), `resolveModelPolicy` (stored → env default → auto), `defaults`.
The eval creates a fresh tmp dataDir per test case. Each test case is a
**sequence of operations** against a shared dataDir so setup + assertion
are in one self-contained call. **Baseline 100.00** on first run (after a
75→100 fix where the gen script did per-test setup but the eval didn't).
Agent's job: `validateSettings`, `migrateSettings`, `rotateApiKey`,
audit log, encryption at rest.

```bash
cd examples/settings-store
python3 eval.py             # baseline: 100.00
# then point an agent at program.md
```

### `examples/model-catalog/` — OpenRouter model catalog

Faithful Python port of `model-catalog.js` from
[Armosphera/A1-AI-Core](https://github.com/Armosphera/A1-AI-Core). Live
OpenRouter `/models` catalog with injected `safeFetch` + `isEgressAllowed`.
Framework-agnostic. `list_models()` returns `{online, source, reason?, models}`
and **NEVER throws** — degrades to bundled `FALLBACK_MODELS` (5 entries: Claude
3.5 Sonnet, GPT-4o, GPT-4o mini, Gemini Flash 1.5, Llama 3.1 70B). 10 cases
× 7 fields cover egress-blocked, HTTP 200 live, HTTP 500, empty list,
fetch-error, with/without apiKey, custom referer/title, invalid payload,
missing-id model filter. **Baseline 100.00** on first run. Agent's job:
caching with TTL, `filterByContext`, `filterByModality`, `searchModels`.

```bash
cd examples/model-catalog
python3 eval.py             # baseline: 100.00
# then point an agent at program.md
```

### `examples/supplemental-sources/` — Advisory source policy

Faithful Python port of `supplemental.js` from
[Armosphera/A1-AI-Core](https://github.com/Armosphera/A1-AI-Core). Advisory-only
"supplemental sources" policy — e.g. Open Notebook hits shown BESIDE a
product's authoritative citations. Pure (no I/O). Smallest example in the
suite (44 lines JS, ~80 lines Python). Cap (3) / dedupe key (sourceUrl‖title) /
ordering (score desc) / excerpt length (280). **Supplemental sources are
ADVISORY** — never satisfy a required citation gate. **Baseline 100.00** on
first run. Agent's job: sentence-boundary snippet, custom `origin_tag`,
`groupedByOrigin` rollup, PII redaction.

```bash
cd examples/supplemental-sources
python3 eval.py             # baseline: 100.00
# then point an agent at program.md
```

### `examples/open-notebook/` — Open Notebook RAG connector

Faithful Python port of `open-notebook.js` from
[Armosphera/A1-AI-Core](https://github.com/Armosphera/A1-AI-Core). Connector
for lfnovo/open-notebook — opt-in AI source that sits BESIDE a product's
local RAG. **3 ops:** `isEnabled`, `normalizeResults` (tolerates 4 response
shapes: `{results}|{sources}|{data}|array`), `createOpenNotebook` +
`search`. Framework-agnostic: egress-gated `safeFetch` is INJECTED. The
connector is opt-in (only runs when `settings.openNotebook.enabled +
baseUrl` are set), egress-gated, and non-throwing (any failure returns
`[]`). 16 cases × 11 fields cover all 4 normalize shapes, no-text filter,
k-cap, disabled/empty/HTTP200/HTTP500/throws/apiKey/custom searchPath.
**Baseline 100.00** on first run. Agent's job: `summary` field, caching,
`mergeWithLocalRAG`, `searchWithRetry`, `groupByNotebook`.

```bash
cd examples/open-notebook
python3 eval.py             # baseline: 100.00
# then point an agent at program.md
```

### `examples/product-research/` — Autoresearch primitives

**The most meta example** — these are the primitives autoresearch itself
uses. Faithful Python port of `product-research.js` from
[Armosphera/A1-AI-Core](https://github.com/Armosphera/A1-AI-Core). Pure
helpers (no I/O, no shells, no model calls) for rendering the agent
program, comparing fixed-budget eval results, and recording experiment
rows in a stable TSV format. **8 ops:** `normalizeConfig`,
`renderProgram`, `decide` (keep / discard / crash based on metric delta +
complexity delta), `metricDelta`, `extractMetricFromText`, `formatHeader`,
`formatResult`, `parseTsv`. **Baseline 100.00** after a 75→100 fix
(float precision in JS math: 0.6 − 0.5 = 0.0999…; fixed eval to use
approximate float comparison + recursive `_eq` for nested dicts). Agent's
job: `validateConfig` (return errors instead of raising),
`experimentSummary` rollup, `progressVsBudget`, `detectRegression`,
`renderProgramAsYaml`.

```bash
cd examples/product-research
python3 eval.py             # baseline: 100.00
# then point an agent at program.md
```

| `examples/cross-link-sweep/` | **22-file cross-account link sweep** (SamStep74 -> Armosphera mirror) | 22.0000 / 22 | infra score (not business); baseline 15/22 -> sweep -> 22/22 |

## Related

- [karpathy/autoresearch](https://github.com/karpathy/autoresearch) — the original
- [miolini/autoresearch-macos](https://github.com/miolini/autoresearch-macos) — PyTorch + MPS fork
- [trevin-creator/autoresearch-mlx](https://github.com/trevin-creator/autoresearch-mlx) — Apple MLX fork
- [Armosphera/A1-Validator](https://github.com/Armosphera/A1-Validator) — Python port of the 37 business-ID validators; vendors from this repo's `examples/*/`
- [Armosphera/SBOS-A1-ERP](https://github.com/Armosphera/SBOS-A1-ERP) — the sovereign business-ops ERP built on top of these validators
- [A1-Platform](https://github.com/Armosphera/A1-Platform) — the SBOSS product this is built for

## License

MIT
