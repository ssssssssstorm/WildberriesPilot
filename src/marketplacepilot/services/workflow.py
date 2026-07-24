from __future__ import annotations

from marketplacepilot.demo.gateway import MarketplaceGateway
from marketplacepilot.models import Priority, ShiftSummary, Task, TaskKind, TaskStatus
from marketplacepilot.services.decision_engine import DemoDecisionEngine
from marketplacepilot.storage.sqlite import SqliteRepository


class TransitionError(ValueError):
    pass


class WorkflowService:
    def __init__(
        self,
        repository: SqliteRepository,
        gateway: MarketplaceGateway,
        decision_engine: DemoDecisionEngine,
    ) -> None:
        self._repository = repository
        self._gateway = gateway
        self._decision_engine = decision_engine

    async def ensure_session(self, user_id: int) -> None:
        tasks = await self._build_seed_tasks()
        await self._repository.ensure_session(user_id, tasks)

    async def reset_demo(self, user_id: int) -> None:
        tasks = await self._build_seed_tasks()
        await self._repository.reset_session(user_id, tasks)

    async def get_summary(self, user_id: int) -> ShiftSummary:
        tasks = await self._repository.list_tasks(user_id, include_completed=False)
        return ShiftSummary(
            questions=sum(task.kind is TaskKind.QUESTION for task in tasks),
            reviews=sum(task.kind is TaskKind.REVIEW for task in tasks),
            dialogues=sum(task.kind is TaskKind.DIALOGUE for task in tasks),
            returns=sum(task.kind is TaskKind.RETURN for task in tasks),
            urgent=sum(task.priority is Priority.URGENT for task in tasks),
            awaiting_human=sum(task.status is TaskStatus.AWAITING_HUMAN or task.needs_human for task in tasks),
            open_tasks=len(tasks),
        )

    async def list_open_tasks(self, user_id: int) -> list[Task]:
        return await self._repository.list_tasks(user_id, include_completed=False)

    async def get_task(self, user_id: int, task_id: str) -> Task:
        return await self._repository.get_task(user_id, task_id)

    async def edit_draft(self, user_id: int, task_id: str, draft: str) -> None:
        cleaned_draft = draft.strip()
        if not cleaned_draft:
            raise TransitionError("Черновик не может быть пустым.")
        await self._repository.update_draft(user_id, task_id, cleaned_draft)

    async def send_simulated_response(self, user_id: int, task_id: str) -> None:
        task = await self.get_task(user_id, task_id)
        self._ensure_open(task)
        if task.requires_confirmation:
            raise TransitionError("Возврат нельзя завершить без подтверждения человека.")
        await self._repository.apply_action(
            user_id,
            task_id,
            TaskStatus.COMPLETED,
            "simulated_response_sent",
            "Ответ подтверждён и отправлен в симуляции.",
        )

    async def confirm_return(self, user_id: int, task_id: str) -> None:
        task = await self.get_task(user_id, task_id)
        self._ensure_open(task)
        if not task.requires_confirmation:
            raise TransitionError("Подтверждение возврата доступно только для заявок на возврат.")
        await self._repository.apply_action(
            user_id,
            task_id,
            TaskStatus.COMPLETED,
            "return_confirmed_by_human",
            "Возврат подтверждён человеком в симуляции.",
            return_confirmed=True,
        )

    async def handoff_to_human(self, user_id: int, task_id: str) -> None:
        task = await self.get_task(user_id, task_id)
        self._ensure_open(task)
        await self._repository.apply_action(
            user_id, task_id, TaskStatus.AWAITING_HUMAN, "handed_to_human", "Задача передана человеку."
        )

    async def defer_task(self, user_id: int, task_id: str) -> None:
        task = await self.get_task(user_id, task_id)
        self._ensure_open(task)
        await self._repository.apply_action(user_id, task_id, TaskStatus.DEFERRED, "deferred", "Задача отложена.")

    async def close_task(self, user_id: int, task_id: str) -> None:
        task = await self.get_task(user_id, task_id)
        self._ensure_open(task)
        if task.requires_confirmation:
            raise TransitionError("Заявку на возврат нельзя закрыть без подтверждения человека.")
        await self._repository.apply_action(
            user_id, task_id, TaskStatus.COMPLETED, "closed", "Задача закрыта пользователем."
        )

    async def _build_seed_tasks(self) -> list[Task]:
        products = await self._gateway.fetch_products()
        incoming_tasks = await self._gateway.fetch_tasks()
        tasks: list[Task] = []
        for incoming in incoming_tasks:
            recommendation = self._decision_engine.recommend(incoming, products[incoming.product_id])
            tasks.append(
                Task(
                    id=incoming.id,
                    kind=incoming.kind,
                    status=TaskStatus.NEW,
                    product=products[incoming.product_id],
                    buyer_label=incoming.buyer_label,
                    subject=incoming.subject,
                    message=incoming.message,
                    history=incoming.history,
                    scenario=recommendation.scenario,
                    priority=recommendation.priority,
                    priority_reason=recommendation.priority_reason,
                    draft=recommendation.draft,
                    proposed_action=recommendation.proposed_action,
                    risks=recommendation.risks,
                    needs_human=recommendation.needs_human,
                    requires_confirmation=recommendation.requires_confirmation,
                )
            )
        return tasks

    @staticmethod
    def _ensure_open(task: Task) -> None:
        if task.status is TaskStatus.COMPLETED:
            raise TransitionError("Задача уже завершена.")
