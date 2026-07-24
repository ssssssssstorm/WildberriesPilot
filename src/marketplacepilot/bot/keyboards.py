from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from marketplacepilot.models import Task, TaskKind, TaskStatus


def shift_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📬 Открыть очередь", callback_data="queue")],
            [InlineKeyboardButton(text="↻ Начать смену заново", callback_data="reset")],
        ]
    )


def queue_keyboard(tasks: list[Task]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"{_kind_icon(task.kind)} {task.subject}", callback_data=f"task:{task.id}")]
        for task in tasks
    ]
    rows.append([InlineKeyboardButton(text="‹ К сводке", callback_data="shift")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def task_keyboard(task: Task) -> InlineKeyboardMarkup:
    if task.status is TaskStatus.COMPLETED:
        return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="‹ К очереди", callback_data="queue")]])
    rows: list[list[InlineKeyboardButton]] = []
    if task.requires_confirmation:
        rows.append([InlineKeyboardButton(text="✅ Подтвердить возврат", callback_data=f"confirm:{task.id}")])
    else:
        rows.append([InlineKeyboardButton(text="✅ Подтвердить ответ", callback_data=f"send:{task.id}")])
    rows.extend(
        [
            [InlineKeyboardButton(text="✏️ Изменить ответ", callback_data=f"edit:{task.id}")],
            [
                InlineKeyboardButton(text="👤 Передать человеку", callback_data=f"handoff:{task.id}"),
                InlineKeyboardButton(text="🕓 Отложить", callback_data=f"defer:{task.id}"),
            ],
            [InlineKeyboardButton(text="✓ Закрыть задачу", callback_data=f"close:{task.id}")],
            [InlineKeyboardButton(text="‹ К очереди", callback_data="queue")],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _kind_icon(kind: TaskKind) -> str:
    return {
        TaskKind.QUESTION: "❓",
        TaskKind.REVIEW: "⭐",
        TaskKind.DIALOGUE: "💬",
        TaskKind.RETURN: "↩️",
    }[kind]
