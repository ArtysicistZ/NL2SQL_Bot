from __future__ import annotations

from google.adk.models.lite_llm import LiteLlm

from ..config import load_config, require_ai_api_key, require_ai_model

_MODELS: dict[str, LiteLlm] = {}


def get_model(deployment: str | None = None) -> LiteLlm:
    """Return a cached LiteLlm model for the active provider.

    Provider is selected with AI_PROVIDER (default: "openai"). The same agent
    code works for either backend; only env vars change.
    """
    config = load_config()
    model_name = deployment or require_ai_model(config)
    api_key = require_ai_api_key(config)

    cache_key = f"{config.ai_provider}:{model_name}"
    if cache_key not in _MODELS:
        if config.ai_provider == "azure":
            _MODELS[cache_key] = LiteLlm(
                model=f"azure/{model_name}",
                api_key=api_key,
                api_base=config.ai_endpoint,
                api_version=config.ai_version,
            )
        else:
            # Standard OpenAI API (https://api.openai.com/v1).
            _MODELS[cache_key] = LiteLlm(
                model=f"openai/{model_name}",
                api_key=api_key,
            )
    return _MODELS[cache_key]
