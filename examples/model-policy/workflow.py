"""
workflow.py — A1 model policy resolver, Python port + extension hooks.

Default implementation is a faithful Python port of src/model-policy.js::resolveModelForRequest()
from @a1/ai (the official SBOSS AI provider core). The agent's job is to extend it:
most importantly, return a `source` field showing which precedence rule fired
(JS only returns the resolved model id; tracking the rule is the agent's first lever).

Source of truth (JS, MIT): https://github.com/samstep74/A1-AI-Core
Corresponding JS file:   src/model-policy.js
Public API:              resolveModelForRequest(policy, ctx) -> string

Precedence rules (highest first):
  1. per-module override  (module ∈ {finance, crm, docs} AND policy[module] non-empty)
  2. per-aspect override  (aspect ∈ {copilot, transform} AND policy[aspect] non-empty)
  3. global default       (policy[default] non-empty)
  4. auto / pick at call time (return "")
"""

from __future__ import annotations

from typing import Any

MODEL_KEYS = ("default", "copilot", "transform", "finance", "crm", "docs")
MODULES = frozenset({"finance", "crm", "docs"})
ASPECTS = frozenset({"copilot", "transform"})


def _pick(policy: dict[str, Any], key: str) -> str:
    """Return policy[key] if it's a non-empty string after trim, else ""."""
    val = policy.get(key) if isinstance(policy, dict) else None
    if isinstance(val, str):
        trimmed = val.strip()
        return trimmed if trimmed else ""
    return ""


def resolve_model(policy: dict[str, Any] | None = None,
                  ctx: dict[str, Any] | None = None) -> str:
    """Faithful port of resolveModelForRequest() from src/model-policy.js.

    Returns the model id (or "" for auto). Does NOT return source/chain.
    """
    if policy is None:
        policy = {}
    if ctx is None:
        ctx = {}
    module = ctx.get("module")
    aspect = ctx.get("aspect")

    if module and module in MODULES:
        m = _pick(policy, module)
        if m:
            return m
    if aspect and aspect in ASPECTS:
        a = _pick(policy, aspect)
        if a:
            return a
    return _pick(policy, "default")


# ---------------------------------------------------------------------------
# run_workflow — the agent-edited adapter for the eval harness.
#
# The JS reference returns ONLY the resolved model id. The agent's job is to
# extend this with a `source` field showing which precedence rule fired:
#   - "module"   if module override matched
#   - "aspect"   if aspect override matched
#   - "default"  if global default matched
#   - "auto"     if everything fell through
# ---------------------------------------------------------------------------

def run_workflow(input_data: dict[str, Any]) -> dict[str, Any]:
    """Adapter for eval.py.

    Input:  { "policy": {default?, copilot?, transform?, finance?, crm?, docs?},
              "ctx":    {module?: str, aspect?: str} }
    Output: { "resolved_model": str, "source": str }
    """
    policy = input_data.get("policy", {})
    ctx = input_data.get("ctx", {})

    # TODO (agent's first lever): add `source` field showing which precedence rule fired.
    resolved = resolve_model(policy, ctx)
    return {"resolved_model": resolved, "source": None}
