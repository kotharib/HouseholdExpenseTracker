from typing import Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    history: list[ChatMessage] = Field(default_factory=list)


class ChatChunk(BaseModel):
    token: str


class ChatDone(BaseModel):
    done: bool


class AiInsightsResponse(BaseModel):
    insights: str
    llm_available: bool
    data: dict


class AiMonthlyReportResponse(BaseModel):
    month: str
    report: str
    llm_available: bool
