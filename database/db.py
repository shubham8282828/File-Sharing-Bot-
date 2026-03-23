# database/db.py
import aiosqlite
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
DB_PATH = "database/bot_database.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
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
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                is_premium INTEGER DEFAULT 0,
                premium_expiry TEXT,
                referral_code TEXT UNIQUE,
                referred_by TEXT,
                referral_count INTEGER DEFAULT 0,
                joined_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
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


# ══════════════════════════════════════════
# FILE FUNCTIONS
# ══════════════════════════════════════════

async def save_file(file_name, telegram_file_id, pixeldrain_id,
                    file_type, file_size, unique_code):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO files
            (file_name, telegram_file_id, pixeldrain_id,
             file_type, file_size, unique_code)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (file_name, telegram_file_id, pixeldrain_id,
              file_type, file_size, unique_code))
        await db.commit()


async def get_file_by_code(unique_code: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM files WHERE unique_code = ?",
            (unique_code,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_all_files():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM files ORDER BY uploaded_at DESC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def delete_file(unique_code: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM files WHERE unique_code = ?",
            (unique_code,)
        )
        await db.commit()


async def update_pixeldrain_id(unique_code: str, new_pixeldrain_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE files SET pixeldrain_id = ? WHERE unique_code = ?",
            (new_pixeldrain_id, unique_code)
        )
        await db.commit()


# ══════════════════════════════════════════
# USER FUNCTIONS
# ══════════════════════════════════════════

async def save_user(telegram_id, username, first_name,
                    referral_code, referred_by=None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR IGNORE INTO users
            (telegram_id, username, first_name,
             referral_code, referred_by)
            VALUES (?, ?, ?, ?, ?)
        """, (telegram_id, username, first_name,
              referral_code, referred_by))
        await db.commit()
        async with db.execute("SELECT changes()") as cursor:
            row = await cursor.fetchone()
            return row[0] > 0


async def get_user(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE telegram_id = ?",
            (telegram_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users ORDER BY joined_at DESC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_total_users():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            row = await cursor.fetchone()
            return row[0]


async def update_user_premium(telegram_id: int,
                               is_premium: bool,
                               days: int = 30):
    expiry = (datetime.now() + timedelta(days=days)).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE users
            SET is_premium = ?, premium_expiry = ?
            WHERE telegram_id = ?
        """, (1 if is_premium else 0, expiry, telegram_id))
        await db.commit()


async def check_user_premium(telegram_id: int) -> bool:
    user = await get_user(telegram_id)
    if not user:
        return False
    if not user["is_premium"]:
        return False
    if user["premium_expiry"]:
        expiry = datetime.fromisoformat(user["premium_expiry"])
        if datetime.now() > expiry:
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute(
                    "UPDATE users SET is_premium = 0 WHERE telegram_id = ?",
                    (telegram_id,)
                )
                await db.commit()
            return False
    return True


async def increment_referral_count(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE users
            SET referral_count = referral_count + 1
            WHERE telegram_id = ?
        """, (telegram_id,))
        await db.commit()


async def get_user_by_referral_code(referral_code: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE referral_code = ?",
            (referral_code,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


# ══════════════════════════════════════════
# TOKEN FUNCTIONS
# ══════════════════════════════════════════

async def save_token(telegram_id: int, token: str, expires_at: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM tokens WHERE telegram_id = ?",
            (telegram_id,)
        )
        await db.execute("""
            INSERT INTO tokens (telegram_id, token, expires_at)
            VALUES (?, ?, ?)
        """, (telegram_id, token, expires_at))
        await db.commit()


async def get_token(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM tokens WHERE telegram_id = ?",
            (telegram_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def delete_expired_tokens():
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM tokens WHERE expires_at < ?", (now,)
        )
        await db.commit()
        logger.info("🧹 Expired tokens cleaned!")


# ══════════════════════════════════════════
# PAYMENT FUNCTIONS
# ══════════════════════════════════════════

async def save_payment(telegram_id: int, utr_number: str,
                        amount: float, plan: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO payments
            (telegram_id, utr_number, amount, plan, status)
            VALUES (?, ?, ?, ?, 'pending')
        """, (telegram_id, utr_number, amount, plan))
        await db.commit()


async def get_pending_payments():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT p.*, u.username, u.first_name
            FROM payments p
            LEFT JOIN users u ON p.telegram_id = u.telegram_id
            WHERE p.status = 'pending'
            ORDER BY p.submitted_at DESC
        """) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def update_payment_status(payment_id: int, status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE payments SET status = ? WHERE id = ?",
            (status, payment_id)
        )
        await db.commit()


async def get_payment_by_id(payment_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM payments WHERE id = ?",
            (payment_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None
