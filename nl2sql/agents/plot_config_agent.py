from google.adk.agents import Agent

from ..tools.plot_tools import get_sql_result, save_plot_config
from ..utils import load_prompt
from .model_provider import get_model


plot_config_agent = Agent(
    name="plot_config_agent",
    model=get_model(),
    description="Generates JSON plot configuration from SQL results.",
    instruction=load_prompt("plot_config_agent"),
    tools=[get_sql_result, save_plot_config],
)
