from marketplacepilot.bot.renderers import render_task
from marketplacepilot.models import Priority, Product, Task, TaskKind, TaskStatus


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

    text = render_task(task)

    assert "• Точный срок доставки зависит от Wildberries." in text
    assert "• Т\n• о\n• ч" not in text
