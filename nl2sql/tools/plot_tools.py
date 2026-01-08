from __future__ import annotations

import json
from typing import Dict

from google.adk.tools.tool_context import ToolContext


def _parse_plot_config(plot_config: object) -> Dict[str, object] | None:
    if isinstance(plot_config, dict):
        return plot_config
    if isinstance(plot_config, str):
        try:
            parsed = json.loads(plot_config)
        except json.JSONDecodeError:
            return None
        if isinstance(parsed, dict):
            return parsed
    return None


def get_sql_result(tool_context: ToolContext, max_rows: int = 20) -> Dict[str, object]:
    """Fetch the latest SQL result from tool_context.state with optional sampling."""
    result = tool_context.state.get("sql_result")
    if not result:
        return {"status": "error", "error_message": "SQL result not available."}

    columns = result.get("columns") or []
    rows = result.get("rows") or []
    row_count = result.get("row_count", len(rows))
    sql = result.get("sql")
    result_sets = result.get("result_sets") or []
    if result_sets:
        full_sets = []
        for result_set in result_sets:
            set_rows = result_set.get("rows") or []
            full_sets.append(
                {
                    "sql": result_set.get("sql", ""),
                    "columns": result_set.get("columns") or [],
                    "rows": set_rows,
                    "row_count": result_set.get("row_count", len(set_rows)),
                }
            )
        result_sets = full_sets
        primary = result_sets[0]
        columns = primary.get("columns") or columns
        rows = primary.get("rows") or rows
        row_count = primary.get("row_count", len(rows))

    if max_rows is not None and max_rows >= 0:
        rows = rows[:max_rows]

    sampled = len(rows) < row_count

    payload = {
        "status": "success",
        "sql": sql,
        "columns": columns,
        "rows": rows,
        "row_count": row_count,
        "sampled": sampled,
        "sample_size": len(rows),
    }
    if result_sets:
        payload["result_sets"] = result_sets
    return payload


def save_plot_config(plot_config: object, tool_context: ToolContext) -> Dict[str, object]:
    """Persist plot_config JSON in tool_context.state for downstream agents."""
    parsed = _parse_plot_config(plot_config)
    if not parsed:
        return {"status": "error", "error_message": "Invalid plot_config JSON."}
    if not parsed.get("type"):
        return {"status": "error", "error_message": "plot_config missing 'type'."}
    tool_context.state["plot_config"] = parsed
    return {"status": "success", "plot_config": parsed}


def get_plot_config(tool_context: ToolContext) -> Dict[str, object]:
    """Return the latest plot_config JSON from tool_context.state."""
    plot_config = tool_context.state.get("plot_config")
    if not plot_config:
        return {"status": "error", "error_message": "plot_config not available."}
    return {"status": "success", "plot_config": plot_config}
