# bot/handlers/token.py
# /gettoken command handler

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.utils.token_manager import generate_token, verify_token, get_token_expiry
from bot.utils.shortener import shorten_url
import asyncio


async def gettoken_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /gettoken — User ko token lene ka link do.
    """
    user = update.effective_user

    # Pehle check karo — token already valid hai?
    if await verify_token(user.id):
        expiry = await get_token_expiry(user.id)
        await update.message.reply_text(
            f"✅ *Tumhara token already valid hai!*\n\n"
            f"⏰ Expires in: `{expiry}`\n\n"
            f"Saari files access kar sakte ho!",
            parse_mode="Markdown"
        )
        return

    # Naya token generate karo
    token = await generate_token(user.id)

    # Verify URL banao
    bot_username = (await context.bot.get_me()).username
    verify_url = f"https://t.me/{bot_username}?start=token_{token}"

    # Shorten karo
    loop = asyncio.get_event_loop()
    short_url = await loop.run_in_executor(
        None, shorten_url, verify_url
    )

    keyboard = [[
        InlineKeyboardButton("🔑 Get Token Now", url=short_url)
    ]]

    await update.message.reply_text(
        f"🔑 *Token Lene Ka Tarika:*\n\n"
        f"1️⃣ Neeche button dabao\n"
        f"2️⃣ Shortener link open hoga\n"
        f"3️⃣ Ad complete karo\n"
        f"4️⃣ Bot pe wapas aao automatically\n\n"
        f"✅ *Token 24 ghante valid rahega!*\n"
        f"✅ *Saari files access hongi!*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
