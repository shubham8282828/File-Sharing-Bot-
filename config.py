# config.py
# Yahan se saari settings load hoti hain

import os
from dotenv import load_dotenv

# .env file se values load karo
load_dotenv()

# Bot ka token (BotFather se milta hai)
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Admin ka Telegram User ID
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# Bot ka naam (apna naam daal sakte ho)
BOT_NAME = "My File Bot"

# Token kitne ghante valid rahega
TOKEN_VALID_HOURS = 24
