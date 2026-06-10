"""
╔══════════════════════════════════════════════════════════╗
║       USER MANAGEMENT EXTENSION — database_user_mgmt    ║
║   Advanced filters · Admin notes · Bulk actions · VIP   ║
╚══════════════════════════════════════════════════════════╝
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
#  MIGRATION — create new tables on first import
# ─────────────────────────────────────────────

def init_user_mgmt_tables():
    """Create admin_notes and user_vip tables if not already present."""
    from database import get_db
    with get_db() as conn:
        c = conn.cursor()

        # Admin Notes
        c.execute("""
            CREATE TABLE IF NOT EXISTS admin_notes (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                admin_id    INTEGER NOT NULL,
                admin_name  TEXT,
                note        TEXT NOT NULL,
                created_at  TEXT DEFAULT (datetime('now')),
                updated_at  TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # VIP / Rank
        c.execute("""
            CREATE TABLE IF NOT EXISTS user_vip (
                user_id     INTEGER PRIMARY KEY,
                vip_rank    INTEGER DEFAULT 0,
                assigned_by INTEGER,
                assigned_at TEXT DEFAULT (datetime('now')),
                notes       TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # Indexes for performance
        c.execute("CREATE INDEX IF NOT EXISTS idx_users_balance    ON users(balance)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_users_total_spent ON users(total_spent)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_users_total_orders ON users(total_orders)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_users_joined_at  ON users(joined_at)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_users_last_seen  ON users(last_seen)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_users_is_banned  ON users(is_banned)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_admin_notes_user ON admin_notes(user_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_user_vip_rank    ON user_vip(vip_rank)")

    logger.info("✅ user_mgmt tables ready")


# ─────────────────────────────────────────────────────────────────────────────
#  FILTER BUILDER
#  Returns (where_clause, params) for use in SELECT … FROM users …
# ─────────────────────────────────────────────────────────────────────────────

VIP_LABELS = {0: "None", 1: "🥉 Bronze", 2: "🥈 Silver", 3: "🥇 Gold", 4: "💎 Diamond", 5: "👑 Legend"}

def build_user_filter_query(filters: Dict) -> Tuple[str, list]:
    """
    Translate a filter dict into a SQL WHERE clause + params.
    Returns ("WHERE …", [params])  or  ("", []) when no filters.
    """
    conditions = []
    params: list = []

    # ── Balance ──────────────────────────────
    if filters.get("balance_min") is not None:
        conditions.append("u.balance >= ?")
        params.append(float(filters["balance_min"]))
    if filters.get("balance_max") is not None:
        conditions.append("u.balance <= ?")
        params.append(float(filters["balance_max"]))

    # ── Spent ────────────────────────────────
    if filters.get("spent_min") is not None:
        conditions.append("u.total_spent >= ?")
        params.append(float(filters["spent_min"]))
    if filters.get("spent_max") is not None:
        conditions.append("u.total_spent <= ?")
        params.append(float(filters["spent_max"]))

    # ── Purchase count ────────────────────────
    if filters.get("orders_min") is not None:
        conditions.append("u.total_orders >= ?")
        params.append(int(filters["orders_min"]))
    if filters.get("orders_max") is not None:
        conditions.append("u.total_orders <= ?")
        params.append(int(filters["orders_max"]))

    # ── Join date ─────────────────────────────
    if filters.get("joined_after"):
        conditions.append("u.joined_at >= ?")
        params.append(filters["joined_after"])
    if filters.get("joined_before"):
        conditions.append("u.joined_at <= ?")
        params.append(filters["joined_before"])

    # ── Last seen ─────────────────────────────
    if filters.get("seen_after"):
        conditions.append("u.last_seen >= ?")
        params.append(filters["seen_after"])
    if filters.get("seen_before"):
        conditions.append("u.last_seen <= ?")
        params.append(filters["seen_before"])

    # ── Language ──────────────────────────────
    if filters.get("language"):
        conditions.append("u.language = ?")
        params.append(filters["language"])

    # ── Ban status ────────────────────────────
    if filters.get("is_banned") is not None:
        conditions.append("u.is_banned = ?")
        params.append(1 if filters["is_banned"] else 0)

    # ── Preset shortcuts ─────────────────────
    if filters.get("preset") == "inactive":
        cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
        conditions.append("(u.last_seen IS NULL OR u.last_seen < ?)")
        params.append(cutoff)
        conditions.append("u.is_banned = 0")

    elif filters.get("preset") == "high_spenders":
        # Top by total_spent — enforced via ORDER+LIMIT in caller
        conditions.append("u.total_spent > 0")

    elif filters.get("preset") == "new_users":
        cutoff = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        conditions.append("u.joined_at >= ?")
        params.append(cutoff)

    elif filters.get("preset") == "has_referrals":
        conditions.append("""
            EXISTS (SELECT 1 FROM referrals r WHERE r.referrer_id = u.user_id)
        """)

    elif filters.get("preset") == "has_notes":
        conditions.append("""
            EXISTS (SELECT 1 FROM admin_notes n WHERE n.user_id = u.user_id)
        """)

    elif filters.get("preset") == "has_ticket":
        conditions.append("""
            EXISTS (SELECT 1 FROM support_tickets t
                    WHERE t.user_id = u.user_id AND t.status = 'open')
        """)

    elif filters.get("preset") == "has_pending_orders":
        conditions.append("""
            EXISTS (SELECT 1 FROM orders o
                    WHERE o.user_id = u.user_id AND o.status = 'pending')
        """)

    # ── VIP rank ──────────────────────────────
    if filters.get("vip_rank") is not None:
        rank = int(filters["vip_rank"])
        if rank == 0:
            # not VIP: no row or rank=0
            conditions.append("""
                NOT EXISTS (SELECT 1 FROM user_vip v
                            WHERE v.user_id = u.user_id AND v.vip_rank > 0)
            """)
        else:
            conditions.append("""
                EXISTS (SELECT 1 FROM user_vip v
                        WHERE v.user_id = u.user_id AND v.vip_rank = ?)
            """)
            params.append(rank)

    # ── Referral count ────────────────────────
    if filters.get("referrals_min") is not None:
        conditions.append("""
            (SELECT COUNT(*) FROM referrals r WHERE r.referrer_id = u.user_id) >= ?
        """)
        params.append(int(filters["referrals_min"]))

    # ── Coupon usage ──────────────────────────
    if filters.get("has_used_coupon"):
        conditions.append("""
            EXISTS (SELECT 1 FROM coupon_usage cu WHERE cu.user_id = u.user_id)
        """)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    return where, params


# ─────────────────────────────────────────────────────────────────────────────
#  FILTERED USER QUERIES
# ─────────────────────────────────────────────────────────────────────────────

SORT_COLS = {
    "joined_at":    "u.joined_at",
    "last_seen":    "u.last_seen",
    "balance":      "u.balance",
    "total_spent":  "u.total_spent",
    "total_orders": "u.total_orders",
    "username":     "u.username",
}


def get_users_filtered(
    filters: Dict,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = "joined_at",
    sort_dir: str = "DESC",
    search: str = None,
) -> Tuple[List[Dict], int]:
    """
    Return (users_list, total_count) with full filter + sort + search support.
    """
    init_user_mgmt_tables()
    from database import get_db

    where, params = build_user_filter_query(filters)

    # Text search (id / username / referral_code / note keywords)
    search_where = ""
    search_params: list = []
    if search and search.strip():
        q = search.strip()
        # Strip leading @ so admins can type @username naturally
        if q.startswith("@"):
            q = q[1:]
        if q.isdigit():
            # Use WHERE or AND depending on whether base filters exist
            keyword = "AND" if where else "WHERE"
            search_where = f"{keyword} u.user_id = ?"
            search_params = [int(q)]
        else:
            pattern = f"%{q}%"
            keyword = "AND" if where else "WHERE"
            search_where = f"""{keyword} (
                u.username LIKE ?
                OR u.first_name LIKE ?
                OR u.referral_code LIKE ?
                OR EXISTS (SELECT 1 FROM admin_notes an
                           WHERE an.user_id = u.user_id AND an.note LIKE ?)
            )"""
            search_params = [pattern, pattern, pattern, pattern]

    col = SORT_COLS.get(sort_by, "u.joined_at")
    direction = "ASC" if sort_dir.upper() == "ASC" else "DESC"
    offset = (page - 1) * per_page

    base_sql = f"""
        FROM users u
        LEFT JOIN user_vip v ON v.user_id = u.user_id
        {where} {search_where}
    """
    all_params = params + search_params

    with get_db() as conn:
        c = conn.cursor()
        c.execute(f"SELECT COUNT(*) {base_sql}", all_params)
        total = c.fetchone()[0]

        c.execute(f"""
            SELECT u.*,
                   COALESCE(v.vip_rank, 0) as vip_rank,
                   (SELECT COUNT(*) FROM referrals r WHERE r.referrer_id = u.user_id) as referral_count
            {base_sql}
            ORDER BY {col} {direction}
            LIMIT ? OFFSET ?
        """, all_params + [per_page, offset])
        users = [dict(r) for r in c.fetchall()]

    return users, total


def export_users_filtered(filters: Dict, search: str = None) -> List[Dict]:
    """Return all matching users (no pagination) for CSV export."""
    users, _ = get_users_filtered(filters, page=1, per_page=99999, search=search)
    return users


# ─────────────────────────────────────────────────────────────────────────────
#  ADMIN NOTES
# ─────────────────────────────────────────────────────────────────────────────

def get_admin_notes(user_id: int) -> List[Dict]:
    init_user_mgmt_tables()
    from database import get_db
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT * FROM admin_notes WHERE user_id = ?
            ORDER BY created_at DESC
        """, (user_id,))
        return [dict(r) for r in c.fetchall()]


def add_admin_note(user_id: int, admin_id: int, admin_name: str, note: str) -> int:
    init_user_mgmt_tables()
    from database import get_db
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO admin_notes (user_id, admin_id, admin_name, note)
            VALUES (?, ?, ?, ?)
        """, (user_id, admin_id, admin_name, note.strip()))
        return c.lastrowid


def edit_admin_note(note_id: int, new_text: str) -> bool:
    from database import get_db
    with get_db() as conn:
        conn.execute("""
            UPDATE admin_notes SET note = ?, updated_at = datetime('now')
            WHERE id = ?
        """, (new_text.strip(), note_id))
    return True


def delete_admin_note(note_id: int) -> bool:
    from database import get_db
    with get_db() as conn:
        conn.execute("DELETE FROM admin_notes WHERE id = ?", (note_id,))
    return True


def get_admin_note(note_id: int) -> Optional[Dict]:
    from database import get_db
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM admin_notes WHERE id = ?", (note_id,))
        row = c.fetchone()
        return dict(row) if row else None


# ─────────────────────────────────────────────────────────────────────────────
#  VIP / RANK SYSTEM
# ─────────────────────────────────────────────────────────────────────────────

def get_user_vip(user_id: int) -> Optional[Dict]:
    init_user_mgmt_tables()
    from database import get_db
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM user_vip WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        return dict(row) if row else None


def set_user_vip(user_id: int, vip_rank: int, assigned_by: int, notes: str = "") -> bool:
    init_user_mgmt_tables()
    from database import get_db
    with get_db() as conn:
        if vip_rank == 0:
            conn.execute("DELETE FROM user_vip WHERE user_id = ?", (user_id,))
        else:
            conn.execute("""
                INSERT OR REPLACE INTO user_vip (user_id, vip_rank, assigned_by, notes, assigned_at)
                VALUES (?, ?, ?, ?, datetime('now'))
            """, (user_id, vip_rank, assigned_by, notes))
    return True


def get_vip_label(rank: int) -> str:
    return VIP_LABELS.get(rank, f"Rank {rank}")


# ─────────────────────────────────────────────────────────────────────────────
#  BULK ACTIONS
# ─────────────────────────────────────────────────────────────────────────────

def bulk_ban(user_ids: List[int], reason: str, admin_id: int) -> int:
    from database import get_db, PRIMARY_ADMIN_ID, add_admin_log
    count = 0
    with get_db() as conn:
        for uid in user_ids:
            if uid == PRIMARY_ADMIN_ID:
                continue
            conn.execute(
                "UPDATE users SET is_banned=1, ban_reason=? WHERE user_id=?",
                (reason, uid)
            )
            count += 1
    if count:
        add_admin_log(admin_id, "bulk_ban",
                      f"Banned {count} users. Reason: {reason}", None)
    return count


def bulk_unban(user_ids: List[int], admin_id: int) -> int:
    from database import get_db, add_admin_log
    count = 0
    with get_db() as conn:
        for uid in user_ids:
            conn.execute(
                "UPDATE users SET is_banned=0, ban_reason=NULL WHERE user_id=?",
                (uid,)
            )
            count += 1
    if count:
        add_admin_log(admin_id, "bulk_unban", f"Unbanned {count} users", None)
    return count


def bulk_adjust_balance(user_ids: List[int], amount: float, admin_id: int) -> int:
    from database import get_db, add_admin_log
    count = 0
    with get_db() as conn:
        for uid in user_ids:
            if amount >= 0:
                conn.execute(
                    "UPDATE users SET balance = balance + ? WHERE user_id = ?",
                    (amount, uid)
                )
            else:
                conn.execute(
                    "UPDATE users SET balance = MAX(0, balance + ?) WHERE user_id = ?",
                    (amount, uid)
                )
            count += 1
    action = "give_balance" if amount >= 0 else "remove_balance"
    add_admin_log(admin_id, f"bulk_{action}",
                  f"{action.replace('_',' ').title()} {abs(amount)} to {count} users", None)
    return count


def bulk_set_vip(user_ids: List[int], vip_rank: int, admin_id: int) -> int:
    count = 0
    for uid in user_ids:
        set_user_vip(uid, vip_rank, admin_id)
        count += 1
    from database import add_admin_log
    add_admin_log(admin_id, "bulk_set_vip",
                  f"Set VIP rank {vip_rank} for {count} users", None)
    return count


def bulk_add_note(user_ids: List[int], note_text: str, admin_id: int, admin_name: str) -> int:
    count = 0
    for uid in user_ids:
        add_admin_note(uid, admin_id, admin_name, note_text)
        count += 1
    return count


# ─────────────────────────────────────────────────────────────────────────────
#  ENRICHED USER PROFILE  (single user, all data merged)
# ─────────────────────────────────────────────────────────────────────────────

def get_user_full_profile(user_id: int) -> Optional[Dict]:
    """Return a single dict with every piece of info for the user profile page."""
    from database import get_db, get_user, get_user_orders, get_user_referrals
    user = get_user(user_id)
    if not user:
        return None

    # Referrals
    try:
        referrals = get_user_referrals(user_id)
        ref_count = len(referrals)
        ref_earned = sum(r.get("bonus_paid", 0) for r in referrals)
    except Exception:
        ref_count = ref_earned = 0

    # Recent orders
    try:
        orders, order_total = get_user_orders(user_id, 1, 5)
    except Exception:
        orders, order_total = [], 0

    # Pending orders count
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM orders WHERE user_id=? AND status='pending'",
                      (user_id,))
            pending_orders = c.fetchone()[0]
    except Exception:
        pending_orders = 0

    # Coupons used
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM coupon_usage WHERE user_id=?", (user_id,))
            coupons_used = c.fetchone()[0]
    except Exception:
        coupons_used = 0

    # Open tickets
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute(
                "SELECT COUNT(*) FROM support_tickets WHERE user_id=? AND status='open'",
                (user_id,)
            )
            open_tickets = c.fetchone()[0]
    except Exception:
        open_tickets = 0

    # Admin notes
    notes = get_admin_notes(user_id)

    # VIP
    vip = get_user_vip(user_id)
    vip_rank = vip["vip_rank"] if vip else 0

    return {
        **user,
        "ref_count":     ref_count,
        "ref_earned":    ref_earned,
        "pending_orders": pending_orders,
        "order_total":   order_total,
        "recent_orders": orders,
        "coupons_used":  coupons_used,
        "open_tickets":  open_tickets,
        "admin_notes":   notes,
        "vip_rank":      vip_rank,
        "vip_label":     get_vip_label(vip_rank),
    }


# ─────────────────────────────────────────────────────────────────────────────
#  CSV EXPORT HELPER
# ─────────────────────────────────────────────────────────────────────────────

def users_to_csv(users: List[Dict]) -> str:
    """Convert list of user dicts to CSV text."""
    if not users:
        return "No users found."
    cols = ["user_id", "username", "first_name", "language", "balance",
            "total_spent", "total_orders", "is_banned", "joined_at", "last_seen",
            "referral_code", "vip_rank"]
    lines = [",".join(cols)]
    for u in users:
        row = []
        for col in cols:
            val = str(u.get(col, "")).replace(",", ";").replace("\n", " ")
            row.append(val)
        lines.append(",".join(row))
    return "\n".join(lines)
