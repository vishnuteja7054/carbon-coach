"""
Programmatic Google ADK Runner Service for Carbon Coach.

Executes `root_agent` via `google.adk.runners.InMemoryRunner`, captures all live
tool calls (`function_call` and `function_response`) for full auditability, and
returns the agent reply along with the latest deterministic summary and reduction tips.
"""

from typing import Dict, Any, List, Optional
from google.adk.runners import InMemoryRunner
from google.genai import types

from carbon_coach.agent import root_agent
from carbon_coach.tools import get_summary, suggest_reductions

APP_NAME = "carbon_coach_app"
_runner: Optional[InMemoryRunner] = None
_initialized_sessions: set[str] = set()


def get_runner() -> InMemoryRunner:
    global _runner
    if _runner is None:
        _runner = InMemoryRunner(agent=root_agent, app_name=APP_NAME)
    return _runner


async def ensure_session(user_id: str, session_id: str) -> None:
    runner = get_runner()
    key = f"{user_id}:{session_id}"
    if key not in _initialized_sessions:
        existing = await runner.session_service.get_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id,
        )
        if existing is None:
            await runner.session_service.create_session(
                app_name=APP_NAME,
                user_id=user_id,
                session_id=session_id,
            )
        _initialized_sessions.add(key)


async def run_carbon_coach_turn(
    user_message: str,
    user_id: str = "default_user",
    session_id: str = "default_session",
) -> Dict[str, Any]:
    """Run a single conversational turn through the Google ADK `root_agent`."""
    runner = get_runner()
    await ensure_session(user_id=user_id, session_id=session_id)

    content = types.Content(
        role="user",
        parts=[types.Part.from_text(text=user_message)],
    )

    tool_calls_trace: List[Dict[str, Any]] = []
    final_text_parts: List[str] = []

    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=content,
    ):
        if not event.content or not event.content.parts:
            continue

        for part in event.content.parts:
            if getattr(part, "function_call", None):
                fc = part.function_call
                tool_calls_trace.append(
                    {
                        "type": "tool_call",
                        "agent": getattr(event, "author", "carbon_coach"),
                        "tool_name": fc.name,
                        "args": dict(fc.args) if fc.args else {},
                    }
                )
            elif getattr(part, "function_response", None):
                fr = part.function_response
                tool_calls_trace.append(
                    {
                        "type": "tool_result",
                        "agent": getattr(event, "author", "carbon_coach"),
                        "tool_name": fr.name,
                        "result": dict(fr.response) if fr.response else {},
                    }
                )
            elif getattr(part, "text", None) and part.text.strip():
                if event.is_final_response():
                    final_text_parts.append(part.text)

    reply_text = "\n".join(final_text_parts).strip()

    return {
        "status": "success",
        "reply": reply_text,
        "tool_trace": tool_calls_trace,
        "summary_today": get_summary(period="today"),
        "reductions_today": suggest_reductions(period="today"),
    }
