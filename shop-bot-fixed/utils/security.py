"""
╔══════════════════════════════════════════════════════════╗
║         TELEGRAM SHOP BOT - SECURITY UTILITIES           ║
║  Anti-spam, callback validation, duplicate purchase guard║
╚══════════════════════════════════════════════════════════╝
"""

import time
import hashlib
import logging
from typing import Dict, Set, Tuple

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
#  DUPLICATE PURCHASE GUARD
#  Tracks recent (user_id, product_id) pairs to
#  prevent double-tap purchases within a short window
# ─────────────────────────────────────────────

_purchase_locks: Dict[str, float] = {}
_PURCHASE_LOCK_TTL = 5.0  # seconds


def acquire_purchase_lock(user_id: int, product_id: int) -> bool:
    """
    Try to acquire a purchase lock for (user, product).
    Returns True if the lock was acquired (safe to proceed),
    False if a purchase for this pair is already in-flight.
    """
    key = f"{user_id}:{product_id}"
    now = time.time()
    if key in _purchase_locks:
        if now - _purchase_locks[key] < _PURCHASE_LOCK_TTL:
            return False
    _purchase_locks[key] = now
    _cleanup_locks(now)
    return True


def release_purchase_lock(user_id: int, product_id: int) -> None:
    _purchase_locks.pop(f"{user_id}:{product_id}", None)


def _cleanup_locks(now: float) -> None:
    expired = [k for k, t in _purchase_locks.items() if now - t > _PURCHASE_LOCK_TTL * 2]
    for k in expired:
        del _purchase_locks[k]


# ─────────────────────────────────────────────
#  CALLBACK DATA VALIDATION
# ─────────────────────────────────────────────

VALID_PREFIXES = {
    "home", "shop", "noop", "balance", "deposit:usdt", "deposit:stars",
    "deposit:stars_menu", "submit_tx", "profile", "search", "referral",
    "referral_list", "language", "support", "check_subscribe",
    "daily_gift:claim", "admin", "admin_stats", "admin_categories",
    "admin_add_product", "admin_add_category", "admin_deposits",
    "admin_coupons", "admin_add_coupon", "admin_broadcast",
    "admin_backup", "admin_export", "admin_user_search", "admin_settings",
    "dg:panel", "dg:toggle", "fs:toggle", "fs:add", "ref:toggle",
    "ref:reward_type", "ref:leaderboard", "ref:stats",
    "stars:toggle", "stars:packages", "stars:add_pkg",
    "adm:add", "rl:panel", "rl:create",
    "cfg:general", "cfg:force_sub", "cfg:payment", "cfg:stars",
    "cfg:referral", "cfg:security", "cfg:notify", "cfg:messages",
    "cfg:delivery", "cfg:admins",
}

VALID_PATTERN_PREFIXES = (
    "cats_page:", "cat:", "product:", "buy:", "confirm_buy:", "coupon:",
    "buy_stars_pkg:", "orders:", "order_detail:", "search_pg:", "setlang:",
    "captcha:", "admin_products:", "admin_product:", "ap_cat:", "stg:",
    "admin_edit_product:", "admin_toggle_product:", "admin_delete_product:",
    "admin_cat:", "admin_toggle_cat:", "admin_delete_cat:", "admin_edit_cat:",
    "admin_users:", "admin_user:", "admin_ban:", "admin_unban:",
    "admin_adjust:", "admin_adjust_stars:", "admin_user_orders:",
    "admin_dep:", "admin_dep_confirm:", "admin_dep_reject:",
    "admin_orders:", "admin_coupon:", "admin_toggle_coupon:",
    "admin_delete_coupon:", "coupon_type:", "admin_logs:",
    "confirm_delete:", "admin_product_share:", "fs:detail:", "fs:toggle_ch:",
    "fs:remove:", "fs:edit_link:", "ref:set_type:", "ref:edit:",
    "stars:pkg:", "stars:pkg_toggle:", "stars:pkg_del:", "stars:pkg_edit:",
    "stars:edit:", "stars:test:", "adm:detail:", "adm:remove:",
    "rl:detail:", "rl:delete:", "rl:copy:", "dg:edit:",
)


def is_valid_callback(data: str) -> bool:
    """Basic validation — rejects empty or suspiciously long payloads."""
    if not data or len(data) > 200:
        return False
    if data in VALID_PREFIXES:
        return True
    for prefix in VALID_PATTERN_PREFIXES:
        if data.startswith(prefix):
            return True
    return True  # Allow unknown — handled by the else branch in router


# ─────────────────────────────────────────────
#  ADMIN ACTION DEDUP  (prevent double-taps on
#  destructive admin operations)
# ─────────────────────────────────────────────

_admin_dedup: Dict[str, float] = {}
_ADMIN_DEDUP_TTL = 3.0


def admin_action_allowed(admin_id: int, action: str) -> bool:
    key = f"{admin_id}:{action}"
    now = time.time()
    if key in _admin_dedup and now - _admin_dedup[key] < _ADMIN_DEDUP_TTL:
        return False
    _admin_dedup[key] = now
    return True
