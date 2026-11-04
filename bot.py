"""
Tewabu ERP - Tailor House Cost & Profit Manager
Main entry point and Telegram bot runner.
"""

import asyncio
import io
import logging
import os
import sys
from pathlib import Path
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config.settings import settings
from database.engine import init_db
from middlewares.auth_middleware import AuthMiddleware
from handlers import setup_routers
from services.reminder_service import start_reminder_scheduler

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s : %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("tewabu_erp")

async def setup_bot_commands(bot: Bot) -> None:
    """Register bot slash commands visible in Telegram UI."""
    commands = [
        BotCommand(command="start", description="🧵 የተዋቡ ERP መነሻ / Start Tewabu ERP"),
        BotCommand(command="help", description="📖 መመሪያ እና የቀመር ማብራሪያ / Help & Formulas"),
        BotCommand(command="cancel", description="❌ ክንውንን ሰርዝ / Cancel active action"),
    ]
    await bot.set_my_commands(commands)

async def start_health_server(port: int):
    """Optional lightweight HTTP server for Render/Cloud free tier health checks."""
    app = web.Application()
    async def index(request):
        return web.Response(text="🧵 Tewabu ERP Telegram Bot is running live 24/7!", status=200)
    app.router.add_get("/", index)
    app.router.add_get("/health", index)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Cloud health-check server listening on port {port}")

async def main() -> None:
    logger.info("Initializing Tewabu ERP Database...")
    await init_db()
    logger.info("Database initialized successfully.")

    if not settings.BOT_TOKEN or settings.BOT_TOKEN.startswith("123456789"):
        logger.warning(
            "\n"
            "==========================================================\n"
            "⚠️  BOT_TOKEN is not configured or using example placeholder!\n"
            "Please create a .env file and set your BOT_TOKEN from @BotFather:\n"
            "BOT_TOKEN=your_real_telegram_bot_token_here\n"
            "==========================================================\n"
        )
        # If run without valid token, exit cleanly with informative message
        print("Please configure BOT_TOKEN in .env to start receiving Telegram events.")
        return

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Register Outer Middlewares (intercepts all updates before filters)
    auth_middleware = AuthMiddleware()
    dp.message.outer_middleware(auth_middleware)
    dp.callback_query.outer_middleware(auth_middleware)

    # Register Handlers
    setup_routers(dp)

    await setup_bot_commands(bot)

    # Start optional web server if deployed on Render/Cloud (PORT variable present)
    port_env = os.getenv("PORT")
    if port_env:
        try:
            await start_health_server(int(port_env))
        except Exception as e:
            logger.warning(f"Could not start health check server: {e}")

    logger.info("Starting Tewabu ERP Bot Polling...")
    # Start background 5-day delivery reminder scheduler
    asyncio.create_task(start_reminder_scheduler(bot))

    try:
        # Drop pending updates so bot doesn't process stale messages upon boot
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        logger.info("Closing bot session...")
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Tewabu ERP Bot stopped.")
