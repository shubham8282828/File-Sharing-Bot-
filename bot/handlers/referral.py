# bot/handlers/referral.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.db import (
    get_user, get_user_by_referral_code,
    increment_referral_count, update_user_premium,
    check_user_premium, DB_PATH
)
from config import ADMIN_ID
import aiosqlite
import logging

logger = logging.getLogger(__name__)

REFERRALS_FOR_PREMIUM = 10
PREMIUM_REWARD_DAYS = 7


async def referral_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_user = await get_user(user.id)

    if not db_user:
        await update.message.reply_text("❌ Pehle /start karo!")
        return

    referral_code = db_user["referral_code"]
    referral_count = db_user["referral_count"]
    bot_username = (await context.bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref_{referral_code}"

    remaining = REFERRALS_FOR_PREMIUM - (referral_count % REFERRALS_FOR_PREMIUM)
    progress_bar = make_progress_bar(
        referral_count % REFERRALS_FOR_PREMIUM,
        REFERRALS_FOR_PREMIUM
    )

    is_premium = await check_user_premium(user.id)
    premium_text = "💎 Premium Active" if is_premium else "👤 Normal User"

    keyboard = [[
        InlineKeyboardButton(
            "🔗 Share Referral Link",
            url=f"https://t.me/share/url?url={referral_link}&text=Join%20this%20bot!"
        )
    ]]

    await update.message.reply_text(
        f"👥 *Referral System*\n\n"
        f"📊 Status: {premium_text}\n"
        f"👥 Total Referrals: `{referral_count}`\n\n"
        f"🎯 *Next Reward:*\n"
        f"{progress_bar}\n"
        f"`{referral_count % REFERRALS_FOR_PREMIUM}/{REFERRALS_FOR_PREMIUM}` "
        f"— {remaining} aur chahiye!\n\n"
        f"🏆 *Rewards:*\n"
        f"• {REFERRALS_FOR_PREMIUM} referrals = "
        f"{PREMIUM_REWARD_DAYS} din Premium FREE!\n\n"
        f"🔗 *Tera Referral Link:*\n"
        f"`{referral_link}`\n\n"
        f"👇 Share karo:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_referral_join(new_user_id: int,
                                referral_code: str,
                                context) -> bool:
    referrer = await get_user_by_referral_code(referral_code)

    if not referrer:
        logger.warning(f"❌ Referral code nahi mila: {referral_code}")
        return False

    referrer_id = referrer["telegram_id"]

    if referrer_id == new_user_id:
        logger.warning(f"❌ Self referral: {new_user_id}")
        return False

    # Already referred check
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT referred_by FROM users WHERE telegram_id = ?",
            (new_user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row and row[0]:
                logger.warning(f"❌ Already referred: {new_user_id}")
                return False

        # referred_by update karo
        await db.execute(
            "UPDATE users SET referred_by = ? WHERE telegram_id = ?",
            (referral_code, new_user_id)
        )
        await db.commit()

    # Count badhao
    await increment_referral_count(referrer_id)

    updated_referrer = await get_user(referrer_id)
    new_count = updated_referrer["referral_count"]

    logger.info(
        f"✅ Referral counted! "
        f"Referrer: {referrer_id}, Count: {new_count}"
    )

    if new_count % REFERRALS_FOR_PREMIUM == 0:
        await update_user_premium(
            referrer_id, is_premium=True, days=PREMIUM_REWARD_DAYS
        )
        try:
            await context.bot.send_message(
                chat_id=referrer_id,
                text=(
                    f"🎉 *Congratulations!*\n\n"
                    f"Tumne {REFERRALS_FOR_PREMIUM} referrals complete kiye!\n"
                    f"💎 *{PREMIUM_REWARD_DAYS} din ka Premium* add ho gaya! 🚀"
                ),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Notify error: {e}")
    else:
        remaining = REFERRALS_FOR_PREMIUM - (new_count % REFERRALS_FOR_PREMIUM)
        try:
            await context.bot.send_message(
                chat_id=referrer_id,
                text=(
                    f"👥 *Naya Referral!*\n\n"
                    f"Kisi ne tumhara link use kiya! 🎉\n"
                    f"Total: `{new_count}` referrals\n\n"
                    f"🎯 Premium ke liye `{remaining}` aur chahiye!"
                ),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Notify error: {e}")

    return True


def make_progress_bar(current: int, total: int, length: int = 10) -> str:
    filled = int((current / total) * length)
    empty = length - filled
    bar = "█" * filled + "░" * empty
    return f"[{bar}]"


async def referral_stats_handler(update: Update,
                                   context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ Sirf admin ke liye!")
        return

    from database.db import get_all_users
    users = await get_all_users()
    total_referrals = sum(u["referral_count"] for u in users)
    top_referrers = sorted(
        users, key=lambda x: x["referral_count"], reverse=True
    )[:5]

    text = f"📊 *Referral Stats*\n\n"
    text += f"👥 Total Referrals: `{total_referrals}`\n\n"
    text += f"🏆 *Top Referrers:*\n"

    for i, u in enumerate(top_referrers, 1):
        name = u["first_name"] or u["username"] or "Unknown"
        text += f"{i}. {name} — `{u['referral_count']}` referrals\n"

    await update.message.reply_text(text, parse_mode="Markdown")
