# Architecture

This project follows a small, predictable ADK agent flow. The root agent only
routes, SQL work happens in a dedicated sub-agent, and the result interpreter
turns raw rows into a user answer.

## Agents
- root_agent (Agent): orchestrates agentic tools and assembles final JSON.
- sql_task_agent: SQL generation -> query execution (schema load is handled by tool wrapper).
- sql_generator_agent: produces SQL only (no JSON, no markdown).
- plot_config_agent: generates JSON plot configuration from SQL results.
- result_interpreter_agent: writes the answer text to session state.

## Model provider
- `nl2sql/agents/model_provider.py`: builds a cached LiteLLM model per agent.
- `AI_PROVIDER` selects `openai` (default) or `azure`; only env vars differ between them.

## App Server (API-only)
- `app/server.py`: FastAPI app factory + uvicorn entrypoint. Binds `0.0.0.0` by default;
  the legacy static `frontend/` is mounted only when `SERVE_STATIC` is set.
- `app/api.py`: `/ask` runs the ADK flow; `/run_sql` executes read-only SQL for charts;
  `/health` is a DB-free liveness probe (used by the Docker healthcheck).
- The app server uses ADK `InMemoryRunner` to run the root agent with a per-request session.

## Database
- `nl2sql/database/mysql_client.py`: a `MySQLConnectionPool` (size `MYSQL_POOL_SIZE`).
  Callers borrow a connection per request and `close()` it to return it to the pool — safe
  under Starlette's threadpool, where `/run_sql` runs concurrently.

## Frontend (`web/`, Next.js App Router + TypeScript)
- `web/src/app/page.tsx`: composes the panels (query, answer, chart, results, SQL editor, history).
- `web/src/hooks/useNl2Sql.ts`: orchestrates `/ask` → `/run_sql`, with request cancellation.
- `web/src/lib/`: typed API client, plot-config → Plotly translation, CSV export.
- `web/next.config.mjs`: `rewrites` proxy `/api/*` → `BACKEND_ORIGIN` (same-origin, no CORS).

## Tools
- inspect_table_schema: queries `information_schema.columns` for all allowed tables.
- run_sql_task_agent_tool: loads schemas, runs sql_task_agent, stores sql_result + sql_query.
- run_plot_config_agent_tool: runs plot_config_agent and stores plot_config.
- run_result_interpreter_agent_tool: runs result_interpreter_agent and stores answer.
- run_output_tool: builds final JSON directly from state.
- generate_sql: wraps sql_generator_agent output into JSON.
- run_sql: validates and executes read-only SQL via MySQL.
- get_sql_result: exposes the latest SQL result to the plot_config_agent.
- save_plot_config/get_plot_config: persist and read plot_config from state.
- save_answer/get_answer: persist and read the answer text from state.

## Execution Flow
```
User -> root_agent
  -> run_sql_task_agent_tool
      -> inspect_table_schema
      -> sql_task_agent
          -> generate_sql
          -> run_sql
  -> run_plot_config_agent_tool
      -> plot_config_agent
          -> save_plot_config
          -> request_sql_retry
  -> run_result_interpreter_agent_tool
      -> result_interpreter_agent
          -> save_answer
  -> run_output_tool
  -> final JSON answer
```

## Frontend Flow
```
User -> /ask
  -> ADK runner executes root_agent
  -> final_response (answer + plot_config + sql)
Frontend -> /run_sql
  -> run_sql validates and executes SQL
  -> sql_result for chart rendering
```

## Session State (tool_context.state)
Keys used by tools and agents:
- generated_sql
- sql_result
- last_error
- table_schemas
- sql_query
- plot_config
- answer
- final_response

## Security Boundaries
- Allowed tables only (from ALLOWED_TABLES / TARGET_TABLE) for schema inspection
- Read-only SQL validation
- `/run_sql` uses the same read-only validation for frontend chart data
