<h1 align="center">ADK NL2SQL</h1>

<p align="center">
  <img alt="Status" src="https://img.shields.io/badge/status-active-success" />
  <img alt="Python" src="https://img.shields.io/badge/python-3.10%2B-blue" />
  <img alt="License" src="https://img.shields.io/badge/license-MIT-lightgrey" />
</p>
<p align="center">
  Lightweight NL2SQL service built on Google ADK with Azure OpenAI and MySQL.
</p>
ADK NL2SQL is a light-weight AI agent that can turn natural language questions into trustworthy data answers through SQL-based RAG architecture.
It combines LLM‑driven reasoning with controlled SQL execution to deliver
clear explanations, visualizations, and the exact query used to compute them.

## Features
- Ask questions in plain language and get clear, structured answers backed by SQL queries.
- Visualize SQL results instantly with charts and tables in the built-in UI.
- See the SQL behind every answer for transparency and trust.
- Keep data safe with read-only queries and allowlisted tables only.
- Make analysis repeatable with consistent outputs and visible logic.

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

3) Run the SPA + API server (serves the frontend at `/`)
```
python app/server.py
```
Open `http://127.0.0.1:8080` in your browser.

4) Optional: run the ADK webapp for prompt debugging
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
- `ALLOWED_TABLES` (comma-separated allowlist)

Optional:
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
AI_ENDPOINT=...
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
The `/ask` response is JSON:
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

The `/run_sql` response returns row data for charts:
```json
{
  "status": "success",
  "sql": "SELECT ...",
  "columns": ["col_a", "col_b"],
  "rows": [["x", 1], ["y", 2]],
  "row_count": 2
}
```

## Security
- SQL execution is read-only (SELECT/SHOW/DESCRIBE/EXPLAIN).
- Non-read queries are blocked by a simple keyword scan.
- Optional allowlist limits which tables are inspected.
- `/run_sql` reuses the same read-only validation as agent execution.

## Limitations
- SQL generation currently avoids joins, aliases, and functions.
- Only the allowlisted tables are introspected.

## Project Structure
```
adk_nl2sql/
  app/
    api.py
    server.py
    schemas.py
    settings.py
  frontend/
    index.html
    app.js
    styles.css
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
- `docs/FRONTEND_PLAN.md`

## Troubleshooting
- `mysql` not found: install MySQL and add `mysql.exe` to PATH.
- Schema errors: ensure `ALLOWED_TABLES` exist in `MYSQL_DATABASE`.
- Plot config missing: check that the plot agent calls `save_plot_config` with
  `{"plot_config": ...}`.

## Contributing
Issues and PRs are welcome. Keep changes small and focused, and update docs
when behavior changes.
