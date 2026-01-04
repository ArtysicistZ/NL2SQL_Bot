# ADK NL2SQL

Lightweight NL2SQL bot built on Google ADK and Azure OpenAI. It connects to a
local MySQL database to read table data and then lets agents generate and
interpret SQL.

## Overview
- Minimal workflow: schema -> SQL -> query -> answer
- Read-only by design (SELECT only)
- Optional table allowlist for schema inspection
- Direct MySQL connection

## How It Works
```
User question
  -> root_agent routes to sql_task_agent
  -> inspect_table_schema (MySQL information_schema lookup)
  -> generate_sql (LLM tool, SQL only)
  -> run_sql (MySQL query)
  -> result_interpreter_agent answers
```

## Quick Start
1) Install deps
```
pip install -r requirements.txt
```

2) Create `.env` from `.env.example` and fill values.

3) Run the web UI from the repo root:
```
python -m google.adk.cli web .
```

If port 8000 is busy:
```
python -m google.adk.cli web . --port 8010
```

## Configuration
Required:
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_VERSION`
- `AZURE_OPENAI_DEPLOYMENT` (or `MODEL`)
- `MYSQL_HOST`
- `MYSQL_PORT`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DATABASE`
- `TARGET_TABLE`

Optional:
- `ALLOWED_TABLES` (comma-separated)
- `DB_TYPE` (postgres/mysql/sqlite; default: mysql)
- `MAX_ROWS` (default: 200)

## Project Structure
```
adk_nl2sql/
  nl2sql/
    agent.py
    agents/
    database/
    prompts/
    tools/
    utils/
  docs/
  requirements.txt
  .env.example
```

## Notes and Limits
- Schema inference uses `information_schema.columns`.
- SQL runner only enforces a read-only safety check.

## Docs
- `docs/ARCHITECTURE.md`
- `docs/NL2SQL_ADK_Plan.md`
