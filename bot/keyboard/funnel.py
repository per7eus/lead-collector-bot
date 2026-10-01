from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def start_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Узнать о мастер-классе", callback_data="1.1")],
        [InlineKeyboardButton(text="Сразу зарегистрироваться", callback_data="1.2")],
    ])


def menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Что будет на тренинге", callback_data="funnel:program")],
        [InlineKeyboardButton(text="Кому подойдёт", callback_data="funnel:for_whom")],
        [InlineKeyboardButton(text="Кто такой Чёрный Кролик", callback_data="funnel:expert")],
        [InlineKeyboardButton(text="Условия участия", callback_data="funnel:conditions")],
        [InlineKeyboardButton(text="Зарегистрироваться и оплатить", callback_data="1.2")],
        [InlineKeyboardButton(text="Задать вопрос администратору", url="https://t.me/blackbrabbit")],

    ])

def back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="⬅️ Назад", callback_data="1.1"),
            InlineKeyboardButton(text="Зарегистрироваться и оплатить", callback_data="1.2"),
    ]])