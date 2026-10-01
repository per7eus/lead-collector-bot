from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
    InlineKeyboardMarkup, InlineKeyboardButton,
)


def phone_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Поделиться номером", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


# Необязательно: быстрые варианты возраста
def age_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="18–25"), KeyboardButton(text="26–35")],
            [KeyboardButton(text="36–50"), KeyboardButton(text="50+")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Всё верно — Оплатить 4 000 ₽", callback_data="reg_confirm")],
        [InlineKeyboardButton(text="✏️ Изменить данные", callback_data="reg_edit")],
    ])


def edit_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Изменить имя", callback_data="edit_first_name")],
        [InlineKeyboardButton(text="Изменить фамилию", callback_data="edit_last_name")],
        [InlineKeyboardButton(text="Изменить возраст", callback_data="edit_age")],
        [InlineKeyboardButton(text="Изменить телефон", callback_data="edit_phone")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="reg_back")],
    ])


remove_kb = ReplyKeyboardRemove()