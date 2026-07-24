from pathlib import Path

import pytest

from marketplacepilot.demo.gateway import DemoMarketplaceGateway
from marketplacepilot.services.decision_engine import DemoDecisionEngine
from marketplacepilot.services.workflow import WorkflowService
from marketplacepilot.storage.sqlite import SqliteRepository


@pytest.fixture
async def workflow(tmp_path: Path) -> WorkflowService:
    repository = SqliteRepository(tmp_path / "marketplacepilot.sqlite3")
    await repository.initialize()
    return WorkflowService(repository, DemoMarketplaceGateway(), DemoDecisionEngine())
