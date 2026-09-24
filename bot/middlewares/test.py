from collections.abc import Awaitable, Callable
from typing import Any, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class MaimMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]], event: TelegramObject, data: dict[str, Any]) -> Any:
        print(f"Пришло событие {event}")

        data["my_value"] = "hello"

        result = await handler(event, data)

        print(result)
        
        return result