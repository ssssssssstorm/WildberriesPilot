from __future__ import annotations

from typing import Protocol

from marketplacepilot.demo.fixtures import DEMO_PRODUCTS, DEMO_TASKS
from marketplacepilot.models import IncomingTask, Product


class MarketplaceGateway(Protocol):
    """Источник обращений маркетплейса, независимый от Telegram и хранилища."""

    async def fetch_products(self) -> dict[str, Product]: ...

    async def fetch_tasks(self) -> list[IncomingTask]: ...


class DemoMarketplaceGateway:
    """Единственный адаптер первой версии: возвращает синтетические обращения."""

    async def fetch_products(self) -> dict[str, Product]:
        return {product.id: product for product in DEMO_PRODUCTS}

    async def fetch_tasks(self) -> list[IncomingTask]:
        return list(DEMO_TASKS)
