from __future__ import annotations

import json
from typing import Any, Dict, Optional

from google.genai import types
from fastapi import APIRouter, HTTPException
from google.adk.runners import InMemoryRunner
from google.adk.utils.context_utils import Aclosing

from nl2sql.agent import root_agent
from nl2sql.tools.sql.run_sql import run_sql as run_sql_tool

from .schemas import AskRequest, RunSqlRequest

router = APIRouter()
_RUNNER = InMemoryRunner(agent=root_agent, app_name="nl2sql")
_DEFAULT_USER_ID = "local-user"

class _SimpleToolContext:
    def __init__(self) -> None:
        self.state: Dict[str, Any] = {}


def _coerce_to_dict(payload: Any) -> Optional[Dict[str, Any]]:
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, str):
        try:
            return json.loads(payload)
        except Exception:
            return None
    for attr in ("output", "text", "value"):
        if hasattr(payload, attr):
            return _coerce_to_dict(getattr(payload, attr))
    return None


def _normalize_final_response(state: Dict[str, Any], response: Any) -> Dict[str, Any]:
    final_response = state.get("final_response")
    if isinstance(final_response, dict):
        payload = dict(final_response)
    else:
        payload = _coerce_to_dict(response) or {}

    if not payload:
        message = state.get("last_error") or "Agent response missing."
        payload = {
            "answer": message,
            "plot_config": {"type": "none", "reason": "error"},
            "sql": "",
        }

    payload.setdefault("answer", "No answer available.")
    payload.setdefault("plot_config", {"type": "none", "reason": "plot_config missing"})
    payload.setdefault("sql", "")
    return payload


async def _run_root_agent(question: str) -> Dict[str, Any]:
    session = await _RUNNER.session_service.create_session(
        app_name=_RUNNER.app_name,
        user_id=_DEFAULT_USER_ID,
    )
    content = types.Content(role="user", parts=[types.Part(text=question)])
    async with Aclosing(
        _RUNNER.run_async(
            user_id=session.user_id,
            session_id=session.id,
            new_message=content,
        )
    ) as agen:
        async for _ in agen:
            pass

    updated_session = await _RUNNER.session_service.get_session(
        app_name=_RUNNER.app_name,
        user_id=session.user_id,
        session_id=session.id,
    )
    state = updated_session.state if updated_session else {}
    await _RUNNER.session_service.delete_session(
        app_name=_RUNNER.app_name,
        user_id=session.user_id,
        session_id=session.id,
    )
    return state


@router.post("/ask")
async def ask(request: AskRequest) -> Dict[str, Any]:
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        state = await _run_root_agent(question)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {exc}") from exc

    return _normalize_final_response(state, state.get("final_response"))


@router.post("/run_sql")
def run_sql(request: RunSqlRequest) -> Dict[str, Any]:
    sql = request.sql.strip()
    if not sql:
        raise HTTPException(status_code=400, detail="SQL cannot be empty.")

    tool_context = _SimpleToolContext()
    result = run_sql_tool(sql, tool_context)
    if result.get("status") != "success":
        message = result.get("error_message") or "SQL run failed."
        raise HTTPException(status_code=400, detail=message)
    return result
