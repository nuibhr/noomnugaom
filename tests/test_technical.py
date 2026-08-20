from __future__ import annotations

import numpy as np
import pandas as pd

from app.services.technical import analyse_technical


def test_technical_analysis_returns_levels_and_indicators() -> None:
    closes = np.linspace(10, 30, 240) + np.sin(np.arange(240) / 5)
    frame = pd.DataFrame(
        {
            "Open": closes - 0.2,
            "High": closes + 0.5,
            "Low": closes - 0.5,
            "Close": closes,
            "Volume": np.full(240, 1_000_000),
        }
    )
    result = analyse_technical(frame, "1d")
    assert result.trend == "bullish"
    assert result.indicators.rsi_14 is not None
    assert len(result.support) >= 1
    assert len(result.resistance) >= 1


def test_technical_analysis_requires_enough_bars() -> None:
    frame = pd.DataFrame({"High": [2.0] * 10, "Low": [1.0] * 10, "Close": [1.5] * 10})
    assert analyse_technical(frame, "1d").trend == "insufficient_data"

