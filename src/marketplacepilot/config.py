from __future__ import annotations

import os
from asyncio import to_thread
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True, slots=True)
class Settings:
    telegram_bot_token: str
    database_path: Path
    telegram_webhook_secret: str | None = None
    webhook_base_url: str | None = None
    port: int = 8000

    @classmethod
    async def from_environment(cls, *, require_webhook: bool = False) -> Settings:
        await to_thread(load_dotenv)
        token = _required_value("TELEGRAM_BOT_TOKEN")
        database_path = Path(os.getenv("DATABASE_PATH", "").strip() or "data/marketplacepilot.sqlite3")
        port = _read_port(os.getenv("PORT", "8000"))
        if not require_webhook:
            return cls(token, database_path, port=port)

        secret = _required_value("TELEGRAM_WEBHOOK_SECRET")
        webhook_base_url = _required_value("WEBHOOK_BASE_URL")
        if not webhook_base_url.startswith("https://") or webhook_base_url.endswith("/"):
            message = "WEBHOOK_BASE_URL должен быть HTTPS URL без завершающего '/'."
            raise RuntimeError(message)
        return cls(token, database_path, secret, webhook_base_url, port)


def _required_value(name: str) -> str:
    value = os.getenv(name, "").strip()
    if value:
        return value
    raise RuntimeError(f"Укажите {name} в локальном .env или переменных окружения.")


def _read_port(raw_value: str) -> int:
    try:
        port = int(raw_value)
    except ValueError as error:
        raise RuntimeError("PORT должен быть целым числом.") from error
    if not 1 <= port <= 65535:
        raise RuntimeError("PORT должен быть в диапазоне от 1 до 65535.")
    return port
