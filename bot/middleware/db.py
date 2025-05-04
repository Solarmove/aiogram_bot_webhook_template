from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from bot.utils.unitofwork import UnitOfWork


class DbSessionMiddleware(BaseMiddleware):
    """
    Middleware to provide a database session to handlers.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        uow = UnitOfWork
        async with uow() as uow:
            data["uow"] = uow
            return await handler(event, data)
