from dataclasses import replace

from marketplacepilot.bot.keyboards import about_keyboard, draft_keyboard, queue_keyboard, shift_keyboard, task_keyboard
from marketplacepilot.bot.renderers import render_draft, render_shift
from marketplacepilot.models import Priority, Product, ShiftSummary, Task, TaskKind, TaskStatus


def test_task_risks_render_as_one_bullet_for_legacy_string() -> None:
    task = Task(
        id="task",
        kind=TaskKind.DIALOGUE,
        status=TaskStatus.NEW,
        product=Product("product", "Товар", "Категория", "Факт"),
        buyer_label="Покупатель ••• 1234",
        subject="Доставка",
        message="Когда привезут?",
        history=("Покупатель написал сегодня.",),
        scenario="Статус доставки",
        priority=Priority.NORMAL,
        priority_reason="Срок зависит от Wildberries.",
        draft="Здравствуйте! Проверяем статус.",
        proposed_action="Подготовить ответ",
        risks="Точный срок доставки зависит от Wildberries.",  # type: ignore[arg-type]
        needs_human=False,
        requires_confirmation=False,
    )

    text = render_draft(task)

    assert "• Точный срок доставки зависит от Wildberries." in text
    assert "• Т\n• о\n• ч" not in text


def test_first_screen_guides_seller_to_the_important_task() -> None:
    task = _task()

    text = render_shift(ShiftSummary(3, 2, 2, 2, 1, 2, 9), task)
    buttons = shift_keyboard(task)

    assert "Главное сейчас" in text
    assert "Открыть следующую задачу" in buttons.inline_keyboard[0][0].text
    assert buttons.inline_keyboard[0][0].callback_data == "task:task"


def test_task_and_draft_actions_follow_a_clear_sequence() -> None:
    task = _task()

    task_actions = _callback_data(task_keyboard(task))
    draft_actions = _callback_data(draft_keyboard(task))

    assert task_actions[0] == "draft:task"
    assert "send:task" not in task_actions
    assert draft_actions[0] == "send:task"
    assert "edit:task" in draft_actions


def test_all_button_routes_are_supported_by_the_bot_flow() -> None:
    task = _task()
    completed_task = replace(task, status=TaskStatus.COMPLETED)
    return_task = replace(task, kind=TaskKind.RETURN, requires_confirmation=True)
    routes = {
        *(_callback_data(shift_keyboard(task))),
        *(_callback_data(about_keyboard(task))),
        *(_callback_data(queue_keyboard([task]))),
        *(_callback_data(task_keyboard(task))),
        *(_callback_data(task_keyboard(completed_task))),
        *(_callback_data(draft_keyboard(task))),
        *(_callback_data(draft_keyboard(return_task))),
    }

    supported_prefixes = {"task", "draft", "send", "confirm", "edit", "handoff", "defer", "close"}
    supported_actions = {"queue", "about", "shift", "reset"}
    for route in routes:
        action = route.split(":", maxsplit=1)[0]
        assert action in supported_actions | supported_prefixes


def _task() -> Task:
    return Task(
        id="task",
        kind=TaskKind.DIALOGUE,
        status=TaskStatus.NEW,
        product=Product("product", "Товар", "Категория", "Факт"),
        buyer_label="Покупатель ••• 1234",
        subject="Доставка",
        message="Когда привезут?",
        history=("Покупатель написал сегодня.",),
        scenario="Статус доставки",
        priority=Priority.NORMAL,
        priority_reason="Срок зависит от Wildberries.",
        draft="Здравствуйте! Проверяем статус.",
        proposed_action="Подготовить ответ",
        risks="Точный срок доставки зависит от Wildberries.",  # type: ignore[arg-type]
        needs_human=False,
        requires_confirmation=False,
    )


def _callback_data(keyboard) -> list[str]:
    return [button.callback_data for row in keyboard.inline_keyboard for button in row]
