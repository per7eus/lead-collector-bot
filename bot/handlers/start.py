from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from bot.keyboard.start import start_inline_keyboard
from bot.core.texts import START_TEXT


router = Router()




@router.message(Command("start"))
async def start(mes: Message):
    print(mes.from_user.id)
    await mes.answer(START_TEXT, reply_markup=start_inline_keyboard)
