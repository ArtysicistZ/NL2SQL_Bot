from __future__ import annotations

from typing import Dict

from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.tool_context import ToolContext

from ...agents.plot_config_agent import plot_config_agent
from .agentic_utils import (
    log_tool_input,
    log_tool_output,
    log_tool_status,
    set_status,
    state_remove,
    state_take,
)

_PLOT_CONFIG_TOOL = AgentTool(plot_config_agent)


async def run_plot_config_agent_tool(
    question: str,
    tool_context: ToolContext,
    refinement: str | None = None,
) -> Dict[str, object]:
    """Call plot_config_agent with SQL query loaded from state."""
    state_remove(tool_context, "plot_config")
    state_remove(tool_context, "plot_config_status")
    state_remove(tool_context, "sql_retry_request")

    sql_result = tool_context.state.get("sql_result")
    if not sql_result or sql_result.get("status") != "success":
        message = "SQL result missing or failed."
        log_tool_status(
            "run_plot_config_agent_tool",
            f"needs_retry: sql_result_status={getattr(sql_result, 'get', lambda *_: None)('status')}",
        )
        return set_status(
            tool_context,
            "plot_config_status",
            "needs_retry",
            message,
            refinement="Rerun SQL with correct table/filters so plotting can proceed.",
        )

    sql_query = tool_context.state.get("sql_query") or sql_result.get("sql", "")
    result_sets = sql_result.get("result_sets") or []
    log_tool_status(
        "run_plot_config_agent_tool",
        f"sql_result_ok: result_sets={len(result_sets)} rows_per_set="
        f"{[len(rs.get('rows') or []) for rs in result_sets]}",
    )
    request_parts = [
        f"User question: {question}",
        f"Refinement: {refinement or ''}",
        f"SQL query: {sql_query}",
    ]
    request = "\n".join(request_parts)
    log_tool_input("plot_config_agent", request)

    try:
        response = await _PLOT_CONFIG_TOOL.run_async(
            args={"request": request},
            tool_context=tool_context,
        )
        log_tool_output("plot_config_agent", response)
    except Exception as exc:
        message = f"Plot config agent failed: {exc}"
        tool_context.state["last_error"] = message
        log_tool_status("run_plot_config_agent_tool", message)
        return set_status(tool_context, "plot_config_status", "error", message)

    retry_request = state_take(tool_context, "sql_retry_request")
    if retry_request:
        reason = retry_request.get("reason", "Plot config requested SQL retry.")
        log_tool_status(
            "run_plot_config_agent_tool",
            f"needs_retry: plot_agent_requested reason={reason}",
        )
        return set_status(
            tool_context,
            "plot_config_status",
            "needs_retry",
            "Plot config requested SQL retry.",
            refinement=reason,
        )

    plot_config = tool_context.state.get("plot_config")
    if not plot_config:
        message = "plot_config not available after agent run."
        tool_context.state["last_error"] = message
        log_tool_status("run_plot_config_agent_tool", message)
        return set_status(tool_context, "plot_config_status", "error", message)

    status_payload = set_status(
        tool_context,
        "plot_config_status",
        "success",
        "Plot config saved.",
    )
    log_tool_output("run_plot_config_agent_tool", status_payload)
    return status_payload
