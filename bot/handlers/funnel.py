from aiogram import F, Router
from aiogram.types import CallbackQuery

from core.texts import (
    get_conditions_text,
    get_expert_text,
    get_for_whom_text,
    get_menu_text,
    get_problem_text,
    get_program_text,
)
from bot.keyboard.funnel import back_kb, menu_kb

router = Router()


@router.callback_query(F.data == "1.1")
async def show_menu(call: CallbackQuery):
    await call.message.edit_text(get_menu_text(), reply_markup=menu_kb())
    await call.answer()


@router.callback_query(F.data == "funnel:problem")
async def show_problem(call: CallbackQuery, db):
    await call.message.edit_text(get_problem_text(), reply_markup=back_kb())
    await call.answer()
    await db.update_user(call.from_user.id, registration_status="funnel")


@router.callback_query(F.data == "funnel:program")
async def show_program(call: CallbackQuery):
    await call.message.edit_text(get_program_text(), reply_markup=back_kb())
    await call.answer()


@router.callback_query(F.data == "funnel:for_whom")
async def show_for_whom(call: CallbackQuery):
    await call.message.edit_text(get_for_whom_text(), reply_markup=back_kb())
    await call.answer()


@router.callback_query(F.data == "funnel:expert")
async def show_expert(call: CallbackQuery):
    await call.message.edit_text(get_expert_text(), reply_markup=back_kb())
    await call.answer()


@router.callback_query(F.data == "funnel:conditions")
async def show_conditions(call: CallbackQuery):
    await call.message.edit_text(get_conditions_text(), reply_markup=back_kb())
    await call.answer()