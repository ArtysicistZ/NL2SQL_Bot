from __future__ import annotations

from typing import Dict

from google.adk.tools.tool_context import ToolContext


def save_answer(answer: str, tool_context: ToolContext) -> Dict[str, object]:
    """Persist the final answer text in tool_context.state."""
    text = (answer or "").strip()
    if not text:
        return {"status": "error", "error_message": "Answer is empty."}
    tool_context.state["final_answer"] = text
    return {"status": "success", "answer": text}


def get_answer(tool_context: ToolContext) -> Dict[str, object]:
    """Return the latest saved answer text from tool_context.state."""
    answer = tool_context.state.get("final_answer")
    if not answer:
        return {"status": "error", "error_message": "Answer not available."}
    return {"status": "success", "answer": answer}
