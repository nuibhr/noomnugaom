from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers.analysis import router as analysis_router
from app.schemas import HealthResponse


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.environment == "production" and not settings.action_api_key:
        raise RuntimeError("ACTION_API_KEY must be configured when APP_ENV=production")
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Free-data-first technical and fundamental context API for a Thai stock-analysis chatbot.",
    servers=[{"url": settings.public_base_url}] if settings.public_base_url else None,
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.allowed_origins),
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)
app.include_router(analysis_router)


@app.get("/health", tags=["system"], operation_id="healthCheck", response_model=HealthResponse)
async def health() -> HealthResponse:
    return {"status": "ok", "service": settings.app_name}