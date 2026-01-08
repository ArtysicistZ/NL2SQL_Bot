from __future__ import annotations

from typing import Dict

from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.tool_context import ToolContext

from ...agents.sql_task_agent import sql_task_agent
from ..schema_tools import inspect_table_schema
from .agentic_utils import (
    clear_downstream_state,
    format_table_schemas,
    log_tool_input,
    log_tool_output,
    log_tool_status,
    set_status,
    state_remove,
)

_SQL_TASK_TOOL = AgentTool(sql_task_agent)


async def run_sql_task_agent_tool(
    question: str,
    tool_context: ToolContext,
    refinement: str | None = None,
) -> Dict[str, object]:
    """Load schemas, call sql_task_agent, and persist SQL results.
    This tool is able to handle complex and multiple user requests in one call, never call me twice consequently if user question contains multiple parts about different sql commands."""
    clear_downstream_state(tool_context)
    state_remove(tool_context, "sql_retry_request")

    schema_result = inspect_table_schema(tool_context=tool_context)
    if schema_result.get("status") != "success":
        message = schema_result.get("error_message", "Schema inspection failed.")
        tool_context.state["last_error"] = message
        log_tool_status("run_sql_task_agent_tool", message)
        return set_status(tool_context, "sql_task_status", "error", message)

    table_schemas = tool_context.state.get("table_schemas") or {}
    request_parts = [
        "Input:",
        f"- question: {question}",
        f"- refinement: {refinement or ''}",
        "Allowed table schemas (JSON):",
        format_table_schemas(table_schemas),
    ]
    request = "\n".join(request_parts)
    log_tool_input("sql_task_agent", request)

    try:
        response = await _SQL_TASK_TOOL.run_async(
            args={"request": request},
            tool_context=tool_context,
        )
        log_tool_output("sql_task_agent", response)
    except Exception as exc:
        message = f"SQL task agent failed: {exc}"
        tool_context.state["last_error"] = message
        log_tool_status("run_sql_task_agent_tool", message)
        return set_status(tool_context, "sql_task_status", "error", message)

    sql_result = tool_context.state.get("sql_result") or {}
    if sql_result.get("status") != "success":
        message = tool_context.state.get("last_error") or "SQL execution failed."
        log_tool_status("run_sql_task_agent_tool", message)
        return set_status(tool_context, "sql_task_status", "error", message)

    sql_query = sql_result.get("sql") or tool_context.state.get("generated_sql") or ""
    if sql_query:
        tool_context.state["sql_query"] = sql_query

    status_payload = set_status(
        tool_context,
        "sql_task_status",
        "success",
        "SQL task completed.",
    )
    log_tool_output("run_sql_task_agent_tool", status_payload)
    if sql_query:
        status_payload["sql_query"] = sql_query
    return status_payload
