# program.md — AI settings store research charter

You are an autonomous research agent. Your job: improve `workflow.py` so that the field-level
exact-match F1 score from `eval.py` goes up. You do not edit `eval.py`, `eval_set.json`, or
`pyproject.toml`. You only edit `workflow.py` and append to `results.tsv`.

## The task

The default `workflow.py` is a faithful Python port of
`src/settings-store.js` from
[samstep74/A1-AI-Core](https://github.com/samstep74/A1-AI-Core).
Local file-backed AI settings (local-first): the single OpenRouter API key,
the per-aspect model policy, and the opt-in Open Notebook connector. Stored
as JSON with 0600 perms in a product-provided data dir.

Framework-agnostic: the data-dir, file name, policy keys, and the env default
models are INJECTED via `run_workflow` input. Secrets never leave the server
raw — use `redactedForClient()` for anything sent to a browser.

The current **baseline score is 100.00 / 100** — the JS reference is
correct. Your job is to make the Python implementation **STRICTLY MORE
USEFUL** than the JS reference by adding capabilities the JS lacks.

Your job, in priority order:

1. **Add `validateSettings` method.** Verify stored settings against a schema
   (e.g. `openrouterApiKey` is non-empty string, `models` keys are in `modelKeys`,
   `openNotebook.baseUrl` is valid URL when `enabled: true`).
2. **Add `migrateSettings` method.** Version the settings file (add
   `schemaVersion: 1`) and migrate older schemas forward on load.
3. **Add `rotateApiKey` method.** Atomic key rotation: write new key to a
   temp file, fsync, then rename. Returns the new redacted view.
4. **Add audit log.** Log every read/write to a sibling `ai-settings.audit.json`
   with timestamp + operation + actor. Useful for compliance reviews.
5. **Add encryption at rest.** Optional `encryptionKey` parameter; if set,
   encrypt the API key fields using Fernet (or similar) before write.

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

1. **`validateSettings`** — schema check, return `{ok, errors[]}`.
2. **`migrateSettings`** — version-based migration.
3. **`rotateApiKey`** — atomic rotation with fsync.
4. **Audit log** — sibling JSON file with timestamped operations.
5. **Encryption at rest** — Fernet-based key encryption.

## When to stop

- Score = 100 AND `validateSettings` + `migrateSettings` + audit log all work → done with v0.1.
- 20 experiments with no improvement → consider rewriting `program.md`.

## Logging format for results.tsv

Tab-separated:
`timestamp\tcommit\tstatus\tscore\tbudget_sec\tdescription`

## Environment

This example uses NO LLM. The eval creates a fresh tmp data dir per test case,
runs the workflow, and cleans up after. The workflow uses real file I/O (the
production behavior) so the eval is honest about what ships.

- `EXPERIMENT_BUDGET_SEC` (optional): wall-clock budget. Default `60`.

## Have fun

The point: a Python settings store that's STRICTLY MORE USEFUL than the JS
reference — with schema validation, version migration, audit logging, and
(optionally) encryption at rest. Worst case you revert.
