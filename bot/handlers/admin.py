# bot/handlers/admin.py
# Admin ke liye file upload handler

from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_ID


def is_admin(user_id: int) -> bool:
    """
    Check karo ki user admin hai ya nahi.
    """
    return user_id == ADMIN_ID


async def upload_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Jab admin koi file/video bhejta hai tab yeh chalta hai.
    Abhi sirf file_id print karega — Step 3 mein Pixeldrain pe upload hoga.
    """
    user = update.effective_user

    # Admin check — agar admin nahi hai to reject karo
    if not is_admin(user.id):
        await update.message.reply_text("❌ Sirf admin files upload kar sakta hai!")
        return

    message = update.message

    # Kaunsi file aayi — video, document, ya audio?
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

    # File ID aur basic info
    file_id = file.file_id
    file_name = getattr(file, "file_name", f"{file_type}_{file_id[:8]}")
    file_size = getattr(file, "file_size", 0)

    # Size MB mein convert karo
    size_mb = round(file_size / (1024 * 1024), 2)

    # Admin ko confirmation do
    await message.reply_text(
        f"✅ *File Received!*\n\n"
        f"📄 Name: `{file_name}`\n"
        f"🆔 File ID: `{file_id}`\n"
        f"📦 Type: `{file_type}`\n"
        f"💾 Size: `{size_mb} MB`\n\n"
        f"⏳ Step 3 mein Pixeldrain pe upload hoga...",
        parse_mode="Markdown"
    )


async def admin_panel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /admin command — Admin panel dikhao.
    """
    user = update.effective_user

    # Admin check
    if not is_admin(user.id):
        await update.message.reply_text("❌ Yeh command sirf admin ke liye hai!")
        return

    await update.message.reply_text(
        "🛠 *Admin Panel*\n\n"
        "📤 File upload karne ke liye:\n"
        "Seedha video/document bhejo is chat mein!\n\n"
        "📋 *Available Commands:*\n"
        "/admin — Yeh panel\n"
        "/stats — Bot stats (aayega aage)\n"
        "/broadcast — Sabko message (aayega aage)\n",
        parse_mode="Markdown"
    )
