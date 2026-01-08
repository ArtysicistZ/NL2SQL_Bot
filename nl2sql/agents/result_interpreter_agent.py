import os

from google.adk.agents import Agent

from ..tools.answer_tools import save_answer
from ..utils import load_prompt
from .model_provider import get_model


result_interpreter_agent = Agent(
    name="result_interpreter_agent",
    model=get_model(os.getenv("RESULT_INTERPRETER_MODEL")),
    description="Interprets raw SQL results and answers the user.",
    instruction=load_prompt("result_interpreter_agent"),
    tools=[save_answer],
)
