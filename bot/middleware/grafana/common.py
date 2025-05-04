import logging
import time
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from prometheus_client import Counter, Histogram

# Инициализация метрик
BOT_REQUESTS = Counter("bot_requests", "Total bot requests")
BOT_ERRORS = Counter("bot_errors", "Total bot errors")
RESPONSE_TIME = Histogram(
    "bot_handler_duration_seconds",
    "Time spent processing requests",
    ["handler_type"],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0],
)


class TotalRequestCounter(BaseMiddleware):
    """
    Middleware to count total requests to the bot.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        BOT_REQUESTS.inc()
        return await handler(event, data)


class ErrorRequestCounter(BaseMiddleware):
    """
    Middleware to count total errors in requests to the bot.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as e:
            BOT_ERRORS.inc()
            raise e


class TimingMiddleware(BaseMiddleware):
    """
    Middleware to measure the time spent on processing requests.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:  # Определяем тип обработчика
        handler_type = self._get_handler_type(handler, event)

        # Засекаем время
        start_time = time.time()
        try:
            return await handler(event, data)
        finally:
            # Вычисляем длительность
            duration = time.time() - start_time
            logging.info(f"duration: {duration}")
            RESPONSE_TIME.labels(handler_type=handler_type).observe(duration)

    def _get_handler_type(self, handler, event: TelegramObject) -> str:
        """Определяем тип обработчика автоматически"""
        if event.message:
            if event.message.text and event.message.text.startswith("/"):
                return "command"
            return "message"
        if event.callback_query:
            return "callback"
        if event.inline_query:
            return "inline"
        return "other"
