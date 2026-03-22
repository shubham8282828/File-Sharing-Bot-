# database/db.py
# SQLite database — sabki info yahan store hogi

import aiosqlite
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

DB_PATH = "database/bot_database.db"


async def init_db():
    """
    Database aur tables banao.
    Pehli baar chalega tab tables create hongi.
    """
    async with aiosqlite.connect(DB_PATH) as db:

        # ✅ Files table — uploaded files ki info
        await db.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT NOT NULL,
                telegram_file_id TEXT NOT NULL,
                pixeldrain_id TEXT,
                file_type TEXT,
                file_size REAL,
                unique_code TEXT UNIQUE NOT NULL,
                uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ✅ Users table — bot use karne wale users
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                is_premium INTEGER DEFAULT 0,
                premium_expiry TEXT,
                referral_code TEXT UNIQUE,
                referred_by INTEGER,
                joined_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ✅ Tokens table — shortener tokens
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ✅ Payments table — UPI payments
        await db.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                utr_number TEXT NOT NULL,
                amount REAL NOT NULL,
                plan TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                submitted_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.commit()
        logger.info("✅ Database initialized!")


# ─── FILE FUNCTIONS ───────────────────────────────────────────

async def save_file(file_name, telegram_file_id, pixeldrain_id,
                    file_type, file_size, unique_code):
    """File database mein save karo."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO files 
            (file_name, telegram_file_id, pixeldrain_id, file_type, file_size, unique_code)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (file_name, telegram_file_id, pixeldrain_id,
              file_type, file_size, unique_code))
        await db.commit()
        logger.info(f"✅ File saved: {unique_code}")


async def get_file_by_code(unique_code: str):
    """Unique code se file dhundo."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM files WHERE unique_code = ?",
            (unique_code,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_all_files():
    """Saari files list karo."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM files ORDER BY uploaded_at DESC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def update_pixeldrain_id(unique_code: str, new_pixeldrain_id: str):
    """Pixeldrain ID update karo (re-upload ke baad)."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE files SET pixeldrain_id = ? WHERE unique_code = ?",
            (new_pixeldrain_id, unique_code)
        )
        await db.commit()


# ─── USER FUNCTIONS ───────────────────────────────────────────

async def save_user(telegram_id, username, first_name, referral_code, referred_by=None):
    """Naya user save karo."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR IGNORE INTO users 
            (telegram_id, username, first_name, referral_code, referred_by)
            VALUES (?, ?, ?, ?, ?)
        """, (telegram_id, username, first_name, referral_code, referred_by))
        await db.commit()


async def get_user(telegram_id: int):
    """User ki info lo."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE telegram_id = ?",
            (telegram_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_total_users():
    """Total users count karo."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            row = await cursor.fetchone()
            return row[0]
