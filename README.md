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
| `examples/model-policy/` | **A1 model policy resolver** (per-module / per-aspect precedence) | 50.00 / 100 | [samstep74/A1-AI-Core](https://github.com/samstep74/A1-AI-Core) `src/model-policy.js` |

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

## Related

- [karpathy/autoresearch](https://github.com/karpathy/autoresearch) — the original
- [miolini/autoresearch-macos](https://github.com/miolini/autoresearch-macos) — PyTorch + MPS fork
- [trevin-creator/autoresearch-mlx](https://github.com/trevin-creator/autoresearch-mlx) — Apple MLX fork
- [A1-Suite](https://github.com/samstep74/A1-Platform) — the SBOSS product this is built for

## License

MIT
