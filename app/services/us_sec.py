from __future__ import annotations

import httpx

from app.schemas import FundamentalMetric, Fundamentals
from app.services.market import ProviderUnavailableError


class SecProvider:
    """Official US filing adapter; SEC_USER_AGENT is required by SEC fair-access guidance."""

    source = "US SEC EDGAR (official filings)"

    def __init__(self, user_agent: str) -> None:
        if not user_agent:
            raise ValueError("SEC_USER_AGENT is required for the SEC provider")
        self.headers = {"User-Agent": user_agent, "Accept-Encoding": "gzip, deflate"}

    def _get_json(self, url: str) -> dict:
        try:
            response = httpx.get(url, headers=self.headers, timeout=20.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            raise ProviderUnavailableError("SEC EDGAR is temporarily unavailable; retry later") from exc

    def _cik_for_ticker(self, ticker: str) -> str:
        mapping = self._get_json("https://www.sec.gov/files/company_tickers.json")
        for row in mapping.values():
            if row.get("ticker", "").upper() == ticker.upper():
                return str(row["cik_str"]).zfill(10)
        raise LookupError(f"SEC has no CIK mapping for {ticker}")

    @staticmethod
    def _latest_metric(facts: dict, tags: list[str]) -> FundamentalMetric:
        for tag in tags:
            fact = facts.get("us-gaap", {}).get(tag, {})
            units = fact.get("units", {})
            entries = next(iter(units.values()), [])
            accepted = [item for item in entries if item.get("form") in {"10-Q", "10-K"}]
            if accepted:
                latest = sorted(accepted, key=lambda item: (item.get("filed", ""), item.get("end", "")), reverse=True)[0]
                return FundamentalMetric(
                    value=float(latest["val"]),
                    currency="USD",
                    period_end=latest.get("end"),
                )
        return FundamentalMetric(currency="USD")

    def fetch(self, ticker: str) -> Fundamentals:
        cik = self._cik_for_ticker(ticker)
        payload = self._get_json(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json")
        facts = payload.get("facts", {})
        return Fundamentals(
            source=self.source,
            as_of=payload.get("entityName"),
            revenue=self._latest_metric(facts, ["Revenues", "SalesRevenueNet"]),
            net_income=self._latest_metric(facts, ["NetIncomeLoss"]),
            diluted_eps=self._latest_metric(facts, ["EarningsPerShareDiluted"]),
            operating_cash_flow=self._latest_metric(facts, ["NetCashProvidedByUsedInOperatingActivities"]),
            cash_and_equivalents=self._latest_metric(facts, ["CashAndCashEquivalentsAtCarryingValue"]),
            total_debt=self._latest_metric(facts, ["LongTermDebtCurrent", "LongTermDebtAndFinanceLeaseObligationsCurrent"]),
            note="Latest reported US-GAAP fact from SEC 10-Q/10-K filings; values may use different fiscal periods.",
        )
