# Agentic Tool Encapsulation Plan

## Goals
- Wrap each of the four sub-agents as a tool so the root agent can orchestrate them.
- Each tool preloads relevant state, injects it into the agent prompt, and stores results back into state as structured JSON.
- Root agent can re-run a tool when another tool reports missing/incorrect data, with a refinement message.

## Current Baseline
- `root_agent` is a `SequentialAgent` that always runs:
  `sql_task_agent -> plot_config_agent -> result_interpreter_agent -> output_agent`
- State keys already in use:
  `table_schemas`, `allowed_tables`, `sql_result`, `plot_config`, `answer`, `generated_sql`, `last_error`

## Proposed Architecture
### New "Agentic Tools" (wrappers)
Create four tools that call their respective agents via `AgentTool` and manage state:

1) `run_sql_task_agent_tool`
   - Inputs: `question`, optional `refinement`
   - Reads: none (loads schemas itself)
   - Behavior:
     - Always call `inspect_table_schema` first and store `table_schemas` in state.
     - Build a structured prompt that includes:
       - User question
       - Refinement note (if any)
       - Allowed table schemas (names + columns)
     - Call `sql_task_agent` via `AgentTool` to generate SQL and run SQL.
     - Verify that `sql_result` is present and has `status == success`.
   - Writes:
     - `sql_task_status` (JSON status object)
     - `last_error` on failure

2) `run_plot_config_agent_tool`
   - Inputs: `question`, optional `refinement`
   - Reads: `sql_result`
   - Behavior:
     - If `sql_result` missing or error, return `needs_retry` targeting SQL tool.
     - Provide `sql_result` + question to agent prompt.
     - Call `plot_config_agent` via `AgentTool`.
     - Verify `plot_config` exists and is valid JSON.
   - Writes:
     - `plot_config_status` (JSON status object)
     - `last_error` on failure

3) `run_result_interpreter_agent_tool`
   - Inputs: `question`, optional `refinement`
   - Reads: `sql_result`
   - Behavior:
     - If `sql_result` missing or error, return `needs_retry` targeting SQL tool.
     - Provide `sql_result` + question to agent prompt.
     - Call `result_interpreter_agent` via `AgentTool`.
     - Verify `answer` exists and is non-empty.
   - Writes:
     - `answer_status` (JSON status object)
     - `last_error` on failure

4) `run_output_tool` (no agent)
   - Inputs: optional `refinement`
   - Reads: `answer`, `plot_config`, `sql_result`
   - Behavior:
     - If any dependency missing, return `needs_retry` targeting the missing tool.
     - Build the final JSON directly from state (no agent call).
   - Writes:
     - `final_response` (JSON payload)
      - `output_status` (JSON status object)

### Standard Tool Status Schema
Each wrapper tool returns and stores a consistent JSON result:
```
{
  "status": "success" | "error" | "needs_retry",
  "message": "...",
  "refinement": "..."   // optional instruction for retry
}
```
Note:
- `run_sql_task_agent_tool` never returns `needs_retry`. It returns `success` or `error` only.
- `run_plot_config_agent_tool` and `run_result_interpreter_agent_tool` may return `needs_retry`,
  and any retry always triggers a re-run of `run_sql_task_agent_tool`.

## Root Agent Orchestration
Replace the `SequentialAgent` with a decision-capable `Agent`:
- Tools: `run_sql_task_agent_tool`, `run_plot_config_agent_tool`,
  `run_result_interpreter_agent_tool`, `run_output_tool`
- Prompt behavior:
  - Call tools in a sensible order.
  - If `run_plot_config_agent_tool` or `run_result_interpreter_agent_tool` returns `needs_retry`,
    the root agent decides whether to re-run `run_sql_task_agent_tool`.
  - When re-running `run_sql_task_agent_tool`, the root agent must pass the original
    user question plus the new refinement requirement.
  - Stop when `final_response` is available and valid.

## Prompt Changes (High-Level)
Each agent prompt should accept a structured input block from its wrapper tool:
- Explicitly mention it will receive schemas, SQL results, or refinement notes.
- Instruct the agent to rely on the provided context (not to invent missing info).

## State Contract
Mandatory state fields after each phase:
- After SQL tool: `sql_result` with `status == success` and `sql_query`
- After plot tool: `plot_config` JSON
- After interpreter tool: `answer` text
- After output tool: `final_response` JSON
Note: Every tool must write its success payload into state when it completes successfully.

## Implementation Steps
1) Add new tool wrappers and register them in `nl2sql/tools/__init__.py`.
2) Update prompts for each agent to accept structured inputs.
3) Remove `inspect_table_schema` from `sql_task_agent` tools; schema load is handled
   inside `run_sql_task_agent_tool`.
4) Replace `root_agent` with decision agent + tool loop.
5) Ensure errors are surfaced via the standard tool status schema.
6) Add documentation for the new orchestration model.

## Open Questions
- Should the root agent have a max retry count per tool to avoid loops?
