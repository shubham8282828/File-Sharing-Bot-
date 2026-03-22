# bot/handlers/start.py
# /start command ka handler

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import BOT_NAME, ADMIN_ID


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Jab user /start bhejta hai tab yeh function chalta hai.
    """
    user = update.effective_user  # User ki info

    # Welcome message banao
    welcome_text = (
        f"👋 Hello, {user.first_name}!\n\n"
        f"🤖 Welcome to *{BOT_NAME}*\n\n"
        f"📁 Yeh bot aapko files share karne aur "
        f"videos stream karne mein help karta hai.\n\n"
        f"👇 Neeche buttons use karo:"
    )

    # Buttons banao (InlineKeyboard)
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
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Message bhejo
    await update.message.reply_text(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Jab user koi button dabata hai tab yeh chalta hai.
    Abhi sirf placeholder response deta hai.
    """
    query = update.callback_query
    await query.answer()  # Loading spinner hatao

    # Kaunsa button daba
    data = query.data

    responses = {
        "show_files": "📂 *Files*\nYeh feature jald aayega! (Step 4)",
        "show_premium": "💎 *Premium*\nYeh feature jald aayega! (Step 8)",
        "show_referral": "👥 *Referral*\nYeh feature jald aayega! (Step 7)",
        "show_help": (
            "ℹ️ *Help*\n\n"
            "/start - Bot start karo\n"
            "/premium - Premium plans dekho\n"
            "/referral - Apna referral link lo\n"
        ),
    }

    # Response bhejo
    await query.edit_message_text(
        responses.get(data, "❓ Unknown button"),
        parse_mode="Markdown",
    )
