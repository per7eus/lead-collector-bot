from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.core.texts import (
    CONDITIONS_TEXT,
    EXPERT_TEXT,
    FOR_WHOM_TEXT,
    MENU_TEXT,
    PROBLEM_TEXT,
    PROGRAM_TEXT,
)
from bot.keyboard.funnel import back_kb, menu_kb

router = Router()


@router.callback_query(F.data == "1.1")
async def show_menu(call: CallbackQuery):
    await call.message.edit_text(MENU_TEXT, reply_markup=menu_kb())
    await call.answer()


@router.callback_query(F.data == "funnel:problem")
async def show_problem(call: CallbackQuery, db):
    await call.message.edit_text(PROBLEM_TEXT, reply_markup=back_kb())
    await call.answer()
    await db.update_user(call.from_user.id, registration_status="funnel")


@router.callback_query(F.data == "funnel:program")
async def show_program(call: CallbackQuery):
    await call.message.edit_text(PROGRAM_TEXT, reply_markup=back_kb())
    await call.answer()


@router.callback_query(F.data == "funnel:for_whom")
async def show_for_whom(call: CallbackQuery):
    await call.message.edit_text(FOR_WHOM_TEXT, reply_markup=back_kb())
    await call.answer()


@router.callback_query(F.data == "funnel:expert")
async def show_expert(call: CallbackQuery):
    await call.message.edit_text(EXPERT_TEXT, reply_markup=back_kb())
    await call.answer()


@router.callback_query(F.data == "funnel:conditions")
async def show_conditions(call: CallbackQuery):
    await call.message.edit_text(CONDITIONS_TEXT, reply_markup=back_kb())
    await call.answer()