from google.adk.agents import SequentialAgent

from .agents.output_agent import output_agent
from .agents.plot_config_agent import plot_config_agent
from .agents.result_interpreter_agent import result_interpreter_agent
from .agents.sql_task_agent import sql_task_agent


root_agent = SequentialAgent(
    name="nl2sql_root",
    description="Runs sql_task_agent, plot_config_agent, result_interpreter_agent, and output_agent in order.",
    sub_agents=[sql_task_agent, plot_config_agent, result_interpreter_agent, output_agent],
)
