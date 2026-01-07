from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

def _load_env() -> None:
    try:
        from dotenv import load_dotenv
    except Exception:
        # Optional dependency; environment variables can be loaded by the runner.
        return

    env_path = Path(__file__).resolve().parents[1] / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True, encoding="utf-8")
    else:
        load_dotenv()


_load_env()


@dataclass(frozen=True)
class AppConfig:
    ai_api_key: Optional[str]
    ai_endpoint: Optional[str]
    ai_version: str
    ai_model: Optional[str]
    mysql_host: Optional[str]
    mysql_port: int
    mysql_user: Optional[str]
    mysql_password: Optional[str]
    mysql_database: Optional[str]
    db_type: str
    db_schema: str
    allowed_tables: List[str]
    max_rows: int


def _split_csv(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def load_config() -> AppConfig:
    allowed_tables = _split_csv(os.getenv("ALLOWED_TABLES"))
    target_table = os.getenv("TARGET_TABLE")
    if target_table and target_table not in allowed_tables:
        allowed_tables.append(target_table)

    max_rows_raw = os.getenv("MAX_ROWS", "200").strip()
    try:
        max_rows = int(max_rows_raw)
    except ValueError:
        max_rows = 200

    mysql_port_raw = os.getenv("MYSQL_PORT", "3306").strip()
    try:
        mysql_port = int(mysql_port_raw)
    except ValueError:
        mysql_port = 3306

    return AppConfig(
        ai_api_key=os.getenv("AI_API_KEY"),
        ai_endpoint=os.getenv("AI_ENDPOINT"),
        ai_version=os.getenv("AI_API_VERSION", "2025-01-01-preview"),
        ai_model=os.getenv("AI_MODEL"),
        mysql_host=os.getenv("MYSQL_HOST"),
        mysql_port=mysql_port,
        mysql_user=os.getenv("MYSQL_USER"),
        mysql_password=os.getenv("MYSQL_PASSWORD"),
        mysql_database=os.getenv("MYSQL_DATABASE"),
        db_type=os.getenv("DB_TYPE", "mysql").strip().lower(),
        db_schema=os.getenv("DB_SCHEMA", "public"),
        allowed_tables=allowed_tables,
        max_rows=max_rows,
    )


def require_ai_model(config: AppConfig) -> str:
    if not config.ai_model:
        raise ValueError(
            "Missing AI_MODEL in .env for LiteLLM."
        )
    return config.ai_model


def require_mysql_config(config: AppConfig) -> tuple[str, int, str, str, str]:
    if not config.mysql_host:
        raise ValueError("Missing MYSQL_HOST in .env.")
    if not config.mysql_user:
        raise ValueError("Missing MYSQL_USER in .env.")
    if not config.mysql_password:
        raise ValueError("Missing MYSQL_PASSWORD in .env.")
    if not config.mysql_database:
        raise ValueError("Missing MYSQL_DATABASE in .env.")
    return (
        config.mysql_host,
        config.mysql_port,
        config.mysql_user,
        config.mysql_password,
        config.mysql_database,
    )
