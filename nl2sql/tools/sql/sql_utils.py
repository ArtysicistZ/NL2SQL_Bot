from __future__ import annotations

import json
import re

import sqlparse


DANGEROUS_SQL_PATTERNS = [
    r"\bDELETE\b",
    r"\bINSERT\b",
    r"\bUPDATE\b",
    r"\bDROP\b",
    r"\bTRUNCATE\b",
    r"\bALTER\b",
    r"\bCREATE\b",
    r"\bGRANT\b",
    r"\bREVOKE\b",
    r"\bEXEC\b",
    r"\bEXECUTE\b",
    r"\bCALL\b",
    r"\bRENAME\b",
    r"\bREPLACE\b",
    r"\bMERGE\b",
    r"\bLOAD\b",
    r"\bINTO\s+OUTFILE\b",
    r"\bINTO\s+DUMPFILE\b",
]


def validate_sql_is_readonly(sql: str) -> bool:
    """
    Args:
        sql: The SQL statement to validate

    Returns:
        True if SQL is safe (read-only), False otherwise
    """
    if not sql or not sql.strip():
        return False

    cleaned = _strip_sql_comments(sql).strip()
    if not cleaned:
        return False

    for pattern in DANGEROUS_SQL_PATTERNS:
        if re.search(pattern, cleaned, re.IGNORECASE):
            return False

    statements = _split_sql_statements(cleaned)
    if not statements:
        return False
    for stmt in statements:
        stmt_upper = stmt.strip().upper()
        if not re.match(r"^(SELECT|WITH|SHOW|DESCRIBE|DESC|EXPLAIN)\b", stmt_upper):
            return False

    return True


def _normalize_sql(sql: str) -> str:
    cleaned = sql.strip().strip("`").strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
    return cleaned


def _coerce_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=True)
    return str(value)


def _split_sql_statements(sql: str) -> list[str]:
    return [stmt.strip() for stmt in sqlparse.split(sql) if stmt.strip()]


def _strip_sql_comments(sql: str) -> str:
    return sqlparse.format(sql, strip_comments=True)
