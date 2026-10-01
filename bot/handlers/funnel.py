from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.core.texts import (
    PROBLEM_TEXT, PROGRAM_TEXT, FOR_WHOM_TEXT, EXPERT_TEXT, CONDITIONS_TEXT, MENU_TEXT
)
from bot.keyboard.funnel import (
 menu_kb, back_kb
)


router = Router()


@router.callback_query(F.data == "1.1")
async def show_menu(call: CallbackQuery):
    await call.message.edit_text(MENU_TEXT, reply_markup=menu_kb())
    await call.answer()


@router.callback_query(F.data == "funnel:problem")
async def show_problem(call: CallbackQuery, state: FSMContext, db):
    await call.message.edit_text(PROBLEM_TEXT, reply_markup=back_kb())
    await call.answer()
    await db.update_user(call.from_user.id, registration_status="funnel")


@router.callback_query(F.data == "funnel:program")
async def show_program(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(PROGRAM_TEXT, reply_markup=back_kb())
    await call.answer()


@router.callback_query(F.data == "funnel:for_whom")
async def show_for_whom(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(FOR_WHOM_TEXT, reply_markup=back_kb())
    await call.answer()


@router.callback_query(F.data == "funnel:expert")
async def show_expert(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(EXPERT_TEXT, reply_markup=back_kb())
    await call.answer()


@router.callback_query(F.data == "funnel:conditions")
async def show_conditions(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(CONDITIONS_TEXT, reply_markup=back_kb())
    await call.answer()