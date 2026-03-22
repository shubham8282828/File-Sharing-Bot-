# main.py

import logging
import asyncio

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
)

from config import BOT_TOKEN
from bot.handlers.start import start_handler, button_handler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def main():
    # Bot application banao
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers add karo
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("🤖 Bot chal raha hai...")

    # ✅ Python 3.14 fix — async properly start karo
    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query"]
        )
        # Bot ko hamesha chalta rakho
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
