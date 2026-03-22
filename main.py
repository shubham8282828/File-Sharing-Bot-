# main.py

import logging
import asyncio
import threading
from flask import Flask
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from config import BOT_TOKEN
from bot.handlers.start import start_handler, button_handler
from bot.handlers.admin import upload_handler, admin_panel_handler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ✅ Flask app — sirf port 8080 ke liye
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "🤖 Bot is running!", 200

@flask_app.route("/health")
def health():
    return "OK", 200


def run_flask():
    """Flask ko alag thread mein chalao."""
    flask_app.run(host="0.0.0.0", port=8080)


async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("admin", admin_panel_handler))
    app.add_handler(MessageHandler(
        filters.VIDEO | filters.Document.ALL | filters.AUDIO,
        upload_handler
    ))
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("🤖 Bot chal raha hai...")

    # Webhook delete karo
    await app.bot.delete_webhook(drop_pending_updates=True)

    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query"]
        )
        await asyncio.Event().wait()


if __name__ == "__main__":
    # ✅ Flask alag thread mein start karo
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("🌐 Flask running on port 8080")

    # ✅ Bot start karo
    asyncio.run(main())
