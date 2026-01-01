from __future__ import annotations
from google.adk.models.lite_llm import LiteLlm
from ..config import load_config, require_azure_deployment

_MODEL = None


def get_model() -> LiteLlm:
    global _MODEL
    if _MODEL is None:
        config = load_config()
        deployment = require_azure_deployment(config)
        _MODEL = LiteLlm(
            model=f"azure/{deployment}",
            api_key=config.azure_api_key,
            api_base=config.azure_endpoint,
            api_version=config.azure_api_version,
        )
    return _MODEL
