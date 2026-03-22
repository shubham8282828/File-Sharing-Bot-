# main.py

import logging
import os
from flask import Flask, request
from telegram import Update
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

# Flask app
flask_app = Flask(__name__)

# Bot application (global)
bot_app = None


async def setup_bot():
    """Bot setup karo."""
    global bot_app

    bot_app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers add karo
    bot_app.add_handler(CommandHandler("start", start_handler))
    bot_app.add_handler(CommandHandler("admin", admin_panel_handler))
    bot_app.add_handler(MessageHandler(
        filters.VIDEO | filters.Document.ALL | filters.AUDIO,
        upload_handler
    ))
    bot_app.add_handler(CallbackQueryHandler(button_handler))

    # Bot initialize karo
    await bot_app.initialize()
    await bot_app.start()

    return bot_app


@flask_app.route("/")
def home():
    return "🤖 Bot is running!", 200


@flask_app.route("/health")
def health():
    return "OK", 200


@flask_app.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
def webhook():
    """Telegram webhook endpoint."""
    import asyncio
    import json

    if request.method == "POST":
        # Telegram se aaya update process karo
        update_data = request.get_json()
        update = Update.de_json(update_data, bot_app.bot)

        # Async update process karo
        asyncio.run(bot_app.process_update(update))

        return "OK", 200


def set_webhook():
    """Render URL pe webhook set karo."""
    import requests

    # Render automatically RENDER_EXTERNAL_URL set karta hai
    render_url = os.getenv("RENDER_EXTERNAL_URL")

    if not render_url:
        logger.warning("⚠️ RENDER_EXTERNAL_URL nahi mili! Webhook set nahi hoga.")
        return

    webhook_url = f"{render_url}/webhook/{BOT_TOKEN}"

    response = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
        json={"url": webhook_url}
    )

    if response.status_code == 200:
        logger.info(f"✅ Webhook set: {webhook_url}")
    else:
        logger.error(f"❌ Webhook set failed: {response.text}")


if __name__ == "__main__":
    import asyncio

    # Bot setup karo
    asyncio.run(setup_bot())

    # Webhook set karo
    set_webhook()

    logger.info("🚀 Starting Flask on port 8080...")

    # Flask start karo
    flask_app.run(host="0.0.0.0", port=8080)
