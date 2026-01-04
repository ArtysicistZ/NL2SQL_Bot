from google.adk.agents import SequentialAgent

from .plot_config_agent import plot_config_agent
from .result_interpreter_agent import result_interpreter_agent
from .sql_task_agent import sql_task_agent


workflow_agent = SequentialAgent(
    name="nl2sql_workflow",
    description="Runs sql_task_agent, plot_config_agent, then result_interpreter_agent in order.",
    sub_agents=[sql_task_agent, plot_config_agent, result_interpreter_agent],
)
