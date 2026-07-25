from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from marketplacepilot.bot.renderers import kind_icon, priority_icon
from marketplacepilot.models import Task, TaskStatus


def shift_keyboard(focus_task: Task | None) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if focus_task:
        rows.append([InlineKeyboardButton(text="🎯 Открыть следующую задачу", callback_data=f"task:{focus_task.id}")])
    rows.extend(
        [
            [InlineKeyboardButton(text="📬 Открыть всю очередь", callback_data="queue")],
            [InlineKeyboardButton(text="ℹ️ Как помогает AI-менеджер", callback_data="about")],
            [InlineKeyboardButton(text="↻ Начать демонстрацию заново", callback_data="reset")],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def about_keyboard(focus_task: Task | None) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if focus_task:
        rows.append([InlineKeyboardButton(text="🎯 Открыть следующую задачу", callback_data=f"task:{focus_task.id}")])
    rows.append([InlineKeyboardButton(text="‹ На главный экран", callback_data="shift")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def queue_keyboard(tasks: list[Task]) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"{priority_icon(task.priority)} {kind_icon(task.kind)} {task.subject}",
                callback_data=f"task:{task.id}",
            )
        ]
        for task in tasks
    ]
    rows.append([InlineKeyboardButton(text="‹ На главный экран", callback_data="shift")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def task_keyboard(task: Task) -> InlineKeyboardMarkup:
    if task.status is TaskStatus.COMPLETED:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📬 К следующей задаче", callback_data="queue")],
                [InlineKeyboardButton(text="⌂ На главный экран", callback_data="shift")],
            ]
        )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✍️ Посмотреть ответ AI", callback_data=f"draft:{task.id}")],
            [InlineKeyboardButton(text="👤 Передать человеку", callback_data=f"handoff:{task.id}")],
            [InlineKeyboardButton(text="🕓 Отложить", callback_data=f"defer:{task.id}")],
            *(
                []
                if task.requires_confirmation
                else [[InlineKeyboardButton(text="✓ Закрыть без ответа", callback_data=f"close:{task.id}")]]
            ),
            [InlineKeyboardButton(text="‹ К очереди", callback_data="queue")],
        ]
    )


def draft_keyboard(task: Task) -> InlineKeyboardMarkup:
    if task.requires_confirmation:
        primary = InlineKeyboardButton(text="✅ Подтвердить возврат", callback_data=f"confirm:{task.id}")
    else:
        primary = InlineKeyboardButton(text="✅ Подтвердить ответ", callback_data=f"send:{task.id}")
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [primary],
            [InlineKeyboardButton(text="✏️ Изменить текст", callback_data=f"edit:{task.id}")],
            [InlineKeyboardButton(text="👤 Передать человеку", callback_data=f"handoff:{task.id}")],
            [InlineKeyboardButton(text="‹ К задаче", callback_data=f"task:{task.id}")],
        ]
    )
