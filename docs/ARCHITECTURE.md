# Architecture

This project follows a small, predictable ADK agent flow. The root agent only
routes, SQL work happens in a dedicated sub-agent, and the result interpreter
turns raw rows into a user answer.

## Agents
- root_agent: routes tasks to sql_task_agent and result_interpreter_agent.
- sql_task_agent: schema -> SQL generation -> query execution.
- sql_generator_agent: produces SQL only (no JSON, no markdown).
- result_interpreter_agent: explains query output to the user.

## Tools
- inspect_table_schema: fetches one row via Supabase and infers column names.
- generate_sql: wraps sql_generator_agent output into JSON.
- run_sql: validates and executes simple SELECT queries via Supabase.

## Execution Flow
```
User -> root_agent
  -> sql_task_agent
      -> inspect_table_schema
      -> generate_sql
      -> run_sql
  -> result_interpreter_agent
  -> final answer
```

## Session State (tool_context.state)
Keys used by tools and agents:
- selected_table
- table_columns
- generated_sql
- sql_result
- last_error

## Security Boundaries
- Allowed tables only (from ALLOWED_TABLES / TARGET_TABLE)
- SELECT-only, single statement
- No JOIN/UNION/GROUP BY/HAVING
- Max rows enforced (MAX_ROWS)
