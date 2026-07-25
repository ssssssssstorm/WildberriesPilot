from dataclasses import replace

from marketplacepilot.bot.keyboards import (
    about_keyboard,
    draft_keyboard,
    group_keyboard,
    pause_keyboard,
    task_actions_keyboard,
    task_keyboard,
    welcome_keyboard,
    workspace_keyboard,
)
from marketplacepilot.bot.renderers import render_draft, render_welcome, render_workspace
from marketplacepilot.bot.router import _split_tasks
from marketplacepilot.models import Priority, Product, Task, TaskKind, TaskStatus


def test_welcome_is_a_short_conversation_with_yes_or_no() -> None:
    buttons = welcome_keyboard()

    assert "Добрый вечер, Сэр" in render_welcome()
    assert _callback_data(buttons) == ["workspace", "pause"]


def test_workspace_contains_only_the_three_work_sections() -> None:
    text = render_workspace(agent_count=5, manager_count=2, decision_count=2)
    buttons = workspace_keyboard()

    assert "Решения AI" in text
    assert _callback_data(buttons) == ["group:agent", "group:manager", "group:decision"]


def test_task_risks_render_as_one_bullet_for_legacy_string() -> None:
    task = _task(risks="Точный срок доставки зависит от Wildberries.")  # type: ignore[arg-type]

    text = render_draft(task)

    assert "• Точный срок доставки зависит от Wildberries." in text
    assert "• Т\n• о\n• ч" not in text


def test_tasks_are_split_between_agent_manager_and_owner() -> None:
    safe_task = _task()
    manager_task = replace(safe_task, id="manager", needs_human=True)
    owner_task = replace(safe_task, id="owner", kind=TaskKind.RETURN, needs_human=True, requires_confirmation=True)

    agent_tasks, manager_tasks, decision_tasks = _split_tasks([safe_task, manager_task, owner_task])

    assert [task.id for task in agent_tasks] == ["task"]
    assert [task.id for task in manager_tasks] == ["manager"]
    assert [task.id for task in decision_tasks] == ["owner"]


def test_all_button_routes_are_supported_by_the_bot_flow() -> None:
    task = _task()
    completed_task = replace(task, status=TaskStatus.COMPLETED)
    return_task = replace(task, kind=TaskKind.RETURN, requires_confirmation=True)
    routes = {
        *(_callback_data(welcome_keyboard())),
        *(_callback_data(pause_keyboard())),
        *(_callback_data(workspace_keyboard())),
        *(_callback_data(group_keyboard("agent", [task]))),
        *(_callback_data(task_keyboard(task))),
        *(_callback_data(task_keyboard(completed_task))),
        *(_callback_data(draft_keyboard(task))),
        *(_callback_data(draft_keyboard(return_task))),
        *(_callback_data(task_actions_keyboard(task))),
        *(_callback_data(task_actions_keyboard(return_task))),
        *(_callback_data(about_keyboard())),
    }

    supported = {
        "workspace",
        "pause",
        "about",
        "reset",
        "group",
        "task",
        "draft",
        "actions",
        "send",
        "confirm",
        "edit",
        "handoff",
        "defer",
        "close",
    }
    assert {route.split(":", maxsplit=1)[0] for route in routes} <= supported


def _task(**changes: object) -> Task:
    values: dict[str, object] = {
        "id": "task",
        "kind": TaskKind.DIALOGUE,
        "status": TaskStatus.NEW,
        "product": Product("product", "Товар", "Категория", "Факт"),
        "buyer_label": "Покупатель ••• 1234",
        "subject": "Доставка",
        "message": "Когда привезут?",
        "history": ("Покупатель написал сегодня.",),
        "scenario": "Статус доставки",
        "priority": Priority.NORMAL,
        "priority_reason": "Срок зависит от Wildberries.",
        "draft": "Здравствуйте! Проверяем статус.",
        "proposed_action": "Подготовить ответ",
        "risks": (),
        "needs_human": False,
        "requires_confirmation": False,
    }
    values.update(changes)
    return Task(**values)  # type: ignore[arg-type]


def _callback_data(keyboard) -> list[str]:
    return [button.callback_data for row in keyboard.inline_keyboard for button in row]
