# Plot Config Agent Plan

## Goals
- Add a new ADK agent that outputs JSON describing how to visualize query results.
- Keep the existing SQL workflow intact and read-only.
- Support no-plot cases in addition to table and chart types.

## Current System Summary (adk_nl2sql)
- root_agent routes to sql_task_agent, then result_interpreter_agent.
- sql_task_agent calls inspect_table_schema -> generate_sql -> run_sql.
- run_sql returns {status, sql, columns, rows, row_count} and stores state in tool_context.state:
  - selected_table, table_columns, generated_sql, sql_result, last_error.

## SQLBot Visualization Learnings
- Chart config is generated after SQL execution.
- JSON config contains type and either:
  - table: columns [{name, value}]
  - column/bar/line: axis {x, y, series?}
  - pie: axis {series, y}
- Axis values reference field names in the query result; names are display labels.
- Supported chart types in SQLBot frontend: table, bar, column, line, pie.

## Proposed JSON Schema (new agent output)
Fields:
- type: "none" | "table" | "column" | "bar" | "line" | "pie"
- title: short string (optional for type=none)
- columns: array of {name, value} (table only)
- axis: {x, y, series} each {name, value} (charts only)
- reason: string (type=none)

Example (no plot):
```json
{"type":"none","reason":"Only one value returned; no plot needed."}
```

Example (table):
```json
{"type":"table","title":"Top customers","columns":[{"name":"Customer","value":"customer_name"},{"name":"Spend","value":"total_spend"}]}
```

Example (column):
```json
{"type":"column","title":"Orders by day","axis":{"x":{"name":"Day","value":"order_date"},"y":{"name":"Orders","value":"order_count"}}}
```

Example (pie):
```json
{"type":"pie","title":"Share by category","axis":{"series":{"name":"Category","value":"category"},"y":{"name":"Revenue","value":"revenue"}}}
```

## Agent and Tool Design
- New prompt: nl2sql/prompts/plot_config_agent.py
  - Inputs: user question, SQL, columns, rows (sampled), row_count, allowed types.
  - Rules: output JSON only; use column names exactly; choose none when not plot-worthy.
- New agent: nl2sql/agents/plot_config_agent.py
  - Uses get_model(); description focuses on plotting config generation.
- New tool: nl2sql/tools/plot_tools.py (or extend sql_tools.py)
  - generate_plot_config(question, sql_result, tool_context).
  - Samples rows (e.g., first 20) to keep prompt size small.
  - Saves tool_context.state["plot_config"] for downstream use.

## Integration Options
Option A: Add tool call to sql_task_agent flow
- After run_sql succeeds, call generate_plot_config.
- root_agent flow remains: sql_task_agent -> result_interpreter_agent.

Option B: Add a dedicated plot_config_agent and update root_agent prompt
- root_agent calls sql_task_agent, then plot_config_agent, then result_interpreter_agent.
- Keeps plotting logic separate but adds routing complexity.

## Output Surface
- Keep final user answer as text for now.
- Expose plot_config via tool_context.state for UI or API integration.
- Optional later: return a structured response containing both answer and plot_config.

## Edge Cases and Heuristics
- row_count == 0 -> type none with a reason.
- No numeric column found -> type none or table.
- Single numeric column with no categorical/time column -> type none or table.
- Time-like column present -> prefer line.
- Avoid inventing aggregations (SQL generator disallows GROUP BY).

## Validation
- Manual runs with representative queries.
- Verify JSON is valid and uses exact column names.
- Ensure none/table cases are produced when data is not plot-friendly.

## Implementation Steps (pending approval)
1. Add prompt and agent files.
2. Add plot tool and integrate into the agent flow.
3. Update root_agent prompt/flow if needed.
4. Thread plot_config into state and/or final response.
5. Update docs and README with the new agent and JSON schema.

## Open Questions
- Where should plot_config be surfaced (state only vs final answer)?
- Should we add extra types (scatter, number)?
- How many rows should be sampled for the plot agent context?
