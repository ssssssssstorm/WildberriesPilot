from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from marketplacepilot.bot.renderers import kind_icon, priority_icon
from marketplacepilot.models import Task, TaskStatus


def welcome_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да, приступаем", callback_data="workspace")],
            [InlineKeyboardButton(text="🕓 Нет, позже", callback_data="pause")],
        ]
    )


def pause_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="▶️ Приступить", callback_data="workspace")],
            [InlineKeyboardButton(text="ℹ️ О боте", callback_data="about")],
        ]
    )


def workspace_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Решения AI", callback_data="group:agent")],
            [InlineKeyboardButton(text="👤 Передано менеджеру", callback_data="group:manager")],
            [InlineKeyboardButton(text="🔴 Требуют вашего решения", callback_data="group:decision")],
        ]
    )


def group_keyboard(group: str, tasks: list[Task]) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"{priority_icon(task.priority)} {kind_icon(task.kind)} {task.subject}",
                callback_data=f"task:{task.id}",
            )
        ]
        for task in tasks
    ]
    rows.append([InlineKeyboardButton(text="‹ К обзору", callback_data="workspace")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def task_keyboard(task: Task) -> InlineKeyboardMarkup:
    if task.status is TaskStatus.COMPLETED:
        return InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="⌂ К обзору задач", callback_data="workspace")]]
        )
    rows = [
        [InlineKeyboardButton(text="✍️ Открыть решение AI", callback_data=f"draft:{task.id}")],
        [InlineKeyboardButton(text="⚙️ Другие действия", callback_data=f"actions:{task.id}")],
        [InlineKeyboardButton(text="‹ К обзору", callback_data="workspace")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def draft_keyboard(task: Task) -> InlineKeyboardMarkup:
    if task.requires_confirmation:
        primary = InlineKeyboardButton(text="✅ Подтвердить возврат", callback_data=f"confirm:{task.id}")
    else:
        primary = InlineKeyboardButton(text="✅ Подтвердить решение", callback_data=f"send:{task.id}")
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [primary],
            [InlineKeyboardButton(text="✏️ Изменить текст", callback_data=f"edit:{task.id}")],
            [InlineKeyboardButton(text="👤 Передать менеджеру", callback_data=f"handoff:{task.id}")],
            [InlineKeyboardButton(text="‹ К задаче", callback_data=f"task:{task.id}")],
        ]
    )


def task_actions_keyboard(task: Task) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="👤 Передать менеджеру", callback_data=f"handoff:{task.id}")],
        [InlineKeyboardButton(text="🕓 Отложить", callback_data=f"defer:{task.id}")],
    ]
    if not task.requires_confirmation:
        rows.append([InlineKeyboardButton(text="✓ Закрыть без ответа", callback_data=f"close:{task.id}")])
    rows.append([InlineKeyboardButton(text="‹ К задаче", callback_data=f"task:{task.id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def about_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="▶️ Приступить к задачам", callback_data="workspace")],
            [InlineKeyboardButton(text="↻ Сбросить рабочий день", callback_data="reset")],
        ]
    )
