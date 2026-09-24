from aiogram import Router
from aiogram.types import Message 

from bot.keyboard.start import start_inline_keyboard

router = Router()

START_TEXT = """Привет 👋

Я бот проекта Чёрного Кролика — эксперта по межполовым коммуникациям.

Здесь ты можешь узнать подробности о мастер-классе «Пробуждение», зарегистрироваться и сразу оплатить участие.

🎟 Стоимость участия:

до 20 сентября — 3 000 ₽
с 21 по 30 сентября — 4 000 ₽
с 1 по 10 октября — 5 000 ₽

Чем ближе мастер-класс, тем выше стоимость участия.

После регистрации и оплаты я пришлю подтверждение и всю необходимую информацию.

👇 Начнём с самого главного: что будет на мастер-классе и зачем тебе туда."""


@router.message()
async def start(mes: Message):
    await mes.answer(START_TEXT, reply_markup=start_inline_keyboard)
    