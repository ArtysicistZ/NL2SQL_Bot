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
    azure_api_key: Optional[str]
    azure_endpoint: Optional[str]
    azure_api_version: str
    azure_deployment: Optional[str]
    supabase_url: Optional[str]
    supabase_key: Optional[str]
    supabase_service_key: Optional[str]
    db_connection_string: Optional[str]
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

    return AppConfig(
        azure_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview"),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT") or os.getenv("MODEL"),
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY"),
        supabase_service_key=os.getenv("SUPABASE_SERVICE_KEY"),
        db_connection_string=os.getenv("POSTGRES_CONNECTION_STRING"),
        db_schema=os.getenv("DB_SCHEMA", "public"),
        allowed_tables=allowed_tables,
        max_rows=max_rows,
    )


def require_azure_deployment(config: AppConfig) -> str:
    if not config.azure_deployment:
        raise ValueError(
            "Missing AZURE_OPENAI_DEPLOYMENT (or MODEL) in .env for LiteLLM."
        )
    return config.azure_deployment


def require_db_connection_string(config: AppConfig) -> str:
    if not config.db_connection_string:
        raise ValueError("Missing POSTGRES_CONNECTION_STRING in .env.")
    return config.db_connection_string


def require_supabase_config(config: AppConfig) -> tuple[str, str]:
    if not config.supabase_url or not config.supabase_key:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in .env.")
    return config.supabase_url, (config.supabase_service_key or config.supabase_key)
