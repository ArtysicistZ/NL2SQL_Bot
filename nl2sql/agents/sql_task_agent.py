from google.adk.agents import Agent

from ..tools.sql_tools import generate_sql, run_sql
from ..utils import load_prompt
from .model_provider import get_model


sql_task_agent = Agent(
    name="sql_task_agent",
    model=get_model(),
    description="Handles SQL generation and SQL execution.",
    instruction=load_prompt("sql_task_agent"),
    tools=[generate_sql, run_sql],
)
