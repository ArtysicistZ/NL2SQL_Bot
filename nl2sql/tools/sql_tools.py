from __future__ import annotations

import re
from typing import Dict, List, Tuple

from google.adk.tools.tool_context import ToolContext

from ..agents.sql_generator_agent import sql_generator_agent
from ..config import load_config
from ..database import get_supabase_client


def _normalize_sql(sql: str) -> str:
    cleaned = sql.strip().strip("`").strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
    return cleaned


def _ensure_single_statement(sql: str) -> bool:
    parts = [part.strip() for part in sql.split(";") if part.strip()]
    return len(parts) == 1


def _is_read_only(sql: str) -> bool:
    normalized = re.sub(r"--.*?$", "", sql, flags=re.MULTILINE).strip()
    if not normalized.lower().startswith(("select", "with")):
        return False
    forbidden = re.compile(
        r"\b(insert|update|delete|drop|alter|create|truncate|grant|revoke)\b",
        re.IGNORECASE,
    )
    return not forbidden.search(normalized)


def _parse_sql_value(raw_value: str):
    value = raw_value.strip()
    if value.lower() in {"null", "none"}:
        return None
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    if (value.startswith("'") and value.endswith("'")) or (
        value.startswith('"') and value.endswith('"')
    ):
        value = value[1:-1]
        value = value.replace("''", "'")
        return value
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def _parse_sql_select(sql: str) -> Dict[str, object]:
    cleaned = re.sub(r"\s+", " ", sql.strip().rstrip(";"))
    if re.search(r"\bjoin\b|\bunion\b|\bgroup\b|\bhaving\b", cleaned, flags=re.IGNORECASE):
        return {"success": False, "error": "Only simple SELECT queries (no JOIN/UNION/GROUP BY) are supported."}

    match = re.match(
        r"(?is)^select\s+(?P<select>.+?)\s+from\s+(?P<table>[a-zA-Z0-9_.\"]+)(?P<rest>.*)$",
        cleaned,
    )
    if not match:
        return {"success": False, "error": "Unsupported SQL. Use SELECT ... FROM <table>."}

    select_clause = match.group("select").strip()
    table = match.group("table").strip().strip('"')
    rest = match.group("rest") or ""

    if re.search(r"\s", table):
        return {"success": False, "error": "Table aliases are not supported. Use a single table name."}

    limit = None
    order_by = None
    where_clause = ""

    limit_match = re.search(r"(?is)\s+limit\s+(\d+)\s*$", rest)
    if limit_match:
        limit = int(limit_match.group(1))
        rest = rest[: limit_match.start()]

    order_match = re.search(r"(?is)\s+order\s+by\s+(.+)$", rest)
    if order_match:
        order_by = order_match.group(1).strip()
        rest = rest[: order_match.start()]

    where_match = re.search(r"(?is)\s+where\s+(.+)$", rest)
    if where_match:
        where_clause = where_match.group(1).strip()

    if select_clause == "*":
        columns = ["*"]
    else:
        columns = [col.strip().strip('"') for col in select_clause.split(",") if col.strip()]
        if not columns:
            return {"success": False, "error": "No columns selected."}

    filters: List[Tuple[str, str, object]] = []
    if where_clause:
        conditions = re.split(r"\s+and\s+", where_clause, flags=re.IGNORECASE)
        for condition in conditions:
            condition = condition.strip()
            cond_match = re.match(
                r"(?is)^([a-zA-Z0-9_.\"]+)\s*(=|!=|<>|>=|<=|>|<|ilike|like)\s*(.+)$",
                condition,
            )
            if not cond_match:
                return {
                    "success": False,
                    "error": "Unsupported WHERE clause. Use simple ANDed comparisons.",
                }
            column = cond_match.group(1).strip().strip('"')
            operator = cond_match.group(2).lower()
            value = _parse_sql_value(cond_match.group(3))
            filters.append((column, operator, value))

    return {
        "success": True,
        "table": table,
        "columns": columns,
        "filters": filters,
        "limit": limit,
        "order_by": order_by,
    }


def _apply_filters(query, filters: List[Tuple[str, str, object]]):
    for column, operator, value in filters:
        if operator == "=":
            query = query.eq(column, value)
        elif operator in ("!=", "<>"):
            query = query.neq(column, value)
        elif operator == ">":
            query = query.gt(column, value)
        elif operator == ">=":
            query = query.gte(column, value)
        elif operator == "<":
            query = query.lt(column, value)
        elif operator == "<=":
            query = query.lte(column, value)
        elif operator == "ilike":
            query = query.ilike(column, value)
        elif operator == "like":
            query = query.like(column, value)
    return query


def _apply_order(query, order_by: str):
    if not order_by:
        return query
    first = order_by.split(",")[0].strip()
    parts = first.split()
    column = parts[0].strip('"')
    desc = len(parts) > 1 and parts[1].lower() == "desc"
    return query.order(column, desc=desc)


async def generate_sql(
    question: str,
    table: str,
    columns: List[Dict[str, str]],
    tool_context: ToolContext,
) -> Dict[str, object]:
    """Call SQLGeneratorAgent and wrap its SQL output as JSON."""
    prompt = (
        f"User question: {question}\n"
        f"Target table: {table}\n"
        "Columns:\n"
        + "\n".join([f"- {col['name']} ({col.get('type', '')})" for col in columns])
    )
    try:
        sql_text = await sql_generator_agent.run(prompt)
    except Exception as exc:
        tool_context.state["last_error"] = str(exc)
        return {"success": False, "message": "SQL generator failed."}

    sql_text = _normalize_sql(sql_text)
    if not sql_text:
        tool_context.state["last_error"] = "Empty SQL from generator."
        return {"success": False, "message": "Empty SQL from generator."}

    tool_context.state["generated_sql"] = sql_text
    return {"success": True, "sql": sql_text, "reason": "generated by sql_generator_agent"}


def run_sql(query: str, tool_context: ToolContext) -> Dict[str, object]:
    """Execute SQL after validating it is read-only and within allowed tables."""
    config = load_config()
    sql = _normalize_sql(query)

    if not _ensure_single_statement(sql):
        tool_context.state["last_error"] = "Multiple SQL statements are not allowed."
        return {"status": "error", "error_message": "Multiple SQL statements are not allowed."}
    if not _is_read_only(sql):
        tool_context.state["last_error"] = "Only SELECT/CTE queries are allowed."
        return {"status": "error", "error_message": "Only SELECT/CTE queries are allowed."}

    parsed = _parse_sql_select(sql)
    if not parsed.get("success"):
        tool_context.state["last_error"] = parsed.get("error", "Unsupported SQL.")
        return {"status": "error", "error_message": parsed.get("error", "Unsupported SQL.")}

    table = parsed["table"]
    columns = parsed["columns"]
    filters = parsed["filters"]
    limit = parsed["limit"]
    order_by = parsed["order_by"]

    if columns == ["*"]:
        tool_context.state["last_error"] = "SELECT * is not allowed."
        return {"status": "error", "error_message": "SELECT * is not allowed."}

    if config.allowed_tables:
        allowed = {t.lower() for t in config.allowed_tables}
        if table.lower() not in allowed:
            tool_context.state["last_error"] = f"Table '{table}' is not allowed."
            return {"status": "error", "error_message": f"Table '{table}' is not allowed."}

    max_rows = config.max_rows
    if limit is None or limit > max_rows:
        limit = max_rows

    client = get_supabase_client()
    try:
        query_builder = client.table(table).select(",".join(columns))
        query_builder = _apply_filters(query_builder, filters)
        query_builder = _apply_order(query_builder, order_by)
        response = query_builder.limit(limit).execute()
    except Exception as exc:
        tool_context.state["last_error"] = str(exc)
        return {"status": "error", "error_message": "Supabase query failed."}

    if getattr(response, "error", None):
        tool_context.state["last_error"] = str(response.error)
        return {"status": "error", "error_message": "Supabase query failed."}

    data = response.data or []
    rows = [[row.get(col) for col in columns] for row in data]

    payload = {
        "status": "success",
        "sql": sql,
        "columns": columns,
        "rows": rows,
        "row_count": len(rows),
    }
    tool_context.state["generated_sql"] = sql
    tool_context.state["sql_result"] = payload
    return payload
