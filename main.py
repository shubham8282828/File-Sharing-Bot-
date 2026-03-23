# main.py
# Gunicorn + Async properly handle

import logging
import asyncio
import os
import threading
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
from bot.handlers.token import gettoken_handler
from bot.handlers.referral import referral_handler, referral_stats_handler
from database.db import init_db

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Flask app
flask_app = Flask(__name__)

# Global variables
bot_app = None
bot_loop = None  # ✅ Ek hi loop — baar baar nahi banega


def get_or_create_loop():
    """
    Dedicated event loop — ek baar banta hai,
    baar baar use hota hai. Speed fix!
    """
    global bot_loop
    if bot_loop is None or bot_loop.is_closed():
        bot_loop = asyncio.new_event_loop()
    return bot_loop


async def setup_bot():
    """Bot setup karo."""
    global bot_app

    # Database banao
    await init_db()

    bot_app = ApplicationBuilder().token(BOT_TOKEN).build()

    # ✅ Saare handlers
    bot_app.add_handler(CommandHandler("start", start_handler))
    bot_app.add_handler(CommandHandler("admin", admin_panel_handler))
    bot_app.add_handler(CommandHandler("files", list_files_handler))
    bot_app.add_handler(CommandHandler("gettoken", gettoken_handler))
    bot_app.add_handler(CommandHandler("referral", referral_handler))
    bot_app.add_handler(CommandHandler("refstats", referral_stats_handler))
    bot_app.add_handler(MessageHandler(
        filters.VIDEO | filters.Document.ALL | filters.AUDIO,
        upload_handler
    ))
    bot_app.add_handler(CallbackQueryHandler(button_handler))

    await bot_app.initialize()
    await bot_app.start()

    logger.info("🤖 Bot setup complete!")


# ─── FLASK ROUTES ─────────────────────────────────────────────

@flask_app.route("/")
def home():
    return "🤖 Bot is running!", 200


@flask_app.route("/health")
def health():
    return "OK", 200


@flask_app.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
def webhook():
    """
    Telegram se aane wale updates.
    ✅ Dedicated loop use karo — fast response!
    """
    if request.method == "POST":
        update_data = request.get_json()

        if update_data and bot_app:
            try:
                update = Update.de_json(update_data, bot_app.bot)

                # ✅ Dedicated loop mein run karo
                loop = get_or_create_loop()
                future = asyncio.run_coroutine_threadsafe(
                    bot_app.process_update(update),
                    loop
                )
                future.result(timeout=30)  # 30 sec timeout

            except Exception as e:
                logger.error(f"Webhook error: {e}")

        return "OK", 200

    return "Method Not Allowed", 405


# ─── WEBHOOK SETUP ────────────────────────────────────────────

def set_webhook():
    """Webhook set karo."""
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
            "allowed_updates": ["message", "callback_query"],
            "max_connections": 40  # ✅ More connections = faster
        }
    )

    if response.status_code == 200:
        logger.info(f"✅ Webhook set: {webhook_url}")
    else:
        logger.error(f"❌ Webhook failed: {response.text}")


# ─── EVENT LOOP THREAD ────────────────────────────────────────

def start_event_loop(loop):
    """
    ✅ Dedicated thread mein event loop chalao.
    Yeh bot ko fast banata hai!
    """
    asyncio.set_event_loop(loop)
    loop.run_forever()


# ─── MAIN ─────────────────────────────────────────────────────

# ✅ Dedicated loop banao
bot_loop = asyncio.new_event_loop()

# ✅ Loop alag thread mein chalao
loop_thread = threading.Thread(
    target=start_event_loop,
    args=(bot_loop,),
    daemon=True
)
loop_thread.start()

# ✅ Bot setup karo us loop mein
future = asyncio.run_coroutine_threadsafe(setup_bot(), bot_loop)
future.result(timeout=60)  # 60 sec wait

# ✅ Webhook set karo
set_webhook()

logger.info("🚀 Bot ready!")


if __name__ == "__main__":
    logger.info("🌐 Starting Flask on port 8080...")
    flask_app.run(
        host="0.0.0.0",
        port=8080,
        debug=False
    )
