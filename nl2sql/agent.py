from google.adk.agents import Agent

from .agents import result_interpreter_agent, sql_task_agent
from .agents.model_provider import get_model
from .utils import load_prompt

root_agent = Agent(
    name="nl2sql_root",
    model=get_model(),
    description="Routes SQL tasks to sql_task_agent and analysis to result_interpreter_agent.",
    instruction=load_prompt("root_agent"),
    sub_agents=[sql_task_agent, result_interpreter_agent],
)
