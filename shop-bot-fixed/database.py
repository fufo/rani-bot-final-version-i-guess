"""
╔══════════════════════════════════════════════════════════╗
║           TELEGRAM SHOP BOT - DATABASE MODULE            ║
║     SQLite3 — all settings stored & editable live        ║
╚══════════════════════════════════════════════════════════╝
"""

import sqlite3
import json
import logging
import shutil
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager

from config import DATABASE_PATH, DEFAULT_SETTINGS, PRIMARY_ADMIN_ID

logger = logging.getLogger(__name__)

# Lazy import to avoid circular — cache is initialised after this module loads
def _cache():
    from utils.cache import settings_cache, products_cache
    return settings_cache, products_cache


# ─────────────────────────────────────────────
#  CONNECTION MANAGER
# ─────────────────────────────────────────────

@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE_PATH, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA synchronous=NORMAL")
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        conn.close()


# ─────────────────────────────────────────────
#  INIT
# ─────────────────────────────────────────────

def init_database():
    with get_db() as conn:
        c = conn.cursor()

        # USERS
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id              INTEGER PRIMARY KEY,
                user_id         INTEGER UNIQUE NOT NULL,
                username        TEXT,
                first_name      TEXT,
                last_name       TEXT,
                language        TEXT DEFAULT 'en',
                balance         REAL DEFAULT 0.0,
                stars_balance   INTEGER DEFAULT 0,
                is_banned       INTEGER DEFAULT 0,
                ban_reason      TEXT,
                referral_code   TEXT UNIQUE,
                referred_by     INTEGER,
                total_spent     REAL DEFAULT 0.0,
                total_orders    INTEGER DEFAULT 0,
                joined_at       TEXT DEFAULT (datetime('now')),
                last_seen       TEXT DEFAULT (datetime('now')),
                captcha_passed  INTEGER DEFAULT 0,
                FOREIGN KEY (referred_by) REFERENCES users(user_id)
            )
        """)

        # CATEGORIES
        c.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL,
                name_ar     TEXT,
                name_fr     TEXT,
                emoji       TEXT DEFAULT '📦',
                description TEXT,
                is_active   INTEGER DEFAULT 1,
                sort_order  INTEGER DEFAULT 0,
                created_at  TEXT DEFAULT (datetime('now'))
            )
        """)

        # PRODUCTS
        c.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id     INTEGER,
                name            TEXT NOT NULL,
                name_ar         TEXT,
                name_fr         TEXT,
                description     TEXT,
                description_ar  TEXT,
                description_fr  TEXT,
                price           REAL NOT NULL DEFAULT 0.0,
                price_stars     INTEGER DEFAULT 0,
                stock           INTEGER DEFAULT -1,
                file_id         TEXT,
                file_type       TEXT,
                file_name       TEXT,
                text_content    TEXT,
                thumbnail_id    TEXT,
                is_active       INTEGER DEFAULT 1,
                total_sold      INTEGER DEFAULT 0,
                created_at      TEXT DEFAULT (datetime('now')),
                updated_at      TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        """)

        # Migration: add text_content column if it doesn't exist yet
        try:
            c.execute("ALTER TABLE products ADD COLUMN text_content TEXT")
        except Exception:
            pass  # Column already exists

        # ORDERS
        c.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id        TEXT UNIQUE NOT NULL,
                user_id         INTEGER NOT NULL,
                product_id      INTEGER,
                product_name    TEXT,
                quantity        INTEGER DEFAULT 1,
                amount          REAL NOT NULL,
                payment_method  TEXT NOT NULL,
                status          TEXT DEFAULT 'pending',
                delivered_at    TEXT,
                created_at      TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)

        # Migration: allow NULL product_id in orders (Stars purchases have no product)
        # SQLite doesn't support DROP NOT NULL directly — we recreate if needed
        try:
            c.execute("SELECT product_id FROM orders WHERE product_id IS NULL LIMIT 1")
        except Exception:
            pass  # Column exists and accepts NULL already
        # Ensure any old row with product_id=0 is updated to NULL to avoid FK errors
        try:
            conn.execute("UPDATE orders SET product_id=NULL WHERE product_id=0")
        except Exception:
            pass

        # DEPOSITS
        c.execute("""
            CREATE TABLE IF NOT EXISTS deposits (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                deposit_id      TEXT UNIQUE NOT NULL,
                user_id         INTEGER NOT NULL,
                amount          REAL NOT NULL,
                method          TEXT NOT NULL,
                tx_hash         TEXT,
                status          TEXT DEFAULT 'pending',
                admin_note      TEXT,
                created_at      TEXT DEFAULT (datetime('now')),
                confirmed_at    TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # COUPONS
        c.execute("""
            CREATE TABLE IF NOT EXISTS coupons (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                code            TEXT UNIQUE NOT NULL,
                discount_type   TEXT NOT NULL,
                discount_value  REAL NOT NULL,
                min_purchase    REAL DEFAULT 0.0,
                max_uses        INTEGER DEFAULT -1,
                used_count      INTEGER DEFAULT 0,
                expires_at      TEXT,
                is_active       INTEGER DEFAULT 1,
                created_at      TEXT DEFAULT (datetime('now'))
            )
        """)

        # COUPON USAGE
        c.execute("""
            CREATE TABLE IF NOT EXISTS coupon_usage (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                coupon_id   INTEGER NOT NULL,
                user_id     INTEGER NOT NULL,
                order_id    TEXT,
                used_at     TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (coupon_id) REFERENCES coupons(id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # SETTINGS (key-value, all dynamic)
        c.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key     TEXT PRIMARY KEY,
                value   TEXT NOT NULL
            )
        """)

        # ADMIN LOGS
        c.execute("""
            CREATE TABLE IF NOT EXISTS admin_logs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id    INTEGER NOT NULL,
                action      TEXT NOT NULL,
                details     TEXT,
                target_id   INTEGER,
                created_at  TEXT DEFAULT (datetime('now'))
            )
        """)

        # BROADCASTS
        c.execute("""
            CREATE TABLE IF NOT EXISTS broadcasts (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id        INTEGER NOT NULL,
                message         TEXT NOT NULL,
                total_sent      INTEGER DEFAULT 0,
                total_failed    INTEGER DEFAULT 0,
                status          TEXT DEFAULT 'pending',
                created_at      TEXT DEFAULT (datetime('now')),
                completed_at    TEXT
            )
        """)

        # REFERRALS
        c.execute("""
            CREATE TABLE IF NOT EXISTS referrals (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id     INTEGER NOT NULL,
                referee_id      INTEGER NOT NULL,
                bonus_paid      REAL DEFAULT 0.0,
                created_at      TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (referrer_id) REFERENCES users(user_id),
                FOREIGN KEY (referee_id) REFERENCES users(user_id)
            )
        """)

        # SUPPORT TICKETS
        c.execute("""
            CREATE TABLE IF NOT EXISTS support_tickets (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                message     TEXT NOT NULL,
                status      TEXT DEFAULT 'open',
                created_at  TEXT DEFAULT (datetime('now'))
            )
        """)

        # ── NEW: BOT ADMINS (dynamic admin management) ──────────────
        c.execute("""
            CREATE TABLE IF NOT EXISTS bot_admins (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id         INTEGER UNIQUE NOT NULL,
                username        TEXT,
                first_name      TEXT,
                permissions     TEXT DEFAULT 'all',
                added_by        INTEGER NOT NULL,
                added_at        TEXT DEFAULT (datetime('now')),
                is_active       INTEGER DEFAULT 1
            )
        """)

        # ── NEW: FORCE SUBSCRIBE CHANNELS ───────────────────────────
        c.execute("""
            CREATE TABLE IF NOT EXISTS force_subscribe_channels (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                username    TEXT NOT NULL,
                title       TEXT,
                link        TEXT,
                is_active   INTEGER DEFAULT 1,
                added_at    TEXT DEFAULT (datetime('now'))
            )
        """)

        # ── NEW: STARS PACKAGES ─────────────────────────────────────
        c.execute("""
            CREATE TABLE IF NOT EXISTS stars_packages (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL,
                stars       INTEGER NOT NULL,
                price_usd   REAL NOT NULL,
                bonus_stars INTEGER DEFAULT 0,
                is_active   INTEGER DEFAULT 1,
                sort_order  INTEGER DEFAULT 0,
                created_at  TEXT DEFAULT (datetime('now'))
            )
        """)

        # ── DAILY GIFT CLAIMS ─────────────────────────────────────────
        c.execute("""
            CREATE TABLE IF NOT EXISTS daily_gift_claims (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                points      REAL NOT NULL,
                claimed_at  TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # ── REWARD LINKS ─────────────────────────────────────────────
        c.execute("""
            CREATE TABLE IF NOT EXISTS reward_links (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                token       TEXT UNIQUE NOT NULL,
                points      REAL NOT NULL DEFAULT 0.0,
                max_uses    INTEGER DEFAULT -1,
                used_count  INTEGER DEFAULT 0,
                expires_at  TEXT,
                target_users TEXT,
                is_active   INTEGER DEFAULT 1,
                created_by  INTEGER NOT NULL,
                created_at  TEXT DEFAULT (datetime('now'))
            )
        """)

        # REWARD LINK CLAIMS
        c.execute("""
            CREATE TABLE IF NOT EXISTS reward_link_claims (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                link_id     INTEGER NOT NULL,
                user_id     INTEGER NOT NULL,
                claimed_at  TEXT DEFAULT (datetime('now')),
                UNIQUE(link_id, user_id),
                FOREIGN KEY (link_id) REFERENCES reward_links(id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # Migration: add product share_token column if it doesn't exist
        try:
            c.execute("ALTER TABLE products ADD COLUMN share_token TEXT")
        except Exception:
            pass

        # ── Seed default settings ───────────────────────────────────
        for key, value in DEFAULT_SETTINGS.items():
            c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                      (key, json.dumps(value)))

        # ── Seed primary admin ──────────────────────────────────────
        c.execute("""
            INSERT OR IGNORE INTO bot_admins (user_id, username, first_name, permissions, added_by)
            VALUES (?, ?, ?, ?, ?)
        """, (PRIMARY_ADMIN_ID, "owner", "Owner", "all", PRIMARY_ADMIN_ID))

        # ── Seed default stars packages ─────────────────────────────
        default_packages = [
            ("Starter Pack", 50,  1.00, 0),
            ("Basic Pack",   100, 1.80, 10),
            ("Pro Pack",     250, 4.00, 25),
            ("Premium Pack", 500, 7.50, 50),
            ("Elite Pack",  1000, 14.0, 100),
        ]
        for pkg in default_packages:
            c.execute("""
                INSERT OR IGNORE INTO stars_packages (name, stars, price_usd, bonus_stars)
                SELECT ?, ?, ?, ?
                WHERE NOT EXISTS (SELECT 1 FROM stars_packages WHERE name = ?)
            """, (*pkg, pkg[0]))

        # ── Migration: reset overpowered wheel segments to corrected house-edge version ──
        try:
            old_segs = get_setting("game_wheel_segments")
            if old_segs:
                import json as _json
                segs = _json.loads(old_segs) if isinstance(old_segs, str) else old_segs
                # Detect old config by checking if expected return > 1.0 (house losing)
                if segs:
                    total_w = sum(s.get("weight", 10) for s in segs)
                    exp_ret = sum(s.get("multiplier", s.get("value", 0)) * s.get("weight", 10) / total_w for s in segs)
                    if exp_ret > 1.0:  # house is losing money — reset to correct config
                        conn.execute("DELETE FROM settings WHERE key='game_wheel_segments'")
                        logger.info(f"🎡 Reset overpowered wheel segments (old RTP={exp_ret*100:.0f}%)")
            # Also reset overpowered slot defaults if stored
            for slot_key, correct_default in [
                ("game_slot_loss_prob", 78), ("game_slot_small_prob", 12),
                ("game_slot_med_prob",  6),  ("game_slot_big_prob",   3),
            ]:
                old_val = get_setting(slot_key)
                if old_val is not None:
                    # If loss prob < 70, it was set to old overpowered value
                    if slot_key == "game_slot_loss_prob" and float(old_val) < 70:
                        conn.execute("DELETE FROM settings WHERE key=?", (slot_key,))
                        logger.info(f"🎰 Reset slot loss prob (was {old_val}% → now uses default 78%)")
        except Exception as e:
            logger.warning(f"Wheel/slot migration check error: {e}")

        # ── One-time migration: convert stars_balance → balance (2 stars = 1 point) ──
        # Runs safely every startup — only affects rows where stars_balance > 0
        # and sets stars_balance to 0 after converting so it never runs twice on same user
        try:
            c.execute("SELECT COUNT(*) FROM users WHERE stars_balance > 0")
            pending = c.fetchone()[0]
            if pending:
                conn.execute("""
                    UPDATE users
                    SET balance       = balance + ROUND(stars_balance / 2.0, 4),
                        stars_balance = 0
                    WHERE stars_balance > 0
                """)
                logger.info(f"\u2b50\u2192\U0001f4b0 Converted stars to points for {pending} user(s) (2 stars = 1 point)")
        except Exception as e:
            logger.warning(f"Stars->points migration error: {e}")

        logger.info("\u2705 Database v3 initialized")


# ─────────────────────────────────────────────
#  SETTINGS
# ─────────────────────────────────────────────

def get_setting(key: str, default=None):
    sc, _ = _cache()
    cached = sc.get(f"setting:{key}")
    if cached is not None:
        return cached
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = c.fetchone()
        if row:
            try:
                val = json.loads(row["value"])
            except Exception:
                val = row["value"]
        else:
            val = default
    if val is not None:
        sc.set(f"setting:{key}", val)
    return val


def safe_float_setting(key: str, default: float) -> float:
    """Get a setting as float, falling back to default if missing or non-numeric."""
    val = get_setting(key, default)
    try:
        return float(val)
    except (TypeError, ValueError):
        return float(default)


def set_setting(key: str, value) -> bool:
    with get_db() as conn:
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                     (key, json.dumps(value)))
    from utils.cache import invalidate_settings
    invalidate_settings(key)
    return True


def get_all_settings() -> Dict:
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT key, value FROM settings")
        result = {}
        for row in c.fetchall():
            try:
                result[row["key"]] = json.loads(row["value"])
            except Exception:
                result[row["key"]] = row["value"]
        return result


# ─────────────────────────────────────────────
#  BOT ADMINS
# ─────────────────────────────────────────────

_admin_cache: Optional[List[int]] = None
_admin_cache_ts: float = 0.0
_ADMIN_CACHE_TTL = 30.0  # seconds


def get_admin_ids() -> List[int]:
    global _admin_cache, _admin_cache_ts
    import time
    now = time.time()
    if _admin_cache is not None and (now - _admin_cache_ts) < _ADMIN_CACHE_TTL:
        return _admin_cache
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT user_id FROM bot_admins WHERE is_active = 1")
        ids = [row["user_id"] for row in c.fetchall()]
    if PRIMARY_ADMIN_ID not in ids:
        ids.insert(0, PRIMARY_ADMIN_ID)
    _admin_cache = ids
    _admin_cache_ts = now
    return ids


def invalidate_admin_cache():
    global _admin_cache
    _admin_cache = None


def get_all_admins() -> List[Dict]:
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM bot_admins WHERE is_active = 1 ORDER BY added_at")
        return [dict(r) for r in c.fetchall()]


def add_admin(user_id: int, username: str, first_name: str,
              added_by: int, permissions: str = "all") -> bool:
    with get_db() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO bot_admins
                (user_id, username, first_name, permissions, added_by, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (user_id, username, first_name, permissions, added_by))
    invalidate_admin_cache()
    return True


def remove_admin(user_id: int) -> bool:
    if user_id == PRIMARY_ADMIN_ID:
        return False  # owner cannot be removed
    with get_db() as conn:
        conn.execute("UPDATE bot_admins SET is_active = 0 WHERE user_id = ?", (user_id,))
    invalidate_admin_cache()
    return True


# ─────────────────────────────────────────────
#  FORCE SUBSCRIBE CHANNELS
# ─────────────────────────────────────────────

def get_force_channels(active_only: bool = True) -> List[Dict]:
    with get_db() as conn:
        c = conn.cursor()
        if active_only:
            c.execute("SELECT * FROM force_subscribe_channels WHERE is_active = 1")
        else:
            c.execute("SELECT * FROM force_subscribe_channels ORDER BY id")
        return [dict(r) for r in c.fetchall()]


def add_force_channel(username: str, title: str = "", link: str = "") -> int:
    username = username.lstrip("@")
    if not link:
        link = f"https://t.me/{username}"
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT OR REPLACE INTO force_subscribe_channels (username, title, link, is_active)
            VALUES (?, ?, ?, 1)
        """, (username, title or username, link))
        return c.lastrowid


def remove_force_channel(channel_id: int) -> bool:
    with get_db() as conn:
        conn.execute("DELETE FROM force_subscribe_channels WHERE id = ?", (channel_id,))
    return True


def toggle_force_channel(channel_id: int) -> bool:
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT is_active FROM force_subscribe_channels WHERE id = ?", (channel_id,))
        row = c.fetchone()
        if row:
            conn.execute("UPDATE force_subscribe_channels SET is_active = ? WHERE id = ?",
                         (0 if row["is_active"] else 1, channel_id))
    return True


def update_force_channel(channel_id: int, **kwargs) -> bool:
    if not kwargs:
        return False
    fields = ", ".join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values()) + [channel_id]
    with get_db() as conn:
        conn.execute(f"UPDATE force_subscribe_channels SET {fields} WHERE id = ?", values)
    return True


# ─────────────────────────────────────────────
#  STARS PACKAGES
# ─────────────────────────────────────────────

def get_stars_packages(active_only: bool = True) -> List[Dict]:
    with get_db() as conn:
        c = conn.cursor()
        if active_only:
            c.execute("SELECT * FROM stars_packages WHERE is_active = 1 ORDER BY sort_order, stars")
        else:
            c.execute("SELECT * FROM stars_packages ORDER BY sort_order, stars")
        return [dict(r) for r in c.fetchall()]


def get_stars_package(pkg_id: int) -> Optional[Dict]:
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM stars_packages WHERE id = ?", (pkg_id,))
        row = c.fetchone()
        return dict(row) if row else None


def create_stars_package(name: str, stars: int, price_usd: float,
                          bonus_stars: int = 0) -> int:
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO stars_packages (name, stars, price_usd, bonus_stars)
            VALUES (?, ?, ?, ?)
        """, (name, stars, price_usd, bonus_stars))
        return c.lastrowid


def update_stars_package(pkg_id: int, **kwargs) -> bool:
    if not kwargs:
        return False
    fields = ", ".join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values()) + [pkg_id]
    with get_db() as conn:
        conn.execute(f"UPDATE stars_packages SET {fields} WHERE id = ?", values)
    return True


def delete_stars_package(pkg_id: int) -> bool:
    with get_db() as conn:
        conn.execute("DELETE FROM stars_packages WHERE id = ?", (pkg_id,))
    return True


def toggle_stars_package(pkg_id: int) -> bool:
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT is_active FROM stars_packages WHERE id = ?", (pkg_id,))
        row = c.fetchone()
        if row:
            conn.execute("UPDATE stars_packages SET is_active = ? WHERE id = ?",
                         (0 if row["is_active"] else 1, pkg_id))
    return True


# ─────────────────────────────────────────────
#  USER OPERATIONS
# ─────────────────────────────────────────────

def get_or_create_user(user_id: int, username: str = None,
                        first_name: str = None, last_name: str = None,
                        referral_code: str = None) -> Dict:
    import random, string

    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = c.fetchone()

        if user:
            c.execute("""
                UPDATE users SET username=?, first_name=?, last_name=?,
                last_seen=datetime('now') WHERE user_id=?
            """, (username, first_name, last_name, user_id))
            c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            return dict(c.fetchone())

        ref_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        referred_by = None
        if referral_code:
            c.execute("SELECT user_id FROM users WHERE referral_code = ?", (referral_code,))
            ref_row = c.fetchone()
            # Prevent self-referral
            if ref_row and ref_row["user_id"] != user_id:
                referred_by = ref_row["user_id"]

        c.execute("""
            INSERT INTO users (user_id, username, first_name, last_name,
                               referral_code, referred_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, username, first_name, last_name, ref_code, referred_by))

        if referred_by:
            bonus_type = get_setting("referral_bonus_type", "balance")
            bonus = get_setting("referral_bonus", 0.5)
            stars_bonus = get_setting("referral_stars_bonus", 0)
            if bonus_type == "stars" and stars_bonus > 0:
                conn.execute("UPDATE users SET stars_balance = stars_balance + ? WHERE user_id = ?",
                             (stars_bonus, referred_by))
                conn.execute("INSERT INTO referrals (referrer_id, referee_id, bonus_paid) VALUES (?, ?, ?)",
                             (referred_by, user_id, 0))
            else:
                conn.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?",
                             (bonus, referred_by))
                conn.execute("INSERT INTO referrals (referrer_id, referee_id, bonus_paid) VALUES (?, ?, ?)",
                             (referred_by, user_id, bonus))

        c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return dict(c.fetchone())


def get_user(user_id: int) -> Optional[Dict]:
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        return dict(row) if row else None


def update_user(user_id: int, **kwargs) -> bool:
    if not kwargs:
        return False
    fields = ", ".join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values()) + [user_id]
    with get_db() as conn:
        conn.execute(f"UPDATE users SET {fields} WHERE user_id = ?", values)
    return True


def get_all_users(active_only: bool = False) -> List[Dict]:
    with get_db() as conn:
        c = conn.cursor()
        if active_only:
            c.execute("SELECT * FROM users WHERE is_banned = 0")
        else:
            c.execute("SELECT * FROM users ORDER BY joined_at DESC")
        return [dict(r) for r in c.fetchall()]


def get_users_paginated(page: int, per_page: int) -> Tuple[List[Dict], int]:
    offset = (page - 1) * per_page
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM users")
        total = c.fetchone()[0]
        c.execute("SELECT * FROM users ORDER BY joined_at DESC LIMIT ? OFFSET ?",
                  (per_page, offset))
        users = [dict(r) for r in c.fetchall()]
    return users, total


def ban_user(user_id: int, reason: str = "No reason provided") -> bool:
    with get_db() as conn:
        conn.execute("UPDATE users SET is_banned=1, ban_reason=? WHERE user_id=?",
                     (reason, user_id))
    return True


def unban_user(user_id: int) -> bool:
    with get_db() as conn:
        conn.execute("UPDATE users SET is_banned=0, ban_reason=NULL WHERE user_id=?",
                     (user_id,))
    return True


def adjust_balance(user_id: int, amount: float) -> float:
    with get_db() as conn:
        c = conn.cursor()
        conn.execute("UPDATE users SET balance=MAX(0,balance+?) WHERE user_id=?",
                     (amount, user_id))
        c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        return c.fetchone()["balance"]


def atomic_deduct_balance(user_id: int, amount: float) -> bool:
    """Atomically deduct balance only if sufficient funds exist. Returns True on success."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            "UPDATE users SET balance = balance - ? WHERE user_id = ? AND balance >= ?",
            (amount, user_id, amount)
        )
        return c.rowcount == 1


def atomic_deduct_stars(user_id: int, amount: int) -> bool:
    """Atomically deduct stars only if sufficient balance exists. Returns True on success."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            "UPDATE users SET stars_balance = stars_balance - ? WHERE user_id = ? AND stars_balance >= ?",
            (amount, user_id, amount)
        )
        return c.rowcount == 1


def adjust_stars(user_id: int, amount: int) -> int:
    with get_db() as conn:
        c = conn.cursor()
        conn.execute("UPDATE users SET stars_balance=MAX(0,stars_balance+?) WHERE user_id=?",
                     (amount, user_id))
        c.execute("SELECT stars_balance FROM users WHERE user_id=?", (user_id,))
        return c.fetchone()["stars_balance"]


# ─────────────────────────────────────────────
#  REFERRAL STATS
# ─────────────────────────────────────────────

def get_user_referrals(user_id: int) -> List[Dict]:
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT r.*, u.first_name, u.username
            FROM referrals r
            JOIN users u ON r.referee_id = u.user_id
            WHERE r.referrer_id = ?
            ORDER BY r.created_at DESC
        """, (user_id,))
        return [dict(r) for r in c.fetchall()]


def get_referral_leaderboard(limit: int = 10) -> List[Dict]:
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT u.user_id, u.first_name, u.username,
                   COUNT(r.id) as referral_count,
                   SUM(r.bonus_paid) as total_earned
            FROM users u
            LEFT JOIN referrals r ON r.referrer_id = u.user_id
            GROUP BY u.user_id
            ORDER BY referral_count DESC
            LIMIT ?
        """, (limit,))
        return [dict(r) for r in c.fetchall()]


def get_referral_stats() -> Dict:
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM referrals")
        total_referrals = c.fetchone()[0]
        c.execute("SELECT SUM(bonus_paid) FROM referrals")
        total_paid = c.fetchone()[0] or 0
        c.execute("SELECT COUNT(DISTINCT referrer_id) FROM referrals")
        active_referrers = c.fetchone()[0]
    return {
        "total_referrals": total_referrals,
        "total_paid": total_paid,
        "active_referrers": active_referrers,
    }


# ─────────────────────────────────────────────
#  CATEGORIES
# ─────────────────────────────────────────────

def create_category(name: str, emoji: str = "📦", description: str = "",
                    name_ar: str = None, name_fr: str = None) -> int:
    with get_db() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO categories (name, name_ar, name_fr, emoji, description) VALUES (?, ?, ?, ?, ?)",
                  (name, name_ar, name_fr, emoji, description))
        new_id = c.lastrowid
    # Bust the categories/products cache so the new category shows immediately
    from utils.cache import invalidate_product
    invalidate_product()
    return new_id


def get_categories(active_only: bool = True) -> List[Dict]:
    _, pc = _cache()
    cache_key = "categories:active" if active_only else "categories:all"
    cached = pc.get(cache_key)
    if cached is not None:
        return cached
    with get_db() as conn:
        c = conn.cursor()
        if active_only:
            c.execute("SELECT * FROM categories WHERE is_active=1 ORDER BY sort_order, id")
        else:
            c.execute("SELECT * FROM categories ORDER BY sort_order, id")
        result = [dict(r) for r in c.fetchall()]
    pc.set(cache_key, result, ttl=60.0)
    return result


def get_category(cat_id: int) -> Optional[Dict]:
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM categories WHERE id=?", (cat_id,))
        row = c.fetchone()
        return dict(row) if row else None


def update_category(cat_id: int, **kwargs) -> bool:
    if not kwargs:
        return False
    fields = ", ".join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values()) + [cat_id]
    with get_db() as conn:
        conn.execute(f"UPDATE categories SET {fields} WHERE id=?", values)
    from utils.cache import invalidate_product
    invalidate_product()  # bust all product/category caches
    return True


def delete_category(cat_id: int) -> bool:
    with get_db() as conn:
        conn.execute("UPDATE categories SET is_active=0 WHERE id=?", (cat_id,))
    return True


# ─────────────────────────────────────────────
#  PRODUCTS
# ─────────────────────────────────────────────

def create_product(category_id: int, name: str, price: float,
                   description: str = "", file_id: str = None,
                   file_type: str = None, file_name: str = None,
                   price_stars: int = 0, stock: int = -1,
                   name_ar: str = None, name_fr: str = None,
                   description_ar: str = None, description_fr: str = None,
                   text_content: str = None) -> int:
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO products (
                category_id, name, name_ar, name_fr,
                description, description_ar, description_fr,
                price, price_stars, stock, file_id, file_type, file_name,
                text_content
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (category_id, name, name_ar, name_fr,
              description, description_ar, description_fr,
              price, price_stars, stock, file_id, file_type, file_name,
              text_content))
        return c.lastrowid


def get_product(product_id: int) -> Optional[Dict]:
    _, pc = _cache()
    cached = pc.get(f"product:{product_id}")
    if cached is not None:
        return cached
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT p.*, c.name as category_name, c.emoji as category_emoji
            FROM products p LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.id=?
        """, (product_id,))
        row = c.fetchone()
        result = dict(row) if row else None
    if result:
        pc.set(f"product:{product_id}", result, ttl=60.0)
    return result


def get_products_by_category(category_id: int, page: int = 1,
                              per_page: int = 6) -> Tuple[List[Dict], int]:
    offset = (page - 1) * per_page
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM products WHERE category_id=? AND is_active=1", (category_id,))
        total = c.fetchone()[0]
        c.execute("""
            SELECT p.*, c.name as category_name, c.emoji as category_emoji
            FROM products p LEFT JOIN categories c ON p.category_id=c.id
            WHERE p.category_id=? AND p.is_active=1
            ORDER BY p.id DESC LIMIT ? OFFSET ?
        """, (category_id, per_page, offset))
        return [dict(r) for r in c.fetchall()], total


def search_products(query: str, page: int = 1, per_page: int = 6) -> Tuple[List[Dict], int]:
    offset = (page - 1) * per_page
    pattern = f"%{query}%"
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT COUNT(*) FROM products WHERE is_active=1 AND
            (name LIKE ? OR description LIKE ? OR name_ar LIKE ? OR name_fr LIKE ?)
        """, (pattern,)*4)
        total = c.fetchone()[0]
        c.execute("""
            SELECT p.*, c.name as category_name, c.emoji as category_emoji
            FROM products p LEFT JOIN categories c ON p.category_id=c.id
            WHERE p.is_active=1 AND (p.name LIKE ? OR p.description LIKE ?
            OR p.name_ar LIKE ? OR p.name_fr LIKE ?)
            ORDER BY p.total_sold DESC LIMIT ? OFFSET ?
        """, (pattern,)*4 + (per_page, offset))
        return [dict(r) for r in c.fetchall()], total


def update_product(product_id: int, **kwargs) -> bool:
    if not kwargs:
        return False
    kwargs["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fields = ", ".join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values()) + [product_id]
    with get_db() as conn:
        conn.execute(f"UPDATE products SET {fields} WHERE id=?", values)
    from utils.cache import invalidate_product
    invalidate_product(product_id)
    return True


def delete_product(product_id: int) -> bool:
    with get_db() as conn:
        conn.execute("DELETE FROM products WHERE id=?", (product_id,))
    from utils.cache import invalidate_product
    invalidate_product(product_id)
    return True


def get_all_products_admin(page: int = 1, per_page: int = 10) -> Tuple[List[Dict], int]:
    offset = (page - 1) * per_page
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM products")
        total = c.fetchone()[0]
        c.execute("""
            SELECT p.*, c.name as category_name
            FROM products p LEFT JOIN categories c ON p.category_id=c.id
            ORDER BY p.id DESC LIMIT ? OFFSET ?
        """, (per_page, offset))
        return [dict(r) for r in c.fetchall()], total


# ─────────────────────────────────────────────
#  ORDERS
# ─────────────────────────────────────────────

def create_order(user_id: int, product_id, amount: float,
                 payment_method: str, product_name: str = "") -> str:
    """Create an order record. product_id may be None for non-product purchases (e.g. Stars packages)."""
    import uuid
    order_id = f"ORD-{uuid.uuid4().hex[:10].upper()}"
    with get_db() as conn:
        conn.execute("""
            INSERT INTO orders (order_id, user_id, product_id, product_name, amount, payment_method)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (order_id, user_id, product_id, product_name, amount, payment_method))
    return order_id


def complete_order(order_id: str) -> bool:
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT user_id, product_id, amount FROM orders WHERE order_id=?", (order_id,))
        order = c.fetchone()
        if not order:
            return False
        conn.execute("""
            UPDATE orders SET status='completed', delivered_at=datetime('now') WHERE order_id=?
        """, (order_id,))
        conn.execute("""
            UPDATE users SET total_orders=total_orders+1, total_spent=total_spent+?
            WHERE user_id=?
        """, (order["amount"], order["user_id"]))
        conn.execute("UPDATE products SET total_sold=total_sold+1 WHERE id=?",
                     (order["product_id"],))
        # Decrement stock for limited-stock products (stock=-1 means unlimited)
        conn.execute(
            "UPDATE products SET stock = MAX(0, stock - 1) WHERE id = ? AND stock > 0",
            (order["product_id"],)
        )
    return True


def get_user_orders(user_id: int, page: int = 1, per_page: int = 5) -> Tuple[List[Dict], int]:
    offset = (page - 1) * per_page
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM orders WHERE user_id=?", (user_id,))
        total = c.fetchone()[0]
        c.execute("""
            SELECT o.*, p.file_id, p.file_type FROM orders o
            LEFT JOIN products p ON o.product_id=p.id
            WHERE o.user_id=? ORDER BY o.created_at DESC LIMIT ? OFFSET ?
        """, (user_id, per_page, offset))
        return [dict(r) for r in c.fetchall()], total


def get_all_orders_admin(page: int = 1, per_page: int = 10) -> Tuple[List[Dict], int]:
    offset = (page - 1) * per_page
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM orders")
        total = c.fetchone()[0]
        c.execute("""
            SELECT o.*, u.username, u.first_name
            FROM orders o LEFT JOIN users u ON o.user_id=u.user_id
            ORDER BY o.created_at DESC LIMIT ? OFFSET ?
        """, (per_page, offset))
        return [dict(r) for r in c.fetchall()], total


# ─────────────────────────────────────────────
#  DEPOSITS
# ─────────────────────────────────────────────

def create_deposit(user_id: int, amount: float, method: str,
                   tx_hash: str = None) -> str:
    import uuid
    dep_id = f"DEP-{uuid.uuid4().hex[:10].upper()}"
    with get_db() as conn:
        conn.execute("""
            INSERT INTO deposits (deposit_id, user_id, amount, method, tx_hash)
            VALUES (?, ?, ?, ?, ?)
        """, (dep_id, user_id, amount, method, tx_hash))
    return dep_id


def get_pending_deposits() -> List[Dict]:
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT d.*, u.username, u.first_name
            FROM deposits d JOIN users u ON d.user_id=u.user_id
            WHERE d.status='pending' ORDER BY d.created_at
        """)
        return [dict(r) for r in c.fetchall()]


def confirm_deposit(deposit_id: str) -> bool:
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM deposits WHERE deposit_id=? AND status='pending'", (deposit_id,))
        dep = c.fetchone()
        if not dep:
            return False
        dep = dict(dep)
        conn.execute("""
            UPDATE deposits SET status='confirmed', confirmed_at=datetime('now')
            WHERE deposit_id=?
        """, (deposit_id,))
        conn.execute("UPDATE users SET balance=balance+? WHERE user_id=?",
                     (dep["amount"], dep["user_id"]))
    return True


# ─────────────────────────────────────────────
#  COUPONS
# ─────────────────────────────────────────────

def create_coupon(code: str, discount_type: str, discount_value: float,
                  min_purchase: float = 0, max_uses: int = -1) -> int:
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO coupons (code, discount_type, discount_value, min_purchase, max_uses)
            VALUES (?, ?, ?, ?, ?)
        """, (code, discount_type, discount_value, min_purchase, max_uses))
        return c.lastrowid


def validate_coupon(code: str, user_id: int, purchase_amount: float) -> Tuple[bool, str, float]:
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM coupons WHERE code=? AND is_active=1", (code,))
        coupon = c.fetchone()
        if not coupon:
            return False, "Invalid coupon", 0.0
        coupon = dict(coupon)
        if coupon["max_uses"] != -1 and coupon["used_count"] >= coupon["max_uses"]:
            return False, "Coupon exhausted", 0.0
        if purchase_amount < coupon["min_purchase"]:
            return False, f"Min purchase ${coupon['min_purchase']:.2f}", 0.0
        if coupon["expires_at"]:
            try:
                exp = datetime.strptime(coupon["expires_at"], "%Y-%m-%d %H:%M:%S")
                if exp < datetime.now():
                    return False, "Coupon expired", 0.0
            except Exception:
                pass
        # Already used?
        c.execute("SELECT id FROM coupon_usage WHERE coupon_id=? AND user_id=?",
                  (coupon["id"], user_id))
        if c.fetchone():
            return False, "Already used", 0.0
        discount = (purchase_amount * coupon["discount_value"] / 100
                    if coupon["discount_type"] == "percentage"
                    else coupon["discount_value"])
        return True, "Valid", min(discount, purchase_amount)


def use_coupon(code: str, user_id: int, order_id: str) -> bool:
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM coupons WHERE code=?", (code,))
        row = c.fetchone()
        if not row:
            return False
        cid = row["id"]
        conn.execute("UPDATE coupons SET used_count=used_count+1 WHERE id=?", (cid,))
        conn.execute("INSERT INTO coupon_usage (coupon_id, user_id, order_id) VALUES (?, ?, ?)",
                     (cid, user_id, order_id))
    return True


def delete_coupon(coupon_id: int) -> bool:
    with get_db() as conn:
        # Also remove coupon usage records (fix cascade)
        conn.execute("DELETE FROM coupon_usage WHERE coupon_id = ?", (coupon_id,))
        conn.execute("DELETE FROM coupons WHERE id = ?", (coupon_id,))
    return True


def get_all_coupons() -> List[Dict]:
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM coupons ORDER BY created_at DESC")
        return [dict(r) for r in c.fetchall()]


# ─────────────────────────────────────────────
#  STATISTICS
# ─────────────────────────────────────────────

def get_statistics() -> Dict:
    with get_db() as conn:
        c = conn.cursor()

        def scalar(sql, *args):
            c.execute(sql, args)
            row = c.fetchone()
            return row[0] if row else 0

        return {
            "total_users":      scalar("SELECT COUNT(*) FROM users"),
            "new_users_today":  scalar("SELECT COUNT(*) FROM users WHERE date(joined_at)=date('now')"),
            "new_users_week":   scalar("SELECT COUNT(*) FROM users WHERE joined_at>=datetime('now','-7 days')"),
            "banned_users":     scalar("SELECT COUNT(*) FROM users WHERE is_banned=1"),
            "total_orders":     scalar("SELECT COUNT(*) FROM orders"),
            "completed_orders": scalar("SELECT COUNT(*) FROM orders WHERE status='completed'"),
            "total_revenue":    scalar("SELECT COALESCE(SUM(amount),0) FROM orders WHERE status='completed'"),
            "revenue_today":    scalar("SELECT COALESCE(SUM(amount),0) FROM orders WHERE status='completed' AND date(created_at)=date('now')"),
            "active_products":  scalar("SELECT COUNT(*) FROM products WHERE is_active=1"),
            "active_categories":scalar("SELECT COUNT(*) FROM categories WHERE is_active=1"),
            "pending_deposits": scalar("SELECT COUNT(*) FROM deposits WHERE status='pending'"),
            "top_products":     _get_top_products(c),
        }


def _get_top_products(c) -> List[Dict]:
    c.execute("SELECT name, total_sold FROM products WHERE is_active=1 ORDER BY total_sold DESC LIMIT 5")
    return [dict(r) for r in c.fetchall()]


# ─────────────────────────────────────────────
#  ADMIN LOGS
# ─────────────────────────────────────────────

def add_admin_log(admin_id: int, action: str, details: str = "",
                  target_id: int = None) -> bool:
    with get_db() as conn:
        conn.execute("""
            INSERT INTO admin_logs (admin_id, action, details, target_id)
            VALUES (?, ?, ?, ?)
        """, (admin_id, action, details, target_id))
    return True


def get_admin_logs(page: int = 1, per_page: int = 10) -> Tuple[List[Dict], int]:
    offset = (page - 1) * per_page
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM admin_logs")
        total = c.fetchone()[0]
        c.execute("SELECT * FROM admin_logs ORDER BY created_at DESC LIMIT ? OFFSET ?",
                  (per_page, offset))
        return [dict(r) for r in c.fetchall()], total


# ─────────────────────────────────────────────
#  BACKUP / EXPORT
# ─────────────────────────────────────────────

def backup_database() -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"backup_{ts}.db"
    shutil.copy2(DATABASE_PATH, backup_path)
    return backup_path


def export_users_csv() -> str:
    import csv
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"users_{ts}.csv"
    users = get_all_users()
    if users:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=users[0].keys())
            writer.writeheader()
            writer.writerows(users)
    return path


# ─────────────────────────────────────────────
#  PRODUCT SHARE LINKS
# ─────────────────────────────────────────────

def get_or_create_product_share_token(product_id: int) -> str:
    import secrets
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT share_token FROM products WHERE id = ?", (product_id,))
        row = c.fetchone()
        if row and row["share_token"]:
            return row["share_token"]
        token = "prod" + secrets.token_hex(8)
        conn.execute("UPDATE products SET share_token = ? WHERE id = ?", (token, product_id))
        return token


def get_product_by_share_token(token: str) -> Optional[Dict]:
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT p.*, c.name as category_name, c.emoji as category_emoji
            FROM products p LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.share_token = ? AND p.is_active = 1
        """, (token,))
        row = c.fetchone()
        return dict(row) if row else None


# ─────────────────────────────────────────────
#  REWARD LINKS
# ─────────────────────────────────────────────

def create_reward_link(points: float, max_uses: int = -1,
                        expires_at: str = None, target_users: str = None,
                        created_by: int = 0) -> Dict:
    import secrets
    token = "r_" + secrets.token_urlsafe(12)
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO reward_links (token, points, max_uses, expires_at, target_users, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (token, points, max_uses, expires_at, target_users, created_by))
        link_id = c.lastrowid
    return {"id": link_id, "token": token}


def get_reward_link_by_token(token: str) -> Optional[Dict]:
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM reward_links WHERE token = ? AND is_active = 1", (token,))
        row = c.fetchone()
        return dict(row) if row else None


def get_all_reward_links() -> List[Dict]:
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM reward_links ORDER BY created_at DESC")
        return [dict(r) for r in c.fetchall()]


def delete_reward_link(link_id: int) -> bool:
    with get_db() as conn:
        conn.execute("DELETE FROM reward_link_claims WHERE link_id = ?", (link_id,))
        conn.execute("DELETE FROM reward_links WHERE id = ?", (link_id,))
    return True


def claim_reward_link(token: str, user_id: int) -> Tuple[bool, str, float]:
    """Try to claim a reward link. Returns (success, message, points_given)."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM reward_links WHERE token = ? AND is_active = 1", (token,))
        link = c.fetchone()
        if not link:
            return False, "Invalid or expired link", 0.0
        link = dict(link)

        # Check expiry
        if link.get("expires_at"):
            try:
                exp = datetime.strptime(link["expires_at"], "%Y-%m-%d %H:%M:%S")
                if exp < datetime.now():
                    return False, "This reward link has expired", 0.0
            except Exception:
                pass

        # Check max uses
        if link["max_uses"] != -1 and link["used_count"] >= link["max_uses"]:
            return False, "This reward link has reached its maximum uses", 0.0

        # Check target users
        if link.get("target_users"):
            allowed = [int(x.strip()) for x in link["target_users"].split(",") if x.strip().isdigit()]
            if allowed and user_id not in allowed:
                return False, "This link is not available for you", 0.0

        # Check duplicate claim
        c.execute("SELECT id FROM reward_link_claims WHERE link_id = ? AND user_id = ?",
                  (link["id"], user_id))
        if c.fetchone():
            return False, "You have already claimed this reward", 0.0

        # Credit points (as balance)
        points = float(link["points"])
        conn.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?",
                     (points, user_id))
        conn.execute("INSERT INTO reward_link_claims (link_id, user_id) VALUES (?, ?)",
                     (link["id"], user_id))
        conn.execute("UPDATE reward_links SET used_count = used_count + 1 WHERE id = ?",
                     (link["id"],))
        return True, "Reward claimed successfully!", points


# ─────────────────────────────────────────────
#  DAILY GIFT
# ─────────────────────────────────────────────

def can_claim_daily_gift(user_id: int) -> Tuple[bool, Optional[str]]:
    """Returns (can_claim, next_claim_time_str)."""
    if not get_setting("daily_gift_enabled", False):
        return False, None
    cooldown_hours = int(get_setting("daily_gift_cooldown_hours", 24))
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT claimed_at FROM daily_gift_claims
            WHERE user_id = ?
            ORDER BY claimed_at DESC LIMIT 1
        """, (user_id,))
        row = c.fetchone()
        if not row:
            return True, None
        last_claim = datetime.strptime(row["claimed_at"], "%Y-%m-%d %H:%M:%S")
        next_claim = last_claim.replace(microsecond=0)
        from datetime import timedelta
        next_claim = next_claim + timedelta(hours=cooldown_hours)
        if datetime.now() >= next_claim:
            return True, None
        return False, next_claim.strftime("%Y-%m-%d %H:%M:%S")


def claim_daily_gift(user_id: int) -> Tuple[bool, str, float]:
    """Claim daily gift. Returns (success, message, points)."""
    if not get_setting("daily_gift_enabled", False):
        return False, "Daily gift is currently disabled", 0.0
    can_claim, next_time = can_claim_daily_gift(user_id)
    if not can_claim:
        return False, f"You can claim your next gift at {next_time}", 0.0
    points = safe_float_setting("daily_gift_points", 1.0)
    with get_db() as conn:
        # Ensure table exists (migration safe)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_gift_claims (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                points      REAL NOT NULL,
                claimed_at  TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        conn.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?",
                     (points, user_id))
        conn.execute("INSERT INTO daily_gift_claims (user_id, points) VALUES (?, ?)",
                     (user_id, points))
    return True, "Daily gift claimed!", points


# ═══════════════════════════════════════════════════════════
#   v3.1 ADDITIONS — ratings, delivery_logs, milestones
# ═══════════════════════════════════════════════════════════

def _run_v31_migrations():
    """Idempotent migrations to add v3.1 tables/columns."""
    with get_db() as conn:
        c = conn.cursor()

        # ── PRODUCT RATINGS ──────────────────────────────────────
        c.execute("""
            CREATE TABLE IF NOT EXISTS product_ratings (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                product_id  INTEGER NOT NULL,
                order_id    TEXT NOT NULL,
                rating      INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
                review      TEXT,
                created_at  TEXT DEFAULT (datetime('now')),
                UNIQUE(user_id, product_id),
                FOREIGN KEY (user_id)    REFERENCES users(user_id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)

        # ── DELIVERY LOGS ─────────────────────────────────────────
        c.execute("""
            CREATE TABLE IF NOT EXISTS delivery_logs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id    TEXT NOT NULL,
                user_id     INTEGER NOT NULL,
                product_id  INTEGER NOT NULL,
                attempt     INTEGER DEFAULT 1,
                status      TEXT NOT NULL,
                error_msg   TEXT,
                delivered_at TEXT DEFAULT (datetime('now'))
            )
        """)

        # ── REFERRAL MILESTONES ───────────────────────────────────
        c.execute("""
            CREATE TABLE IF NOT EXISTS referral_milestones (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                milestone   INTEGER NOT NULL,
                reward      REAL NOT NULL,
                claimed_at  TEXT DEFAULT (datetime('now')),
                UNIQUE(user_id, milestone),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # ── WEEKLY LEADERBOARD REWARDS ────────────────────────────
        c.execute("""
            CREATE TABLE IF NOT EXISTS weekly_rewards (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                week        TEXT NOT NULL,
                rank        INTEGER NOT NULL,
                reward      REAL NOT NULL,
                paid_at     TEXT DEFAULT (datetime('now')),
                UNIQUE(user_id, week),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        logger.info("✅ v3.1 migrations applied")


# ─────────────────────────────────────────────
#  RATINGS
# ─────────────────────────────────────────────

def add_rating(user_id: int, product_id: int, order_id: str,
               rating: int, review: str = "") -> bool:
    """Add or update a product rating. Returns True on success."""
    try:
        with get_db() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO product_ratings
                    (user_id, product_id, order_id, rating, review)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, product_id, order_id, rating, review or ""))
        return True
    except Exception as e:
        logger.error(f"add_rating error: {e}")
        return False


def get_product_rating(product_id: int) -> dict:
    """Returns avg_rating, rating_count, and recent reviews."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT AVG(rating) as avg_rating, COUNT(*) as count
            FROM product_ratings WHERE product_id = ?
        """, (product_id,))
        row = dict(c.fetchone())
        c.execute("""
            SELECT r.rating, r.review, r.created_at,
                   u.first_name, u.username
            FROM product_ratings r
            JOIN users u ON r.user_id = u.user_id
            WHERE r.product_id = ?
            ORDER BY r.created_at DESC LIMIT 5
        """, (product_id,))
        row["reviews"] = [dict(r) for r in c.fetchall()]
    return row


def can_rate_product(user_id: int, product_id: int) -> bool:
    """User can rate only if they purchased and haven't rated yet."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT COUNT(*) FROM orders
            WHERE user_id = ? AND product_id = ? AND status = 'completed'
        """, (user_id, product_id))
        purchased = c.fetchone()[0] > 0
        if not purchased:
            return False
        c.execute("""
            SELECT COUNT(*) FROM product_ratings
            WHERE user_id = ? AND product_id = ?
        """, (user_id, product_id))
        already_rated = c.fetchone()[0] > 0
        return not already_rated


def get_user_pending_ratings(user_id: int) -> List[Dict]:
    """Products purchased but not yet rated."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT DISTINCT o.product_id, o.product_name, o.order_id,
                   p.name, p.category_id
            FROM orders o
            JOIN products p ON o.product_id = p.id
            WHERE o.user_id = ? AND o.status = 'completed'
            AND o.product_id NOT IN (
                SELECT product_id FROM product_ratings WHERE user_id = ?
            )
            ORDER BY o.delivered_at DESC LIMIT 10
        """, (user_id, user_id))
        return [dict(r) for r in c.fetchall()]


# ─────────────────────────────────────────────
#  DELIVERY LOGS
# ─────────────────────────────────────────────

def log_delivery(order_id: str, user_id: int, product_id: int,
                 status: str, attempt: int = 1, error_msg: str = "") -> None:
    with get_db() as conn:
        conn.execute("""
            INSERT INTO delivery_logs
                (order_id, user_id, product_id, attempt, status, error_msg)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (order_id, user_id, product_id, attempt, status, error_msg))


def get_failed_deliveries() -> List[Dict]:
    """Orders that completed but had delivery failures."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT dl.*, o.product_id, p.file_id, p.file_type,
                   p.text_content, p.name as product_name,
                   u.first_name, u.username
            FROM delivery_logs dl
            JOIN orders o ON dl.order_id = o.order_id
            JOIN products p ON dl.product_id = p.id
            JOIN users u ON dl.user_id = u.user_id
            WHERE dl.status = 'failed'
            ORDER BY dl.delivered_at DESC LIMIT 50
        """)
        return [dict(r) for r in c.fetchall()]


def get_delivery_log(order_id: str) -> List[Dict]:
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT * FROM delivery_logs WHERE order_id = ?
            ORDER BY delivered_at
        """, (order_id,))
        return [dict(r) for r in c.fetchall()]


# ─────────────────────────────────────────────
#  REFERRAL MILESTONES
# ─────────────────────────────────────────────

def check_and_award_milestones(user_id: int) -> List[dict]:
    """
    Check if user has reached new milestones. Awards balance and returns
    list of newly unlocked milestones.
    """
    from utils.formatting import MILESTONES
    referrals = get_user_referrals(user_id)
    count = len(referrals)
    awarded = []

    with get_db() as conn:
        c = conn.cursor()
        for m in MILESTONES:
            if count >= m["count"]:
                # Try to insert (UNIQUE constraint prevents duplicates)
                try:
                    c.execute("""
                        INSERT OR IGNORE INTO referral_milestones
                            (user_id, milestone, reward)
                        VALUES (?, ?, ?)
                    """, (user_id, m["count"], m["reward"]))
                    if c.rowcount:
                        # Actually inserted — new milestone!
                        conn.execute(
                            "UPDATE users SET balance = balance + ? WHERE user_id = ?",
                            (m["reward"], user_id)
                        )
                        awarded.append(m)
                except Exception:
                    pass
    return awarded


def get_user_milestones(user_id: int) -> List[Dict]:
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT * FROM referral_milestones WHERE user_id = ?
            ORDER BY milestone
        """, (user_id,))
        return [dict(r) for r in c.fetchall()]


# ─────────────────────────────────────────────
#  WEEKLY LEADERBOARD REWARDS
# ─────────────────────────────────────────────

def get_weekly_top_inviters(limit: int = 3) -> List[Dict]:
    """Top inviters for the current ISO week."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT u.user_id, u.first_name, u.username,
                   COUNT(r.id) as weekly_count
            FROM referrals r
            JOIN users u ON r.referrer_id = u.user_id
            WHERE strftime('%Y-%W', r.created_at) = strftime('%Y-%W', 'now')
            GROUP BY r.referrer_id
            ORDER BY weekly_count DESC
            LIMIT ?
        """, (limit,))
        return [dict(r) for r in c.fetchall()]


def pay_weekly_rewards(rewards: List[Tuple[int, float]], week_str: str) -> int:
    """
    Pay weekly rewards. Returns count of users rewarded.
    week_str format: '2024-W12'
    """
    paid = 0
    for rank, (user_id, amount) in enumerate(rewards, 1):
        with get_db() as conn:
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO weekly_rewards
                        (user_id, week, rank, reward)
                    VALUES (?, ?, ?, ?)
                """, (user_id, week_str, rank, amount))
                if conn.execute(
                    "SELECT changes()"
                ).fetchone()[0]:
                    conn.execute(
                        "UPDATE users SET balance = balance + ? WHERE user_id = ?",
                        (amount, user_id)
                    )
                    paid += 1
            except Exception as e:
                logger.error(f"weekly reward error: {e}")
    return paid


# ─────────────────────────────────────────────
#  ENHANCED STATISTICS (v3.1)
# ─────────────────────────────────────────────

def get_enhanced_statistics() -> Dict:
    """Extends get_statistics() with delivery and rating data."""
    base = get_statistics()
    with get_db() as conn:
        c = conn.cursor()

        def scalar(sql, *args):
            c.execute(sql, args)
            row = c.fetchone()
            return row[0] if row else 0

        base.update({
            "total_ratings":       scalar("SELECT COUNT(*) FROM product_ratings"),
            "avg_rating":          scalar("SELECT ROUND(AVG(rating),1) FROM product_ratings") or 0,
            "failed_deliveries":   scalar("SELECT COUNT(*) FROM delivery_logs WHERE status='failed'"),
            "successful_deliveries": scalar("SELECT COUNT(*) FROM delivery_logs WHERE status='success'"),
            "total_referrals":     scalar("SELECT COUNT(*) FROM referrals"),
            "active_referrers":    scalar("SELECT COUNT(DISTINCT referrer_id) FROM referrals"),
            "weekly_top":          get_weekly_top_inviters(3),
        })
    return base


# ─────────────────────────────────────────────
#  FLASH SALE
# ─────────────────────────────────────────────

def init_flash_sale_table():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS flash_sales (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id  INTEGER NOT NULL,
                discount    REAL NOT NULL,
                starts_at   TEXT NOT NULL,
                ends_at     TEXT NOT NULL,
                is_active   INTEGER DEFAULT 1,
                created_by  INTEGER,
                created_at  TEXT DEFAULT (datetime('now'))
            )
        """)

def create_flash_sale(product_id: int, discount: float,
                      starts_at: str, ends_at: str, admin_id: int) -> int:
    init_flash_sale_table()
    with get_db() as conn:
        c = conn.cursor()
        conn.execute(
            "UPDATE flash_sales SET is_active=0 WHERE product_id=? AND is_active=1",
            (product_id,)
        )
        c.execute("""
            INSERT INTO flash_sales (product_id, discount, starts_at, ends_at, created_by)
            VALUES (?, ?, ?, ?, ?)
        """, (product_id, discount, starts_at, ends_at, admin_id))
        return c.lastrowid

def get_active_flash_sales() -> List[Dict]:
    init_flash_sale_table()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT f.*, p.name, p.price, p.price_stars, p.stock
            FROM flash_sales f
            JOIN products p ON f.product_id = p.id
            WHERE f.is_active=1 AND f.starts_at <= ? AND f.ends_at >= ?
            AND p.is_active=1
        """, (now, now))
        return [dict(r) for r in c.fetchall()]

def get_flash_sale_for_product(product_id: int) -> Optional[Dict]:
    init_flash_sale_table()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT * FROM flash_sales
            WHERE product_id=? AND is_active=1
            AND starts_at <= ? AND ends_at >= ?
        """, (product_id, now, now))
        row = c.fetchone()
        return dict(row) if row else None

def cancel_flash_sale(sale_id: int):
    init_flash_sale_table()
    with get_db() as conn:
        conn.execute("UPDATE flash_sales SET is_active=0 WHERE id=?", (sale_id,))

def get_all_flash_sales_admin() -> List[Dict]:
    init_flash_sale_table()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT f.*, p.name as product_name
            FROM flash_sales f
            JOIN products p ON f.product_id = p.id
            ORDER BY f.created_at DESC LIMIT 20
        """)
        rows = [dict(r) for r in c.fetchall()]
        for r in rows:
            r["is_live"] = (r["is_active"] == 1 and
                            r["starts_at"] <= now <= r["ends_at"])
        return rows


# ─────────────────────────────────────────────
#  PRODUCT OF THE DAY
# ─────────────────────────────────────────────

def set_product_of_day(product_id: int, admin_id: int):
    set_setting("product_of_day_id", product_id)
    set_setting("product_of_day_set_by", admin_id)
    set_setting("product_of_day_date", datetime.now().strftime("%Y-%m-%d"))
    add_admin_log(admin_id, "set_product_of_day", f"Product #{product_id}")

def get_product_of_day() -> Optional[Dict]:
    pid = get_setting("product_of_day_id")
    if not pid:
        return None
    return get_product(int(pid))


# ─────────────────────────────────────────────
#  WIN-BACK (notify inactive users)
# ─────────────────────────────────────────────

def get_inactive_users(days: int = 7) -> List[Dict]:
    """Users who haven't interacted for X days and are not banned."""
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT user_id, first_name FROM users
            WHERE is_banned=0
            AND (last_seen IS NULL OR last_seen < ?)
            LIMIT 1000
        """, (cutoff,))
        return [dict(r) for r in c.fetchall()]

def get_pending_orders_admin(page: int = 1, per_page: int = 10):
    """Orders with status = pending (manual delivery needed)."""
    offset = (page - 1) * per_page
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM orders WHERE status='pending'")
        total = c.fetchone()[0]
        c.execute("""
            SELECT o.*, u.first_name, u.username
            FROM orders o LEFT JOIN users u ON o.user_id=u.user_id
            WHERE o.status='pending'
            ORDER BY o.created_at DESC LIMIT ? OFFSET ?
        """, (per_page, offset))
        return [dict(r) for r in c.fetchall()], total



# ═══════════════════════════════════════════════════════════════
#  GAMES CENTER — DATABASE FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def init_games_tables():
    """Create games tables if they don't exist. Call once at startup."""
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS games_history (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                game_type   TEXT NOT NULL,
                bet         REAL NOT NULL,
                profit      REAL NOT NULL,
                result      TEXT,
                played_at   TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS leaderboard_stats (
                user_id           INTEGER PRIMARY KEY,
                total_wins        INTEGER DEFAULT 0,
                total_losses      INTEGER DEFAULT 0,
                total_spins       INTEGER DEFAULT 0,
                total_points_won  REAL    DEFAULT 0.0,
                total_points_lost REAL    DEFAULT 0.0,
                last_play         TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS daily_rewards (
                user_id     INTEGER PRIMARY KEY,
                last_claim  TEXT NOT NULL,
                streak      INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );

            CREATE INDEX IF NOT EXISTS idx_games_history_user
                ON games_history(user_id, played_at DESC);
            CREATE INDEX IF NOT EXISTS idx_leaderboard_won
                ON leaderboard_stats(total_points_won DESC);
        """)


def record_game(user_id: int, game_type: str, bet: float,
                profit: float, result: str = "") -> None:
    """Record a game play and update leaderboard stats atomically."""
    won = profit > 0
    with get_db() as conn:
        conn.execute("""
            INSERT INTO games_history (user_id, game_type, bet, profit, result)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, game_type, round(bet, 4), round(profit, 4), result))

        conn.execute("""
            INSERT INTO leaderboard_stats
                (user_id, total_wins, total_losses, total_spins,
                 total_points_won, total_points_lost, last_play)
            VALUES (?, ?, ?, 1, ?, ?, datetime('now'))
            ON CONFLICT(user_id) DO UPDATE SET
                total_wins        = total_wins        + ?,
                total_losses      = total_losses      + ?,
                total_spins       = total_spins       + 1,
                total_points_won  = total_points_won  + ?,
                total_points_lost = total_points_lost + ?,
                last_play         = datetime('now')
        """, (
            user_id,
            1 if won else 0, 0 if won else 1,
            max(0.0, profit), 0.0 if won else abs(profit),
            # ON CONFLICT values:
            1 if won else 0, 0 if won else 1,
            max(0.0, profit), 0.0 if won else abs(profit),
        ))


def get_game_stats(user_id: int) -> Optional[Dict]:
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM leaderboard_stats WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        return dict(row) if row else None


def get_game_last_play(user_id: int, game_type: str) -> Optional[datetime]:
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT played_at FROM games_history
            WHERE user_id = ? AND game_type = ?
            ORDER BY played_at DESC LIMIT 1
        """, (user_id, game_type))
        row = c.fetchone()
        if not row:
            return None
        try:
            return datetime.strptime(row["played_at"], "%Y-%m-%d %H:%M:%S")
        except Exception:
            return None


def get_game_history(user_id: int, page: int = 1,
                     per_page: int = 8) -> tuple[List[Dict], int]:
    offset = (page - 1) * per_page
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM games_history WHERE user_id = ?", (user_id,))
        total = c.fetchone()[0]
        c.execute("""
            SELECT * FROM games_history
            WHERE user_id = ?
            ORDER BY played_at DESC
            LIMIT ? OFFSET ?
        """, (user_id, per_page, offset))
        return [dict(r) for r in c.fetchall()], total


def get_game_leaderboard(mode: str = "points", limit: int = 10) -> List[Dict]:
    with get_db() as conn:
        c = conn.cursor()
        if mode == "games":
            order = "(total_wins + total_losses) DESC"
        elif mode == "winrate":
            order = "CASE WHEN (total_wins+total_losses)>=5 THEN CAST(total_wins AS REAL)/(total_wins+total_losses) ELSE -1 END DESC"
        else:
            order = "total_points_won DESC"

        c.execute(f"""
            SELECT ls.*, u.first_name, u.username
            FROM leaderboard_stats ls
            JOIN users u ON u.user_id = ls.user_id
            WHERE u.is_banned = 0
            ORDER BY {order}
            LIMIT ?
        """, (limit,))
        return [dict(r) for r in c.fetchall()]


def claim_daily_reward(user_id: int) -> tuple[bool, float, Optional[datetime]]:
    """
    Try to claim the daily reward.
    Returns (claimed, reward_amount, next_claim_time).
    """
    cd_hours = int(get_setting("game_daily_cooldown_hours", 24))
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT last_claim, streak FROM daily_rewards WHERE user_id = ?", (user_id,))
        row = c.fetchone()

        now = datetime.now()
        if row:
            last = datetime.strptime(row["last_claim"], "%Y-%m-%d %H:%M:%S")
            elapsed = (now - last).total_seconds()
            if elapsed < cd_hours * 3600:
                next_claim = last + timedelta(hours=cd_hours)
                return False, 0.0, next_claim
            streak = (row["streak"] or 1) + 1 if elapsed < (cd_hours + 24) * 3600 else 1
        else:
            streak = 1

        # Compute reward
        dr_min = safe_float_setting("game_daily_min", 5.0)
        dr_max = safe_float_setting("game_daily_max", 50.0)
        import random as _r
        reward = round(_r.uniform(dr_min, dr_max), 4)

        # Streak bonus (every 7 days = +50%)
        if streak % 7 == 0:
            reward = round(reward * 1.5, 4)

        conn.execute("""
            INSERT INTO daily_rewards (user_id, last_claim, streak)
            VALUES (?, datetime('now'), ?)
            ON CONFLICT(user_id) DO UPDATE SET
                last_claim = datetime('now'),
                streak     = ?
        """, (user_id, streak, streak))

        # Credit balance
        conn.execute(
            "UPDATE users SET balance = balance + ? WHERE user_id = ?",
            (reward, user_id)
        )

        return True, reward, None


# ═══════════════════════════════════════════════════════════════
#  GAMES ECONOMY ENGINE — DATABASE FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def get_economy_snapshot() -> Dict:
    """Return overall platform game economy stats."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT
                COUNT(*)                                          AS total_games,
                COALESCE(SUM(bet), 0)                            AS total_bets,
                COALESCE(SUM(CASE WHEN profit>0 THEN profit ELSE 0 END), 0) AS total_paid_out,
                COALESCE(SUM(CASE WHEN profit<0 THEN ABS(profit) ELSE 0 END), 0) AS total_collected,
                COALESCE(SUM(-profit), 0)                        AS net_profit,
                COALESCE(SUM(CASE WHEN profit>0 THEN 1 ELSE 0 END),0) AS total_wins,
                COALESCE(SUM(CASE WHEN profit<0 THEN 1 ELSE 0 END),0) AS total_losses
            FROM games_history
        """)
        row = dict(c.fetchone())

        # Recent window (last 100 games) for dynamic adjustment
        c.execute("""
            SELECT COALESCE(SUM(-profit), 0) AS recent_net
            FROM (SELECT profit FROM games_history ORDER BY id DESC LIMIT 100)
        """)
        row["recent_net"] = c.fetchone()[0] or 0
        return row


def get_effective_rtp(game_type: str, bet: float = 0.0) -> float:
    """
    Return the effective player win-rate for a game, combining:
    - Global base RTP
    - Economy engine auto-adjustment
    - Per-game override (if set)
    - Bet-size scaling: larger bets get lower RTP (protects house)
    Result is clamped between admin-set min/max.

    Bet scaling formula:
      reduction = bet_rtp_factor × log2(1 + bet / bet_scale_base)
      e.g. with factor=5, base=1: bet=$1 → -5%, bet=$10 → -17%, bet=$50 → -28%
    """
    base_rtp   = safe_float_setting("game_global_rtp", 55.0)
    eco_adj    = safe_float_setting("game_eco_adjustment", 0.0)
    per_game   = get_setting(f"game_{game_type}_rtp_override", None)
    rtp_min    = safe_float_setting("game_rtp_min", 10.0)
    rtp_max    = safe_float_setting("game_rtp_max", 70.0)

    if per_game is not None:
        effective = float(per_game)
    else:
        effective = base_rtp + eco_adj

    # Bet-size scaling — bigger bet = lower player RTP
    if bet > 0:
        import math
        factor    = safe_float_setting("game_bet_rtp_factor", 5.0)   # % reduction per log2 unit
        scale_base = safe_float_setting("game_bet_scale_base", 1.0)  # bet reference point
        reduction = factor * math.log2(1.0 + bet / max(scale_base, 0.01))
        effective  = effective - reduction

    return max(rtp_min, min(rtp_max, effective))


def run_economy_engine() -> dict:
    """
    Dynamic economy protection — auto-adjust eco_adjustment based on
    recent platform profit/loss. Called after every game.
    Returns a dict with the new adjustment and status.
    """
    snap     = get_economy_snapshot()
    net      = snap.get("net_profit", 0)        # positive = platform profit
    recent   = snap.get("recent_net", 0)        # recent 100-game window

    current_adj = safe_float_setting("game_eco_adjustment", 0.0)
    step        = safe_float_setting("game_eco_step", 1.0)   # % per trigger
    threshold   = safe_float_setting("game_eco_threshold", 0.0)
    eco_enabled = get_setting("game_eco_enabled", True)

    if not eco_enabled:
        return {"adjustment": current_adj, "status": "disabled"}

    # Determine status
    if recent < threshold:          # platform losing recently
        new_adj  = max(current_adj - step, -30.0)   # reduce player RTP
        status   = "recovery"
    elif recent > threshold * 2:    # platform very profitable
        new_adj  = min(current_adj + step * 0.5, 0.0)   # ease back to normal
        status   = "profit"
    else:
        new_adj  = current_adj
        status   = "neutral"

    if new_adj != current_adj:
        set_setting("game_eco_adjustment", round(new_adj, 2))

    return {"adjustment": new_adj, "status": status, "recent_net": recent}
