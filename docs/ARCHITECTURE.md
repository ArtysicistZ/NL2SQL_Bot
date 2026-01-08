# Architecture

This project follows a small, predictable ADK agent flow. The root agent only
routes, SQL work happens in a dedicated sub-agent, and the result interpreter
turns raw rows into a user answer.

## Agents
- root_agent (Agent): orchestrates agentic tools and assembles final JSON.
- sql_task_agent: SQL generation -> query execution (schema load is handled by tool wrapper).
- sql_generator_agent: produces SQL only (no JSON, no markdown).
- plot_config_agent: generates JSON plot configuration from SQL results.
- result_interpreter_agent: writes the final answer text to session state.

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
- save_answer/get_answer: persist and read the final answer text from state.

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
