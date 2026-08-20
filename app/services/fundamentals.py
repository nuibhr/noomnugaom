from __future__ import annotations

from datetime import date

import pandas as pd
import yfinance as yf

from app.schemas import FundamentalMetric, Fundamentals, Market
from app.services.cache import TTLCache
from app.services.market import DataUnavailableError, ProviderUnavailableError, YahooMarketProvider


def _value_at(frame: pd.DataFrame, labels: list[str], column: object) -> float | None:
    for label in labels:
        if label in frame.index:
            value = frame.at[label, column]
            if pd.notna(value):
                return float(value)
    return None


def _pct_change(current: float | None, earlier: float | None) -> float | None:
    if current is None or earlier in (None, 0):
        return None
    return round(((current / earlier) - 1) * 100, 4)


def _metric(frame: pd.DataFrame, labels: list[str], currency: str | None) -> FundamentalMetric:
    if frame.empty or not len(frame.columns):
        return FundamentalMetric(currency=currency)
    columns = sorted(frame.columns, reverse=True)
    current_column = columns[0]
    current = _value_at(frame, labels, current_column)
    qoq = _value_at(frame, labels, columns[1]) if len(columns) > 1 else None
    yoy = _value_at(frame, labels, columns[4]) if len(columns) > 4 else None
    period_end = current_column.date().isoformat() if hasattr(current_column, "date") else str(current_column)
    return FundamentalMetric(
        value=current,
        currency=currency,
        period_end=period_end,
        qoq_pct=_pct_change(current, qoq),
        yoy_pct=_pct_change(current, yoy),
    )


class YahooFundamentalProvider:
    source = "Yahoo Finance via yfinance (unofficial)"

    def __init__(self, cache_ttl_seconds: int = 3600) -> None:
        self.cache: TTLCache[Fundamentals] = TTLCache(cache_ttl_seconds)

    def fetch(self, symbol: str, market: Market) -> Fundamentals:
        provider_symbol = YahooMarketProvider.provider_symbol(symbol, market)
        return self.cache.get_or_set(provider_symbol, lambda: self._download(provider_symbol))

    def _download(self, provider_symbol: str) -> Fundamentals:
        try:
            ticker = yf.Ticker(provider_symbol)
            income = ticker.quarterly_income_stmt
            balance = ticker.quarterly_balance_sheet
            cashflow = ticker.quarterly_cashflow
            currency = ticker.fast_info.get("currency")
        except Exception as exc:
            raise ProviderUnavailableError(
                f"Fundamental data provider is temporarily unavailable for {provider_symbol}; retry later"
            ) from exc
        if income.empty and balance.empty and cashflow.empty:
            raise DataUnavailableError(f"No fundamental data returned for {provider_symbol}")
        return Fundamentals(
            source=self.source,
            as_of=date.today().isoformat(),
            revenue=_metric(income, ["Total Revenue", "Operating Revenue"], currency),
            net_income=_metric(income, ["Net Income", "Net Income Common Stockholders"], currency),
            diluted_eps=_metric(income, ["Diluted EPS", "Basic EPS"], currency),
            operating_cash_flow=_metric(cashflow, ["Operating Cash Flow", "Total Cash From Operating Activities"], currency),
            cash_and_equivalents=_metric(balance, ["Cash Cash Equivalents And Short Term Investments", "Cash And Cash Equivalents"], currency),
            total_debt=_metric(balance, ["Total Debt", "Long Term Debt And Capital Lease Obligation"], currency),
            note=(
                "Figures are provider-reported quarterly fields and can be missing or restated. "
                "For Thai issuers, verify against SET and SEC Thailand filings."
            ),
        )
