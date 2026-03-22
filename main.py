# main.py
# Yeh poore bot ka entry point hai
# Isko run karte hain: python main.py

import logging
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
)

from config import BOT_TOKEN
from bot.handlers.start import start_handler, button_handler

# Logging setup — errors/info terminal mein dikhenge
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main():
    """
    Bot start karne ka main function.
    """
    # Bot application banao
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # /start command ke liye handler add karo
    app.add_handler(CommandHandler("start", start_handler))

    # Buttons ke liye handler add karo
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("🤖 Bot chal raha hai...")

    # Bot start karo (polling mode — Render ke liye baad mein webhook karenge)
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
