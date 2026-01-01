from __future__ import annotations

from typing import Dict, List

from google.adk.tools.tool_context import ToolContext

from ..config import load_config
from ..database import get_supabase_client


def _infer_columns_from_row(row: Dict[str, object]) -> List[Dict[str, str]]:
    columns = []
    for key, value in row.items():
        if value is None:
            col_type = "unknown"
        else:
            col_type = type(value).__name__
        columns.append({"name": key, "type": col_type})
    return columns


def inspect_table_schema(
    table_name: str, tool_context: ToolContext
) -> Dict[str, List[Dict[str, str]]]:
    """Return column names and types for a target table."""
    config = load_config()
    default_table = config.allowed_tables[0] if config.allowed_tables else None
    table = (table_name or default_table or "").strip()
    if not table:
        return {
            "status": "error",
            "error_message": "Missing table name. Provide a table or set TARGET_TABLE.",
        }

    if config.allowed_tables:
        allowed = {t.lower() for t in config.allowed_tables}
        if table.lower() not in allowed:
            return {
                "status": "error",
                "error_message": f"Table '{table}' is not allowed.",
            }

    client = get_supabase_client()
    try:
        response = client.table(table).select("*").limit(1).execute()
    except Exception as exc:
        return {
            "status": "error",
            "error_message": f"Supabase query failed: {exc}",
        }

    if getattr(response, "error", None):
        return {
            "status": "error",
            "error_message": f"Supabase error: {response.error}",
        }

    data = response.data or []
    if data:
        columns = _infer_columns_from_row(data[0])
    else:
        columns = []
    if not columns:
        return {
            "status": "error",
            "error_message": (
                f"No rows found for table '{table}'. Add at least one row so the "
                "schema can be inferred via Supabase."
            ),
        }

    tool_context.state["selected_table"] = table
    tool_context.state["table_columns"] = columns
    return {"status": "success", "table": table, "columns": columns}
