<h1 align="center">ADK NL2SQL</h1>

<p align="center">
  <img alt="Status" src="https://img.shields.io/badge/status-active-success" />
  <img alt="Python" src="https://img.shields.io/badge/python-3.10%2B-blue" />
  <img alt="License" src="https://img.shields.io/badge/license-MIT-lightgrey" />
</p>
<p align="center">
  Lightweight NL2SQL service built on Google ADK with Azure OpenAI and MySQL.
</p>
It inspects allowed tables, generates read-only SQL, executes it, and returns
both an answer and a plot configuration.

## Features
- Read-only SQL enforcement (SELECT only)
- Table allowlist for schema inspection
- Multi-statement SQL support (semicolon separated)
- Agentic workflow: SQL -> plot config -> interpretation -> final JSON
- Per-agent model overrides (optional)

## How It Works
```
User question
  -> root_agent orchestrates tool calls
  -> run_sql_task_agent_tool (schema -> SQL -> run)
  -> run_plot_config_agent_tool (plot config)
  -> run_result_interpreter_agent_tool (answer)
  -> run_output_tool (final JSON)
```

## Requirements
- Python 3.10+
- MySQL 8.x (local or remote)
- Azure OpenAI deployment(s)

## Quick Start
1) Install dependencies
```
pip install -r requirements.txt
```

2) Create `.env` from `.env.example` and fill values.

3) Run the web UI from the repo root
```
python -m google.adk.cli web .
```

If port 8000 is busy:
```
python -m google.adk.cli web . --port 8010
```

## Configuration
Required:
- `AI_API_KEY`
- `AI_ENDPOINT`
- `AI_API_VERSION`
- `AI_MODEL` (default deployment used by agents)
- `MYSQL_HOST`
- `MYSQL_PORT`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DATABASE`

Optional:
- `ALLOWED_TABLES` (comma-separated allowlist)
- `DB_TYPE` (default: mysql)
- `DB_SCHEMA` (default: public)
- `MAX_ROWS` (default: 200)

Per-agent model overrides (optional):
- `ROOT_MODEL`
- `SQL_TASK_MODEL`
- `SQL_GENERATOR_MODEL`
- `PLOT_CONFIG_MODEL`
- `RESULT_INTERPRETER_MODEL`

Example `.env`:
```
AI_API_KEY=...
AI_ENDPOINT=https://your-azure-endpoint.openai.azure.com
AI_API_VERSION=2025-01-01-preview
AI_MODEL=gpt-4o-mini

SQL_GENERATOR_MODEL=gpt-5-mini
PLOT_CONFIG_MODEL=gpt-4o-mini

MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=sakila

ALLOWED_TABLES=film,language,customer,rental,payment
MAX_ROWS=200
```

## Output Format
The final response is JSON:
```json
{
  "answer": "Short natural language answer.",
  "plot_config": {
    "type": "bar",
    "title": "Example",
    "axis": {
      "x": {"name": "Category", "value": "category"},
      "y": {"name": "Count", "value": "count"}
    }
  },
  "sql": "SELECT ... LIMIT 100"
}
```

## Security
- SQL execution is read-only (SELECT/SHOW/DESCRIBE/EXPLAIN).
- Non-read queries are blocked by a simple keyword scan.
- Optional allowlist limits which tables are inspected.

## Limitations
- SQL generation currently avoids joins, aliases, and functions.
- Only the allowlisted tables are introspected.

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

## Docs
- `docs/ARCHITECTURE.md`
- `docs/AGENTIC_TOOLS_PLAN.md`

## Troubleshooting
- `mysql` not found: install MySQL and add `mysql.exe` to PATH.
- Schema errors: ensure `ALLOWED_TABLES` exist in `MYSQL_DATABASE`.
- Plot config missing: check that the plot agent calls `save_plot_config` with
  `{"plot_config": ...}`.

## Contributing
Issues and PRs are welcome. Keep changes small and focused, and update docs
when behavior changes.
