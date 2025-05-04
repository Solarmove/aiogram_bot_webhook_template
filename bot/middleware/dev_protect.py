from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User

from configreader import config


class DevProtectMiddleware(BaseMiddleware):
    """
    Middleware to protect dev commands from non-dev users.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ):
        user: Optional[User] = data["event_from_user"]
        if user.id not in config.devs:
            return
        await handler(event, data)
