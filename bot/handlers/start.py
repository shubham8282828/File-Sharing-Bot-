# bot/handlers/start.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import BOT_NAME, ADMIN_ID
from database.db import save_user, get_user, get_file_by_code
from bot.utils.helpers import generate_referral_code
from bot.utils.token_manager import (
    generate_token, verify_token,
    verify_token_by_string, get_token_expiry
)
from bot.utils.shortener import shorten_url
import asyncio


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    existing_user = await get_user(user.id)

    if context.args:
        arg = context.args[0]

        # ✅ REFERRAL
        if arg.startswith("ref_"):
            referral_code = arg[4:]
            if not existing_user:
                ref_code = generate_referral_code(user.id)
                await save_user(
                    telegram_id=user.id,
                    username=user.username or "",
                    first_name=user.first_name or "",
                    referral_code=ref_code,
                    referred_by=referral_code
                )
                from bot.handlers.referral import handle_referral_join
                success = await handle_referral_join(
                    user.id, referral_code, context
                )
                if success:
                    await update.message.reply_text(
                        f"👋 Welcome, *{user.first_name}*!\n\n"
                        f"🎉 Referral link se aaye ho!\n"
                        f"✅ Account ban gaya!",
                        parse_mode="Markdown"
                    )
                else:
                    await update.message.reply_text(
                        f"👋 Welcome, *{user.first_name}*!\n\n"
                        f"✅ Account ban gaya!",
                        parse_mode="Markdown"
                    )
            else:
                await update.message.reply_text(
                    f"👋 Welcome back, *{user.first_name}*!",
                    parse_mode="Markdown"
                )
            await show_welcome(update, user)
            return

        # ✅ TOKEN VERIFY
        elif arg.startswith("token_"):
            actual_token = arg[6:]
            if not existing_user:
                ref_code = generate_referral_code(user.id)
                await save_user(
                    telegram_id=user.id,
                    username=user.username or "",
                    first_name=user.first_name or "",
                    referral_code=ref_code
                )
            await handle_token_verify(update, context, actual_token)
            return

        # ✅ FILE REQUEST
        else:
            if not existing_user:
                ref_code = generate_referral_code(user.id)
                await save_user(
                    telegram_id=user.id,
                    username=user.username or "",
                    first_name=user.first_name or "",
                    referral_code=ref_code
                )
            await handle_file_request(update, context, arg)
            return

    # ✅ NORMAL /start
    if not existing_user:
        ref_code = generate_referral_code(user.id)
        await save_user(
            telegram_id=user.id,
            username=user.username or "",
            first_name=user.first_name or "",
            referral_code=ref_code
        )
    await show_welcome(update, user)


async def show_welcome(update, user):
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
    user = update.effective_user

    if user.id != ADMIN_ID:
        from database.db import check_user_premium
        is_premium = await check_user_premium(user.id)
        if not is_premium:
            token_valid = await verify_token(user.id)
            if not token_valid:
                await send_token_required_message(update, context, unique_code)
                return

    file_data = await get_file_by_code(unique_code)
    if not file_data:
        await update.message.reply_text(
            "❌ *File nahi mili!*\n\n"
            "Link galat hai ya file delete ho gayi.",
            parse_mode="Markdown"
        )
        return

    from database.db import check_user_premium
    is_premium = await check_user_premium(user.id)

    if is_premium:
        access_text = "💎 Premium Access"
    elif user.id == ADMIN_ID:
        access_text = "👑 Admin Access"
    else:
        expiry = await get_token_expiry(user.id)
        access_text = f"🔑 Token expires in: `{expiry}`"

    keyboard = [[
        InlineKeyboardButton(
            "▶️ Watch Now",
            url=f"https://pixeldrain.com/u/{file_data['pixeldrain_id']}"
        )
    ]]

    await update.message.reply_text(
        f"🎬 *{file_data['file_name']}*\n\n"
        f"💾 Size: `{file_data['file_size']} MB`\n"
        f"📅 Uploaded: `{file_data['uploaded_at'][:10]}`\n"
        f"🔐 {access_text}\n\n"
        f"👇 Watch karo:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def send_token_required_message(update, context, unique_code: str):
    user = update.effective_user
    token = await generate_token(user.id)
    bot_username = (await context.bot.get_me()).username
    verify_url = f"https://t.me/{bot_username}?start=token_{token}"

    loop = asyncio.get_event_loop()
    short_url = await loop.run_in_executor(None, shorten_url, verify_url)

    keyboard = [
        [InlineKeyboardButton("🔑 Get Token", url=short_url)],
        [InlineKeyboardButton("💎 Buy Premium", callback_data="show_premium")]
    ]

    await update.message.reply_text(
        f"🔐 *Token Required!*\n\n"
        f"Is file ko access karne ke liye\n"
        f"pehle token lena hoga.\n\n"
        f"*Token Kaise Milega?*\n"
        f"1️⃣ Neeche *Get Token* button dabao\n"
        f"2️⃣ Link khulega — complete karo\n"
        f"3️⃣ Bot pe wapas aao\n"
        f"4️⃣ File automatically milegi!\n\n"
        f"✅ Token *24 ghante* valid rahega!\n"
        f"✅ *Saari files* access hongi!\n\n"
        f"💎 *Ya Premium lo — token ki zaroorat nahi!*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "show_files":
        text = (
            "📂 *Files*\n\n"
            "Admin se share link lo!\n"
            "Ya /gettoken karke files access karo."
        )
    elif data == "show_premium":
        text = (
            "💎 *Premium Benefits*\n\n"
            "✅ Token ki zaroorat nahi\n"
            "✅ Unlimited file access\n"
            "✅ Fast streaming\n\n"
            "📝 /premium command use karo!"
        )
    elif data == "show_referral":
        text = (
            "👥 *Referral System*\n\n"
            "🔗 /referral command use karo!\n\n"
            "🏆 10 referrals = 7 din Premium FREE!"
        )
    elif data == "show_help":
        text = (
            "ℹ️ *Help*\n\n"
            "/start — Bot start karo\n"
            "/gettoken — Token lo\n"
            "/referral — Referral link lo\n"
            "/premium — Premium plans\n"
        )
    else:
        text = "❓ Unknown button"

    await query.edit_message_text(text, parse_mode="Markdown")
