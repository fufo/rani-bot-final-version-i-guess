"""
╔══════════════════════════════════════════════════════════╗
║         TELEGRAM SHOP BOT - UI FORMATTING                ║
║  Premium text formatting, dividers, badges, templates    ║
╚══════════════════════════════════════════════════════════╝
"""

from datetime import datetime
from typing import Optional


# ─────────────────────────────────────────────
#  DIVIDERS
# ─────────────────────────────────────────────

DIV      = "─" * 20
DIV_BOLD = "━" * 20
DIV_DOT  = "· " * 10


def section(title: str) -> str:
    return f"<b>{title}</b>\n{DIV_BOLD}"


def subsection(title: str) -> str:
    return f"▸ <b>{title}</b>"


# ─────────────────────────────────────────────
#  STATUS BADGES
# ─────────────────────────────────────────────

def status_badge(status: str) -> str:
    return {
        "completed":  "✅ Completed",
        "pending":    "⏳ Pending",
        "cancelled":  "❌ Cancelled",
        "confirmed":  "✅ Confirmed",
        "rejected":   "❌ Rejected",
        "open":       "🟢 Open",
        "closed":     "🔴 Closed",
    }.get(status.lower(), f"❓ {status.title()}")


def toggle_badge(value: bool) -> str:
    return "🟢 ON" if value else "🔴 OFF"


def stock_badge(stock: int) -> str:
    if stock == -1:
        return "♾️ Unlimited"
    if stock == 0:
        return "❌ Out of Stock"
    if stock <= 5:
        return f"⚠️ Low: {stock} left"
    return f"✅ {stock} in stock"


# ─────────────────────────────────────────────
#  PRICE FORMATTING
# ─────────────────────────────────────────────

def fmt_price(amount: float, symbol: str = "$") -> str:
    return f"{symbol}{amount:,.2f}"


def fmt_stars(stars: int) -> str:
    return f"{stars:,} ⭐"


# ─────────────────────────────────────────────
#  USER CARD
# ─────────────────────────────────────────────

def user_card(user_id: int, name: str, username: Optional[str] = None) -> str:
    uname = f"@{username}" if username else "—"
    return (
        f"👤 <b>{name}</b>\n"
        f"🆔 <code>{user_id}</code> · {uname}"
    )


# ─────────────────────────────────────────────
#  PRODUCT CARD (full detail page)
# ─────────────────────────────────────────────

def product_card(product: dict, lang: str = "en") -> str:
    name  = product.get(f"name_{lang}") or product.get("name", "Product")
    desc  = product.get(f"description_{lang}") or product.get("description", "")
    price = product.get("price", 0.0)
    stars = product.get("price_stars", 0)
    stock = product.get("stock", -1)
    sold  = product.get("total_sold", 0)
    cat   = product.get("category_name", "")
    emoji = product.get("category_emoji", "📦")
    rating = product.get("avg_rating")
    rating_count = product.get("rating_count", 0)

    lines = [
        f"{emoji} <b>{name}</b>",
        DIV_BOLD,
        "",
    ]
    if cat:
        lines.append(f"📂 <b>Category:</b> {cat}")
    lines += [
        f"💰 <b>Price:</b> {fmt_price(price)}",
    ]
    if stars > 0:
        lines.append(f"⭐ <b>Stars Price:</b> {fmt_stars(stars)}")
    lines.append(f"📦 <b>Stock:</b> {stock_badge(stock)}")
    lines.append(f"🛒 <b>Sold:</b> {sold:,}")
    if rating is not None and rating_count > 0:
        stars_str = "⭐" * round(rating) + "☆" * (5 - round(rating))
        lines.append(f"⭐ <b>Rating:</b> {stars_str} ({rating:.1f}/5 · {rating_count} reviews)")
    if desc:
        lines += ["", f"📝 {desc}"]
    return "\n".join(lines)


# ─────────────────────────────────────────────
#  ORDER RECEIPT
# ─────────────────────────────────────────────

def order_receipt(order: dict) -> str:
    oid    = order.get("order_id", "?")
    pname  = order.get("product_name") or order.get("pname", "?")
    amount = order.get("amount", 0)
    method = order.get("payment_method", "?")
    status = order.get("status", "?")
    date   = order.get("created_at", "")
    badge  = status_badge(status)
    dt     = _fmt_dt(date)
    return (
        f"🧾 <b>Order Receipt</b>\n"
        f"{DIV_BOLD}\n\n"
        f"🆔 <code>{oid}</code>\n"
        f"📦 {pname}\n"
        f"💰 {fmt_price(amount)}\n"
        f"💳 {method}\n"
        f"{badge}\n"
        f"📅 {dt}"
    )


# ─────────────────────────────────────────────
#  REFERRAL RANK
# ─────────────────────────────────────────────

RANK_MEDALS = ["🥇", "🥈", "🥉"] + ["🏅"] * 97

RANK_LABELS = {
    1:  ("👑 Legend",    "You're the top referrer!"),
    2:  ("🔥 Elite",     "Almost at the top!"),
    3:  ("💎 Diamond",   "Top 3 referrer!"),
    5:  ("🌟 Gold",      "Fantastic effort!"),
    10: ("🥈 Silver",    "Great work!"),
    25: ("🥉 Bronze",    "Keep going!"),
}


def referral_rank_badge(count: int) -> str:
    for threshold in sorted(RANK_LABELS.keys()):
        if count <= threshold:
            label, _ = RANK_LABELS[threshold]
            return label
    return "🌱 Newcomer"


# ─────────────────────────────────────────────
#  MILESTONE DEFINITIONS
# ─────────────────────────────────────────────

MILESTONES = [
    {"count": 1,   "title": "First Recruit 🌱",    "reward": 0.25},
    {"count": 3,   "title": "Rising Star ⭐",       "reward": 0.50},
    {"count": 5,   "title": "Recruiter 🎯",          "reward": 1.00},
    {"count": 10,  "title": "Ambassador 🏅",         "reward": 2.00},
    {"count": 25,  "title": "Champion 🥉",           "reward": 5.00},
    {"count": 50,  "title": "Elite Recruiter 🥈",   "reward": 10.0},
    {"count": 100, "title": "Legendary 🥇",          "reward": 25.0},
]


def get_next_milestone(current_count: int) -> Optional[dict]:
    for m in MILESTONES:
        if current_count < m["count"]:
            return m
    return None


def get_achieved_milestone(current_count: int) -> Optional[dict]:
    achieved = None
    for m in MILESTONES:
        if current_count >= m["count"]:
            achieved = m
    return achieved


# ─────────────────────────────────────────────
#  INTERNAL HELPERS
# ─────────────────────────────────────────────

def _fmt_dt(date_str: str) -> str:
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d %b %Y · %H:%M")
    except Exception:
        return date_str or "—"
