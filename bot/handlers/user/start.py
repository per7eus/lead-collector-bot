from aiogram import Router
from aiogram.types import Message 


router = Router()


@router.message()
async def start(mes: Message):
    await mes.answer("Hello word")
    