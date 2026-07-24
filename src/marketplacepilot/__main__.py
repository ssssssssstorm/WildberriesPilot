from __future__ import annotations

import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from marketplacepilot.bot.router import build_router
from marketplacepilot.config import Settings
from marketplacepilot.demo.gateway import DemoMarketplaceGateway
from marketplacepilot.services.decision_engine import DemoDecisionEngine
from marketplacepilot.services.workflow import WorkflowService
from marketplacepilot.storage.sqlite import SqliteRepository


async def run() -> None:
    settings = await Settings.from_environment()
    repository = SqliteRepository(settings.database_path)
    await repository.initialize()
    workflow = WorkflowService(repository, DemoMarketplaceGateway(), DemoDecisionEngine())
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.include_router(build_router(workflow))
    bot = Bot(settings.telegram_bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dispatcher.start_polling(bot)


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
