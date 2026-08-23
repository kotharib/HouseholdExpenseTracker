"""Per-request role context for the AI agent.

The AI router (and report/billing routers that call the agent) records the
authenticated user's role before invoking the agent, so the tools can enforce
role-based access on every query regardless of which path (LLM or fallback)
actually runs.
"""
from contextvars import ContextVar

_ai_role: ContextVar[str | None] = ContextVar("ai_role", default=None)

AI_DENIED = "You do not have permission to access that information."


def set_ai_role(role: str) -> None:
    _ai_role.set(role)


def get_ai_role() -> str | None:
    return _ai_role.get()
