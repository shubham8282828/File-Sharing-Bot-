# bot/utils/token_manager.py
# Token system — generate, verify, save

import secrets
import logging
from datetime import datetime, timedelta
from database.db import DB_PATH
import aiosqlite

logger = logging.getLogger(__name__)


async def generate_token(telegram_id: int) -> str:
    """
    User ke liye naya token generate karo.
    Token 24 ghante valid rahega.
    """
    # Random secure token banao
    token = secrets.token_urlsafe(32)

    # Expiry time — 24 ghante baad
    expires_at = (datetime.now() + timedelta(hours=24)).isoformat()

    # Database mein save karo
    async with aiosqlite.connect(DB_PATH) as db:
        # Pehle purana token delete karo (agar hai)
        await db.execute(
            "DELETE FROM tokens WHERE telegram_id = ?",
            (telegram_id,)
        )
        # Naya token save karo
        await db.execute(
            """INSERT INTO tokens (telegram_id, token, expires_at)
               VALUES (?, ?, ?)""",
            (telegram_id, token, expires_at)
        )
        await db.commit()

    logger.info(f"✅ Token generated for user {telegram_id}")
    return token


async def verify_token(telegram_id: int) -> bool:
    """
    Check karo ki user ka token valid hai ya nahi.
    Returns True if valid, False if expired/missing.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """SELECT token, expires_at FROM tokens 
               WHERE telegram_id = ?""",
            (telegram_id,)
        ) as cursor:
            row = await cursor.fetchone()

            if not row:
                return False  # Token hai hi nahi

            token, expires_at = row

            # Expiry check karo
            expiry_time = datetime.fromisoformat(expires_at)
            if datetime.now() > expiry_time:
                # Token expire ho gaya — delete karo
                await db.execute(
                    "DELETE FROM tokens WHERE telegram_id = ?",
                    (telegram_id,)
                )
                await db.commit()
                return False

            return True  # Token valid hai!


async def verify_token_by_string(token: str) -> dict:
    """
    Token string se user dhundo aur verify karo.
    Shortener callback ke liye use hoga.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM tokens WHERE token = ?",
            (token,)
        ) as cursor:
            row = await cursor.fetchone()

            if not row:
                return {"valid": False, "reason": "Token nahi mila"}

            row = dict(row)
            expiry_time = datetime.fromisoformat(row["expires_at"])

            if datetime.now() > expiry_time:
                return {"valid": False, "reason": "Token expire ho gaya"}

            return {
                "valid": True,
                "telegram_id": row["telegram_id"]
            }


async def get_token_expiry(telegram_id: int) -> str:
    """User ke token ki expiry time lo."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT expires_at FROM tokens WHERE telegram_id = ?",
            (telegram_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                expiry = datetime.fromisoformat(row[0])
                remaining = expiry - datetime.now()
                hours = int(remaining.total_seconds() // 3600)
                minutes = int((remaining.total_seconds() % 3600) // 60)
                return f"{hours}h {minutes}m"
            return "0h 0m"
