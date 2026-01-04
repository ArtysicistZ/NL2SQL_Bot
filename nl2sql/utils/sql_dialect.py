from __future__ import annotations

from typing import Dict


_DIALECT_ALIASES = {
    "pg": "postgres",
    "postgres": "postgres",
    "postgresql": "postgres",
    "mysql": "mysql",
    "mariadb": "mysql",
    "sqlite": "sqlite",
    "sqlite3": "sqlite",
}

_DIALECT_RULES: Dict[str, str] = {
    "postgres": "\n".join(
        [
            "- Identifier quoting: use double quotes when needed.",
            "- Case-insensitive match: use ILIKE (not LIKE).",
            "- Row limit: use LIMIT <n> (do not use TOP/FETCH).",
            "- String literals must use single quotes.",
        ]
    ),
    "mysql": "\n".join(
        [
            "- Identifier quoting: use backticks when needed.",
            "- Case-insensitive match: use LIKE (not ILIKE).",
            "- Row limit: use LIMIT <n> (do not use TOP/FETCH).",
            "- String literals must use single quotes.",
        ]
    ),
    "sqlite": "\n".join(
        [
            "- Identifier quoting: use double quotes when needed.",
            "- Case-insensitive match: use LIKE (not ILIKE).",
            "- Row limit: use LIMIT <n> (do not use TOP/FETCH).",
            "- String literals must use single quotes.",
        ]
    ),
}


def normalize_db_type(db_type: str | None) -> str:
    if not db_type:
        return "postgres"
    return _DIALECT_ALIASES.get(db_type.strip().lower(), "postgres")


def get_sql_dialect_rules(db_type: str | None) -> str:
    dialect = normalize_db_type(db_type)
    return _DIALECT_RULES.get(dialect, _DIALECT_RULES["postgres"])
