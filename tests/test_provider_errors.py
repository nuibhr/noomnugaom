from fastapi.testclient import TestClient

from app.main import app
from app.routers import analysis
from app.services.market import ProviderUnavailableError


def test_analysis_returns_503_when_market_provider_is_rate_limited(monkeypatch) -> None:
    def unavailable(*_args, **_kwargs):
        raise ProviderUnavailableError("Market data provider is temporarily unavailable")

    monkeypatch.setattr(analysis.market_provider, "fetch_history", unavailable)
    response = TestClient(app).get("/v1/analysis/PTT?market=TH")
    assert response.status_code == 503
    assert "temporarily unavailable" in response.json()["detail"]
