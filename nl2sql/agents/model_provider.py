from __future__ import annotations
from google.adk.models.lite_llm import LiteLlm
from ..config import load_config, require_ai_model

_MODEL = None


def get_model() -> LiteLlm:
    global _MODEL
    if _MODEL is None:
        config = load_config()
        deployment = require_ai_model(config)
        _MODEL = LiteLlm(
            model=f"azure/{deployment}",
            api_key=config.ai_api_key,
            api_base=config.ai_endpoint,
            api_version=config.ai_version,
        )
    return _MODEL
