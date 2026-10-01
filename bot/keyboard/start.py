from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, \
    InlineKeyboardMarkup, \
    ReplyKeyboardMarkup, \
    KeyboardButton, CallbackQuery,\
    CopyTextButton


start_inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(
    text="Узнать о мастер-классе",callback_data='1.1'), InlineKeyboardButton(text="Сразу зарегистрироваться", callback_data='1.2')]])
