# Architecture

This document describes the structural pattern that `autoresearch-sboss` uses to run
autonomous keep-or-revert research loops over SBOSS sovereign business workflows.

It is **not** an agent charter — for "what to do" read
[`program.md`](../program.md) (eval-loop charter) and
[`program-port-validator.md`](../program-port-validator.md) (validator-port charter).
This file explains **how the pieces fit together**.

---

## 1. The eval-loop pattern

The repo is built around a small, repeated shape:

```
┌──────────────────────────────────────────────────────────────┐
│  agent (Claude Code / Codex / any LLM agent)                 │
│                                                              │
│  1. read results.tsv  →  current best score                  │
│  2. read workflow.py  →  current state                       │
│  3. make ONE hypothesis edit                                │
│  4. run uv run eval.py                                       │
│  5. if new_score > best_score  →  commit ("score: N — …")    │
│     else                      →  git checkout workflow.py   │
│  6. append row to results.tsv                                │
│  7. repeat                                                   │
└──────────────────────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────┐
│  fixed judge (eval.py + eval_set.json)                       │
│  - reads workflow.py dynamically                             │
│  - runs run_workflow(input, WORKFLOW_CONFIG) per item        │
│  - computes field-level exact-match F1                       │
│  - prints: score: N.NNNN  elapsed: X.Xs  n_items: N  …       │
└──────────────────────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────┐
│  results.tsv — append-only experiment log                    │
│  timestamp  commit  status  score  budget_sec  description   │
└──────────────────────────────────────────────────────────────┘
```

Three properties make the loop robust:

1. **The judge is fixed.** `eval.py` and `eval_set.json` are off-limits to the agent.
   This is the same invariant as Karpathy's original `train.py` + `val_bpb`: the
   metric can't drift under the optimizer.
2. **The agent's surface is one file.** `workflow.py` exposes
   `WORKFLOW_CONFIG` (prompt template + LLM params) and `run_workflow()` (the
   body). That's it. Diffs stay reviewable.
3. **Wall-clock budget per experiment.** `EXPERIMENT_BUDGET_SEC` (default 60)
   makes results comparable across experiments regardless of what changed.
   An experiment that overruns is invalid and must be reverted.

## 2. Workflow instances

The repo is a **harness** that hosts many independent workflow targets. The same
3-file shape appears at the top level (the default `invoice-extractor-contract`)
and inside every `examples/<name>/`:

```
workflow.py        — agent's lever (do not touch the eval harness)
eval.py            — fixed: scoring
eval_set.json      — fixed: ground truth
results.tsv        — append-only log
program.md         — per-workflow research charter
```

The top-level pair (`eval.py` + `eval_set.json`) tunes a single business workflow —
**invoice-field extraction** — and ships as the default `npm run karpathy:program --
invoice-extractor-contract` lane.

Each `examples/<name>/` is a **separate** workflow target with its own copy of
`eval.py` / `eval_set.json` / `results.tsv` / `workflow.py`. They never share
state, never compete on the same eval set, and never write to each other's TSV.

| Scale | Files | Eval-set scope |
|---|---|---|
| Top-level invoice extractor | 1 | One shared 20-item set |
| Per-example workflow | 31 | Self-contained, per-example fixtures |

## 3. Two agent charters, one harness

There are exactly two ways an AI agent interacts with this repo:

| Charter | Task | Loop | Edit surface |
|---|---|---|---|
| [`program.md`](../program.md) | **Tune** a SBOSS workflow | edit → eval → keep/revert → log | `workflow.py` + `results.tsv` |
| [`program-port-validator.md`](../program-port-validator.md) | **Port** an upstream validator into a downstream package | read upstream → translate to convention → test → commit | one new validator file + tests + re-export |

The two charters never run on the same commit. The eval-loop charter only edits
`workflow.py`; the porting charter only adds files under `examples/<name>/` (and
in the downstream `A1-Validator` repo, never here). They share the harness shape
but own different surfaces.

## 4. Why this is portable

The eval-loop is **workflow-agnostic**. To point the harness at a new SBOSS
workflow:

1. Replace `eval_set.json` with the new fixtures + ground truth.
2. Replace `workflow.py` with `WORKFLOW_CONFIG` + `run_workflow()` for the new task.
3. Replace `program.md` with a new charter naming the new metric.

The harness — `eval.py`, the score function, the time budget, the keep/revert
discipline, the TSV log format — stays the same. This is the same portability
the original Karpathy autoresearch has: the loop is the product, the experiment
is configurable.

## 5. Cross-repo plumbing

`autoresearch-sboss` does not run in isolation. Two external hooks are wired in:

- **Karpathy shared runner.** `npm run karpathy:*` commands route through
  `scripts/karpathy-eval.mjs`, which uses a cached clone of
  `Armosphera/A1-AI-Core` (pinned commit, override via `A1_AI_CORE_CACHE_DIR` or
  `A1_AI_CORE_PATH`). This is what makes `invoice-extractor-contract` resolvable
  by the shared product-research runner.
- **Validator-porting flow.** `program-port-validator.md` declares
  `armosphera/A1-Validator` as the downstream package. The porting charter lives
  in **this** repo as a contract; the downstream repo hosts the actual
  vendored validators, pydantic result models, and test coverage gate
  (`pytest --cov=a1_validator --cov-fail-under=80`).

## 6. File inventory

| Path | Mutable? | Purpose |
|---|---|---|
| `eval.py` | **no** (fixed judge) | Eval harness + scoring |
| `eval_set.json` | **no** (ground truth) | Sample invoices with expected output |
| `workflow.py` | yes (agent's lever) | `WORKFLOW_CONFIG` + `run_workflow()` |
| `program.md` | yes (human iterates) | Eval-loop agent charter |
| `program-port-validator.md` | yes (human iterates) | Validator-port agent charter |
| `results.tsv` | yes (append-only) | Experiment log |
| `examples/<name>/` | per-example | Self-contained workflow targets |
| `evals/karpathy/` | yes | Karpathy shared-runner contract fixtures |
| `scripts/` | yes | Node-side orchestration scripts |
| `docs/` | yes | Architecture + human-facing reference |

## 7. What this document is not

- **Not a charter.** For "what should the agent do", read `program.md`.
- **Not a porting guide.** For "how do I port a validator", read
  `program-port-validator.md`.
- **Not an API reference.** `eval.py` and `workflow.py` are the API.

If you find yourself wanting to change the keep/revert rule, the scoring
formula, or the agent's edit surface — that's a charter change, not an
architecture change, and belongs in `program.md`.