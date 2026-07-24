from __future__ import annotations

from html import escape

from marketplacepilot.models import Priority, ShiftSummary, Task, TaskKind, TaskStatus

DEMO_BANNER = "<b>🧪 ДЕМО · искусственные данные</b>"


def render_shift(summary: ShiftSummary) -> str:
    return (
        f"{DEMO_BANNER}\n\n"
        "<b>✨ Рабочая смена MarketPlacePilot</b>\n"
        "Центр обработки обращений Wildberries\n\n"
        f"📥 Вопросы <b>{summary.questions}</b>   ⭐ Отзывы <b>{summary.reviews}</b>\n"
        f"💬 Диалоги <b>{summary.dialogues}</b>   ↩️ Возвраты <b>{summary.returns}</b>\n"
        f"🔴 Срочные <b>{summary.urgent}</b>   👤 Нужен человек <b>{summary.awaiting_human}</b>\n\n"
        f"<b>{summary.open_tasks} задач</b> в работе. Начните с приоритетных обращений."
    )


def render_queue(tasks: list[Task]) -> str:
    lines = [DEMO_BANNER, "", "<b>📬 Очередь менеджера</b>", "Сначала — обращения с высоким приоритетом.", ""]
    for task in tasks:
        lines.append(f"{_priority_marker(task.priority)} <b>{escape(task.subject)}</b> · {_kind_label(task.kind)}")
    if not tasks:
        lines.append("🎉 Очередь пуста. Все задачи этой смены завершены.")
    return "\n".join(lines)


def render_task(task: Task) -> str:
    risks = _bullet_list(task.risks, "Риски для выбранного сценария не выявлены.")
    history = _bullet_list(task.history, "Дополнительной истории пока нет.")
    confirmation = ""
    if task.requires_confirmation:
        confirmation = (
            "\n\n<b>👤 Решение принимает человек</b>\n"
            "Возврат нельзя завершить без подтверждения ответственного сотрудника."
        )
    status_line = (
        f"{_priority_marker(task.priority)} · <b>{_status_label(task.status)}</b>\n"
        f"📌 {escape(task.priority_reason)}\n\n"
    )
    product_details = (
        f"<b>🛍 Товар</b>\n{escape(task.product.name)} · {escape(task.product.category)}\n"
        f"<i>{escape(task.product.facts)}</i>\n\n"
    )
    details = (
        product_details + f"<b>👤 Покупатель</b>\n{escape(task.buyer_label)}\n\n"
        f"<b>💬 Обращение</b>\n{escape(task.message)}\n\n"
        f"<b>🕘 Контекст</b>\n{history}\n\n"
        f"<b>🤖 План AI-менеджера</b>\n{escape(task.scenario)}\n"
        f"→ {escape(task.proposed_action)}\n\n"
        f"<b>✍️ Готовый ответ</b>\n{escape(task.draft)}\n\n"
        f"<b>⚠️ Учесть</b>\n{risks}{confirmation}"
    )
    return f"{DEMO_BANNER}\n\n<b>{escape(task.subject)}</b>\n" + status_line + details


def _bullet_list(items: tuple[str, ...], empty_text: str) -> str:
    """Render both current tuple data and legacy single-string session values safely."""
    if isinstance(items, str):
        items = (items,)
    return "\n".join(f"• {escape(item)}" for item in items) or f"• {empty_text}"


def _kind_label(kind: TaskKind) -> str:
    return {
        TaskKind.QUESTION: "вопрос",
        TaskKind.REVIEW: "отзыв",
        TaskKind.DIALOGUE: "диалог",
        TaskKind.RETURN: "возврат",
    }[kind]


def _priority_marker(priority: Priority) -> str:
    return {
        Priority.URGENT: "🔴 Срочно",
        Priority.HIGH: "🟠 Высокий",
        Priority.NORMAL: "🔵 Обычный",
        Priority.LOW: "⚪ Низкий",
    }[priority]


def _status_label(status: TaskStatus) -> str:
    return {
        TaskStatus.NEW: "новая",
        TaskStatus.DEFERRED: "отложена",
        TaskStatus.AWAITING_HUMAN: "ожидает человека",
        TaskStatus.COMPLETED: "завершена",
    }[status]
