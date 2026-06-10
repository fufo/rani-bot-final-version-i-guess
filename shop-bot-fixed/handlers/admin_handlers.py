"""
╔══════════════════════════════════════════════════════════╗
║         TELEGRAM SHOP BOT - ADMIN HANDLERS              ║
╚══════════════════════════════════════════════════════════╝
"""

import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import database as db
from config import PRIMARY_ADMIN_ID, PRODUCTS_PER_PAGE, ORDERS_PER_PAGE
from utils.helpers import (
    is_admin, is_owner, safe_edit_message, safe_answer_callback,
    format_price, format_datetime, format_date, get_user_display_name,
    UserState, detect_file_type
)
from keyboards.inline import (
    admin_main_keyboard, admin_stats_keyboard, admin_products_keyboard,
    admin_product_detail_keyboard, admin_categories_keyboard,
    admin_users_keyboard, admin_user_detail_keyboard, admin_deposits_keyboard,
    admin_deposit_action_keyboard, admin_coupons_keyboard, admin_logs_keyboard,
    back_to_admin_keyboard, cancel_keyboard, admin_settings_keyboard
)

logger = logging.getLogger(__name__)


def _lang(context): return context.user_data.get("lang", "en")

ADMIN_PANEL_ITEMS_PER_PAGE = 10


# ─────────────────────────────────────────────
#  ADMIN PANEL
# ─────────────────────────────────────────────

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await safe_answer_callback(update, "⛔ Access denied", show_alert=True)
        return
    crown = "👑" if is_owner(user.id) else "🛡️"
    name = user.first_name or f"User#{user.id}"
    text = (
        f"{crown} <b>Admin Panel</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Welcome, <b>{name}</b>!\n"
        f"🆔 Your ID: <code>{user.id}</code>"
    )
    await safe_edit_message(update, text, admin_main_keyboard(), "HTML")


# ─────────────────────────────────────────────
#  STATISTICS
# ─────────────────────────────────────────────

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        stats = db.get_enhanced_statistics()
    except Exception:
        stats = db.get_statistics()
    top = stats.get("top_products") or []
    top_text = "\n".join(
        f"  {i+1}. {p['name']} ({p['total_sold']} sold)"
        for i, p in enumerate(top)
    ) or "  No data yet"

    weekly_top = stats.get("weekly_top", [])
    weekly_text = ""
    if weekly_top:
        medals = ["🥇", "🥈", "🥉"]
        lines = [
            f"  {medals[i]} {u.get('first_name','User')} — {u.get('weekly_count',0)} invites"
            for i, u in enumerate(weekly_top[:3])
        ]
        weekly_text = "\n🏆 <b>Weekly Top Inviters:</b>\n" + "\n".join(lines)

    avg_rating = stats.get("avg_rating", 0) or 0
    rating_str = f"⭐ {avg_rating:.1f}/5" if avg_rating else "No ratings yet"

    text = (
        "📊 <b>Bot Statistics</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 Total Users: <b>{stats['total_users']:,}</b>\n"
        f"🆕 New Today: <b>{stats['new_users_today']}</b> · "
        f"Week: <b>{stats['new_users_week']}</b>\n"
        f"🚫 Banned: <b>{stats['banned_users']}</b>\n\n"
        f"🛒 Total Orders: <b>{stats['total_orders']:,}</b>\n"
        f"✅ Completed: <b>{stats['completed_orders']:,}</b>\n"
        f"💰 Revenue: <b>${format_price(stats['total_revenue'])}</b>\n"
        f"💵 Today: <b>${format_price(stats['revenue_today'])}</b>\n\n"
        f"📦 Active Products: <b>{stats['active_products']}</b>\n"
        f"📂 Categories: <b>{stats['active_categories']}</b>\n"
        f"💎 Pending Deposits: <b>{stats['pending_deposits']}</b>\n\n"
        f"⭐ Ratings: <b>{stats.get('total_ratings', 0)}</b> · Avg: <b>{rating_str}</b>\n"
        f"🚀 Deliveries: ✅ {stats.get('successful_deliveries',0)} · "
        f"❌ {stats.get('failed_deliveries',0)}\n"
        f"🔗 Referrals: <b>{stats.get('total_referrals',0)}</b> · "
        f"Referrers: <b>{stats.get('active_referrers',0)}</b>"
        f"{weekly_text}\n\n"
        f"🏆 <b>Top Products:</b>\n{top_text}"
    )
    kb_rows = [
        [InlineKeyboardButton("🔄 Refresh", callback_data="admin_stats"),
         InlineKeyboardButton("⚠️ Failed Deliveries", callback_data="admin_failed_deliveries")],
        [InlineKeyboardButton("◀️ Admin Panel", callback_data="admin")],
    ]
    await safe_edit_message(update, text, InlineKeyboardMarkup(kb_rows), "HTML")


# ─────────────────────────────────────────────
#  PRODUCTS
# ─────────────────────────────────────────────

async def admin_products(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 1):
    products, total = db.get_all_products_admin(page, ADMIN_PANEL_ITEMS_PER_PAGE)
    total_pages = max(1, (total + ADMIN_PANEL_ITEMS_PER_PAGE - 1) // ADMIN_PANEL_ITEMS_PER_PAGE)
    text = f"📦 <b>Products</b> ({total} total) — Page {page}/{total_pages}"
    await safe_edit_message(update, text,
                             admin_products_keyboard(products, page, total_pages), "HTML")


async def admin_product_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, product_id: int):
    product = db.get_product(product_id)
    if not product:
        await safe_answer_callback(update, "Product not found", show_alert=True)
        return
    text = (
        f"📦 <b>{product['name']}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📂 Category: <b>{product.get('category_name', '—')}</b>\n"
        f"💵 Price: <b>${product.get('price', 0):.2f}</b>\n"
        f"⭐ Stars Price: <b>{product.get('price_stars', 0)}</b>\n"
        f"📦 Stock: <b>{'Unlimited' if product.get('stock') == -1 else product.get('stock', '?')}</b>\n"
        f"🛒 Total Sold: <b>{product.get('total_sold', 0)}</b>\n"
        f"📎 File: <b>{'Yes' if product.get('file_id') else 'No'}</b>\n"
        f"Status: <b>{'✅ Active' if product.get('is_active') else '❌ Inactive'}</b>"
    )
    await safe_edit_message(update, text,
                             admin_product_detail_keyboard(
                                 product_id, bool(product.get("is_active"))
                             ), "HTML")


async def admin_add_product_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cats = db.get_categories(active_only=True)
    if not cats:
        await safe_answer_callback(update, "❌ No categories found. Add a category first.",
                                   show_alert=True)
        return
    context.user_data[UserState.ADMIN_ADD_PRODUCT] = True
    context.user_data[UserState.ADMIN_PRODUCT_STEP] = "category"
    context.user_data[UserState.ADMIN_PRODUCT_DATA] = {}
    rows = [[InlineKeyboardButton(f"{c.get('emoji','📦')} {c['name']}",
                                  callback_data=f"ap_cat:{c['id']}")]
            for c in cats]
    rows.append([InlineKeyboardButton("✖️ Cancel", callback_data="admin_products:1")])
    await safe_edit_message(update, "📦 <b>Add Product</b>\n\nStep 1: Select category:",
                             InlineKeyboardMarkup(rows), "HTML")


async def admin_add_product_category(update: Update, context: ContextTypes.DEFAULT_TYPE, cat_id: int):
    context.user_data[UserState.ADMIN_PRODUCT_DATA]["category_id"] = cat_id
    context.user_data[UserState.ADMIN_PRODUCT_STEP] = "name"
    await safe_edit_message(
        update, "📦 <b>Add Product</b>\n\nStep 2: Enter product name:",
        cancel_keyboard("admin_products:1"), "HTML"
    )


async def admin_edit_product_field(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                    field: str, product_id: int):
    labels = {
        "name":  "✏️ Enter new product name:",
        "price": "💰 Enter new price in USD (e.g. 9.99):",
        "desc":  "📝 Enter new description:",
        "stock": "📦 Enter stock (-1 for unlimited):",
        "file":  "📁 Send the new file/photo/video for this product:",
    }
    prompt = labels.get(field, "Enter new value:")
    context.user_data[UserState.ADMIN_EDIT_PRODUCT] = True
    context.user_data["edit_product_id"] = product_id
    context.user_data["edit_product_field"] = field
    await safe_edit_message(update, prompt,
                             cancel_keyboard(f"admin_product:{product_id}"), "HTML")


async def admin_toggle_product(update: Update, context: ContextTypes.DEFAULT_TYPE, product_id: int):
    product = db.get_product(product_id)
    if not product:
        return
    db.update_product(product_id, is_active=0 if product.get("is_active") else 1)
    db.add_admin_log(update.effective_user.id, "toggle_product", f"Product #{product_id}", product_id)
    await safe_answer_callback(update, "✅ Updated", show_alert=False)
    await admin_product_detail(update, context, product_id)


async def admin_delete_product_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                        product_id: int):
    product = db.get_product(product_id)
    if not product:
        return
    text = f"⚠️ Delete <b>{product['name']}</b>?\n\nThis will deactivate it."
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm Delete",
                              callback_data=f"confirm_delete:product:{product_id}"),
         InlineKeyboardButton("✖️ Cancel",
                              callback_data=f"admin_product:{product_id}")],
    ])
    await safe_edit_message(update, text, keyboard, "HTML")


# ─────────────────────────────────────────────
#  CATEGORIES
# ─────────────────────────────────────────────

async def admin_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cats = db.get_categories(active_only=False)
    text = f"📂 <b>Categories</b> ({len(cats)} total)"
    await safe_edit_message(update, text, admin_categories_keyboard(cats), "HTML")


async def admin_add_category_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data[UserState.ADMIN_ADD_CATEGORY] = True
    context.user_data["category_step"] = "name"
    context.user_data["category_data"] = {}
    await safe_edit_message(update, "📂 <b>Add Category</b>\n\nStep 1: Enter category name:",
                             cancel_keyboard("admin_categories"), "HTML")


async def admin_category_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, cat_id: int):
    cat = db.get_category(cat_id)
    if not cat:
        await safe_answer_callback(update, "Category not found", show_alert=True)
        return
    text = (
        f"{cat.get('emoji','📦')} <b>{cat['name']}</b>\n\n"
        f"Status: {'✅ Active' if cat.get('is_active') else '❌ Inactive'}\n"
        f"Description: {cat.get('description') or '—'}"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Name",    callback_data=f"admin_edit_cat:name:{cat_id}"),
         InlineKeyboardButton("🎨 Emoji",   callback_data=f"admin_edit_cat:emoji:{cat_id}")],
        [InlineKeyboardButton(
            "🔴 Deactivate" if cat.get("is_active") else "🟢 Activate",
            callback_data=f"admin_toggle_cat:{cat_id}"
        )],
        [InlineKeyboardButton("🗑️ Delete",  callback_data=f"admin_delete_cat:{cat_id}")],
        [InlineKeyboardButton("◀️ Back",    callback_data="admin_categories")],
    ])
    await safe_edit_message(update, text, keyboard, "HTML")


# ─────────────────────────────────────────────
#  USERS
# ─────────────────────────────────────────────

async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 1):
    per_page = ADMIN_PANEL_ITEMS_PER_PAGE
    users, total = db.get_users_paginated(page, per_page)
    total_pages = max(1, (total + per_page - 1) // per_page)
    text = f"👥 <b>Users</b> ({total} total) — Page {page}/{total_pages}"
    await safe_edit_message(update, text,
                             admin_users_keyboard(users, page, total_pages), "HTML")


async def admin_user_search_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data[UserState.ADMIN_SEARCH_USER] = True
    await safe_edit_message(
        update,
        "🔍 <b>Search User</b>\n\nEnter the Telegram User ID to look up:",
        cancel_keyboard("admin_users:1"), "HTML"
    )


async def admin_user_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int):
    user = db.get_user(target_id)
    if not user:
        await safe_answer_callback(update, "User not found", show_alert=True)
        return
    name = user.get("first_name") or f"User#{target_id}"
    # Enrich with referral / rating data
    try:
        ref_count = len(db.get_user_referrals(target_id))
    except Exception:
        ref_count = 0
    try:
        rating_data = db.get_product_rating(0)  # placeholder
        # Count ratings left by this user
        with db.get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM product_ratings WHERE user_id = ?", (target_id,))
            ratings_given = c.fetchone()[0]
    except Exception:
        ratings_given = 0

    ban_status = "🚫 Banned" if user.get("is_banned") else "✅ Active"
    lang = user.get("language", "en")

    text = (
        f"👤 <b>User Profile</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📛 <b>{name}</b>\n"
        f"🆔 <code>{target_id}</code> · @{user.get('username') or '—'}\n"
        f"🌍 Lang: <b>{lang.upper()}</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Balance: <b>${format_price(user.get('balance', 0))}</b>\n"
        f"⭐ Stars:   <b>{user.get('stars_balance', 0):,}</b>\n\n"
        f"🛒 Orders:  <b>{user.get('total_orders', 0)}</b>\n"
        f"💵 Spent:   <b>${format_price(user.get('total_spent', 0))}</b>\n"
        f"🔗 Referrals: <b>{ref_count}</b>\n"
        f"⭐ Reviews given: <b>{ratings_given}</b>\n\n"
        f"📅 Joined: <b>{format_date(user.get('joined_at', ''))}</b>\n"
        f"Status: <b>{ban_status}</b>"
    )
    await safe_edit_message(update, text,
                             admin_user_detail_keyboard(target_id, bool(user.get("is_banned"))),
                             "HTML")


async def admin_ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int):
    if target_id == PRIMARY_ADMIN_ID:
        await safe_answer_callback(update, "⛔ Cannot ban the owner", show_alert=True)
        return
    context.user_data["ban_target_id"] = target_id
    context.user_data[UserState.ADMIN_BAN_USER] = True
    await safe_edit_message(update, f"🚫 Enter ban reason for <code>{target_id}</code>:",
                             cancel_keyboard(f"admin_user:{target_id}"), "HTML")


async def admin_unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int):
    db.unban_user(target_id)
    db.add_admin_log(update.effective_user.id, "unban_user", f"Unbanned {target_id}", target_id)
    await safe_answer_callback(update, "✅ User unbanned", show_alert=False)
    await admin_user_detail(update, context, target_id)


async def admin_adjust_balance(update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int):
    context.user_data["adjust_target_id"] = target_id
    context.user_data["adjust_type"] = "balance"
    context.user_data[UserState.ADMIN_ADJUST_BAL] = True
    await safe_edit_message(
        update,
        f"💰 Adjust balance for <code>{target_id}</code>\n\nEnter amount (+/- e.g. +5.00 or -3.00):",
        cancel_keyboard(f"admin_user:{target_id}"), "HTML"
    )


async def admin_adjust_stars(update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int):
    context.user_data["adjust_target_id"] = target_id
    context.user_data["adjust_type"] = "stars"
    context.user_data[UserState.ADMIN_ADJUST_BAL] = True
    await safe_edit_message(
        update,
        f"⭐ Adjust stars for <code>{target_id}</code>\n\nEnter amount (+/- e.g. +50 or -20):",
        cancel_keyboard(f"admin_user:{target_id}"), "HTML"
    )


# ─────────────────────────────────────────────
#  DEPOSITS
# ─────────────────────────────────────────────

async def admin_deposits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    deposits = db.get_pending_deposits()
    text = f"💎 <b>Pending Deposits</b> ({len(deposits)})"
    if not deposits:
        text += "\n\nNo pending deposits."
        await safe_edit_message(update, text, back_to_admin_keyboard(), "HTML")
        return
    await safe_edit_message(update, text, admin_deposits_keyboard(deposits), "HTML")


async def admin_deposit_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, deposit_id: str):
    with db.get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT d.*, u.first_name, u.username
            FROM deposits d JOIN users u ON d.user_id=u.user_id
            WHERE d.deposit_id=?
        """, (deposit_id,))
        dep = c.fetchone()
    if not dep:
        await safe_answer_callback(update, "Not found", show_alert=True)
        return
    dep = dict(dep)
    text = (
        f"💎 <b>Deposit Detail</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🆔 ID: <code>{deposit_id}</code>\n"
        f"👤 User: {dep.get('first_name') or '?'} (<code>{dep['user_id']}</code>)\n"
        f"💰 Amount: <b>${dep['amount']:.2f}</b>\n"
        f"📡 Method: <b>{dep['method']}</b>\n"
        f"📄 TX Hash: <code>{dep.get('tx_hash') or '—'}</code>\n"
        f"🕐 Submitted: <b>{format_datetime(dep.get('created_at', ''))}</b>"
    )
    await safe_edit_message(update, text, admin_deposit_action_keyboard(deposit_id), "HTML")


async def admin_deposit_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE, deposit_id: str):
    success = db.confirm_deposit(deposit_id)
    if not success:
        await safe_answer_callback(update, "❌ Already processed or not found", show_alert=True)
        return
    with db.get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT user_id, amount FROM deposits WHERE deposit_id=?", (deposit_id,))
        dep = c.fetchone()
    if dep:
        try:
            await context.bot.send_message(
                chat_id=dep["user_id"],
                text=f"✅ <b>Deposit Confirmed!</b>\n\n💰 <b>${dep['amount']:.2f}</b> added to your balance.",
                parse_mode="HTML"
            )
        except Exception:
            pass
    db.add_admin_log(update.effective_user.id, "confirm_deposit", deposit_id)
    await safe_answer_callback(update, "✅ Deposit confirmed", show_alert=False)
    await admin_deposits(update, context)


async def admin_deposit_reject(update: Update, context: ContextTypes.DEFAULT_TYPE, deposit_id: str):
    with db.get_db() as conn:
        conn.execute("UPDATE deposits SET status='rejected' WHERE deposit_id=?", (deposit_id,))
        c = conn.cursor()
        c.execute("SELECT user_id FROM deposits WHERE deposit_id=?", (deposit_id,))
        dep = c.fetchone()
    if dep:
        try:
            await context.bot.send_message(
                chat_id=dep["user_id"],
                text="❌ <b>Deposit Rejected</b>\n\nContact support for help.",
                parse_mode="HTML"
            )
        except Exception:
            pass
    db.add_admin_log(update.effective_user.id, "reject_deposit", deposit_id)
    await safe_answer_callback(update, "❌ Deposit rejected", show_alert=False)
    await admin_deposits(update, context)


# ─────────────────────────────────────────────
#  ORDERS (admin)
# ─────────────────────────────────────────────

async def admin_orders(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 1):
    per_page = ADMIN_PANEL_ITEMS_PER_PAGE
    orders, total = db.get_all_orders_admin(page, per_page)
    total_pages = max(1, (total + per_page - 1) // per_page)
    rows = []
    for o in orders:
        status_e = {"completed": "✅", "pending": "⏳", "cancelled": "❌"}.get(o.get("status", ""), "❓")
        name = o.get("first_name") or f"User#{o['user_id']}"
        rows.append([InlineKeyboardButton(
            f"{status_e} {o.get('product_name', '?')[:30]} — {name[:15]}",
            callback_data=f"admin_order_detail:{o['order_id']}"
        )])
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("◀️ Prev", callback_data=f"admin_orders:{page-1}"))
    nav.append(InlineKeyboardButton(f"📄 {page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav.append(InlineKeyboardButton("▶️ Next", callback_data=f"admin_orders:{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton("◀️ Admin Panel", callback_data="admin")])
    text = f"📜 <b>All Orders</b> ({total} total) — Page {page}/{total_pages}"
    await safe_edit_message(update, text, InlineKeyboardMarkup(rows), "HTML")


# ─────────────────────────────────────────────
#  COUPONS
# ─────────────────────────────────────────────

async def admin_coupons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    coupons = db.get_all_coupons()
    text = f"🎟️ <b>Coupons</b> ({len(coupons)} total)"
    await safe_edit_message(update, text, admin_coupons_keyboard(coupons), "HTML")


async def admin_add_coupon_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["coupon_step"] = "code"
    context.user_data["coupon_data"] = {}
    await safe_edit_message(
        update, "🎟️ <b>Add Coupon</b>\n\nStep 1: Enter coupon code (e.g. SAVE20):",
        cancel_keyboard("admin_coupons"), "HTML"
    )


async def admin_coupon_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, coupon_id: int):
    with db.get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM coupons WHERE id=?", (coupon_id,))
        coupon = c.fetchone()
    if not coupon:
        await safe_answer_callback(update, "Not found", show_alert=True)
        return
    coupon = dict(coupon)
    active = "✅ Active" if coupon.get("is_active") else "❌ Inactive"
    text = (
        f"🎟️ <b>{coupon['code']}</b>\n"
        f"━━━━━━━━━━━━━━━━\n\n"
        f"💰 Discount: <b>{coupon['discount_value']}{'%' if coupon['discount_type']=='percentage' else '$'}</b>\n"
        f"🛒 Min Purchase: <b>${coupon.get('min_purchase', 0):.2f}</b>\n"
        f"🔢 Max Uses: <b>{'∞' if coupon.get('max_uses') == -1 else coupon.get('max_uses')}</b>\n"
        f"📊 Used: <b>{coupon.get('used_count', 0)}</b>\n"
        f"Status: <b>{active}</b>"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "🔴 Deactivate" if coupon.get("is_active") else "🟢 Activate",
            callback_data=f"admin_toggle_coupon:{coupon_id}"
        )],
        [InlineKeyboardButton("🗑️ Delete",    callback_data=f"admin_delete_coupon:{coupon_id}")],
        [InlineKeyboardButton("◀️ Back",      callback_data="admin_coupons")],
    ])
    await safe_edit_message(update, text, keyboard, "HTML")


# ─────────────────────────────────────────────
#  BROADCAST
# ─────────────────────────────────────────────

async def admin_broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data[UserState.ADMIN_BROADCAST] = True
    await safe_edit_message(
        update,
        "📢 <b>Broadcast Message</b>\n\nSend the message to broadcast to all users:",
        cancel_keyboard("admin"), "HTML"
    )


# ─────────────────────────────────────────────
#  LOGS
# ─────────────────────────────────────────────

async def admin_logs(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 1):
    logs, total = db.get_admin_logs(page, ADMIN_PANEL_ITEMS_PER_PAGE)
    total_pages = max(1, (total + ADMIN_PANEL_ITEMS_PER_PAGE - 1) // ADMIN_PANEL_ITEMS_PER_PAGE)
    if not logs:
        await safe_edit_message(update, "📋 <b>Admin Logs</b>\n\nNo logs yet.",
                                 back_to_admin_keyboard(), "HTML")
        return

    # Action → emoji mapping for a prettier log view
    ACTION_ICONS = {
        "purchase":          "🛒",
        "ban_user":          "🚫",
        "unban_user":        "✅",
        "adjust_balance":    "💰",
        "adjust_stars":      "⭐",
        "add_product":       "📦",
        "edit_product":      "✏️",
        "delete_product":    "🗑️",
        "toggle_product":    "🔄",
        "add_category":      "📂",
        "delete_category":   "🗑️",
        "confirm_deposit":   "✅",
        "reject_deposit":    "❌",
        "broadcast":         "📢",
        "backup_database":   "💾",
        "export_users":      "📤",
        "toggle_setting":    "⚙️",
        "edit_setting":      "✏️",
        "add_coupon":        "🎟️",
        "resend_delivery":   "🚚",
        "clear_errors":      "🛡️",
    }

    lines = []
    for log in logs:
        dt     = format_datetime(log.get("created_at", ""))
        action = log.get("action", "?")
        icon   = ACTION_ICONS.get(action, "🔹")
        admin  = log.get("admin_id", "?")
        detail = (log.get("details") or "")[:80]
        lines.append(
            f"{icon} <b>{action}</b>\n"
            f"   👤 <code>{admin}</code> · <code>{dt}</code>\n"
            f"   {detail}"
        )

    text = (
        f"📋 <b>Admin Logs</b>  <i>({total} total · page {page}/{total_pages})</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        + "\n\n".join(lines)
    )
    await safe_edit_message(update, text, admin_logs_keyboard(page, total_pages), "HTML")


# ─────────────────────────────────────────────
#  BACKUP / EXPORT
# ─────────────────────────────────────────────

async def admin_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        path = db.backup_database()
        await context.bot.send_document(
            chat_id=update.effective_user.id,
            document=open(path, "rb"),
            filename=path,
            caption="💾 Database backup"
        )
        os.remove(path)
        db.add_admin_log(update.effective_user.id, "backup_database", "DB backed up")
    except Exception as e:
        await safe_answer_callback(update, f"❌ Backup failed: {str(e)[:80]}", show_alert=True)


async def admin_export_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        path = db.export_users_csv()
        await context.bot.send_document(
            chat_id=update.effective_user.id,
            document=open(path, "rb"),
            filename=path,
            caption=f"📤 Users export ({path})"
        )
        os.remove(path)
        db.add_admin_log(update.effective_user.id, "export_users", "CSV exported")
    except Exception as e:
        await safe_answer_callback(update, f"❌ Export failed: {str(e)[:80]}", show_alert=True)


# ─────────────────────────────────────────────
#  TAKE DATABASE (send shop.db to admin)
# ─────────────────────────────────────────────

async def admin_take_database(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send the live shop.db file directly to the admin."""
    from config import DATABASE_PATH
    user = update.effective_user
    if not is_admin(user.id):
        await safe_answer_callback(update, "⛔ Access denied", show_alert=True)
        return
    try:
        db_path = DATABASE_PATH  # e.g. "shop.db" → resolves to home/container/shop.db
        if not os.path.exists(db_path):
            await safe_answer_callback(update, "❌ shop.db not found!", show_alert=True)
            return
        size_kb = os.path.getsize(db_path) / 1024
        await context.bot.send_document(
            chat_id=user.id,
            document=open(db_path, "rb"),
            filename="shop.db",
            caption=(
                f"💾 <b>shop.db</b>\n"
                f"📦 Size: <b>{size_kb:.1f} KB</b>\n\n"
                f"To restore: use <b>Upload Database</b> button."
            ),
            parse_mode="HTML"
        )
        db.add_admin_log(user.id, "take_database", f"shop.db sent ({size_kb:.1f} KB)")
        await safe_answer_callback(update, "✅ Database sent!", show_alert=False)
    except Exception as e:
        await safe_answer_callback(update, f"❌ Failed: {str(e)[:80]}", show_alert=True)


# ─────────────────────────────────────────────
#  UPLOAD DATABASE (receive .db file from admin)
# ─────────────────────────────────────────────

async def admin_upload_database_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompt admin to send a .db file to restore."""
    user = update.effective_user
    if not is_admin(user.id):
        await safe_answer_callback(update, "⛔ Access denied", show_alert=True)
        return
    context.user_data[UserState.ADMIN_UPLOAD_DB] = True
    await safe_edit_message(
        update,
        "📤 <b>Upload Database</b>\n\n"
        "Send the <code>shop.db</code> file now.\n\n"
        "⚠️ <b>Warning:</b> This will <u>replace</u> the current database!\n"
        "The file will be saved to <code>home/container/shop.db</code>.",
        cancel_keyboard("admin"),
        "HTML"
    )


async def admin_upload_database_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the incoming .db file and save it to home/container/shop.db."""
    from config import DATABASE_PATH
    user = update.effective_user
    doc = update.message.document

    # Validate file
    if not doc or not doc.file_name.endswith(".db"):
        await update.message.reply_text(
            "❌ Please send a valid <code>.db</code> file.",
            parse_mode="HTML"
        )
        return

    try:
        # Determine save path — always save to home/container/shop.db
        save_path = os.path.join(os.path.expanduser("~"), "container", "shop.db")
        # Fallback: if running in container root, just use the DATABASE_PATH
        if not os.path.isdir(os.path.dirname(save_path)):
            save_path = DATABASE_PATH  # saves next to current shop.db

        # Download the file
        tg_file = await context.bot.get_file(doc.file_id)
        await tg_file.download_to_drive(save_path)

        size_kb = os.path.getsize(save_path) / 1024
        db.add_admin_log(user.id, "upload_database", f"Restored shop.db ({size_kb:.1f} KB) → {save_path}")

        context.user_data.pop(UserState.ADMIN_UPLOAD_DB, None)
        await update.message.reply_text(
            f"✅ <b>Database restored!</b>\n\n"
            f"📦 File: <code>{save_path}</code>\n"
            f"📊 Size: <b>{size_kb:.1f} KB</b>\n\n"
            f"♻️ Restart the bot for changes to take effect.",
            parse_mode="HTML"
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ <b>Upload failed:</b> {str(e)[:200]}",
            parse_mode="HTML"
        )


# ─────────────────────────────────────────────
#  EDIT BOT FILE (upload .py or any file to replace on server)
# ─────────────────────────────────────────────

# Allowed extensions — expand as needed
EDITABLE_EXTENSIONS = {".py", ".txt", ".json", ".env", ".cfg", ".ini", ".yaml", ".yml"}

# Root directory of the bot (same folder as this file's parent)
BOT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Map filename → relative path inside the bot root
def _resolve_bot_file(filename: str):
    """
    Search for 'filename' recursively inside BOT_ROOT.
    Returns the absolute path if found, else None.
    Skips __pycache__ dirs.
    """
    for dirpath, dirnames, filenames in os.walk(BOT_ROOT):
        # skip cache dirs
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        if filename in filenames:
            return os.path.join(dirpath, filename)
    return None


async def admin_upload_file_start(update, context):
    """Prompt admin to send a bot file to replace."""
    user = update.effective_user
    if not is_admin(user.id):
        await safe_answer_callback(update, "⛔ Access denied", show_alert=True)
        return

    context.user_data[UserState.ADMIN_UPLOAD_FILE] = True
    await safe_edit_message(
        update,
        "📝 <b>Edit Bot File</b>\n\n"
        "Send any bot file (e.g. <code>helpers.py</code>, <code>strings.py</code>) "
        "and it will replace the current version on the server.\n\n"
        "✅ Allowed: <code>" + "</code>  <code>".join(EDITABLE_EXTENSIONS) + "</code>\n\n"
        "⚠️ <b>Warning:</b> The old file will be overwritten immediately.\n"
        "♻️ Restart the bot after editing for changes to take effect.",
        cancel_keyboard("admin"),
        "HTML"
    )


async def admin_upload_file_receive(update, context):
    """Handle the incoming file and overwrite the matching file in the bot tree."""
    user = update.effective_user
    doc = update.message.document

    if not doc:
        await update.message.reply_text("❌ Please send a file document.", parse_mode="HTML")
        return

    filename = doc.file_name or ""
    ext = os.path.splitext(filename)[1].lower()

    if ext not in EDITABLE_EXTENSIONS:
        await update.message.reply_text(
            f"❌ Extension <code>{ext}</code> is not allowed.\n"
            f"Allowed: <code>{'</code>  <code>'.join(EDITABLE_EXTENSIONS)}</code>",
            parse_mode="HTML"
        )
        return

    target_path = _resolve_bot_file(filename)

    if not target_path:
        await update.message.reply_text(
            f"❌ File <code>{filename}</code> was not found in the bot directory.\n\n"
            f"Only existing files can be replaced. "
            f"Make sure the filename matches exactly (case-sensitive).",
            parse_mode="HTML"
        )
        return

    try:
        tg_file = await context.bot.get_file(doc.file_id)
        await tg_file.download_to_drive(target_path)

        size_kb = os.path.getsize(target_path) / 1024
        rel_path = os.path.relpath(target_path, BOT_ROOT)

        db.add_admin_log(
            user.id, "edit_bot_file",
            f"Replaced {rel_path} ({size_kb:.1f} KB)"
        )

        context.user_data.pop(UserState.ADMIN_UPLOAD_FILE, None)

        await update.message.reply_text(
            f"✅ <b>File replaced!</b>\n\n"
            f"📄 <code>{rel_path}</code>\n"
            f"📦 Size: <b>{size_kb:.1f} KB</b>\n\n"
            f"♻️ Restart the bot for changes to take effect.",
            parse_mode="HTML"
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ <b>Failed:</b> {str(e)[:200]}",
            parse_mode="HTML"
        )
