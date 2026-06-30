from __future__ import annotations

from typing import Dict

from google.adk.tools.tool_context import ToolContext

from ..plot_tools import (
    _primary_columns_rows,
    derive_plot_config,
    is_renderable_plot_config,
)
from .agentic_utils import log_tool_output, log_tool_status, set_status


def run_output_tool(tool_context: ToolContext) -> Dict[str, object]:
    """Assemble final JSON output directly from state."""
    answer = tool_context.state.get("answer") or "No answer available."

    # Final guarantee: a renderable plot_config must always be present, no matter
    # which path got us here (agent failure, exhausted SQL retries, mismatched
    # axis fields). Derive one deterministically from the SQL result if needed.
    sql_result = tool_context.state.get("sql_result")
    plot_config = tool_context.state.get("plot_config")
    columns, _ = _primary_columns_rows(sql_result) if sql_result else ([], [])
    if not is_renderable_plot_config(plot_config, columns):
        plot_config = derive_plot_config(sql_result)
        tool_context.state["plot_config"] = plot_config

    sql_query = tool_context.state.get("sql_query")
    if not sql_query:
        sql_query = (sql_result or {}).get("sql", "")

    final_response = {
        "answer": answer,
        "plot_config": plot_config,
        "sql": sql_query or "",
    }
    tool_context.state["final_response"] = final_response

    missing = []
    if not tool_context.state.get("answer"):
        missing.append("answer")
    if not tool_context.state.get("plot_config"):
        missing.append("plot_config")
    if not sql_query:
        missing.append("sql_query")

    message = "Output assembled."
    if missing:
        message = f"Output assembled with defaults (missing: {', '.join(missing)})."

    status_payload = set_status(tool_context, "output_status", "success", message)
    log_tool_status("run_output_tool", message)
    log_tool_output("run_output_tool", status_payload)
    return final_response
