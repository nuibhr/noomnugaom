from __future__ import annotations

import math

import pandas as pd

from app.schemas import TechnicalAnalysis, TechnicalIndicators


def _round_or_none(value: float | None) -> float | None:
    return round(float(value), 4) if value is not None and not math.isnan(float(value)) else None


def _last(series: pd.Series) -> float | None:
    return _round_or_none(series.iloc[-1]) if len(series) else None


def _unique_levels(levels: list[float], close: float, reverse: bool) -> list[float]:
    ordered = sorted(levels, key=lambda level: abs(level - close))
    result: list[float] = []
    for level in ordered:
        if not any(abs(level - existing) / max(abs(existing), 1e-9) < 0.004 for existing in result):
            result.append(round(level, 4))
        if len(result) == 2:
            break
    return sorted(result, reverse=reverse)


def _swing_levels(frame: pd.DataFrame, close: float) -> tuple[list[float], list[float]]:
    window = frame.tail(min(120, len(frame))).reset_index(drop=True)
    lows = window["Low"].astype(float).tolist()
    highs = window["High"].astype(float).tolist()
    supports: list[float] = []
    resistances: list[float] = []
    for index in range(2, len(window) - 2):
        if lows[index] <= min(lows[index - 2 : index + 3]) and lows[index] <= close:
            supports.append(lows[index])
        if highs[index] >= max(highs[index - 2 : index + 3]) and highs[index] >= close:
            resistances.append(highs[index])
    if not supports:
        supports.append(min(lows))
    if not resistances:
        resistances.append(max(highs))
    return _unique_levels(supports, close, reverse=True), _unique_levels(resistances, close, reverse=False)


def analyse_technical(frame: pd.DataFrame, timeframe: str) -> TechnicalAnalysis:
    if len(frame) < 15:
        return TechnicalAnalysis(
            timeframe=timeframe,
            bars_used=len(frame),
            trend="insufficient_data",
            support=[],
            resistance=[],
            indicators=TechnicalIndicators(),
            methodology="At least 15 OHLCV bars are required for the technical-analysis model.",
        )

    close = frame["Close"].astype(float)
    sma_20 = close.rolling(20).mean()
    sma_50 = close.rolling(50).mean()
    sma_200 = close.rolling(200).mean()
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    rsi = 100 - (100 / (1 + (gain / loss)))
    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    macd = ema_12 - ema_26
    signal = macd.ewm(span=9, adjust=False).mean()

    current = float(close.iloc[-1])
    ma50, ma200 = _last(sma_50), _last(sma_200)
    if ma50 is not None and ma200 is not None and current > ma50 > ma200:
        trend = "bullish"
    elif ma50 is not None and ma200 is not None and current < ma50 < ma200:
        trend = "bearish"
    else:
        trend = "sideways"

    support, resistance = _swing_levels(frame, current)
    indicators = TechnicalIndicators(
        sma_20=_last(sma_20),
        sma_50=ma50,
        sma_200=ma200,
        rsi_14=_last(rsi),
        macd=_last(macd),
        macd_signal=_last(signal),
        macd_histogram=_round_or_none(macd.iloc[-1] - signal.iloc[-1]),
    )
    return TechnicalAnalysis(
        timeframe=timeframe,
        bars_used=len(frame),
        trend=trend,
        support=support,
        resistance=resistance,
        invalidation_level=support[-1] if support else None,
        indicators=indicators,
        methodology=(
            "Support/resistance uses local swing lows/highs from up to 120 bars. "
            "Trend uses the close versus SMA50 and SMA200; RSI uses Wilder smoothing."
        ),
    )

