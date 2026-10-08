"""Settings from environment variables. Nothing secret lives in code."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_RULES_DIR = REPO_ROOT / "engine" / "rules" / "hu"


class ConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class Settings:
    secret_key: str
    database_path: Path
    rules_dir: Path
    secure_cookies: bool = True
    session_max_age: int = 8 * 3600  # one working day

    @classmethod
    def from_env(cls) -> Settings:
        secret = os.environ.get("VAGYONADO_SECRET_KEY", "")
        if len(secret) < 32:
            raise ConfigError(
                "Set VAGYONADO_SECRET_KEY to a random string of at least 32 characters, "
                "for example: python -c \"import secrets; print(secrets.token_urlsafe(48))\""
            )
        return cls(
            secret_key=secret,
            database_path=Path(os.environ.get("VAGYONADO_DB", "vagyonado.sqlite3")),
            rules_dir=Path(os.environ.get("VAGYONADO_RULES_DIR", DEFAULT_RULES_DIR)),
            secure_cookies=os.environ.get("VAGYONADO_INSECURE_COOKIES") != "1",
        )
