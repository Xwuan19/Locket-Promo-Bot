import sqlite3
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

DB_PATH = "/tmp/locket_promo.db" if os.path.exists("/tmp") else os.path.join(os.path.dirname(__file__), "locket_promo.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS promo_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                target_username TEXT,
                target_uid TEXT,
                referrals_completed INTEGER DEFAULT 0,
                referrals_needed INTEGER DEFAULT 3,
                status TEXT DEFAULT 'PENDING',
                product_type TEXT DEFAULT 'rc_promo_Gold_custom',
                expires_date TEXT,
                created_at TEXT
            )
        """)
        conn.commit()
        conn.close()
        logger.info("Database initialized at %s", DB_PATH)
    except Exception as e:
        logger.error("Failed to init database: %s", e)

def record_promo_order(user_id: int, target_username: str, target_uid: str, referrals_completed: int, referrals_needed: int, status: str, expires_date: str = ""):
    try:
        conn = get_db()
        cursor = conn.cursor()
        now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO promo_orders (user_id, target_username, target_uid, referrals_completed, referrals_needed, status, expires_date, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, target_username, target_uid, referrals_completed, referrals_needed, status, expires_date, now_str))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error("Failed to record promo order: %s", e)

def get_system_stats():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM promo_orders")
        total = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) as success FROM promo_orders WHERE status = 'SUCCESS'")
        success = cursor.fetchone()["success"]
        cursor.execute("SELECT * FROM promo_orders ORDER BY id DESC LIMIT 10")
        recent = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return {"total_orders": total, "success_orders": success, "recent_orders": recent}
    except Exception as e:
        logger.error("Failed to fetch system stats: %s", e)
        return {"total_orders": 0, "success_orders": 0, "recent_orders": []}
