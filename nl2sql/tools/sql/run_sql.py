from __future__ import annotations

from typing import Dict

from google.adk.tools.tool_context import ToolContext

from ...database import get_mysql_connection
from .sql_utils import _normalize_sql, _split_sql_statements, validate_sql_is_readonly


def run_sql(query: str, tool_context: ToolContext) -> Dict[str, object]:
    """Execute SQL after validating it is read-only."""
    sql = _normalize_sql(query)

    if not validate_sql_is_readonly(sql):
        tool_context.state["last_error"] = "Only read-only SQL queries are allowed."
        return {"status": "error", "error_message": "Only read-only SQL queries are allowed."}

    try:
        connection = get_mysql_connection()
        cursor = connection.cursor()
        result_sets = []
        statements = _split_sql_statements(sql)
        if not statements:
            tool_context.state["last_error"] = "Empty SQL after parsing."
            return {"status": "error", "error_message": "Empty SQL after parsing."}
        for statement in statements:
            cursor.execute(statement)
            with_rows = getattr(cursor, "with_rows", False)
            if with_rows or cursor.description:
                rows_data = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                rows = [list(row) for row in rows_data]
                result_sets.append(
                    {
                        "sql": statement,
                        "columns": columns,
                        "rows": rows,
                        "row_count": len(rows),
                    }
                )
            else:
                row_count = cursor.rowcount if cursor.rowcount is not None else 0
                result_sets.append(
                    {
                        "sql": statement,
                        "columns": [],
                        "rows": [],
                        "row_count": row_count,
                    }
                )
    except Exception as exc:
        tool_context.state["last_error"] = str(exc)
        return {"status": "error", "error_message": "MySQL query failed."}
    finally:
        if "cursor" in locals():
            cursor.close()

    if not result_sets:
        result_sets = [{"sql": sql, "columns": [], "rows": [], "row_count": 0}]

    primary = result_sets[0]
    payload = {
        "status": "success",
        "sql": sql,
        "columns": primary.get("columns", []),
        "rows": primary.get("rows", []),
        "row_count": primary.get("row_count", 0),
        "result_sets": result_sets,
    }
    tool_context.state["generated_sql"] = sql
    tool_context.state["sql_result"] = payload
    tool_context.state["last_error"] = None
    tool_context.state["sql_run_success"] = True
    return payload
