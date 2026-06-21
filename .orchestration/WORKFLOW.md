# Workflow

This document tracks the active workflows in `autoresearch-sboss` and their
status.

## Active workflows

- **Top-level `workflow.py`** — the canonical SBOSS invoice-extractor workflow
  that the eval loop tunes. Current best score: see `results.tsv` (latest
  `keep` row).

## Workflow instances (one per example)

Each `examples/<name>/` is a self-contained workflow instance. Status:

- [x] `hhvh` — Armenian taxpayer ID (ՀՎՀհ) — DONE upstream
- [x] `inn` — Russian INN/OGRN/OGRNIP/SNILS dispatcher — DONE upstream
- [ ] `mx-rfc` — Mexican RFC (planned)
- [ ] `jp-mynumber` — Japanese My Number (planned)
- [ ] `au-abn` — Australian Business Number (mod-89 check)
- [ ] `gstin` — India GSTIN
- [ ] `swiss-uid` — Swiss UID
- [ ] `us-ein` — US Employer Identification Number
- [ ] `uk-company` — UK Companies House number
- [ ] `cpf` — Brazilian individual taxpayer id (mod-11 DV1+DV2)

(See `examples/` for the full 31+ directory list.)

## Eval loop status

Latest `results.tsv` row determines current state. Read with:

```bash
tail -1 results.tsv
# Or run the Karpathy lane runner:
npm run karpathy:run -- invoice-extractor-contract
```

## Cross-repo plumbing

This repo is consumed by:

- `armosphera/A1-Validator` — ports validators from `examples/<name>/workflow.py`
  into a Python package.
- `armosphera/A1-Suite-Local-{MAX,ANT}` — consume `@a1/ai` from
  `armosphera/A1-AI-Core`, which uses this repo as a runtime example via
  `scripts/karpathy-eval.mjs`.

---

*Companion to `program.md` (eval-loop charter), `program-port-validator.md`
(porting charter), and `docs/ARCHITECTURE.md` (how pieces fit together).*