from google.adk.agents import Agent

from ..tools import get_answer, get_plot_config
from ..utils import load_prompt
from .model_provider import get_model


output_agent = Agent(
    name="output_agent",
    model=get_model(),
    description="Fetches saved answer/plot_config and outputs final JSON.",
    instruction=load_prompt("output_agent"),
    tools=[get_answer, get_plot_config],
)
