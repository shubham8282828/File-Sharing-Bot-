# main.py

import logging
import asyncio

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from config import BOT_TOKEN
from bot.handlers.start import start_handler, button_handler
from bot.handlers.admin import upload_handler, admin_panel_handler  # ✅ New

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Start handler
    app.add_handler(CommandHandler("start", start_handler))

    # ✅ Admin handlers
    app.add_handler(CommandHandler("admin", admin_panel_handler))

    # ✅ File upload handler — video, document, audio
    app.add_handler(MessageHandler(
        filters.VIDEO | filters.Document.ALL | filters.AUDIO,
        upload_handler
    ))

    # Button handler
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("🤖 Bot chal raha hai...")

    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query"]
        )
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
