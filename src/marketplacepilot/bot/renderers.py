from __future__ import annotations

from html import escape

from marketplacepilot.models import Priority, ShiftSummary, Task, TaskKind, TaskStatus

DEMO_BANNER = "<b>🧪 ДЕМО · искусственные данные</b>"


def render_shift(summary: ShiftSummary, focus_task: Task | None) -> str:
    focus = ""
    if focus_task:
        focus = (
            "\n\n<b>🔴 Главное сейчас</b>\n"
            f"{_kind_icon(focus_task.kind)} <b>{escape(focus_task.subject)}</b>\n"
            f"{escape(focus_task.priority_reason)}\n"
            "AI уже подготовил безопасный сценарий — проверьте его перед решением."
        )
    return (
        f"{DEMO_BANNER}\n\n"
        "<b>🤖 MarketPlacePilot</b>\n"
        "Ваш AI-менеджер Wildberries на смене.\n\n"
        "Я разобрал входящие обращения и расставил приоритеты.\n"
        f"📬 В работе: <b>{summary.open_tasks}</b>\n"
        f"🔴 Срочные: <b>{summary.urgent}</b>   👤 Нужен человек: <b>{summary.awaiting_human}</b>\n"
        f"💬 Вопросы и диалоги: <b>{summary.questions + summary.dialogues}</b>   ⭐ Отзывы: <b>{summary.reviews}</b>"
        f"{focus}\n\n"
        "<b>С чего начнём?</b>"
    )


def render_about() -> str:
    return (
        f"{DEMO_BANNER}\n\n"
        "<b>🤖 Что делает AI-менеджер</b>\n\n"
        "1️⃣ Собирает обращения покупателей в одну очередь.\n"
        "2️⃣ Оценивает срочность и объясняет причину.\n"
        "3️⃣ Готовит ответ по данным товара.\n"
        "4️⃣ Передаёт спорные случаи человеку — особенно возвраты.\n\n"
        "Откройте важную задачу: это самый короткий путь увидеть пользу менеджера."
    )


def render_queue(tasks: list[Task]) -> str:
    if not tasks:
        return f"{DEMO_BANNER}\n\n<b>🎉 Очередь пуста</b>\nВсе задачи этой смены завершены."
    urgent = sum(task.priority is Priority.URGENT for task in tasks)
    return (
        f"{DEMO_BANNER}\n\n"
        "<b>📬 Вся очередь</b>\n"
        f"Открыто задач: <b>{len(tasks)}</b> · срочных: <b>{urgent}</b>\n\n"
        "Выберите обращение — покажу контекст, решение AI и следующий шаг."
    )


def render_task(task: Task) -> str:
    if task.status is TaskStatus.COMPLETED:
        return (
            f"{DEMO_BANNER}\n\n"
            "<b>✅ Задача завершена</b>\n"
            f"{_kind_icon(task.kind)} <b>{escape(task.subject)}</b>\n\n"
            "Решение зафиксировано в этой сессии. Можно перейти к следующему обращению."
        )

    human_note = ""
    if task.needs_human:
        human_note = "\n\n<b>👤 Важно</b>\nФинальное решение остаётся за человеком."
    return (
        f"{DEMO_BANNER}\n\n"
        f"{_priority_marker(task.priority)}\n"
        f"<b>{escape(task.subject)}</b>\n\n"
        f"<b>🛍 Товар</b>\n{escape(task.product.name)} · {escape(task.product.category)}\n\n"
        f"<b>💬 Покупатель пишет</b>\n{escape(task.message)}\n\n"
        f"<b>🤖 Вывод AI-менеджера</b>\n{escape(task.scenario)}\n"
        f"→ {escape(task.proposed_action)}{human_note}\n\n"
        "<b>Следующий шаг</b>\nОткройте подготовленный ответ и примите решение."
    )


def render_draft(task: Task) -> str:
    risks = _bullet_list(task.risks, "Риски для выбранного сценария не выявлены.")
    confirmation = ""
    if task.requires_confirmation:
        confirmation = "\n\n<b>👤 Подтверждение обязательно</b>\nВозврат можно завершить только после вашего решения."
    return (
        f"{DEMO_BANNER}\n\n"
        f"<b>✍️ Ответ подготовлен</b>\n"
        f"{_kind_icon(task.kind)} {escape(task.subject)}\n\n"
        f"<b>Текст для покупателя</b>\n{escape(task.draft)}\n\n"
        f"<b>⚠️ Перед подтверждением</b>\n{risks}{confirmation}\n\n"
        "Проверьте текст и выберите действие ниже."
    )


def _bullet_list(items: tuple[str, ...], empty_text: str) -> str:
    """Render current tuple data and legacy single-string session values safely."""
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


def _kind_icon(kind: TaskKind) -> str:
    return {
        TaskKind.QUESTION: "❓",
        TaskKind.REVIEW: "⭐",
        TaskKind.DIALOGUE: "💬",
        TaskKind.RETURN: "↩️",
    }[kind]


def _priority_marker(priority: Priority) -> str:
    return {
        Priority.URGENT: "🔴 <b>Срочно</b> · требуется ваше решение",
        Priority.HIGH: "🟠 <b>Высокий приоритет</b>",
        Priority.NORMAL: "🔵 <b>Обычный приоритет</b>",
        Priority.LOW: "⚪ <b>Можно обработать позже</b>",
    }[priority]


def priority_icon(priority: Priority) -> str:
    return {
        Priority.URGENT: "🔴",
        Priority.HIGH: "🟠",
        Priority.NORMAL: "🔵",
        Priority.LOW: "⚪",
    }[priority]


def kind_icon(kind: TaskKind) -> str:
    return _kind_icon(kind)
