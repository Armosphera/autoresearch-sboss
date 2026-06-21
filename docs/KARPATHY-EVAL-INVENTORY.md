# Karpathy Eval Lane Inventory

**Effective:** 2026-06-21
**Owner:** Armosphera LLC

This document is the **canonical inventory** of all Karpathy eval lanes across
the A1 portfolio. For each repo, it lists the lanes under `evals/karpathy/`,
the contract specs, and the check scripts.

## TL;DR — every repo has at least one Karpathy lane

| Repo | Public? | Lanes | Lane files | Check script |
|---|---|---|---|---|
| `autoresearch-sboss` | ✅ | 1 + 33 sub-examples | `evals/karpathy/invoice-extractor-contract.json` + `examples/*/eval.py` (33 of them) | `scripts/check-invoice-extractor-contract.mjs` + `examples/*/eval.py` (regression gate via CI `sub-examples-eval` job) |
| `A1-Validator` | ✅ | 0 | — | (no Karpathy runner yet — uses pytest) |
| `A1-Localization-AM` | ✅ | 1 | `evals/karpathy/vat-return-contract.json` | `scripts/check-vat-return-contract.mjs` |
| `A1-Localization-RU` | ✅ | 1 | `evals/karpathy/vat-einvoice-contract.json` | `scripts/check-vat-einvoice-contract.mjs` |
| `A1-AI-Core` | ✅ | 2 (Wave 4+6) | `evals/di-contract-frozen/`, `evals/fallback-models-stability/` (NOT under `evals/karpathy/`) | inline check.js |
| `A1-portfolio` | ✅ | 0 (portfolio-drift is at repo root) | `scripts/check-portfolio-drift.js` | (drift check, not lane) |
| `A1-Suite-Local-ANT` | private | 1 | `evals/karpathy/egress-policy-contract.json` | `scripts/check-egress-policy-contract.mjs` |
| `A1-Suite-Local-MAX` | private | 7 | `ap-billing-agent.json`, `finance-close-agent.json`, `finance-close-api.json`, `helpdesk-triage-agent.json`, `inventory-reorder-agent.json`, `payroll-agent.json`, `shell-health.json` | inline check scripts |
| `A1-AI-ERP-SBOS-MSTUDIO-sovereign` | private | 1 | `evals/karpathy/sovereignty-contract.json` | `scripts/check-sovereignty-contract.mjs` |
| `SBOS-A1-ERP` | private | 1 | `evals/karpathy/open-core-boundary-contract.json` | `scripts/check-open-core-boundary-contract.mjs` |

**Total: 13+ Karpathy lanes across 8 repos.**

## How a Karpathy lane works

Each lane is a self-contained contract:

1. **Contract spec** (`evals/karpathy/<lane>.json`) — JSON describing:
   - `id`, `productName`, `runTag`, `branchPrefix`
   - `editableFiles` — what the agent is allowed to modify
   - `readOnlyFiles` — what is fixed
   - `contextFiles` — what the agent should read
   - `guardrails` — explicit constraints (e.g. "do not log API keys")
   - `eval` — command, args, metric, expected score

2. **Check script** (`scripts/check-<lane>.mjs` or inline) — runs the
   contract's `eval` against current repo state. Exit 0 = pass.

3. **Lane runner** (`scripts/karpathy-eval.mjs`) — generic Node.js runner that
   discovers lanes via `evals/karpathy/*.json`, runs each check script,
   returns aggregate pass/fail.

## What each lane locks

| Lane | Locks |
|---|---|
| `invoice-extractor-contract` (autoresearch-sboss) | Workflow edits improve business score on `eval_set.json` |
| `vat-return-contract` (AM) | Armenian VAT return cross-foot tie-out |
| `vat-einvoice-contract` (RU) | Russian УПД format 5.03 structural validity |
| `di-contract-frozen` (A1-AI-Core, Wave 4) | `@a1/ai` createAi() signature + module.exports |
| `fallback-models-stability` (A1-AI-Core, Wave 6) | `FALLBACK_MODELS` constant in `src/model-policy.js` |
| `egress-policy-contract` (ANT) | Sovereignty posture (egress OFF by default) |
| 7 lanes in MAX | App-level contracts (billing, finance-close, helpdesk, etc.) |
| `sovereignty-contract` (sovereign) | Air-gapped SBOSS sovereignty posture |
| `open-core-boundary-contract` (SBOS-A1-ERP) | Brand-neutral distribution (no HayHashvapah identifiers) |

## Why some repos have lanes under different paths

Two conventions coexist:

- **Traditional:** `evals/karpathy/<lane>.json` + `scripts/check-<lane>.mjs` + `scripts/karpathy-eval.mjs`
  (used by autoresearch-sboss, A1-Localization-{AM,RU}, A1-Suite-Local-{ANT,MAX}, sovereign, SBOS-A1-ERP)
- **Inline:** `evals/<lane>/check.js` + `evals/<lane>/program.md` + `evals/<lane>/lane.json`
  (used by A1-AI-Core, where I added `di-contract-frozen` and `fallback-models-stability` in Wave 4+6)

Both are valid. The first is older (Karpathy convention from upstream);
the second is what I used for AST-based checks that needed more per-lane docs.

A future cleanup could unify them, but **not required** — both work.

## How to add a new lane

For a new repo:

1. Create `evals/karpathy/<lane>.json` (or `evals/<lane>/lane.json` for inline-style).
2. Create `scripts/check-<lane>.mjs` (or `evals/<lane>/check.js` for inline).
3. If using the traditional convention, ensure `scripts/karpathy-eval.mjs`
   picks up the new lane (it auto-discovers via `evals/karpathy/*.json` glob).
4. Add the lane to CI: `npm run karpathy:run -- <lane-id>` or
   `node evals/<lane>/check.js`.
5. Add the lane to this inventory (Karpathy-Eval-Lane-Inventory.md).

## Cross-references

- [`CONTRIBUTING.md`](./CONTRIBUTING.md) — how to contribute (per-repo)
- [`REPO-TEMPLATE.md`](./REPO-TEMPLATE.md) — how to add a new repo
- [`CROSS-REPO-COORDINATION.md`](./CROSS-REPO-COORDINATION.md) — recipes for cross-repo changes

---

*This file is the canonical inventory. Update it when lanes are added or removed.*