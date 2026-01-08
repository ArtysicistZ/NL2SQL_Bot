from __future__ import annotations

import json
from typing import Dict

from google.adk.tools.tool_context import ToolContext


def _coerce_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=True)
    except TypeError:
        return str(value)


def request_sql_retry(reason: str, tool_context: ToolContext, source: str | None = None) -> Dict[str, object]:
    """Record a request to rerun the SQL tool with a refinement."""
    if isinstance(reason, str):
        cleaned = reason.strip()
    elif reason is None:
        cleaned = ""
    else:
        try:
            cleaned = json.dumps(reason, ensure_ascii=True)
        except TypeError:
            cleaned = str(reason)
        cleaned = cleaned.strip()
    if not cleaned:
        return {"status": "error", "error_message": "Missing retry reason."}
    source_cleaned = _coerce_text(source).strip() or "unknown"
    tool_context.state["sql_retry_request"] = {
        "reason": cleaned,
        "source": source_cleaned,
    }
    return {"status": "success", "reason": cleaned}
