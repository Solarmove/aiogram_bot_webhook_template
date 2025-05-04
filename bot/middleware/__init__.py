from aiogram import Dispatcher

from bot.middleware.db import DbSessionMiddleware
from bot.middleware.grafana.active_user_middleware import (
    UniqueUserActivityMiddleware,
    UserActivityMiddleware,
)
from bot.middleware.grafana.common import (
    TotalRequestCounter,
    ErrorRequestCounter,
    TimingMiddleware,
)


def load_metrics(dp: Dispatcher):
    dp.update.middleware(TotalRequestCounter())
    dp.update.middleware(ErrorRequestCounter())
    dp.update.middleware(TimingMiddleware())
    dp.update.middleware(UniqueUserActivityMiddleware())
    dp.update.middleware(UserActivityMiddleware())


def load_middleware(dp: Dispatcher):
    """
    Load all middlewares into the dispatcher
    """
    load_metrics(dp)
    dp.update.middleware(DbSessionMiddleware())  # Add database session middleware
