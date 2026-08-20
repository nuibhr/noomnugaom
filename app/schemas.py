from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Market = Literal["TH", "US"]


class PriceSnapshot(BaseModel):
    symbol: str
    provider_symbol: str
    market: Market
    currency: str | None = None
    close: float
    previous_close: float | None = None
    change_pct: float | None = None
    volume: int | None = None
    as_of: datetime
    data_status: Literal["end_of_day", "intraday", "unknown"] = "unknown"
    source: str
    source_notice: str


class TechnicalIndicators(BaseModel):
    sma_20: float | None = None
    sma_50: float | None = None
    sma_200: float | None = None
    rsi_14: float | None = Field(default=None, description="Wilder RSI")
    macd: float | None = None
    macd_signal: float | None = None
    macd_histogram: float | None = None


class TechnicalAnalysis(BaseModel):
    timeframe: str
    bars_used: int
    trend: Literal["bullish", "bearish", "sideways", "insufficient_data"]
    support: list[float]
    resistance: list[float]
    invalidation_level: float | None = None
    indicators: TechnicalIndicators
    methodology: str


class FundamentalMetric(BaseModel):
    value: float | None = None
    currency: str | None = None
    period_end: str | None = None
    qoq_pct: float | None = None
    yoy_pct: float | None = None


class Fundamentals(BaseModel):
    source: str
    as_of: str | None = None
    revenue: FundamentalMetric
    net_income: FundamentalMetric
    diluted_eps: FundamentalMetric
    operating_cash_flow: FundamentalMetric
    cash_and_equivalents: FundamentalMetric
    total_debt: FundamentalMetric
    note: str


class AnalysisResponse(BaseModel):
    price: PriceSnapshot
    technical: TechnicalAnalysis
    requested_at: datetime
    disclaimer: str


class ChatContextResponse(BaseModel):
    system_prompt: str
    market_data: PriceSnapshot
    technical_analysis: TechnicalAnalysis
    fundamentals: Fundamentals | None = None
    generated_at: datetime

