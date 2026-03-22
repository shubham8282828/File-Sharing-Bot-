# bot/handlers/admin.py
# Admin ke liye file upload handler — Pixeldrain integration added

import os
import asyncio
import logging
from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_ID
from bot.utils.pixeldrain import upload_to_pixeldrain

logger = logging.getLogger(__name__)

# Temp folder jahan file temporarily save hogi
TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)  # Folder banao agar nahi hai


def is_admin(user_id: int) -> bool:
    """Check karo ki user admin hai ya nahi."""
    return user_id == ADMIN_ID


async def upload_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Admin file bhejta hai → Bot download karta hai → Pixeldrain pe upload karta hai.
    """
    user = update.effective_user

    # Admin check
    if not is_admin(user.id):
        await update.message.reply_text("❌ Sirf admin files upload kar sakta hai!")
        return

    message = update.message

    # Kaunsi file aayi?
    file = None
    file_type = None

    if message.video:
        file = message.video
        file_type = "video"
    elif message.document:
        file = message.document
        file_type = "document"
    elif message.audio:
        file = message.audio
        file_type = "audio"
    else:
        await message.reply_text("⚠️ Sirf video, document ya audio bhejo!")
        return

    # File info
    file_id = file.file_id
    file_name = getattr(file, "file_name", f"{file_type}_{file_id[:8]}")
    file_size = getattr(file, "file_size", 0)
    size_mb = round(file_size / (1024 * 1024), 2)

    # ⚠️ Telegram 20MB limit check
    if file_size > 20 * 1024 * 1024:
        await message.reply_text(
            f"⚠️ File {size_mb}MB hai!\n"
            f"Telegram Bot API sirf 20MB tak download kar sakta hai.\n"
            f"Chhoti file bhejo."
        )
        return

    # Processing message bhejo
    status_msg = await message.reply_text(
        f"⏳ Processing...\n\n"
        f"📄 File: `{file_name}`\n"
        f"💾 Size: `{size_mb} MB`\n\n"
        f"Step 1: Telegram se download ho raha hai...",
        parse_mode="Markdown"
    )

    try:
        # Step 1: Telegram se file download karo
        tg_file = await context.bot.get_file(file_id)
        temp_path = os.path.join(TEMP_DIR, file_name)
        await tg_file.download_to_drive(temp_path)

        await status_msg.edit_text(
            f"⏳ Processing...\n\n"
            f"📄 File: `{file_name}`\n"
            f"💾 Size: `{size_mb} MB`\n\n"
            f"✅ Download complete!\n"
            f"Step 2: Pixeldrain pe upload ho raha hai...",
            parse_mode="Markdown"
        )

        # Step 2: Pixeldrain pe upload karo (blocking call — thread mein chalao)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            upload_to_pixeldrain,
            temp_path,
            file_name
        )

        # Temp file delete karo
        if os.path.exists(temp_path):
            os.remove(temp_path)

        # Result check karo
        if result["success"]:
            pd_file_id = result["file_id"]

            await status_msg.edit_text(
                f"✅ *Upload Complete!*\n\n"
                f"📄 Name: `{file_name}`\n"
                f"💾 Size: `{size_mb} MB`\n"
                f"🆔 Telegram ID: `{file_id}`\n"
                f"🌐 Pixeldrain ID: `{pd_file_id}`\n\n"
                f"🔗 Link: `https://pixeldrain.com/u/{pd_file_id}`\n\n"
                f"⚠️ Step 4 mein yeh ID database mein save hoga!",
                parse_mode="Markdown"
            )
        else:
            await status_msg.edit_text(
                f"❌ *Pixeldrain Upload Failed!*\n\n"
                f"Error: `{result['error']}`\n\n"
                f"Dobara try karo.",
                parse_mode="Markdown"
            )

    except Exception as e:
        logger.error(f"Upload error: {e}")
        # Temp file cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)
        await status_msg.edit_text(f"❌ Error: `{str(e)}`", parse_mode="Markdown")


async def admin_panel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /admin command — Admin panel dikhao.
    """
    user = update.effective_user

    if not is_admin(user.id):
        await update.message.reply_text("❌ Yeh command sirf admin ke liye hai!")
        return

    await update.message.reply_text(
        "🛠 *Admin Panel*\n\n"
        "📤 *File Upload:*\n"
        "Seedha video/document bhejo — bot Pixeldrain pe upload karega!\n\n"
        "📋 *Commands:*\n"
        "/admin — Yeh panel\n"
        "/stats — Bot stats\n"
        "/broadcast — Sabko message\n",
        parse_mode="Markdown"
    )
