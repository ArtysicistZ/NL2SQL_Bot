__all__ = [
    "output_agent",
    "plot_config_agent",
    "result_interpreter_agent",
    "sql_generator_agent",
    "sql_task_agent",
]


def __getattr__(name: str):
    if name in __all__:
        import importlib

        module = importlib.import_module(f"{__name__}.{name}")
        return getattr(module, name)
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
