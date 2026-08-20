import asyncio
from dataclasses import replace

import pytest
from fastapi import HTTPException

from app.config import settings
import app.security as security


def test_action_key_is_optional_in_development(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(security, "settings", replace(settings, action_api_key=None))
    asyncio.run(security.require_action_api_key(None))


def test_action_key_rejects_a_wrong_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(security, "settings", replace(settings, action_api_key="correct-value"))
    with pytest.raises(HTTPException) as exc:
        asyncio.run(security.require_action_api_key("wrong-value"))
    assert exc.value.status_code == 401
