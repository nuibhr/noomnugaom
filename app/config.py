from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "Noom Nugaom Stock Analyst API"
    cache_ttl_seconds: int = 300
    allowed_origins: tuple[str, ...] = ("http://localhost:3000", "http://localhost:5173")
    sec_user_agent: str | None = None
    environment: str = "development"
    public_base_url: str | None = None
    action_api_key: str | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173")
        return cls(
            cache_ttl_seconds=int(os.getenv("CACHE_TTL_SECONDS", "300")),
            allowed_origins=tuple(origin.strip() for origin in origins.split(",") if origin.strip()),
            sec_user_agent=os.getenv("SEC_USER_AGENT") or None,
            environment=os.getenv("APP_ENV", "development").lower(),
            public_base_url=(os.getenv("PUBLIC_BASE_URL") or "").rstrip("/") or None,
            action_api_key=os.getenv("ACTION_API_KEY") or None,
        )


settings = Settings.from_env()
