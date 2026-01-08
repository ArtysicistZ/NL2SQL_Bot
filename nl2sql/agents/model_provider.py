from __future__ import annotations
from google.adk.models.lite_llm import LiteLlm
from ..config import load_config, require_ai_model

_MODELS: dict[str, LiteLlm] = {}


def get_model(deployment: str | None = None) -> LiteLlm:
    config = load_config()
    deployment_name = deployment or require_ai_model(config)
    if deployment_name not in _MODELS:
        _MODELS[deployment_name] = LiteLlm(
            model=f"azure/{deployment_name}",
            api_key=config.ai_api_key,
            api_base=config.ai_endpoint,
            api_version=config.ai_version,
        )
    return _MODELS[deployment_name]
