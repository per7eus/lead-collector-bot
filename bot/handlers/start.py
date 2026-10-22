from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from core.texts import get_start_text
from bot.keyboard.start import start_inline_keyboard

router = Router()




@router.message(Command("start"))
async def start(mes: Message):
    await mes.answer(get_start_text(), reply_markup=start_inline_keyboard)
