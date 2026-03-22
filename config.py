# config.py
# Yahan se saari settings load hoti hain

import os
from dotenv import load_dotenv

# .env file se values load karo
load_dotenv()

# Bot ka token (BotFather se milta hai)
BOT_TOKEN = os.getenv("8686466169:AAEL4HyE01x74Z-c6HgJsF0bVuqj5Z4lDus")

# Admin ka Telegram User ID
ADMIN_ID = int(os.getenv("8488620690", "0"))

# Bot ka naam (apna naam daal sakte ho)
BOT_NAME = "My File Bot"

# Token kitne ghante valid rahega
TOKEN_VALID_HOURS = 24
