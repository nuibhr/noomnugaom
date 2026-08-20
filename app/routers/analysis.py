from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from app.config import settings
from app.schemas import AnalysisResponse, ChatContextResponse, Fundamentals, Market
from app.services.fundamentals import YahooFundamentalProvider
from app.services.market import DataUnavailableError, YahooMarketProvider
from app.services.technical import analyse_technical
from app.services.us_sec import SecProvider
from app.security import require_action_api_key

router = APIRouter(prefix="/v1", tags=["analysis"], dependencies=[Depends(require_action_api_key)])
market_provider = YahooMarketProvider(settings.cache_ttl_seconds)
fundamental_provider = YahooFundamentalProvider()
ALLOWED_PERIODS = {"1mo", "3mo", "6mo", "1y", "2y", "5y"}
ALLOWED_INTERVALS = {"1d", "1wk"}


async def _analysis(symbol: str, market: Market, period: str, interval: str):
    try:
        history = await asyncio.to_thread(market_provider.fetch_history, symbol, market, period, interval)
    except (DataUnavailableError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    technical = analyse_technical(history.frame, interval)
    return history.snapshot, technical


@router.get("/analysis/{symbol}", response_model=AnalysisResponse)
async def get_analysis(
    symbol: str,
    market: Market = Query("TH"),
    period: str = Query("1y"),
    interval: str = Query("1d"),
) -> AnalysisResponse:
    if period not in ALLOWED_PERIODS or interval not in ALLOWED_INTERVALS:
        raise HTTPException(status_code=422, detail=f"period must be one of {sorted(ALLOWED_PERIODS)} and interval one of {sorted(ALLOWED_INTERVALS)}")
    price, technical = await _analysis(symbol, market, period, interval)
    return AnalysisResponse(
        price=price,
        technical=technical,
        requested_at=datetime.now(timezone.utc),
        disclaimer="Educational analysis only. Market data may be delayed or inaccurate; verify with an official source before trading.",
    )


@router.get("/fundamentals/{symbol}", response_model=Fundamentals)
async def get_fundamentals(
    symbol: str,
    market: Market = Query("TH"),
    provider: Literal["auto", "yahoo", "sec"] = Query("auto"),
) -> Fundamentals:
    if provider == "sec" and market != "US":
        raise HTTPException(status_code=422, detail="The SEC provider supports US issuers only")
    try:
        if (provider == "sec" or (provider == "auto" and market == "US" and settings.sec_user_agent)):
            if not settings.sec_user_agent:
                raise HTTPException(status_code=400, detail="Set SEC_USER_AGENT to enable official SEC filings")
            return await asyncio.to_thread(SecProvider(settings.sec_user_agent).fetch, symbol)
        return await asyncio.to_thread(fundamental_provider.fetch, symbol, market)
    except (DataUnavailableError, LookupError, ValueError, OSError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/chat-context/{symbol}", response_model=ChatContextResponse)
async def get_chat_context(
    symbol: str,
    market: Market = Query("TH"),
    include_fundamentals: bool = Query(True),
) -> ChatContextResponse:
    price, technical = await _analysis(symbol, market, "1y", "1d")
    fundamentals = None
    if include_fundamentals:
        try:
            fundamentals = await asyncio.to_thread(fundamental_provider.fetch, symbol, market)
        except DataUnavailableError:
            fundamentals = None
    prompt_path = Path(__file__).resolve().parents[1] / "data" / "master_prompt.txt"
    return ChatContextResponse(
        system_prompt=prompt_path.read_text(encoding="utf-8"),
        market_data=price,
        technical_analysis=technical,
        fundamentals=fundamentals,
        generated_at=datetime.now(timezone.utc),
    )
