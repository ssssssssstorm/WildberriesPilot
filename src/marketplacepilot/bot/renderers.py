from __future__ import annotations

from html import escape

from marketplacepilot.models import Priority, Task, TaskKind, TaskStatus


def render_welcome() -> str:
    return (
        "<b>🌙 Добрый вечер, Сэр!</b>\n\n"
        "🤖 Я собрал все события в вашем магазине на Wildberries за сегодня.\n\n"
        "Приступим к их решению?"
    )


def render_pause() -> str:
    return (
        "<b>🕓 Хорошо, Сэр.</b>\n\n"
        "Я оставил рабочий день в готовности. Когда будете готовы — вернёмся к обращениям покупателей."
    )


def render_workspace(agent_count: int, manager_count: int, decision_count: int) -> str:
    return (
        "<b>🧠 Рабочий день готов</b>\n\n"
        "Я распределил все обращения и подготовил следующий шаг для каждого.\n\n"
        f"✅ <b>Решения AI</b> — {agent_count}\n"
        f"👤 <b>Передано менеджеру</b> — {manager_count}\n"
        f"🔴 <b>Требуют вашего решения</b> — {decision_count}\n\n"
        "Выберите раздел, с которого начнём."
    )


def render_group(group: str, tasks: list[Task]) -> str:
    titles = {
        "agent": ("✅ Решения AI", "Я подготовил ответ и действие по каждому обращению."),
        "manager": (
            "👤 Передано менеджеру",
            "Эти случаи требуют проверки специалиста, прежде чем обещать результат покупателю.",
        ),
        "decision": (
            "🔴 Требуют вашего решения",
            "Здесь нужен ваш выбор: AI не завершает такие действия самостоятельно.",
        ),
    }
    title, description = titles[group]
    if not tasks:
        return f"<b>{title}</b>\n\n🎉 Сейчас здесь нет задач."
    return f"<b>{title}</b>\n\n{description}\n\nВыберите обращение, чтобы увидеть вывод AI."


def render_task(task: Task) -> str:
    if task.status is TaskStatus.COMPLETED:
        return (
            "<b>✅ Задача завершена</b>\n\n"
            f"{_kind_icon(task.kind)} <b>{escape(task.subject)}</b>\n\n"
            "Решение зафиксировано. Я готов перейти к следующему обращению."
        )

    role_note = "✅ Я подготовил безопасное решение и ответ покупателю."
    if task.needs_human and not task.requires_confirmation:
        role_note = "👤 Я передал задачу на проверку менеджеру: здесь нужна точность."
    if task.requires_confirmation:
        role_note = "🔴 Нужен ваш выбор. Возврат нельзя завершить без подтверждения."
    return (
        f"{_priority_marker(task.priority)}\n"
        f"<b>{escape(task.subject)}</b>\n\n"
        f"<b>🛍 Товар</b>\n{escape(task.product.name)}\n\n"
        f"<b>💬 Покупатель пишет</b>\n{escape(task.message)}\n\n"
        f"<b>🤖 Что я сделал</b>\n{escape(task.scenario)}\n"
        f"→ {escape(task.proposed_action)}\n\n"
        f"{role_note}\n\n"
        "Откройте подготовленный ответ, чтобы принять решение."
    )


def render_draft(task: Task) -> str:
    risks = _bullet_list(task.risks, "Существенных рисков не выявлено.")
    confirmation = ""
    if task.requires_confirmation:
        confirmation = "\n\n<b>🔐 Важно</b>\nПодтверждение возврата доступно только вам."
    return (
        "<b>✍️ Ответ подготовлен</b>\n\n"
        f"<b>Покупателю</b>\n{escape(task.draft)}\n\n"
        f"<b>⚠️ Учесть</b>\n{risks}{confirmation}\n\n"
        "Проверьте текст и выберите действие."
    )


def render_task_actions(task: Task) -> str:
    return (
        "<b>⚙️ Дополнительные действия</b>\n\n"
        f"{_kind_icon(task.kind)} <b>{escape(task.subject)}</b>\n\n"
        "Используйте их, если стандартное решение AI сейчас не подходит."
    )


def render_about() -> str:
    return (
        "<b>ℹ️ О MarketPlacePilot</b>\n\n"
        "Это тестовый режим: товары, обращения и действия созданы для демонстрации сценария.\n\n"
        "В рабочей версии AI-менеджер подключается к магазину через официальный WB API. "
        "Рискованные решения, включая возвраты, всегда подтверждает человек."
    )


def _bullet_list(items: tuple[str, ...], empty_text: str) -> str:
    """Render current tuple data and legacy single-string session values safely."""
    if isinstance(items, str):
        items = (items,)
    return "\n".join(f"• {escape(item)}" for item in items) or f"• {empty_text}"


def kind_icon(kind: TaskKind) -> str:
    return _kind_icon(kind)


def priority_icon(priority: Priority) -> str:
    return {
        Priority.URGENT: "🔴",
        Priority.HIGH: "🟠",
        Priority.NORMAL: "🔵",
        Priority.LOW: "⚪",
    }[priority]


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
