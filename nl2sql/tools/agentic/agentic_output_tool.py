from __future__ import annotations

from typing import Dict

from google.adk.tools.tool_context import ToolContext

from .agentic_utils import log_tool_output, log_tool_status, set_status


def run_output_tool(tool_context: ToolContext) -> Dict[str, object]:
    """Assemble final JSON output directly from state."""
    answer = tool_context.state.get("answer") or "No answer available."
    plot_config = tool_context.state.get("plot_config") or {
        "type": "none",
        "reason": "plot_config unavailable",
    }
    sql_query = tool_context.state.get("sql_query")
    if not sql_query:
        sql_result = tool_context.state.get("sql_result") or {}
        sql_query = sql_result.get("sql", "")

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
