from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers.analysis import router as analysis_router

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Free-data-first technical and fundamental context API for a Thai stock-analysis chatbot.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.allowed_origins),
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)
app.include_router(analysis_router)


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}

