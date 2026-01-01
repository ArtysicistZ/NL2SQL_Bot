from __future__ import annotations
import importlib


def load_prompt(module_name: str, var_name: str = "PROMPT") -> str:
    module = importlib.import_module(f"nl2sql.prompts.{module_name}")
    return getattr(module, var_name)
