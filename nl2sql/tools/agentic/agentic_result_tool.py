from __future__ import annotations

from typing import Dict

from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.tool_context import ToolContext

from ...agents.result_interpreter_agent import result_interpreter_agent
from .agentic_utils import (
    format_sql_result,
    log_tool_input,
    log_tool_output,
    log_tool_status,
    set_status,
    state_remove,
)

_RESULT_INTERPRETER_TOOL = AgentTool(result_interpreter_agent)


async def run_result_interpreter_agent_tool(
    question: str,
    tool_context: ToolContext,
    refinement: str | None = None,
) -> Dict[str, object]:
    """Call result_interpreter_agent with SQL results loaded from state."""
    state_remove(tool_context, "answer")
    state_remove(tool_context, "answer_status")
    state_remove(tool_context, "sql_retry_request")

    sql_result = tool_context.state.get("sql_result")
    if not sql_result or sql_result.get("status") != "success":
        message = "SQL result missing or failed."
        log_tool_status("run_result_interpreter_agent_tool", message)
        return set_status(
            tool_context,
            "answer_status",
            "needs_retry",
            message,
            refinement="Rerun SQL with correct table/filters so analysis can proceed.",
        )

    sql_query = tool_context.state.get("sql_query") or sql_result.get("sql", "")
    request_parts = [
        f"User question: {question}",
        f"Refinement: {refinement or ''}",
        f"SQL query: {sql_query}",
        "SQL result (JSON; use result_sets if present):",
        format_sql_result(sql_result, include_all_rows=True),
    ]
    request = "\n".join(request_parts)
    log_tool_input("result_interpreter_agent", request)

    try:
        response = await _RESULT_INTERPRETER_TOOL.run_async(
            args={"request": request},
            tool_context=tool_context,
        )
        log_tool_output("result_interpreter_agent", response)
    except Exception as exc:
        message = f"Result interpreter agent failed: {exc}"
        tool_context.state["last_error"] = message
        log_tool_status("run_result_interpreter_agent_tool", message)
        return set_status(tool_context, "answer_status", "error", message)

    answer = tool_context.state.get("answer")
    if not answer:
        message = "Answer not available after agent run."
        tool_context.state["last_error"] = message
        log_tool_status("run_result_interpreter_agent_tool", message)
        return set_status(tool_context, "answer_status", "error", message)

    status_payload = set_status(
        tool_context,
        "answer_status",
        "success",
        "Answer saved.",
    )
    log_tool_output("run_result_interpreter_agent_tool", status_payload)
    return status_payload
