import pytest

from marketplacepilot.models import Priority, TaskStatus
from marketplacepilot.services.workflow import TransitionError, WorkflowService


@pytest.mark.asyncio
async def test_prioritization_and_handoff_flags(workflow: WorkflowService) -> None:
    await workflow.ensure_session(101)

    urgent_return = await workflow.get_task(101, "t08")
    compatibility_question = await workflow.get_task(101, "t03")
    positive_review = await workflow.get_task(101, "t04")

    assert urgent_return.priority is Priority.URGENT
    assert urgent_return.requires_confirmation is True
    assert compatibility_question.needs_human is True
    assert positive_review.priority is Priority.LOW


@pytest.mark.asyncio
async def test_task_status_transitions(workflow: WorkflowService) -> None:
    await workflow.ensure_session(102)

    await workflow.handoff_to_human(102, "t03")
    handed_off = await workflow.get_task(102, "t03")
    assert handed_off.status is TaskStatus.AWAITING_HUMAN

    await workflow.defer_task(102, "t01")
    deferred = await workflow.get_task(102, "t01")
    assert deferred.status is TaskStatus.DEFERRED

    await workflow.send_simulated_response(102, "t02")
    completed = await workflow.get_task(102, "t02")
    assert completed.status is TaskStatus.COMPLETED


@pytest.mark.asyncio
async def test_return_cannot_be_finished_without_human_confirmation(workflow: WorkflowService) -> None:
    await workflow.ensure_session(103)

    with pytest.raises(TransitionError, match="без подтверждения"):
        await workflow.send_simulated_response(103, "t08")
    with pytest.raises(TransitionError, match="без подтверждения"):
        await workflow.close_task(103, "t08")

    unchanged = await workflow.get_task(103, "t08")
    assert unchanged.status is TaskStatus.NEW

    await workflow.confirm_return(103, "t08")
    confirmed = await workflow.get_task(103, "t08")
    assert confirmed.status is TaskStatus.COMPLETED
    assert confirmed.return_confirmed is True


@pytest.mark.asyncio
async def test_draft_edit_is_persisted(workflow: WorkflowService) -> None:
    await workflow.ensure_session(104)
    draft = "Здравствуйте! Проверили данные и подготовили ответ для вас."

    await workflow.edit_draft(104, "t01", draft)

    task = await workflow.get_task(104, "t01")
    assert task.draft == draft


@pytest.mark.asyncio
async def test_demo_reset_restores_seed_data(workflow: WorkflowService) -> None:
    await workflow.ensure_session(105)
    original_draft = (await workflow.get_task(105, "t01")).draft
    await workflow.edit_draft(105, "t01", "Изменённый черновик")
    await workflow.send_simulated_response(105, "t01")

    await workflow.reset_demo(105)

    restored = await workflow.get_task(105, "t01")
    assert restored.status is TaskStatus.NEW
    assert restored.draft == original_draft


@pytest.mark.asyncio
async def test_sessions_are_isolated(workflow: WorkflowService) -> None:
    await workflow.ensure_session(201)
    await workflow.ensure_session(202)
    await workflow.edit_draft(201, "t02", "Черновик только первой сессии")
    await workflow.send_simulated_response(201, "t01")

    first_task = await workflow.get_task(201, "t01")
    second_task = await workflow.get_task(202, "t01")
    second_draft = await workflow.get_task(202, "t02")

    assert first_task.status is TaskStatus.COMPLETED
    assert second_task.status is TaskStatus.NEW
    assert second_draft.draft != "Черновик только первой сессии"
