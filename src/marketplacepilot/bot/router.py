from __future__ import annotations

from collections.abc import Awaitable, Callable

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from marketplacepilot.bot.keyboards import about_keyboard, draft_keyboard, queue_keyboard, shift_keyboard, task_keyboard
from marketplacepilot.bot.renderers import render_about, render_draft, render_queue, render_shift, render_task
from marketplacepilot.services.workflow import TransitionError, WorkflowService
from marketplacepilot.storage.sqlite import TaskNotFoundError


class DraftEdit(StatesGroup):
    waiting_for_text = State()


def build_router(workflow: WorkflowService) -> Router:
    router = Router(name="marketplacepilot")

    @router.message(CommandStart())
    async def start(message: Message) -> None:
        await workflow.ensure_session(message.from_user.id)
        await _show_shift(message, workflow)

    @router.callback_query(F.data == "shift")
    async def shift(callback: CallbackQuery) -> None:
        await workflow.ensure_session(callback.from_user.id)
        await _show_shift(callback, workflow)

    @router.callback_query(F.data == "queue")
    async def queue(callback: CallbackQuery) -> None:
        await workflow.ensure_session(callback.from_user.id)
        await _show_queue(callback, workflow)

    @router.callback_query(F.data == "about")
    async def about(callback: CallbackQuery) -> None:
        await workflow.ensure_session(callback.from_user.id)
        await _show_about(callback, workflow)

    @router.callback_query(F.data == "reset")
    async def reset(callback: CallbackQuery) -> None:
        await workflow.reset_demo(callback.from_user.id)
        await _answer_callback(callback, "Смена начата заново ✨")
        await _show_shift(callback, workflow, acknowledge=False)

    @router.callback_query(F.data.startswith("task:"))
    async def task_details(callback: CallbackQuery) -> None:
        await workflow.ensure_session(callback.from_user.id)
        task_id = _task_id(callback)
        await _show_task(callback, workflow, task_id)

    @router.callback_query(F.data.startswith("draft:"))
    async def draft_details(callback: CallbackQuery) -> None:
        await workflow.ensure_session(callback.from_user.id)
        await _show_draft(callback, workflow, _task_id(callback))

    @router.callback_query(F.data.startswith("edit:"))
    async def request_draft_edit(callback: CallbackQuery, state: FSMContext) -> None:
        await workflow.ensure_session(callback.from_user.id)
        task = await workflow.get_task(callback.from_user.id, _task_id(callback))
        await state.update_data(task_id=task.id)
        await state.set_state(DraftEdit.waiting_for_text)
        await _answer_callback(callback)
        await _answer(callback, "✏️ Пришлите новый текст ответа одним сообщением.\nЯ сохраню его в текущей сессии.")

    @router.message(DraftEdit.waiting_for_text, F.text)
    async def save_draft(message: Message, state: FSMContext) -> None:
        data = await state.get_data()
        task_id = data["task_id"]
        try:
            await workflow.edit_draft(message.from_user.id, task_id, message.text)
        except TransitionError as error:
            await message.answer(str(error))
            return
        await state.clear()
        task = await workflow.get_task(message.from_user.id, task_id)
        await message.answer("✅ Текст сохранён.\n\n" + render_draft(task), reply_markup=draft_keyboard(task))

    @router.callback_query(F.data.startswith("send:"))
    async def send_response(callback: CallbackQuery) -> None:
        await _run_action(callback, workflow, workflow.send_simulated_response, "Ответ подтверждён ✅")

    @router.callback_query(F.data.startswith("confirm:"))
    async def confirm_return(callback: CallbackQuery) -> None:
        await _run_action(callback, workflow, workflow.confirm_return, "Возврат подтверждён человеком ✅")

    @router.callback_query(F.data.startswith("handoff:"))
    async def handoff(callback: CallbackQuery) -> None:
        await _run_action(callback, workflow, workflow.handoff_to_human, "Задача передана человеку 👤")

    @router.callback_query(F.data.startswith("defer:"))
    async def defer(callback: CallbackQuery) -> None:
        await _run_action(callback, workflow, workflow.defer_task, "Задача отложена 🕓")

    @router.callback_query(F.data.startswith("close:"))
    async def close(callback: CallbackQuery) -> None:
        await _run_action(callback, workflow, workflow.close_task, "Задача закрыта ✓")

    @router.message(F.text)
    async def fallback(message: Message) -> None:
        await message.answer("Откройте рабочую смену командой /start ✨")

    return router


async def _run_action(
    callback: CallbackQuery,
    workflow: WorkflowService,
    action: Callable[[int, str], Awaitable[None]],
    success_message: str,
) -> None:
    task_id = _task_id(callback)
    try:
        await action(callback.from_user.id, task_id)
    except (TaskNotFoundError, TransitionError) as error:
        await _answer_callback(callback, str(error), show_alert=True)
        return
    await _answer_callback(callback, success_message)
    await _show_task(callback, workflow, task_id, acknowledge=False)


async def _show_shift(
    event: Message | CallbackQuery,
    workflow: WorkflowService,
    *,
    acknowledge: bool = True,
) -> None:
    user_id = _user_id(event)
    summary = await workflow.get_summary(user_id)
    tasks = await workflow.list_open_tasks(user_id)
    focus_task = tasks[0] if tasks else None
    if acknowledge and isinstance(event, CallbackQuery):
        await _answer_callback(event)
    await _replace_or_answer(event, render_shift(summary, focus_task), shift_keyboard(focus_task))


async def _show_about(callback: CallbackQuery, workflow: WorkflowService) -> None:
    tasks = await workflow.list_open_tasks(callback.from_user.id)
    focus_task = tasks[0] if tasks else None
    await _answer_callback(callback)
    await _replace_or_answer(callback, render_about(), about_keyboard(focus_task))


async def _show_queue(event: CallbackQuery, workflow: WorkflowService) -> None:
    tasks = await workflow.list_open_tasks(event.from_user.id)
    await _answer_callback(event)
    await _replace_or_answer(event, render_queue(tasks), queue_keyboard(tasks))


async def _show_task(
    callback: CallbackQuery,
    workflow: WorkflowService,
    task_id: str,
    *,
    acknowledge: bool = True,
) -> None:
    try:
        task = await workflow.get_task(callback.from_user.id, task_id)
    except TaskNotFoundError:
        await _answer_callback(callback, "Задача не найдена. Попробуйте сбросить демо.", show_alert=True)
        return
    if acknowledge:
        await _answer_callback(callback)
    await _replace_or_answer(callback, render_task(task), task_keyboard(task))


async def _show_draft(callback: CallbackQuery, workflow: WorkflowService, task_id: str) -> None:
    try:
        task = await workflow.get_task(callback.from_user.id, task_id)
    except TaskNotFoundError:
        await _answer_callback(callback, "Задача не найдена. Откройте смену заново.", show_alert=True)
        return
    await _answer_callback(callback)
    await _replace_or_answer(callback, render_draft(task), draft_keyboard(task))


async def _replace_or_answer(event: Message | CallbackQuery, text: str, reply_markup: object) -> None:
    if isinstance(event, CallbackQuery) and event.message:
        try:
            await event.message.edit_text(text, reply_markup=reply_markup)
        except TelegramBadRequest as error:
            message = error.message.lower()
            if "message is not modified" in message:
                return
            if "message to edit not found" in message or "message can't be edited" in message:
                await event.message.answer(text, reply_markup=reply_markup)
                return
            raise
        return
    if isinstance(event, Message):
        await event.answer(text, reply_markup=reply_markup)


async def _answer(callback: CallbackQuery, text: str) -> None:
    if callback.message:
        await callback.message.answer(text)


async def _answer_callback(callback: CallbackQuery, text: str | None = None, *, show_alert: bool = False) -> None:
    try:
        await callback.answer(text, show_alert=show_alert)
    except TelegramBadRequest as error:
        message = error.message.lower()
        if "query is too old" not in message and "query id is invalid" not in message:
            raise


def _task_id(callback: CallbackQuery) -> str:
    if not callback.data or ":" not in callback.data:
        raise ValueError("Некорректное действие.")
    return callback.data.split(":", maxsplit=1)[1]


def _user_id(event: Message | CallbackQuery) -> int:
    if isinstance(event, CallbackQuery):
        return event.from_user.id
    return event.from_user.id
