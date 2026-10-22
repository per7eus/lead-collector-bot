import asyncio
import logging

from aiogram import Bot, Dispatcher

from bot.handlers import router
from config import api_key


async def main():
    bot = Bot(token=api_key)    
    dp = Dispatcher()
    dp.include_router(router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        logging.info("Bot started")
        asyncio.run(main())
    except Exception as e:
        logging.info(f"Bot stopped. Error: {e}")