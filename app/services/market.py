from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pandas as pd
import yfinance as yf

from app.schemas import Market, PriceSnapshot
from app.services.cache import TTLCache


class DataUnavailableError(RuntimeError):
    pass


class ProviderUnavailableError(DataUnavailableError):
    pass


@dataclass
class MarketHistory:
    frame: pd.DataFrame
    snapshot: PriceSnapshot


class YahooMarketProvider:
    """Convenience provider for an MVP. Yahoo Finance is an unofficial data source."""

    source = "Yahoo Finance via yfinance (unofficial)"
    source_notice = (
        "Free convenience feed. Verify price, corporate actions, and exchange delay "
        "against an official exchange or broker before making any investment decision."
    )

    def __init__(self, cache_ttl_seconds: int = 300) -> None:
        self.cache: TTLCache[MarketHistory] = TTLCache(cache_ttl_seconds)

    @staticmethod
    def provider_symbol(symbol: str, market: Market) -> str:
        normalized = symbol.upper().strip()
        if not normalized:
            raise ValueError("symbol must not be blank")
        return normalized if market == "US" else f"{normalized}.BK"

    def fetch_history(self, symbol: str, market: Market, period: str, interval: str) -> MarketHistory:
        provider_symbol = self.provider_symbol(symbol, market)
        key = f"{provider_symbol}:{period}:{interval}"
        return self.cache.get_or_set(key, lambda: self._download(symbol, market, provider_symbol, period, interval))

    def _download(self, symbol: str, market: Market, provider_symbol: str, period: str, interval: str) -> MarketHistory:
        ticker = yf.Ticker(provider_symbol)
        try:
            frame = ticker.history(period=period, interval=interval, auto_adjust=False, actions=False)
        except Exception as exc:
            raise ProviderUnavailableError(
                f"Market data provider is temporarily unavailable for {provider_symbol}; retry later"
            ) from exc
        if frame.empty or "Close" not in frame:
            raise DataUnavailableError(f"No market data returned for {provider_symbol}")

        frame = frame.dropna(subset=["Close"]).copy()
        if frame.empty:
            raise DataUnavailableError(f"No usable close prices returned for {provider_symbol}")

        latest = frame.iloc[-1]
        previous_close = float(frame.iloc[-2]["Close"]) if len(frame) > 1 else None
        close = float(latest["Close"])
        change_pct = ((close / previous_close) - 1) * 100 if previous_close else None
        timestamp = frame.index[-1].to_pydatetime()
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        data_status = "end_of_day" if interval in {"1d", "1wk", "1mo"} else "intraday"
        snapshot = PriceSnapshot(
            symbol=symbol.upper().strip(),
            provider_symbol=provider_symbol,
            market=market,
            currency="THB" if market == "TH" else "USD",
            close=round(close, 4),
            previous_close=round(previous_close, 4) if previous_close else None,
            change_pct=round(change_pct, 4) if change_pct is not None else None,
            volume=int(latest["Volume"]) if pd.notna(latest.get("Volume")) else None,
            as_of=timestamp,
            data_status=data_status,
            source=self.source,
            source_notice=self.source_notice,
        )
        return MarketHistory(frame=frame, snapshot=snapshot)
