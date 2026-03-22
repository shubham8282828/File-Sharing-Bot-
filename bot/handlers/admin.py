# bot/handlers/admin.py
# Admin file upload — ab database mein save hoga!

import os
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import ADMIN_ID
from bot.utils.pixeldrain import upload_to_pixeldrain
from bot.utils.helpers import generate_unique_code
from database.db import save_file, get_all_files

logger = logging.getLogger(__name__)

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


async def upload_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin file upload → Pixeldrain → Database save."""
    user = update.effective_user

    if not is_admin(user.id):
        await update.message.reply_text("❌ Sirf admin files upload kar sakta hai!")
        return

    message = update.message
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

    file_id = file.file_id
    file_name = getattr(file, "file_name", f"{file_type}_{file_id[:8]}")
    file_size = getattr(file, "file_size", 0)
    size_mb = round(file_size / (1024 * 1024), 2)

    if file_size > 20 * 1024 * 1024:
        await message.reply_text(f"⚠️ File {size_mb}MB hai! Max 20MB allowed.")
        return

    status_msg = await message.reply_text(
        f"⏳ Processing `{file_name}`...\n"
        f"📥 Telegram se download ho raha hai...",
        parse_mode="Markdown"
    )

    temp_path = os.path.join(TEMP_DIR, file_name)

    try:
        # Step 1: Download
        tg_file = await context.bot.get_file(file_id)
        await tg_file.download_to_drive(temp_path)

        await status_msg.edit_text(
            f"⏳ Processing `{file_name}`...\n"
            f"✅ Download done!\n"
            f"📤 Pixeldrain pe upload ho raha hai...",
            parse_mode="Markdown"
        )

        # Step 2: Pixeldrain upload
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, upload_to_pixeldrain, temp_path, file_name
        )

        # Temp file delete
        if os.path.exists(temp_path):
            os.remove(temp_path)

        if not result["success"]:
            await status_msg.edit_text(f"❌ Upload failed: {result['error']}")
            return

        pd_file_id = result["file_id"]

        # Step 3: Unique code generate karo
        unique_code = generate_unique_code()

        # Step 4: Database mein save karo
        await save_file(
            file_name=file_name,
            telegram_file_id=file_id,
            pixeldrain_id=pd_file_id,
            file_type=file_type,
            file_size=size_mb,
            unique_code=unique_code
        )

        # Step 5: Bot username lo
        bot_username = (await context.bot.get_me()).username
        share_link = f"https://t.me/{bot_username}?start={unique_code}"

        await status_msg.edit_text(
            f"✅ *File Upload Complete!*\n\n"
            f"📄 Name: `{file_name}`\n"
            f"💾 Size: `{size_mb} MB`\n"
            f"🔑 Code: `{unique_code}`\n"
            f"🌐 Pixeldrain: `{pd_file_id}`\n\n"
            f"🔗 *Share Link:*\n`{share_link}`",
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Upload error: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        await status_msg.edit_text(f"❌ Error: `{str(e)}`", parse_mode="Markdown")


async def admin_panel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin panel."""
    user = update.effective_user

    if not is_admin(user.id):
        await update.message.reply_text("❌ Sirf admin ke liye!")
        return

    # Total files count
    files = await get_all_files()
    total_files = len(files)

    await update.message.reply_text(
        f"🛠 *Admin Panel*\n\n"
        f"📁 Total Files: `{total_files}`\n\n"
        f"📤 File upload karne ke liye seedha bhejo!\n\n"
        f"📋 *Commands:*\n"
        f"/admin — Yeh panel\n"
        f"/files — Saari files list\n"
        f"/stats — Bot stats\n",
        parse_mode="Markdown"
    )


async def list_files_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Saari uploaded files list karo."""
    user = update.effective_user

    if not is_admin(user.id):
        await update.message.reply_text("❌ Sirf admin ke liye!")
        return

    files = await get_all_files()

    if not files:
        await update.message.reply_text("📂 Koi file upload nahi hui abhi!")
        return

    # Files list banao
    text = "📁 *Uploaded Files:*\n\n"
    for f in files[:10]:  # Sirf pehli 10 dikhao
        text += (
            f"• `{f['file_name']}`\n"
            f"  Code: `{f['unique_code']}`\n"
            f"  Size: `{f['file_size']} MB`\n\n"
        )

    await update.message.reply_text(text, parse_mode="Markdown")
