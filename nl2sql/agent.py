from google.adk.agents import Agent

from .tools import (
    run_output_tool,
    run_plot_config_agent_tool,
    run_result_interpreter_agent_tool,
    run_sql_task_agent_tool,
)
from .utils import load_prompt
from .agents.model_provider import get_model


root_agent = Agent(
    name="nl2sql_root",
    model=get_model(),
    description="Orchestrates SQL, plot config, interpretation, and final output.",
    instruction=load_prompt("root_agent"),
    tools=[
        run_sql_task_agent_tool,
        run_plot_config_agent_tool,
        run_result_interpreter_agent_tool,
        run_output_tool,
    ],
)
