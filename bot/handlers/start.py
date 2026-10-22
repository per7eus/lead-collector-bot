from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from core.texts import START_TEXT
from bot.keyboard.start import start_inline_keyboard

router = Router()




@router.message(Command("start"))
async def start(mes: Message):
    print(mes.from_user.id)
    await mes.answer(START_TEXT, reply_markup=start_inline_keyboard)
