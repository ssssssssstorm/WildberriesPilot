from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from starlette.testclient import TestClient

from marketplacepilot.config import Settings
from marketplacepilot.web import WEBHOOK_PATH, WebRuntime, create_app


@dataclass
class FakeSession:
    closed: bool = False

    async def close(self) -> None:
        self.closed = True


@dataclass
class FakeStorage:
    closed: bool = False

    async def close(self) -> None:
        self.closed = True


@dataclass
class FakeBot:
    session: FakeSession = field(default_factory=FakeSession)


@dataclass
class FakeDispatcher:
    storage: FakeStorage = field(default_factory=FakeStorage)
    updates: list[tuple[Any, Any]] = field(default_factory=list)

    async def feed_update(self, bot: Any, update: Any) -> None:
        self.updates.append((bot, update))


def test_healthz_returns_public_fast_status(tmp_path) -> None:
    client, _, _ = _make_client(tmp_path)
    with client:
        response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "mode": "demo"}


def test_webhook_rejects_invalid_secret(tmp_path) -> None:
    client, _, dispatcher = _make_client(tmp_path)
    with client:
        response = client.post(
            WEBHOOK_PATH, headers={"X-Telegram-Bot-Api-Secret-Token": "wrong"}, json=_update_payload()
        )

    assert response.status_code == 403
    assert dispatcher.updates == []


def test_webhook_forwards_valid_update_to_dispatcher(tmp_path) -> None:
    client, bot, dispatcher = _make_client(tmp_path)
    with client:
        response = client.post(
            WEBHOOK_PATH,
            headers={"X-Telegram-Bot-Api-Secret-Token": "demo-secret"},
            json=_update_payload(),
        )

    assert response.status_code == 200
    assert len(dispatcher.updates) == 1
    assert dispatcher.updates[0][0] is bot
    assert dispatcher.updates[0][1].update_id == 7001


def _make_client(tmp_path) -> tuple[TestClient, FakeBot, FakeDispatcher]:
    bot = FakeBot()
    dispatcher = FakeDispatcher()
    runtime = WebRuntime(bot, dispatcher, "https://t.me/marketplacepilot_demo")
    settings = Settings(
        telegram_bot_token="123456:TEST_TOKEN",
        database_path=tmp_path / "marketplacepilot.sqlite3",
        telegram_webhook_secret="demo-secret",
        webhook_base_url="https://example.onrender.com",
    )

    async def runtime_factory(_: Settings) -> WebRuntime:
        return runtime

    return TestClient(create_app(settings, runtime_factory=runtime_factory)), bot, dispatcher


def _update_payload() -> dict[str, object]:
    return {
        "update_id": 7001,
        "message": {
            "message_id": 1,
            "date": 1,
            "chat": {"id": 42, "type": "private"},
            "from": {"id": 42, "is_bot": False, "first_name": "Демо"},
            "text": "/start",
        },
    }
