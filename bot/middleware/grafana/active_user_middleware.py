from collections import defaultdict
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from prometheus_client import Gauge

active_users = defaultdict(int)
ACTIVE_USERS = Gauge("bot_active_users_total", "Number of currently active users")

UNIQUE_ACTIVE_USERS = Gauge(
    "bot_unique_active_users_total", "Number of currently active UNIQUE users"
)


async def track_user_activity(user_id: int):
    if active_users[user_id] == 0:
        UNIQUE_ACTIVE_USERS.inc()
    active_users[user_id] += 1


async def untrack_user_activity(user_id: int):
    active_users[user_id] -= 1
    if active_users[user_id] == 0:
        UNIQUE_ACTIVE_USERS.dec()


class UniqueUserActivityMiddleware(BaseMiddleware):
    """
    Middleware to track unique user activity.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ):
        user_id = data["event_from_user"].id
        await track_user_activity(user_id)
        await handler(event, data)
        await untrack_user_activity(user_id)


class UserActivityMiddleware(BaseMiddleware):
    """
    Middleware to track user activity.
    """

    def __init__(self):
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ):
        # Увеличиваем счётчик при начале обработки
        ACTIVE_USERS.inc()
        try:
            return await handler(event, data)
        finally:
            # Уменьшаем после завершения
            ACTIVE_USERS.dec()
