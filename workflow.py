"""
workflow.py — the SBOSS workflow being tuned.

This file is the agent's lever. The agent (Claude Code, Codex, Mavis, etc.) reads this file,
makes a focused change, runs eval.py, and either commits (improvement) or reverts (no help).

By default this is a deterministic mock extractor using regex. To use a real LLM:
1. Set LLM_ENDPOINT_URL, LLM_API_KEY, LLM_MODEL env vars.
2. Replace the body of `run_workflow()` to call the LLM via httpx (the httpx dep is in
   pyproject.toml). The mock call below shows the OpenAI chat-completions shape.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

# ---------------------------------------------------------------------------
# WORKFLOW_CONFIG — the agent's primary tuning surface.
# ---------------------------------------------------------------------------

WORKFLOW_CONFIG: dict[str, Any] = {
    "name": "invoice-extractor-v1",
    "system_prompt": (
        "You are a precise invoice-field extractor. "
        "Given noisy invoice text, output ONLY a JSON object with these exact keys: "
        "vendor_name (string), invoice_date (ISO YYYY-MM-DD), total_amount (number, no currency), "
        "currency (ISO 4217 code like USD, EUR, AMD, RUB), tax_id (string). "
        "Do not include any prose, commentary, or markdown fences. JSON only."
    ),
    "user_template": (
        "Extract the structured fields from this invoice:\n\n"
        "----\n{document}\n----\n\n"
        "Return the JSON object now."
    ),
    "examples": [
        # Few-shot examples the agent can edit. Each is (input_document, expected_output).
        {
            "document": "ACME Corp\nInvoice #1234\nDate: 2025-03-15\nTotal: $1,250.00 USD\nTax ID: 12-3456789",
            "output": {
                "vendor_name": "ACME Corp",
                "invoice_date": "2025-03-15",
                "total_amount": 1250.00,
                "currency": "USD",
                "tax_id": "12-3456789",
            },
        },
    ],
    "temperature": 0.0,
    "max_tokens": 400,
    # If true, the harness pre-processes the document (strips HTML, normalizes whitespace).
    "preprocess_document": True,
    # If true, the harness retries once on malformed JSON.
    "retry_on_parse_error": True,
}


# ---------------------------------------------------------------------------
# run_workflow — execute the workflow on one input. Agent can rewrite freely.
# ---------------------------------------------------------------------------

def run_workflow(input_data: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run the SBOSS workflow on one input document. Returns a dict of extracted fields.

    Args:
        input_data: {"document": "<raw invoice text>"}
        config: override of WORKFLOW_CONFIG (defaults to module-level)

    Returns:
        Dict with keys: vendor_name, invoice_date, total_amount, currency, tax_id.
        Missing fields should be set to None.
    """
    cfg = config if config is not None else WORKFLOW_CONFIG
    document = input_data.get("document", "")

    if cfg.get("preprocess_document", False):
        document = _preprocess(document)

    endpoint = os.environ.get("LLM_ENDPOINT_URL", "").strip()
    if endpoint:
        return _run_with_llm(document, cfg, endpoint)
    return _run_with_mock(document)


# ---------------------------------------------------------------------------
# Pre-processing
# ---------------------------------------------------------------------------

def _preprocess(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)               # strip HTML tags
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Mock extractor (default, no API key needed).
# Deterministic regex-based extraction. Intentionally mediocre — the agent's
# job is to tune WORKFLOW_CONFIG / rewrite run_workflow to beat the baseline.
# ---------------------------------------------------------------------------

_RE_DATE_ISO = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
_RE_DATE_SLASH = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b")
_RE_DATE_DOT_EU = re.compile(r"\b(\d{1,2})\.(\d{1,2})\.(\d{2,4})\b")
_RE_AMOUNT = re.compile(r"(?:total|amount|sum|итого|всего)\s*[:\-]?\s*([0-9][0-9,\.\s]*)", re.IGNORECASE)
_RE_AMOUNT_BARE = re.compile(r"\$\s*([0-9][0-9,\.]*)|([0-9][0-9,\.]*)\s*\$")
_RE_AMOUNT_RUB = re.compile(r"([0-9][0-9,\.\s]*)\s*(?:руб|RUB|р\.)", re.IGNORECASE)
_RE_AMOUNT_AMD = re.compile(r"([0-9][0-9,\.\s]*)\s*(?:драм|AMD|֏)", re.IGNORECASE)
_RE_CURRENCY = re.compile(r"\b(USD|EUR|RUB|AMD|GBP|JPY|CNY|драм|руб)\b", re.IGNORECASE)
_RE_TAX_ID = re.compile(r"(?:tax\s*id|vat\s*id|inn|hhvh|հվհհ|инн)\s*[:\-]?\s*([A-Z0-9\-]{4,})", re.IGNORECASE)
_RE_VENDOR_LINE = re.compile(r"^([A-Z][A-Za-z0-9\.\-& ]{2,40}(?:LLC|Ltd|Inc|Corp|Corp\.|ООО|ЗАО|ИП|ԱՁ|ՓԲԸ|ԲԸ)?)\s*$", re.MULTILINE)


def _run_with_mock(document: str) -> dict[str, Any]:
    out: dict[str, Any] = {
        "vendor_name": None,
        "invoice_date": None,
        "total_amount": None,
        "currency": None,
        "tax_id": None,
    }

    # Vendor: first ALL-CAPS-ish line near the top.
    for line in document.splitlines()[:6]:
        m = _RE_VENDOR_LINE.match(line.strip())
        if m:
            out["vendor_name"] = m.group(1).strip()
            break

    # Date: prefer ISO, fall back to slash / dot.
    m = _RE_DATE_ISO.search(document)
    if m:
        out["invoice_date"] = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    else:
        m = _RE_DATE_SLASH.search(document)
        if m:
            yy = m.group(3)
            if len(yy) == 2:
                yy = "20" + yy
            out["invoice_date"] = f"{yy}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
        else:
            m = _RE_DATE_DOT_EU.search(document)
            if m:
                yy = m.group(3)
                if len(yy) == 2:
                    yy = "20" + yy
                out["invoice_date"] = f"{yy}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"

    # Currency + amount (try labeled first, then currency-symbol based).
    cur = _RE_CURRENCY.search(document)
    if cur:
        c = cur.group(1).upper()
        c_map = {"ДРАМ": "AMD", "РУБ": "RUB"}
        out["currency"] = c_map.get(c, c)

    amount = None
    m = _RE_AMOUNT.search(document)
    if m:
        amount = m.group(1)
    else:
        m = _RE_AMOUNT_BARE.search(document)
        if m:
            amount = m.group(1) or m.group(2)
        else:
            m = _RE_AMOUNT_RUB.search(document)
            if m:
                amount = m.group(1)
                if out["currency"] is None:
                    out["currency"] = "RUB"
            else:
                m = _RE_AMOUNT_AMD.search(document)
                if m:
                    amount = m.group(1)
                    if out["currency"] is None:
                        out["currency"] = "AMD"
    if amount is not None:
        try:
            out["total_amount"] = float(amount.replace(",", "").replace(" ", ""))
        except ValueError:
            pass

    m = _RE_TAX_ID.search(document)
    if m:
        out["tax_id"] = m.group(1).strip()

    return out


# ---------------------------------------------------------------------------
# Real LLM runner (httpx). Opt-in via LLM_ENDPOINT_URL.
# ---------------------------------------------------------------------------

def _run_with_llm(document: str, cfg: dict[str, Any], endpoint: str) -> dict[str, Any]:
    import httpx

    api_key = os.environ.get("LLM_API_KEY", "")
    model = os.environ.get("LLM_MODEL", "openrouter/auto")

    messages: list[dict[str, Any]] = [{"role": "system", "content": cfg["system_prompt"]}]
    for ex in cfg.get("examples", []):
        messages.append({"role": "user", "content": ex["document"]})
        messages.append({"role": "assistant", "content": json.dumps(ex["output"], ensure_ascii=False)})
    messages.append({"role": "user", "content": cfg["user_template"].format(document=document)})

    payload = {
        "model": model,
        "messages": messages,
        "temperature": cfg.get("temperature", 0.0),
        "max_tokens": cfg.get("max_tokens", 400),
    }
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    headers["Content-Type"] = "application/json"

    resp = httpx.post(endpoint, json=payload, headers=headers, timeout=30.0)
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"]

    if cfg.get("retry_on_parse_error", True):
        try:
            return _parse_json(content)
        except (ValueError, KeyError):
            # one retry, slightly more insistent
            payload["messages"].append({"role": "user", "content": "Your last reply was not valid JSON. Reply with JSON only, no fences, no commentary."})
            resp = httpx.post(endpoint, json=payload, headers=headers, timeout=30.0)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
    return _parse_json(content)


def _parse_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```\s*$", "", text)
    return json.loads(text)
