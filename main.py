import logging
from typing import Annotated, Any, Dict

from aiogram import types
from litestar import Litestar, Request, get, post
from litestar.openapi import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin
from litestar.params import Body, Parameter
from litestar.plugins.prometheus import PrometheusConfig, PrometheusController

from bot.bot_settings import bot, dp, start_bot
from bot.utils.misc import create_folder
from configreader import config

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger()


@get("/")
async def root() -> str:
    return "root"


async def on_startup():
    bot_username = await bot.get_me()
    await create_folder("temp_images")
    logger.info(f"🚀 Starting bot - @{bot_username.username}")
    await start_bot()


prometheus_config = PrometheusConfig()


@post(config.bot_config.webhook_path)
async def bot_webhook(
    request: Request,
    data: Annotated[Dict[str, Any], Body()],
    x_telegram_bot_api_secret_token: Annotated[
        str | None, Parameter(header="x-telegram-bot-api-secret-token")
    ] = None,
) -> None | dict:
    """Register webhook endpoint for telegram bot"""
    if x_telegram_bot_api_secret_token != "secret_228":
        logger.error("Wrong secret token !")
        return {"status": "error", "message": "Wrong secret token !"}
    telegram_update = types.Update(**data)
    try:
        await dp.feed_webhook_update(bot=bot, update=telegram_update)
    except Exception as e:
        logger.error(f"Error while processing webhook: {e}")
        return {
            "status": "error",
            "message": f"Error while processing webhook: {e}",
        }
    return {"status": "ok"}


app = Litestar(
    route_handlers=[root, bot_webhook, PrometheusController],
    middleware=[prometheus_config.middleware],
    openapi_config=OpenAPIConfig(
        title="Bot Webhook",
        version="0.0.1",
        render_plugins=[ScalarRenderPlugin()],
        path=None,
    ),
    debug=False,
    on_startup=[on_startup],
)
