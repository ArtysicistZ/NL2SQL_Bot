from __future__ import annotations

from typing import Dict, List

from google.adk.tools.tool_context import ToolContext

from ...config import load_config
from ...database import get_mysql_connection


def inspect_table_schema(tool_context: ToolContext) -> Dict[str, object]:
    """Return column names and types for all allowed tables."""
    config = load_config()
    if not config.allowed_tables:
        return {
            "status": "error",
            "error_message": "Missing allowed tables. Set ALLOWED_TABLES or TARGET_TABLE.",
        }

    try:
        connection = get_mysql_connection()
        cursor = connection.cursor()
        table_schemas: Dict[str, List[Dict[str, str]]] = {}
        missing_tables: List[str] = []
        for table in config.allowed_tables:
            cursor.execute(
                (
                    "SELECT COLUMN_NAME, DATA_TYPE "
                    "FROM INFORMATION_SCHEMA.COLUMNS "
                    "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s "
                    "ORDER BY ORDINAL_POSITION"
                ),
                (config.mysql_database, table),
            )
            rows = cursor.fetchall()
            columns = [{"name": row[0], "type": row[1]} for row in rows]
            if columns:
                table_schemas[table] = columns
            else:
                missing_tables.append(table)
    except Exception as exc:
        return {
            "status": "error",
            "error_message": f"MySQL query failed: {exc}",
        }
    finally:
        if "cursor" in locals():
            cursor.close()

    if not table_schemas:
        return {
            "status": "error",
            "error_message": "No columns found for any allowed tables.",
        }

    tool_context.state["table_schemas"] = table_schemas
    tool_context.state["allowed_tables"] = list(config.allowed_tables)

    response: Dict[str, object] = {
        "status": "success",
        "tables": table_schemas,
    }
    if missing_tables:
        response["missing_tables"] = missing_tables
    return response
