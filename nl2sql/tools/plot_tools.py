from __future__ import annotations

import json
from typing import Dict

from google.adk.tools.tool_context import ToolContext


def _parse_plot_config(plot_config: object) -> Dict[str, object] | None:
    if isinstance(plot_config, dict):
        return plot_config
    if isinstance(plot_config, str):
        try:
            parsed = json.loads(plot_config)
        except json.JSONDecodeError:
            return None
        if isinstance(parsed, dict):
            return parsed
    return None


def get_sql_result(tool_context: ToolContext, max_rows: int = 20) -> Dict[str, object]:
    """Fetch the latest SQL result from tool_context.state with optional sampling."""
    result = tool_context.state.get("sql_result")
    if not result:
        return {"status": "error", "error_message": "SQL result not available."}

    columns = result.get("columns") or []
    rows = result.get("rows") or []
    row_count = result.get("row_count", len(rows))
    sql = result.get("sql")
    result_sets = result.get("result_sets") or []
    if result_sets:
        full_sets = []
        for result_set in result_sets:
            set_rows = result_set.get("rows") or []
            full_sets.append(
                {
                    "sql": result_set.get("sql", ""),
                    "columns": result_set.get("columns") or [],
                    "rows": set_rows,
                    "row_count": result_set.get("row_count", len(set_rows)),
                }
            )
        result_sets = full_sets
        primary = result_sets[0]
        columns = primary.get("columns") or columns
        rows = primary.get("rows") or rows
        row_count = primary.get("row_count", len(rows))

    if max_rows is not None and max_rows >= 0:
        rows = rows[:max_rows]

    sampled = len(rows) < row_count

    payload = {
        "status": "success",
        "sql": sql,
        "columns": columns,
        "rows": rows,
        "row_count": row_count,
        "sampled": sampled,
        "sample_size": len(rows),
    }
    if result_sets:
        payload["result_sets"] = result_sets
    return payload


def save_plot_config(plot_config: object, tool_context: ToolContext) -> Dict[str, object]:
    """Persist plot_config JSON in tool_context.state for downstream agents."""
    parsed = _parse_plot_config(plot_config)
    if not parsed:
        return {"status": "error", "error_message": "Invalid plot_config JSON."}
    if not parsed.get("type"):
        return {"status": "error", "error_message": "plot_config missing 'type'."}
    tool_context.state["plot_config"] = parsed
    return {"status": "success", "plot_config": parsed}


def get_plot_config(tool_context: ToolContext) -> Dict[str, object]:
    """Return the latest plot_config JSON from tool_context.state."""
    plot_config = tool_context.state.get("plot_config")
    if not plot_config:
        return {"status": "error", "error_message": "plot_config not available."}
    return {"status": "success", "plot_config": plot_config}


# --- Deterministic chart selection -----------------------------------------
# The plot_config_agent occasionally fails to save a config (or saves one whose
# axis fields don't match the actual result columns). Chart choice for a result
# set is a deterministic task, so we derive a guaranteed-renderable config from
# the result schema as a default. This reads the SQL result (real data), not the
# model's text output.

_TEMPORAL_HINTS = ("date", "time", "year", "month", "day", "week", "quarter")


def _is_number(value: object) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return True
    try:
        float(value)  # handles Decimal and numeric strings
        return True
    except (TypeError, ValueError):
        return False


def _field(column: str) -> Dict[str, str]:
    label = column.replace("_", " ").strip()
    return {"name": label.title() if label else column, "value": column}


def _primary_columns_rows(sql_result: Dict[str, object]) -> tuple[list, list]:
    result_sets = sql_result.get("result_sets") or []
    source = result_sets[0] if result_sets else sql_result
    return list(source.get("columns") or []), list(source.get("rows") or [])


def derive_plot_config(sql_result: Dict[str, object] | None) -> Dict[str, object]:
    """Pick a sensible chart for a SQL result using only its columns/types."""
    if not sql_result:
        return {"type": "none", "reason": "No SQL result to chart."}
    columns, rows = _primary_columns_rows(sql_result)
    if not columns or not rows:
        return {"type": "none", "reason": "Query returned no rows to chart."}
    if len(columns) == 1:
        return {"type": "table", "title": "Results", "columns": [_field(columns[0])]}

    sample = rows[:20]
    numeric_idx, nonnumeric_idx, temporal_idx = [], [], []
    for j, col in enumerate(columns):
        vals = [r[j] for r in sample if j < len(r) and r[j] is not None]
        is_numeric = bool(vals) and all(_is_number(v) for v in vals)
        if is_numeric:
            numeric_idx.append(j)
        else:
            nonnumeric_idx.append(j)
        if any(h in col.lower() for h in _TEMPORAL_HINTS):
            temporal_idx.append(j)

    # One category/time axis + one measure -> a chart.
    if numeric_idx and (nonnumeric_idx or temporal_idx):
        y = numeric_idx[0]
        x = temporal_idx[0] if temporal_idx else nonnumeric_idx[0]
        if x in temporal_idx:
            ctype = "line"
        else:
            longest = max((len(str(r[x])) for r in sample if x < len(r)), default=0)
            ctype = "bar" if longest > 12 else "column"  # bar = horizontal, for long labels
        title = f"{_field(columns[y])['name']} by {_field(columns[x])['name']}"
        return {"type": ctype, "title": title, "axis": {"x": _field(columns[x]), "y": _field(columns[y])}}

    # Otherwise show a table (cap at 6 columns, per the chart rules).
    return {
        "type": "table",
        "title": "Results",
        "columns": [_field(columns[j]) for j in range(min(6, len(columns)))],
    }


def is_renderable_plot_config(
    plot_config: object, columns: list
) -> bool:
    """True if plot_config is usable as-is: an intentional none/table, or a chart
    whose axis fields actually exist in the result columns."""
    if not isinstance(plot_config, dict):
        return False
    ptype = plot_config.get("type")
    if ptype in ("none", "table"):
        return True
    if ptype not in ("bar", "column", "line", "pie"):
        return False  # missing/unknown/"error"
    axis = plot_config.get("axis") or {}
    cols = set(columns)

    def has(field_key: str) -> bool:
        field = axis.get(field_key) or {}
        return isinstance(field, dict) and field.get("value") in cols

    if ptype == "pie":
        return has("y") and (has("series") or has("x"))
    return has("x") and has("y")
