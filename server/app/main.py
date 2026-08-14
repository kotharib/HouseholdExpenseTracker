"""FastAPI application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ai.agent import agent
from app.config import settings
from app.database import engine, init_db
from app.routers import (
    ai,
    auth,
    billing,
    dashboard,
    diagrams,
    expenses,
    investments,
    milk,
    newspaper,
    reports,
    servants,
)
from app.services.seed import run_seed


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    with next(get_sql_session()) as session:
        run_seed(session)
    yield


def get_sql_session():
    from sqlmodel import Session

    with Session(engine) as session:
        yield session


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description=(
        "Household management & expense tracking API with AI agent, "
        "reports and diagram generation."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (auth.router, expenses.router, servants.router, milk.router,
          newspaper.router, dashboard.router, ai.router, reports.router,
          diagrams.router, investments.router, billing.router):
    app.include_router(r)


@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    return {"status": "ok", "llm_available": agent.is_available}
