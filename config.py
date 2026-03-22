# config.py
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
PIXELDRAIN_API_KEY = os.getenv("PIXELDRAIN_API_KEY")

BOT_NAME = "My File Bot"
TOKEN_VALID_HOURS = 24

# ✅ Shortener settings
# mdiskshortener ya koi bhi shortener API use kar sakte ho
SHORTENER_API_KEY = os.getenv("SHORTENER_API_KEY", "")
SHORTENER_DOMAIN = os.getenv("SHORTENER_DOMAIN", "https://mdiskhub.com")

# ✅ Bot ka URL (Render URL)
BOT_URL = os.getenv("RENDER_EXTERNAL_URL", "")
