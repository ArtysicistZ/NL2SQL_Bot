# Architecture

This project follows a small, predictable ADK agent flow. The root agent only
routes, SQL work happens in a dedicated sub-agent, and the result interpreter
turns raw rows into a user answer.

## Agents
- root_agent (SequentialAgent): runs sql_task_agent, plot_config_agent, result_interpreter_agent, output_agent in order.
- sql_task_agent: schema -> SQL generation -> query execution.
- sql_generator_agent: produces SQL only (no JSON, no markdown).
- plot_config_agent: generates JSON plot configuration from SQL results.
- result_interpreter_agent: writes the final answer text to session state.
- output_agent: reads answer + plot_config from state and returns final JSON.

## Tools
- inspect_table_schema: queries `information_schema.columns` for all allowed tables.
- generate_sql: wraps sql_generator_agent output into JSON.
- run_sql: validates and executes read-only SQL via MySQL.
- get_sql_result: exposes the latest SQL result to the plot_config_agent.
- save_plot_config/get_plot_config: persist and read plot_config from state.
- save_answer/get_answer: persist and read the final answer text from state.

## Execution Flow
```
User -> root_agent
  -> sql_task_agent
      -> inspect_table_schema
      -> generate_sql
      -> run_sql
  -> plot_config_agent
      -> get_sql_result
      -> save_plot_config
  -> result_interpreter_agent
      -> save_answer
  -> output_agent
      -> get_answer
      -> get_plot_config
  -> final JSON answer
```

## Session State (tool_context.state)
Keys used by tools and agents:
- selected_table
- table_columns
- generated_sql
- sql_result
- last_error

## Security Boundaries
- Allowed tables only (from ALLOWED_TABLES / TARGET_TABLE) for schema inspection
- Read-only SQL validation
