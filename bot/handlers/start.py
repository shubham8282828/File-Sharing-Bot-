# bot/handlers/start.py
# Token system integrated!

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import BOT_NAME, ADMIN_ID, BOT_URL
from database.db import save_user, get_user, get_file_by_code
from bot.utils.helpers import generate_referral_code
from bot.utils.token_manager import (
    generate_token,
    verify_token,
    verify_token_by_string,
    get_token_expiry
)
from bot.utils.shortener import shorten_url
import asyncio


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /start handler.
    /start          → Welcome
    /start xyz      → File request (token check hoga)
    /start token_abc → Token verify karo
    """
    user = update.effective_user

    # User save karo
    existing_user = await get_user(user.id)
    if not existing_user:
        referral_code = generate_referral_code(user.id)
        await save_user(
            telegram_id=user.id,
            username=user.username or "",
            first_name=user.first_name or "",
            referral_code=referral_code
        )

    # Deep link args check karo
    if context.args:
        arg = context.args[0]

        # Token verify link? (token_ se shuru hoga)
        if arg.startswith("token_"):
            actual_token = arg[6:]  # "token_" hata do
            await handle_token_verify(update, context, actual_token)
            return

        # File request
        await handle_file_request(update, context, arg)
        return

    # Normal welcome
    await show_welcome(update, user)


async def show_welcome(update, user):
    """Welcome message dikhao."""
    keyboard = [
        [
            InlineKeyboardButton("📂 Files", callback_data="show_files"),
            InlineKeyboardButton("💎 Premium", callback_data="show_premium"),
        ],
        [
            InlineKeyboardButton("👥 Referral", callback_data="show_referral"),
            InlineKeyboardButton("ℹ️ Help", callback_data="show_help"),
        ],
    ]

    await update.message.reply_text(
        f"👋 Hello, {user.first_name}!\n\n"
        f"🤖 Welcome to *{BOT_NAME}*\n\n"
        f"📁 Files share karo aur videos stream karo!\n\n"
        f"👇 Neeche buttons use karo:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_token_verify(update, context, token: str):
    """
    Shortener se aaya token verify karo.
    Agar valid → token database mein save karo.
    """
    result = await verify_token_by_string(token)

    if result["valid"]:
        expiry = await get_token_expiry(result["telegram_id"])
        await update.message.reply_text(
            f"✅ *Token Verified!*\n\n"
            f"⏰ Valid for: `{expiry}`\n\n"
            f"Ab tum saari files access kar sakte ho!\n"
            f"Apna file link dobara open karo. 🎉",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"❌ *Token Invalid!*\n\n"
            f"Reason: {result['reason']}\n\n"
            f"Naya token lo — /gettoken command use karo.",
            parse_mode="Markdown"
        )


async def handle_file_request(update, context, unique_code: str):
    """
    File request — pehle token check, phir file do.
    """
    user = update.effective_user

    # ✅ Admin ke liye token check nahi
    if user.id != ADMIN_ID:
        token_valid = await verify_token(user.id)

        if not token_valid:
            # Token nahi hai — shortener link do
            await send_token_required_message(update, context, unique_code)
            return

    # Token valid — file do
    file_data = await get_file_by_code(unique_code)

    if not file_data:
        await update.message.reply_text(
            "❌ File nahi mili!\n"
            "Link galat hai ya file delete ho gayi."
        )
        return

    expiry = await get_token_expiry(user.id)

    keyboard = [[
        InlineKeyboardButton(
            "▶️ Watch Now",
            url=f"https://pixeldrain.com/u/{file_data['pixeldrain_id']}"
        )
    ]]

    await update.message.reply_text(
        f"🎬 *{file_data['file_name']}*\n\n"
        f"💾 Size: `{file_data['file_size']} MB`\n"
        f"⏰ Token expires in: `{expiry}`\n\n"
        f"👇 Watch karo:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def send_token_required_message(update, context, unique_code: str):
    """
    Token required message — shortener link bhejo.
    """
    user = update.effective_user

    # Naya token generate karo
    token = await generate_token(user.id)

    # Token verify link banao
    bot_username = (await context.bot.get_me()).username
    verify_url = f"https://t.me/{bot_username}?start=token_{token}"

    # URL shorten karo (shortener se task complete karni hogi)
    loop = asyncio.get_event_loop()
    short_url = await loop.run_in_executor(
        None, shorten_url, verify_url
    )

    keyboard = [[
        InlineKeyboardButton("🔑 Get Token", url=short_url)
    ]]

    await update.message.reply_text(
        f"🔐 *Token Required!*\n\n"
        f"Is file ko access karne ke liye\n"
        f"pehle token lena hoga.\n\n"
        f"*Kaise milega token?*\n"
        f"1️⃣ Neeche button dabao\n"
        f"2️⃣ Link open karo\n"
        f"3️⃣ Ad complete karo\n"
        f"4️⃣ Bot pe wapas aao\n\n"
        f"✅ Token 24 ghante valid rahega!\n"
        f"✅ Saari files access hongi!",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Button clicks."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "show_help":
        text = (
            "ℹ️ *Help*\n\n"
            "/start - Bot start karo\n"
            "/gettoken - Naya token lo\n"
            "/premium - Premium plans\n"
            "/referral - Referral link\n"
        )
    elif data == "show_files":
        text = "📂 *Files*\nAdmin se share link lo!"
    elif data == "show_premium":
        text = "💎 *Premium*\nJald aayega!"
    elif data == "show_referral":
        text = "👥 *Referral*\nJald aayega!"
    else:
        text = "❓ Unknown button"

    await query.edit_message_text(text, parse_mode="Markdown")
