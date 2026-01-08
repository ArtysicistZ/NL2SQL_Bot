from google.adk.agents import Agent

from ..tools.plot_tools import save_plot_config
from ..tools.retry_tools import request_sql_retry
from ..utils import load_prompt
from .model_provider import get_model


plot_config_agent = Agent(
    name="plot_config_agent",
    model=get_model(),
    description="Generates JSON plot configuration from SQL queries.",
    instruction=load_prompt("plot_config_agent"),
    tools=[save_plot_config, request_sql_retry],
)
