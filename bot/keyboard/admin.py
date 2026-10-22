from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup,WebAppInfo
from config import URL_ADMIN_PANEL

web_app = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть админку ⚙️",
                    web_app=WebAppInfo(url=URL_ADMIN_PANEL + "/admin")
                )
            ]
        ]
    )