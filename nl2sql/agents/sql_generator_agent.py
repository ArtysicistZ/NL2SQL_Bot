import os

from google.adk.agents import Agent

from ..utils import load_prompt
from .model_provider import get_model


sql_generator_agent = Agent(
    name="sql_generator_agent",
    model=get_model(os.getenv("SQL_GENERATOR_MODEL", "gpt-5-mini")),
    description="Generates read-only SQL for a single target table.",
    instruction=load_prompt("sql_generator_agent"),
)
