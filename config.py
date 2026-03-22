# config.py
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
PIXELDRAIN_API_KEY = os.getenv("PIXELDRAIN_API_KEY")  # ✅ New

BOT_NAME = "My File Bot"
TOKEN_VALID_HOURS = 24
