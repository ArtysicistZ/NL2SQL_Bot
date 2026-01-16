from __future__ import annotations

import json
import logging
from typing import Dict, List

from google.adk.tools.tool_context import ToolContext

_LOGGER = logging.getLogger("nl2sql.agentic")


def _truncate(value: str, limit: int = 800) -> str:
    if len(value) <= limit:
        return value
    return value[:limit] + "...(truncated)"


def _format_for_log(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, str):
        return _truncate(value)
    try:
        return _truncate(json.dumps(value, ensure_ascii=True, default=str))
    except TypeError:
        return _truncate(str(value))


def log_tool_input(tool_name: str, payload: object) -> None:
    _LOGGER.info("tool_input %s: %s", tool_name, _format_for_log(payload))


def log_tool_output(tool_name: str, payload: object) -> None:
    _LOGGER.info("tool_output %s: %s", tool_name, _format_for_log(payload))


def log_tool_status(tool_name: str, message: str) -> None:
    _LOGGER.info("tool_status %s: %s", tool_name, _truncate(message))


def set_status(
    tool_context: ToolContext,
    key: str,
    status: str,
    message: str,
    refinement: str | None = None,
) -> Dict[str, object]:
    payload: Dict[str, object] = {"status": status, "message": message}
    if refinement:
        payload["refinement"] = refinement
    tool_context.state[key] = payload
    return payload


def state_remove(tool_context: ToolContext, key: str) -> None:
    state = tool_context.state
    try:
        del state[key]
        return
    except Exception:
        pass
    try:
        state[key] = None
    except Exception:
        pass


def state_take(tool_context: ToolContext, key: str):
    state = tool_context.state
    try:
        value = state.get(key)
    except Exception:
        try:
            value = state[key]
        except Exception:
            value = None
    state_remove(tool_context, key)
    return value


def clear_downstream_state(tool_context: ToolContext) -> None:
    for key in (
        "sql_result",
        "sql_query",
        "generated_sql",
        "plot_config",
        "answer",
        "final_response",
        "plot_config_status",
        "answer_status",
        "output_status",
    ):
        state_remove(tool_context, key)


def format_table_schemas(table_schemas: Dict[str, List[Dict[str, str]]]) -> str:
    return json.dumps(table_schemas, ensure_ascii=True)


def format_sql_result(
    sql_result: Dict[str, object],
    max_rows: int = 20,
    include_all_rows: bool = False,
) -> str:
    sql_query = sql_result.get("sql", "")
    result_sets = sql_result.get("result_sets") or []
    if result_sets:
        formatted_sets = []
        for result_set in result_sets:
            rows = result_set.get("rows") or []
            sample_rows = rows if include_all_rows else rows[:max_rows]
            formatted_sets.append(
                {
                    "sql": result_set.get("sql", ""),
                    "columns": result_set.get("columns") or [],
                    "rows": sample_rows,
                    "row_count": result_set.get("row_count", len(rows)),
                    "sample_size": len(sample_rows),
                }
            )
        payload = {
            "sql": sql_query,
            "result_sets": formatted_sets,
        }
        return json.dumps(payload, ensure_ascii=True, default=str)

    columns = sql_result.get("columns") or []
    rows = sql_result.get("rows") or []
    row_count = sql_result.get("row_count", len(rows))
    sample_rows = rows if include_all_rows else rows[:max_rows]
    payload = {
        "sql": sql_query,
        "columns": columns,
        "rows": sample_rows,
        "row_count": row_count,
        "sample_size": len(sample_rows),
    }
    return json.dumps(payload, ensure_ascii=True, default=str)

