from __future__ import annotations

from hmac import compare_digest
from typing import Annotated

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.config import settings

action_api_key_header = APIKeyHeader(name="X-API-Key", scheme_name="ActionApiKey", auto_error=False)


async def require_action_api_key(
    supplied_key: Annotated[str | None, Security(action_api_key_header)],
) -> None:
    """Protect GPT Action routes when ACTION_API_KEY is configured.

    Development remains open by default so local curl and Swagger testing work.
    Production refuses to start without ACTION_API_KEY in ``app.main``.
    """

    expected_key = settings.action_api_key
    if expected_key is None:
        return
    if supplied_key is None or not compare_digest(supplied_key, expected_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key",
        )

