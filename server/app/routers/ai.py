import asyncio
import json
import re
from datetime import date

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from app.ai.agent import agent
from app.auth.dependencies import get_current_user
from app.database import get_session
from app.models.user import User
from app.schemas.chat import (
    AiInsightsResponse,
    AiMonthlyReportResponse,
    ChatRequest,
)
from app.utils.helpers import validate_month

router = APIRouter(prefix="/ai", tags=["ai"])


def _stream_events(text: str):
    tokens = re.split(r"(\s+)", text)
    for token in tokens:
        if not token:
            continue
        yield f"data: {json.dumps({'token': token})}\n\n"
    yield f"data: {json.dumps({'done': True})}\n\n"


@router.post("/chat")
async def chat(payload: ChatRequest, _: User = Depends(get_current_user)):
    history = [m.model_dump() for m in payload.history]

    def run() -> str:
        return agent.chat(payload.message, history)

    response_text = await asyncio.to_thread(run)

    async def event_stream():
        for chunk in _stream_events(response_text):
            yield chunk
            await asyncio.sleep(0.008)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/insights", response_model=AiInsightsResponse)
async def insights(session: Session = Depends(get_session), _: User = Depends(get_current_user)):
    text = await asyncio.to_thread(agent.insights)
    from app.services.insights import compute_insights

    data = compute_insights(session)
    return AiInsightsResponse(
        insights=text,
        llm_available=agent.is_available,
        data=data,
    )


@router.get("/report/monthly", response_model=AiMonthlyReportResponse)
async def monthly_report(
    month: str | None = None,
    _: User = Depends(get_current_user),
):
    target = validate_month(month) if month else date.today().strftime("%Y-%m")
    text = await asyncio.to_thread(agent.monthly_report, target)
    return AiMonthlyReportResponse(month=target, report=text, llm_available=agent.is_available)
