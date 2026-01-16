from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str
    plot_config: Dict[str, Any]
    sql: str


class RunSqlRequest(BaseModel):
    sql: str
