# main.py

import logging
import asyncio
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
from bot.handlers.admin import upload_handler, admin_panel_handler, list_files_handler
from database.db import init_db

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
    """Bot setup karo — database + handlers."""
    global bot_app

    # ✅ Pehle database banao
    await init_db()

    bot_app = ApplicationBuilder().token(BOT_TOKEN).build()

    # ✅ Saare handlers add karo
    bot_app.add_handler(CommandHandler("start", start_handler))
    bot_app.add_handler(CommandHandler("admin", admin_panel_handler))
    bot_app.add_handler(CommandHandler("files", list_files_handler))
    bot_app.add_handler(MessageHandler(
        filters.VIDEO | filters.Document.ALL | filters.AUDIO,
        upload_handler
    ))
    bot_app.add_handler(CallbackQueryHandler(button_handler))

    # Bot initialize karo
    await bot_app.initialize()
    await bot_app.start()

    logger.info("🤖 Bot setup complete!")
    return bot_app


# ─── FLASK ROUTES ─────────────────────────────────────────────

@flask_app.route("/")
def home():
    return "🤖 Bot is running!", 200


@flask_app.route("/health")
def health():
    return "OK", 200


@flask_app.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
def webhook():
    """Telegram se aane wale updates handle karo."""
    import json

    if request.method == "POST":
        update_data = request.get_json()

        if update_data:
            update = Update.de_json(update_data, bot_app.bot)

            # Async update process karo
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(bot_app.process_update(update))
            loop.close()

        return "OK", 200

    return "Method Not Allowed", 405


# ─── WEBHOOK SETUP ────────────────────────────────────────────

def set_webhook():
    """Render URL pe webhook set karo."""
    import requests

    render_url = os.getenv("RENDER_EXTERNAL_URL")

    if not render_url:
        logger.warning("⚠️ RENDER_EXTERNAL_URL nahi mili!")
        return

    webhook_url = f"{render_url}/webhook/{BOT_TOKEN}"

    response = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
        json={
            "url": webhook_url,
            "allowed_updates": ["message", "callback_query"]
        }
    )

    if response.status_code == 200:
        logger.info(f"✅ Webhook set: {webhook_url}")
    else:
        logger.error(f"❌ Webhook failed: {response.text}")


# ─── MAIN ─────────────────────────────────────────────────────

if __name__ == "__main__":

    # Bot setup karo
    asyncio.run(setup_bot())

    # Webhook set karo
    set_webhook()

    logger.info("🚀 Starting Flask on port 8080...")

    # Flask start karo
    flask_app.run(
        host="0.0.0.0",
        port=8080,
        debug=False
    )
