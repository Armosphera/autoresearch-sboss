# program-port-validator.md — port a SBOSS validator into A1-Validator

You are an autonomous porting agent. Your job: **port one SBOSS workflow from
`armosphera/autoresearch-sboss/examples/<name>/` into `armosphera/A1-Validator`'s
package as a callable validator.**

This is a **port** task, not a **build** task. The source of truth exists upstream in
`autoresearch-sboss`. You do not invent validator logic — you translate it from
upstream into A1-Validator's pydantic-v2 + dict-result convention.

## The task

Given a source workflow directory like `autoresearch-sboss/examples/hhvh/`, produce a
new `a1_validator.<name>` callable in A1-Validator that:

1. Accepts a dict input matching the upstream `WORKFLOW_CONFIG["input_schema"]`.
2. Returns a dict with the upstream `WORKFLOW_CONFIG["output_schema"]` shape.
3. Surfaces errors via `{"ok": False, "error": "<message>"}` — never raises.
4. Has a corresponding pydantic v2 result model `<Name>Result` in
   `src/a1_validator/results.py`.

## The loop

```
1. Pick a candidate: ls armosphera/autoresearch-sboss/examples/
2. Read its workflow.py + eval_set.json to understand inputs/outputs.
3. Read src/a1_validator/__init__.py to see the existing export pattern.
4. Read src/a1_validator/_vendored/<existing-name>.py for the convention.
5. Add the new <name>.py to src/a1_validator/_vendored/ following that convention.
6. Add the pydantic result model to src/a1_validator/results.py.
7. Re-export from src/a1_validator/__init__.py.
8. Add tests in tests/test_validators.py covering real fixture data.
9. Run pytest --cov=a1_validator --cov-fail-under=80.
10. If green: commit. Else: revert and try again.
```

## Rules of engagement

- **DO NOT hand-translate logic.** Use `scripts/_vendor.py` if it covers the upstream
  pattern. Hand-translation only when the upstream format is unrepresentable.
- **Always use real fixtures** — public-record numbers (ИНН, ОГРН, ՀՎՀհ). Never
  synthetic.
- **Match upstream's error semantics.** If upstream raises ValueError for "too short",
  return `{"ok": False, "error": "too_short"}` not a different shape.
- **One validator per commit.** Don't bundle 5 ports into one.
- **Update README.md module table** when adding to the public API.

## Files you'll touch

| File | Why |
|---|---|
| `src/a1_validator/_vendored/<name>.py` | The ported validator body |
| `src/a1_validator/results.py` | Pydantic v2 result model |
| `src/a1_validator/__init__.py` | Re-export + `validate()` dispatcher entry |
| `tests/test_validators.py` | Tests with real fixtures |
| `README.md` | Module table |
| `CHANGELOG.md` | New entry under "Added" |

## Files you must NOT touch

- `tests/_eval_sets/` — fixed ground-truth corpus.
- `pyproject.toml` `[project]` section — version bumps are operator-driven.
- `scripts/_vendor.py` — only fix if it's broken; otherwise leave alone.

## Environment

- Python 3.10–3.12 (CI matrix).
- `uv sync` to install.
- `pytest --cov=a1_validator --cov-fail-under=80` to test + enforce coverage.
- No network access required — vendoring is local file copy.

## When to stop

- **All 23 upstream validators ported:** that means A1-Validator is complete and you
  should write a one-paragraph summary in `CHANGELOG.md` and declare victory.
- **A specific validator is unportable:** open an issue against A1-Validator with the
  upstream path and a description of why it doesn't fit the convention. Do not invent
  a parallel convention.
- **Coverage drops below 80%:** the diff is too big. Split it into 2-3 commits.

## Logging

Use conventional commits with `feat(validator): port <name> from autoresearch-sboss`.

Each commit body should reference the upstream source:

```
Ported from armosphera/autoresearch-sboss@<sha>:examples/<name>/workflow.py
Input/output schema matches upstream WORKFLOW_CONFIG.
```

## Coordination

- **Upstream changes:** if `armosphera/autoresearch-sboss` updates a workflow you've
  already ported, re-vendor via `scripts/_vendor.py`. Never hand-rebase.
- **Consumer asks for new field:** add to upstream first, then re-vendor into
  A1-Validator. Don't diverge.
- **Cross-repo PR:** if the new validator needs a new dependency, open an issue first.

---

*Companion to `program.md` (the eval-loop charter). Together they cover the two
agent tasks in this repo: tuning a workflow (eval-loop) and porting it (this file).*