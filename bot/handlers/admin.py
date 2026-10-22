from aiogram import Router, F
from aiogram.types import Message

from bot.keyboard.admin import web_app

router = Router()


@router.message(F.text == "/admin")
async def admin(mess: Message):
    await mess.answer("Админ панель", reply_markup=web_app)