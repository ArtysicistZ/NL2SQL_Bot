# ADK NL2SQL

Lightweight NL2SQL bot built on Google ADK and Azure OpenAI. It uses Supabase
HTTP APIs (not a raw Postgres connection) to read table data safely and then
lets agents generate and interpret SQL.

## Overview
- Minimal workflow: schema -> SQL -> query -> answer
- Read-only by design (SELECT only)
- Table allowlist and row limit enforcement
- Supabase HTTP client for reliable connectivity

## How It Works
```
User question
  -> root_agent routes to sql_task_agent
  -> inspect_table_schema (Supabase, infer columns from one row)
  -> generate_sql (LLM tool, SQL only)
  -> run_sql (Supabase query)
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
D:\Anaconda3\envs\veadk312\python.exe -m google.adk.cli web .
```

If port 8000 is busy:
```
D:\Anaconda3\envs\veadk312\python.exe -m google.adk.cli web . --port 8010
```

## Configuration
Required:
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_VERSION`
- `AZURE_OPENAI_DEPLOYMENT` (or `MODEL`)
- `SUPABASE_URL`
- `SUPABASE_KEY` (or `SUPABASE_SERVICE_KEY`)
- `ALLOWED_TABLES` (comma-separated)
- `TARGET_TABLE`

Optional:
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
- Schema inference uses a single row via Supabase; empty tables cannot be
  introspected.
- SQL runner supports simple SELECT queries only (no JOIN/UNION/GROUP BY).
- Always uses a table allowlist and row limit.

## Docs
- `docs/ARCHITECTURE.md`
- `docs/NL2SQL_ADK_Plan.md`
