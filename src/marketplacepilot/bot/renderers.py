from __future__ import annotations

from html import escape

from marketplacepilot.models import Priority, ShiftSummary, Task, TaskKind, TaskStatus

DEMO_BANNER = "<b>ДЕМО-РЕЖИМ · Искусственные данные</b>"


def render_shift(summary: ShiftSummary) -> str:
    return (
        f"{DEMO_BANNER}\n\n"
        "<b>Рабочая смена MarketPlacePilot</b>\n"
        "AI-менеджер Wildberries: очередь на сегодня.\n\n"
        f"Новые вопросы: <b>{summary.questions}</b>\n"
        f"Отзывы: <b>{summary.reviews}</b>\n"
        f"Диалоги: <b>{summary.dialogues}</b>\n"
        f"Возвраты: <b>{summary.returns}</b>\n"
        f"Срочные задачи: <b>{summary.urgent}</b>\n"
        f"Ожидают решения человека: <b>{summary.awaiting_human}</b>\n\n"
        f"В работе: <b>{summary.open_tasks}</b>. Выберите очередь, чтобы открыть задачу."
    )


def render_queue(tasks: list[Task]) -> str:
    lines = [DEMO_BANNER, "", "<b>Очередь менеджера</b>"]
    for task in tasks:
        lines.append(f"{_priority_marker(task.priority)} <b>{escape(task.subject)}</b> · {_kind_label(task.kind)}")
    if not tasks:
        lines.append("Все задачи рабочей смены завершены.")
    return "\n".join(lines)


def render_task(task: Task) -> str:
    risks = "\n".join(f"• {escape(risk)}" for risk in task.risks) or "• Не выявлены для выбранного сценария."
    history = "\n".join(f"• {escape(item)}" for item in task.history)
    confirmation = ""
    if task.requires_confirmation:
        confirmation = "\nТребуется подтверждение человека перед завершением возврата."
    status_line = (
        f"Статус: <b>{_status_label(task.status)}</b> · {_priority_marker(task.priority)} "
        f"{escape(task.priority_reason)}\n\n"
    )
    product_details = (
        f"<b>Товар</b>\n{escape(task.product.name)} · {escape(task.product.category)}\n{escape(task.product.facts)}\n\n"
    )
    details = (
        product_details + f"<b>Покупатель</b>\n{escape(task.buyer_label)}\n\n"
        f"<b>Обращение</b>\n{escape(task.message)}\n\n"
        f"<b>История</b>\n{history}\n\n"
        f"<b>Сценарий AI</b>\n{escape(task.scenario)}\n"
        f"Действие: {escape(task.proposed_action)}\n\n"
        f"<b>Черновик ответа</b>\n{escape(task.draft)}\n\n"
        f"<b>Риски</b>\n{risks}{confirmation}\n\n"
        "Все действия ниже выполняются только в симуляции."
    )
    return f"{DEMO_BANNER}\n\n<b>{escape(task.subject)}</b>\n" + status_line + details


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
