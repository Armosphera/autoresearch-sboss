"""
workflow.py — Open Notebook (lfnovo/open-notebook) connector.

Faithful Python port of src/open-notebook.js from A1-AI-Core.

Open Notebook is an opt-in AI source that sits BESIDE a product's local RAG.
We connect to a self-hosted instance over its REST API; we never bundle its
Python/SurrealDB runtime.

Framework-agnostic: the egress-gated fetch is INJECTED. The connector is:
  - opt-in     — only runs when settings.openNotebook.enabled + baseUrl are set
  - egress-gated — calls go through the injected safeFetch (loopback ok; remote
                   hosts must be allowlisted by the host product)
  - non-throwing — any failure returns [] so the host retrieval flow is never broken

Returned rows match the common RAG result shape so callers can merge sources.

Source of truth (JS, MIT): https://github.com/samstep74/A1-AI-Core
Corresponding JS file:   src/open-notebook.js
"""

from __future__ import annotations

from typing import Any, Callable

DEFAULT_SEARCH_PATH = "/api/search"


def is_enabled(settings: Any) -> bool:
    """Whether the open-notebook connector is configured + enabled."""
    if not isinstance(settings, dict):
        return False
    on = settings.get("openNotebook")
    if not isinstance(on, dict):
        return False
    return bool(on.get("enabled") and on.get("baseUrl"))


def normalize_results(raw: Any, k: int = 6) -> list[dict]:
    """Tolerate the likely Open Notebook response shapes ({results}|{sources}|{data}|array)."""
    items: list = []
    if isinstance(raw, list):
        items = raw
    elif isinstance(raw, dict):
        for key in ("results", "sources", "data"):
            v = raw.get(key)
            if isinstance(v, list):
                items = v
                break
    out: list[dict] = []
    for it in items[:k]:
        if not isinstance(it, dict):
            continue
        title = str(it.get("title") or it.get("name") or it.get("notebook") or "Open Notebook")
        text = str(it.get("text") or it.get("content") or it.get("snippet") or it.get("chunk") or "")
        if not text:
            continue
        score_raw = it.get("score")
        score = score_raw if isinstance(score_raw, (int, float)) else None
        if score is None:
            rel = it.get("relevance")
            score = rel if isinstance(rel, (int, float)) else 0
        source_url = it.get("url") if isinstance(it.get("url"), str) else (it.get("source_url") if isinstance(it.get("source_url"), str) else "")
        out.append({
            "title": title,
            "text": text,
            "score": score,
            "sourceUrl": source_url,
            "origin": "open-notebook",
        })
    return out


class OpenNotebook:
    def __init__(self, safe_fetch: Callable):
        if not callable(safe_fetch):
            raise TypeError("create_open_notebook requires safe_fetch(url, options, env)")
        self._safe_fetch = safe_fetch

    def search(self, query: str, settings: Any = None, k: int = 6, env: Any = None) -> list[dict]:
        if env is None:
            env = {}
        if not is_enabled(settings):
            return []
        q = str(query or "").strip()
        if not q:
            return []
        on = settings["openNotebook"]
        base = str(on.get("baseUrl") or "").rstrip("/")
        search_path = str(on.get("searchPath") or DEFAULT_SEARCH_PATH)
        url = base + search_path
        try:
            headers: dict[str, str] = {"Content-Type": "application/json"}
            if on.get("apiKey"):
                headers["Authorization"] = f"Bearer {on['apiKey']}"
            res = self._safe_fetch(url, {
                "method": "POST",
                "headers": headers,
                "body": json_dumps({"query": q, "limit": k}),
            }, env)
            if not isinstance(res, dict) or not res.get("ok"):
                return []
            try:
                payload = res["json"]() if callable(res.get("json")) else {}
            except Exception:
                payload = {}
            return normalize_results(payload, k)
        except Exception:
            # Egress-blocked, network, or parse error — degrade silently beside local RAG.
            return []


def json_dumps(obj: Any) -> str:
    import json
    return json.dumps(obj)


def create_open_notebook(safe_fetch: Callable) -> OpenNotebook:
    return OpenNotebook(safe_fetch)


# ===========================================================================
# Autoresearch eval entry point
# ===========================================================================
# eval_set items look like:
#   { "input": {operation, ...args}, "expected": {field: value} }
# Operations: isEnabled, normalizeResults, search.
# Per-case field set.

def run_workflow(input: dict) -> dict:
    o = input or {}
    op = o.get("operation")

    if op == "isEnabled":
        return {"enabled": is_enabled(o.get("settings"))}

    if op == "normalizeResults":
        result = normalize_results(o.get("raw"), o.get("k", 6))
        return {
            "count": len(result),
            "titles": [r["title"] for r in result],
            "texts": [r["text"] for r in result],
            "scores": [r["score"] for r in result],
            "origins": [r["origin"] for r in result],
        }

    if op == "search":
        settings = o.get("settings")
        query = o.get("query", "")
        k = o.get("k", 6)
        safe_fetch_response = o.get("safeFetchResponse")
        safe_fetch_status = o.get("safeFetchStatus", 200)
        safe_fetch_ok = o.get("safeFetchOk", True)
        safe_fetch_throws = bool(o.get("safeFetchThrows", False))
        call_log: dict = {"url": None, "options": None}

        def safe_fetch(url, options, env):
            call_log["url"] = url
            call_log["options"] = options
            if safe_fetch_throws:
                raise RuntimeError("simulated")
            return {"ok": safe_fetch_ok, "status": safe_fetch_status, "json": lambda: safe_fetch_response}

        client = create_open_notebook(safe_fetch)
        result = client.search(query, settings=settings, k=k, env={})

        # Parse body for inspection
        try:
            import json as _json
            body = _json.loads(call_log["options"]["body"]) if call_log["options"] else None
        except Exception:
            body = None

        return {
            "count": len(result),
            "results": result,
            "lastRequestUrl": call_log["url"],
            "lastRequestMethod": (call_log["options"] or {}).get("method"),
            "lastRequestHeaders": (call_log["options"] or {}).get("headers"),
            "lastRequestBody": body,
        }

    return {}
