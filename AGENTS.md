# AGENTS.md — autoresearch-sboss

This file applies to every agent (human or AI) that touches the
`armosphera/autoresearch-sboss` repository. It extends, and never weakens, the
global rules in `https://github.com/Armosphera/A1-portfolio/blob/main/LICENSING.md`.

## 1. What this repo is

`autoresearch-sboss` is the **reference eval-loop harness** for SBOSS sovereign
business workflows. MIT-licensed, ported into `A1-Validator`.

Each agent task is governed by one of two charters:

- `program.md` — the eval-loop charter (tune `workflow.py` against `eval.py`)
- `program-port-validator.md` — the validator-port charter (port a workflow
  from `examples/<name>/` into `A1-Validator`)

For "how the pieces fit together" read `docs/ARCHITECTURE.md`.
For "what to actually do" read the appropriate `program*.md`.

## 2. The 3 files you must NOT touch

- **`eval.py`** — fixed eval harness. The judge. Editing it is cheating.
- **`eval_set.json`** — fixed ground-truth corpus. Editing it is cheating.
- **`pyproject.toml` `[project]` section** — package metadata. Bumps are
  operator-driven (release cut), not agent-driven.

You may touch:

- `workflow.py` — the agent's lever (only when running `program.md`)
- `results.tsv` — append-only experiment ledger
- `examples/<name>/workflow.py` — when running `program-port-validator.md`

## 3. Workflow — TDD is N/A (research loop)

This repo is a **research loop**, not a TDD repo. The loop is:

```
1. Read results.tsv → current best score
2. Read workflow.py → current state
3. Make ONE focused change (red hypothesis)
4. Run: uv run eval.py
5. If new_score > best_score → commit (one focused change)
   Else                     → git checkout workflow.py (revert)
6. Append row to results.tsv
7. Repeat
```

**One hypothesis per experiment.** Don't bundle 5 unrelated changes.

## 4. Conventions

- **Conventional commits:** `score: <N.NNN> — <one-line hypothesis>`
  inside the eval loop. `feat(<area>):` / `fix:` / `docs:` for repo-level changes.
- **`uv run eval.py`** for evaluation. No `python eval.py` directly.
- **EXPERIMENT_BUDGET_SEC** default 60s. Override only if eval run exceeds
  budget — but then the score is invalid, revert.
- **Real fixtures** in `eval_set.json` — never synthetic.
- **One validator per commit** when porting. Don't bundle 5 ports.

## 5. The example-per-validator pattern

`examples/` contains 31+ subdirectories, each a self-contained workflow
example:

```
examples/
  hhvh/                  # Armenian taxpayer ID (ՀՎՀՀ)
    workflow.py          # The lever
    eval_set.json        # The ground truth
    results.tsv          # The ledger
  inn/                   # Russian INN/OGRN/OGRNIP/SNILS dispatcher
  ...
```

The **top-level** `workflow.py` is a "best-of" — the canonical SBOSS workflow
that the eval loop tunes. Subdirectories in `examples/` are alternatives.

When porting via `program-port-validator.md`, the upstream is the
**top-level** `workflow.py` (or a specific `examples/<name>/` if the upstream
agent wants a specific feature).

## 6. No debug noise

- `print()` is for development only.
- `breakpoint()` and `pdb.set_trace()` are forbidden in committed code.
- Comments describing past failures are OK if useful — but **delete them once
  the fix lands**.

## 7. Cross-repo plumbing

This repo's eval loop is driven by the shared `scripts/karpathy-eval.mjs` from
downstream consumers (`A1-Suite-Local-ANT`, `A1-Suite-Local-MAX`, etc.). When
running Karpathy evals, the `A1_AI_CORE_CACHE_DIR` env var points to where
`armosphera/A1-AI-Core` is cloned for the agent primitive.

Pin the `@a1/ai` SHA per `A1-AI-Core/AGENTS.md` §"Consumer bump checklist" when
bumping. As of Wave 4+5: pinned to `cec47006` (Wave 4 base), `f917e8a1` (Wave 5
fix), and `a6be1e8` (Wave 6 fallback-models lane).

## 8. Day-One Checklist

```
1. cat AGENTS.md             # this file
2. cat program.md             # eval-loop charter (or program-port-validator.md)
3. cat docs/ARCHITECTURE.md   # how the pieces fit together
4. ls examples/              # see what validators exist
5. uv sync                   # install dependencies
6. uv run eval.py            # confirm baseline works
7. Now you can edit.
```

If `uv run eval.py` baseline fails: STOP, file an issue. Do not edit around a
broken baseline.

## 9. What this repo is NOT

- **Not** a deterministic validator — it's a harness for *finding* good
  validators. Deterministic validation lives in `A1-Validator`.
- **Not** a production codebase — it's a research artifact. Quality of
  `workflow.py` matters less than quality of the *findings* logged in
  `results.tsv`.
- **Not** sovereign-AI product code — for that, see `A1-Suite-Local-{MAX,ANT}`.

---

*Adapted from `armosphera/SBOS-A1-ERP/AGENTS.md`. Specializes for: research-loop
discipline, 3-protected-files rule, examples-vs-top-level pattern.*
*License: MIT. See `LICENSE`.*