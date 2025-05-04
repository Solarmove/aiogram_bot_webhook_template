import logging
import os
from os import getppid

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.fsm.storage.redis import RedisEventIsolation, RedisStorage
from aiogram.types import WebhookInfo
from aiogram_i18n.cores import FluentRuntimeCore

from bot.db.base import create_all
from bot.db.redis import redis
from bot.middleware import load_middleware
from bot.middleware.i18n_dialog import RedisI18nMiddleware
from bot.utils.i18n_utils.i18n_format import make_i18n_middleware
from bot.utils.set_bot_commands import set_default_commands
from configreader import config
# Bot settings

bot = Bot(
    token=config.bot_config.token,
    default=DefaultBotProperties(
        parse_mode=config.bot_config.parse_mode,
    ),
)
key_builder = DefaultKeyBuilder(with_destiny=True, with_bot_id=True)
storage = RedisStorage(redis=redis, key_builder=key_builder)
event_isolation = RedisEventIsolation(redis, key_builder=key_builder)
dp = Dispatcher(storage=storage, events_isolation=event_isolation)
router = Router(name=__name__)

# I18n Settings
path_to_locales = os.path.join("bot", "src", "locales", "{locale}", "LC_MESSAGES")
core = FluentRuntimeCore(path=path_to_locales)
i18n_middleware = RedisI18nMiddleware(
    core=core,
    redis=redis,
)
i18n_dialog_middleware = make_i18n_middleware(path_to_locales)


def set_middleware(dp: Dispatcher):
    load_middleware(dp)


async def set_webhook(my_bot: Bot) -> None:
    # Check and set webhook for Telegram
    async def check_webhook() -> WebhookInfo | None:
        try:
            webhook_info = await my_bot.get_webhook_info()
            return webhook_info
        except Exception as e:
            logging.error(f"Can't get webhook info - {e}")
            return

    current_webhook_info = await check_webhook()
    if config.run_mode == "dev":
        logging.debug(f"Current bot info: {current_webhook_info}")
    await my_bot.delete_webhook(drop_pending_updates=True)
    try:
        url = f"{config.bot_config.webhook_url}{config.bot_config.webhook_path}"
        await my_bot.set_webhook(
            url,
            secret_token="secret_228",
            drop_pending_updates=True,
            max_connections=100,
            allowed_updates=[
                "message",
                "callback_query",
                "chat_join_request",
                "pre_checkout_query",
                "successful_payment",
            ],
        )
        logging.info(f"Webhook set to {url}")
        if config.run_mode == "dev":
            logging.debug(f"Updated bot info: {await check_webhook()}")
    except Exception as e:
        logging.error(f"Can't set webhook - {e}")


async def first_run() -> bool:
    """Check if this is the first run of service. ppid is the parent process id.
    Save ppid to redis and check it on next run. If ppid is the same - this is not the first run.
    """
    ppid = getppid()
    save_pid = await redis.get("tg_bot_ppid")
    if save_pid and int(save_pid) == ppid:
        await redis.close()
        return False
    await redis.set("tg_bot_ppid", ppid)
    await redis.close()
    return True


async def start_bot():
    await create_all()  # Create all database tables
    is_first_run = await first_run()
    set_middleware(dp)
    if config.run_mode == "dev":
        logging.debug(f"First run: {is_first_run}")
    # await startup_action(UnitOfWork)
    if is_first_run:
        await set_default_commands(bot)  # Set default bot commands
        await set_webhook(bot)
