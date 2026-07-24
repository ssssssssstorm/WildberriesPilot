from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from html import escape
from typing import Any

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update
from fastapi import FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import HTMLResponse

from marketplacepilot.bot.router import build_router
from marketplacepilot.config import Settings
from marketplacepilot.demo.gateway import DemoMarketplaceGateway
from marketplacepilot.services.decision_engine import DemoDecisionEngine
from marketplacepilot.services.workflow import WorkflowService
from marketplacepilot.storage.sqlite import SqliteRepository

WEBHOOK_PATH = "/telegram/webhook"


@dataclass(slots=True)
class WebRuntime:
    bot: Any
    dispatcher: Any
    telegram_url: str | None

    async def close(self) -> None:
        await self.dispatcher.storage.close()
        await self.bot.session.close()


RuntimeFactory = Callable[[Settings], Awaitable[WebRuntime]]


def create_app(
    settings: Settings | None = None,
    *,
    runtime_factory: RuntimeFactory | None = None,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        resolved_settings = settings or await Settings.from_environment(require_webhook=True)
        factory = runtime_factory or _create_runtime
        app.state.settings = resolved_settings
        app.state.runtime = await factory(resolved_settings)
        try:
            yield
        finally:
            await app.state.runtime.close()

    app = FastAPI(title="MarketPlacePilot", lifespan=lifespan)

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request) -> str:
        telegram_url = request.app.state.runtime.telegram_url
        link = ""
        if telegram_url:
            link = f'<p><a href="{escape(telegram_url, quote=True)}">Открыть Telegram-демо</a></p>'
        return (
            "<h1>MarketPlacePilot demo is active</h1>"
            "<p>ДЕМО-РЕЖИМ · Искусственные данные. "
            "WB API, LLM и реальные сообщения покупателям не используются.</p>"
            f"{link}"
        )

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok", "mode": "demo"}

    @app.post(WEBHOOK_PATH)
    async def telegram_webhook(
        request: Request,
        x_telegram_bot_api_secret_token: str | None = Header(default=None),
    ) -> Response:
        runtime: WebRuntime = request.app.state.runtime
        expected_secret: str = request.app.state.settings.telegram_webhook_secret
        if x_telegram_bot_api_secret_token != expected_secret:
            raise HTTPException(status_code=403, detail="Invalid webhook secret.")
        payload = await request.json()
        update = Update.model_validate(payload, context={"bot": runtime.bot})
        await runtime.dispatcher.feed_update(runtime.bot, update)
        return Response(status_code=200)

    return app


async def _create_runtime(settings: Settings) -> WebRuntime:
    repository = SqliteRepository(settings.database_path)
    await repository.initialize()
    workflow = WorkflowService(repository, DemoMarketplaceGateway(), DemoDecisionEngine())
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.include_router(build_router(workflow))
    bot = Bot(settings.telegram_bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await bot.set_webhook(
        url=f"{settings.webhook_base_url}{WEBHOOK_PATH}",
        secret_token=settings.telegram_webhook_secret,
        allowed_updates=dispatcher.resolve_used_update_types(),
    )
    bot_info = await bot.get_me()
    telegram_url = f"https://t.me/{bot_info.username}" if bot_info.username else None
    return WebRuntime(bot, dispatcher, telegram_url)


app = create_app()
