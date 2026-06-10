"""
╔══════════════════════════════════════════════════════════╗
║     ADMIN USER MANAGEMENT — ADVANCED FILTER SYSTEM      ║
║   Filters · Notes · VIP · Bulk Actions · Profile Page   ║
╚══════════════════════════════════════════════════════════╝
"""

import io
import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import database as db
import database_user_mgmt as dum
from utils.helpers import (
    is_admin, safe_edit_message, safe_answer_callback,
    format_price, format_datetime, format_date, get_user_display_name,
    UserState,
)

logger = logging.getLogger(__name__)

PER_PAGE = 10


# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _admin_check(update: Update) -> bool:
    return is_admin(update.effective_user.id)


def _filters(context) -> dict:
    return context.user_data.setdefault("uf_filters", {})


def _clear_filters(context):
    context.user_data["uf_filters"] = {}
    context.user_data.pop("uf_sort", None)
    context.user_data.pop("uf_sort_dir", None)
    context.user_data.pop("uf_search", None)
    context.user_data.pop("uf_page", None)
    context.user_data.pop("uf_selected", None)


def _fmt_filters(filters: dict, search: str = None) -> str:
    if not filters and not search:
        return "None (showing all users)"
    parts = []
    if search:
        parts.append(f"🔍 Search: <code>{search}</code>")
    preset = filters.get("preset")
    if preset:
        labels = {
            "inactive": "⏸ Inactive (30d+)",
            "high_spenders": "💎 High Spenders",
            "new_users": "🆕 New (7d)",
            "has_referrals": "🔗 Has Referrals",
            "has_notes": "📝 Has Notes",
            "has_ticket": "🎫 Has Open Ticket",
            "has_pending_orders": "📦 Has Pending Orders",
        }
        parts.append(labels.get(preset, preset))
    if filters.get("balance_min") is not None:
        parts.append(f"💰 Bal ≥ ${filters['balance_min']}")
    if filters.get("balance_max") is not None:
        parts.append(f"💰 Bal ≤ ${filters['balance_max']}")
    if filters.get("spent_min") is not None:
        parts.append(f"💵 Spent ≥ ${filters['spent_min']}")
    if filters.get("orders_min") is not None:
        parts.append(f"🛒 Orders ≥ {filters['orders_min']}")
    if filters.get("language"):
        parts.append(f"🌍 Lang: {filters['language'].upper()}")
    if filters.get("is_banned") is True:
        parts.append("🚫 Banned only")
    elif filters.get("is_banned") is False:
        parts.append("✅ Active only")
    if filters.get("vip_rank") is not None:
        parts.append(f"👑 VIP: {dum.get_vip_label(filters['vip_rank'])}")
    if filters.get("has_used_coupon"):
        parts.append("🎟 Used coupon")
    return " · ".join(parts) if parts else "Custom"


def _paginator_row(page: int, total_pages: int, cb_prefix: str) -> list:
    row = []
    if page > 1:
        row.append(InlineKeyboardButton("◀️", callback_data=f"{cb_prefix}:{page-1}"))
    row.append(InlineKeyboardButton(f"📄 {page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        row.append(InlineKeyboardButton("▶️", callback_data=f"{cb_prefix}:{page+1}"))
    return row


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN USERS PANEL  (replaces old admin_users with filter/sort support)
# ─────────────────────────────────────────────────────────────────────────────

async def admin_users_advanced(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                page: int = 1):
    if not _admin_check(update):
        await safe_answer_callback(update, "⛔ Access denied", show_alert=True)
        return

    dum.init_user_mgmt_tables()
    filters = _filters(context)
    search  = context.user_data.get("uf_search", "")
    sort_by = context.user_data.get("uf_sort", "joined_at")
    sort_dir = context.user_data.get("uf_sort_dir", "DESC")
    context.user_data["uf_page"] = page

    users, total = dum.get_users_filtered(
        filters, page=page, per_page=PER_PAGE,
        sort_by=sort_by, sort_dir=sort_dir, search=search
    )
    total_pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)

    active_filters = _fmt_filters(filters, search)
    sort_label = {
        "joined_at":    "Join Date",
        "last_seen":    "Last Seen",
        "balance":      "Balance",
        "total_spent":  "Total Spent",
        "total_orders": "Orders",
    }.get(sort_by, sort_by)

    text = (
        f"👥 <b>User Management</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 Showing <b>{len(users)}</b> of <b>{total}</b> users\n"
        f"🔽 Sort: <b>{sort_label} {sort_dir}</b>\n"
        f"🎯 Filters: <i>{active_filters}</i>"
    )

    rows = []

    for u in users:
        ban_icon = "🚫" if u.get("is_banned") else "✅"
        name = (u.get("first_name") or f"User#{u['user_id']}")[:18]
        bal = f"${u.get('balance', 0):.2f}"
        vip = u.get("vip_rank", 0)
        vip_tag = f" {dum.get_vip_label(vip)}" if vip else ""
        uname = f"@{u['username']}" if u.get("username") else ""
        rows.append([InlineKeyboardButton(
            f"{ban_icon} {name}{vip_tag} — {bal}",
            callback_data=f"uf_profile:{u['user_id']}"
        )])

    # Navigation
    nav = _paginator_row(page, total_pages, "uf_page")
    if nav:
        rows.append(nav)

    # Controls
    rows.append([
        InlineKeyboardButton("🔍 Search",    callback_data="uf_search_start"),
        InlineKeyboardButton("🎯 Filter",    callback_data="uf_filter_menu"),
        InlineKeyboardButton("🔃 Sort",      callback_data="uf_sort_menu"),
    ])
    rows.append([
        InlineKeyboardButton("⚡ Bulk Actions", callback_data="uf_bulk_menu"),
        InlineKeyboardButton("🧹 Clear",        callback_data="uf_clear_filters"),
    ])
    rows.append([InlineKeyboardButton("◀️ Admin Panel", callback_data="admin")])

    await safe_edit_message(update, text, InlineKeyboardMarkup(rows), "HTML")


# ─────────────────────────────────────────────────────────────────────────────
#  FILTER MENU
# ─────────────────────────────────────────────────────────────────────────────

async def uf_filter_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _admin_check(update):
        return
    filters = _filters(context)
    active = _fmt_filters(filters)
    text = (
        f"🎯 <b>User Filters</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Active: <i>{active}</i>\n\n"
        f"Choose a filter category:"
    )
    rows = [
        [InlineKeyboardButton("⚡ Quick Presets",    callback_data="uf_presets")],
        [InlineKeyboardButton("💰 Balance Range",    callback_data="uf_fset:balance_min"),
         InlineKeyboardButton("💵 Spent Range",      callback_data="uf_fset:spent_min")],
        [InlineKeyboardButton("🛒 Order Count",      callback_data="uf_fset:orders_min"),
         InlineKeyboardButton("🌍 Language",         callback_data="uf_lang_menu")],
        [InlineKeyboardButton("👑 VIP Rank",         callback_data="uf_vip_filter"),
         InlineKeyboardButton("🚫 Ban Status",       callback_data="uf_ban_filter")],
        [InlineKeyboardButton("📅 Join Date",        callback_data="uf_fset:joined_after"),
         InlineKeyboardButton("🕐 Last Active",      callback_data="uf_fset:seen_after")],
        [InlineKeyboardButton("🎟 Used Coupon",      callback_data="uf_toggle:has_used_coupon"),
         InlineKeyboardButton("🧹 Clear All",        callback_data="uf_clear_filters")],
        [InlineKeyboardButton("✅ Apply Filters",    callback_data="uf_page:1")],
        [InlineKeyboardButton("◀️ Back",             callback_data="uf_page:1")],
    ]
    await safe_edit_message(update, text, InlineKeyboardMarkup(rows), "HTML")


async def uf_presets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _admin_check(update):
        return
    rows = [
        [InlineKeyboardButton("⏸ Inactive Users (30d+)", callback_data="uf_preset:inactive")],
        [InlineKeyboardButton("💎 High Spenders",         callback_data="uf_preset:high_spenders")],
        [InlineKeyboardButton("🆕 New Users (7d)",        callback_data="uf_preset:new_users")],
        [InlineKeyboardButton("🔗 Has Referrals",         callback_data="uf_preset:has_referrals")],
        [InlineKeyboardButton("📝 Has Admin Notes",       callback_data="uf_preset:has_notes")],
        [InlineKeyboardButton("🎫 Has Open Ticket",       callback_data="uf_preset:has_ticket")],
        [InlineKeyboardButton("📦 Has Pending Orders",    callback_data="uf_preset:has_pending_orders")],
        [InlineKeyboardButton("◀️ Back",                  callback_data="uf_filter_menu")],
    ]
    await safe_edit_message(update, "⚡ <b>Quick Presets</b>\n\nSelect a preset filter:",
                             InlineKeyboardMarkup(rows), "HTML")


async def uf_lang_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _admin_check(update):
        return
    rows = [
        [InlineKeyboardButton("🇬🇧 English",  callback_data="uf_setlang:en"),
         InlineKeyboardButton("🇸🇦 Arabic",   callback_data="uf_setlang:ar")],
        [InlineKeyboardButton("🇫🇷 French",   callback_data="uf_setlang:fr"),
         InlineKeyboardButton("🌍 Any",       callback_data="uf_setlang:any")],
        [InlineKeyboardButton("◀️ Back",      callback_data="uf_filter_menu")],
    ]
    await safe_edit_message(update, "🌍 <b>Filter by Language</b>",
                             InlineKeyboardMarkup(rows), "HTML")


async def uf_vip_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _admin_check(update):
        return
    rows = []
    for rank, label in dum.VIP_LABELS.items():
        rows.append([InlineKeyboardButton(label, callback_data=f"uf_setvip:{rank}")])
    rows.append([InlineKeyboardButton("◀️ Back", callback_data="uf_filter_menu")])
    await safe_edit_message(update, "👑 <b>Filter by VIP Rank</b>",
                             InlineKeyboardMarkup(rows), "HTML")


async def uf_ban_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _admin_check(update):
        return
    rows = [
        [InlineKeyboardButton("✅ Active Users Only",  callback_data="uf_setban:0"),
         InlineKeyboardButton("🚫 Banned Users Only",  callback_data="uf_setban:1")],
        [InlineKeyboardButton("👥 All Users",          callback_data="uf_setban:all")],
        [InlineKeyboardButton("◀️ Back",               callback_data="uf_filter_menu")],
    ]
    await safe_edit_message(update, "🚫 <b>Filter by Ban Status</b>",
                             InlineKeyboardMarkup(rows), "HTML")


# ─────────────────────────────────────────────────────────────────────────────
#  SORT MENU
# ─────────────────────────────────────────────────────────────────────────────

async def uf_sort_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _admin_check(update):
        return
    current = context.user_data.get("uf_sort", "joined_at")
    direction = context.user_data.get("uf_sort_dir", "DESC")
    rows = [
        [InlineKeyboardButton("📅 Join Date",   callback_data="uf_setsort:joined_at"),
         InlineKeyboardButton("🕐 Last Seen",   callback_data="uf_setsort:last_seen")],
        [InlineKeyboardButton("💰 Balance",     callback_data="uf_setsort:balance"),
         InlineKeyboardButton("💵 Total Spent", callback_data="uf_setsort:total_spent")],
        [InlineKeyboardButton("🛒 Orders",      callback_data="uf_setsort:total_orders"),
         InlineKeyboardButton("📛 Username",    callback_data="uf_setsort:username")],
        [InlineKeyboardButton(
            f"🔃 Direction: {'⬇️ DESC' if direction=='DESC' else '⬆️ ASC'}",
            callback_data="uf_toggle_dir"
        )],
        [InlineKeyboardButton("◀️ Back", callback_data="uf_page:1")],
    ]
    current_label = {
        "joined_at": "Join Date", "last_seen": "Last Seen",
        "balance": "Balance", "total_spent": "Total Spent",
        "total_orders": "Orders", "username": "Username",
    }.get(current, current)
    await safe_edit_message(
        update,
        f"🔃 <b>Sort Users</b>\n\nCurrent: <b>{current_label} {direction}</b>",
        InlineKeyboardMarkup(rows), "HTML"
    )


# ─────────────────────────────────────────────────────────────────────────────
#  USER PROFILE PAGE
# ─────────────────────────────────────────────────────────────────────────────

async def uf_user_profile(update: Update, context: ContextTypes.DEFAULT_TYPE,
                           target_id: int):
    if not _admin_check(update):
        return

    dum.init_user_mgmt_tables()
    profile = dum.get_user_full_profile(target_id)
    if not profile:
        await safe_answer_callback(update, "User not found", show_alert=True)
        return

    name = profile.get("first_name") or f"User#{target_id}"
    uname = f"@{profile['username']}" if profile.get("username") else "—"
    ban_status = "🚫 Banned" if profile.get("is_banned") else "✅ Active"
    vip_str = profile.get("vip_label", "None")
    notes = profile.get("admin_notes", [])
    notes_str = ""
    if notes:
        for n in notes[:3]:
            ts = n.get("created_at", "")[:10]
            admin_n = n.get("admin_name", "Admin")
            notes_str += f"\n  📝 [{ts}] {admin_n}: {n['note'][:60]}"
    else:
        notes_str = "\n  — No notes"

    text = (
        f"👤 <b>User Profile</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📛 <b>{name}</b> {uname}\n"
        f"🆔 <code>{target_id}</code>\n"
        f"🌍 Language: <b>{profile.get('language','en').upper()}</b>\n"
        f"👑 VIP: <b>{vip_str}</b>\n"
        f"Status: <b>{ban_status}</b>\n\n"
        f"━━ 💰 Financials ━━\n"
        f"💰 Balance:     <b>${format_price(profile.get('balance', 0))}</b>\n"
        f"⭐ Stars:       <b>{profile.get('stars_balance', 0):,}</b>\n"
        f"💵 Total Spent: <b>${format_price(profile.get('total_spent', 0))}</b>\n\n"
        f"━━ 📊 Activity ━━\n"
        f"🛒 Orders:      <b>{profile.get('total_orders', 0)}</b> total, "
        f"<b>{profile.get('pending_orders', 0)}</b> pending\n"
        f"🔗 Referrals:   <b>{profile.get('ref_count', 0)}</b> "
        f"(earned ${format_price(profile.get('ref_earned', 0))})\n"
        f"🎟 Coupons used: <b>{profile.get('coupons_used', 0)}</b>\n"
        f"🎫 Open tickets: <b>{profile.get('open_tickets', 0)}</b>\n\n"
        f"━━ 📅 Dates ━━\n"
        f"📅 Joined:     <b>{format_date(profile.get('joined_at',''))}</b>\n"
        f"🕐 Last seen:  <b>{format_date(profile.get('last_seen',''))}</b>\n"
        f"🔑 Ref code:   <code>{profile.get('referral_code','—')}</code>\n\n"
        f"━━ 📝 Admin Notes ({len(notes)}) ━━{notes_str}"
    )

    is_banned = bool(profile.get("is_banned"))
    ban_label = "✅ Unban" if is_banned else "🚫 Ban"
    ban_cb = f"admin_unban:{target_id}" if is_banned else f"admin_ban:{target_id}"
    vip_rank = profile.get("vip_rank", 0)

    rows = [
        [InlineKeyboardButton(ban_label,            callback_data=ban_cb),
         InlineKeyboardButton("💰 Balance",         callback_data=f"admin_adjust:{target_id}")],
        [InlineKeyboardButton("⭐ Stars",            callback_data=f"admin_adjust_stars:{target_id}"),
         InlineKeyboardButton("📜 Orders",          callback_data=f"admin_user_orders:{target_id}")],
        [InlineKeyboardButton("📝 Manage Notes",    callback_data=f"uf_notes:{target_id}"),
         InlineKeyboardButton("👑 Set VIP",         callback_data=f"uf_setvip_user:{target_id}")],
        [InlineKeyboardButton("◀️ Users",           callback_data=f"uf_page:{context.user_data.get('uf_page',1)}")],
    ]

    await safe_edit_message(update, text, InlineKeyboardMarkup(rows), "HTML")


# ─────────────────────────────────────────────────────────────────────────────
#  ADMIN NOTES MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

async def uf_notes_page(update: Update, context: ContextTypes.DEFAULT_TYPE,
                         target_id: int):
    if not _admin_check(update):
        return

    dum.init_user_mgmt_tables()
    user = db.get_user(target_id)
    if not user:
        await safe_answer_callback(update, "User not found", show_alert=True)
        return

    notes = dum.get_admin_notes(target_id)
    name = user.get("first_name") or f"User#{target_id}"

    text = f"📝 <b>Admin Notes — {name}</b>\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    rows = []

    if notes:
        for n in notes:
            ts = n.get("created_at", "")[:16]
            admin_n = n.get("admin_name", "Admin")
            note_preview = n["note"][:50] + ("…" if len(n["note"]) > 50 else "")
            text += f"📎 [{ts}] <b>{admin_n}</b>:\n  {note_preview}\n\n"
            rows.append([
                InlineKeyboardButton(f"✏️ Edit #{n['id']}", callback_data=f"uf_note_edit:{n['id']}:{target_id}"),
                InlineKeyboardButton(f"🗑 Delete",          callback_data=f"uf_note_del:{n['id']}:{target_id}"),
            ])
    else:
        text += "No notes yet."

    rows.append([InlineKeyboardButton("➕ Add Note", callback_data=f"uf_note_add:{target_id}")])
    rows.append([InlineKeyboardButton("◀️ Back", callback_data=f"uf_profile:{target_id}")])

    await safe_edit_message(update, text, InlineKeyboardMarkup(rows), "HTML")


async def uf_note_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE,
                              target_id: int):
    if not _admin_check(update):
        return
    context.user_data["uf_note_target"] = target_id
    context.user_data[UserState.ADMIN_SEARCH_USER] = False  # don't conflict
    context.user_data["uf_state"] = "add_note"
    await safe_edit_message(
        update,
        f"📝 <b>Add Note</b> for user <code>{target_id}</code>\n\n"
        f"Suggested tags: trusted buyer · refund abuse · VIP customer · reseller · support issue\n\n"
        f"Type your note:",
        InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Cancel", callback_data=f"uf_notes:{target_id}")
        ]]),
        "HTML"
    )


async def uf_note_edit_start(update: Update, context: ContextTypes.DEFAULT_TYPE,
                               note_id: int, target_id: int):
    if not _admin_check(update):
        return
    note = dum.get_admin_note(note_id)
    if not note:
        await safe_answer_callback(update, "Note not found", show_alert=True)
        return
    context.user_data["uf_state"] = "edit_note"
    context.user_data["uf_note_id"] = note_id
    context.user_data["uf_note_target"] = target_id
    await safe_edit_message(
        update,
        f"✏️ <b>Edit Note #{note_id}</b>\n\nCurrent: <i>{note['note']}</i>\n\nType new text:",
        InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Cancel", callback_data=f"uf_notes:{target_id}")
        ]]),
        "HTML"
    )


async def uf_note_delete(update: Update, context: ContextTypes.DEFAULT_TYPE,
                          note_id: int, target_id: int):
    if not _admin_check(update):
        return
    dum.delete_admin_note(note_id)
    await safe_answer_callback(update, "🗑 Note deleted")
    await uf_notes_page(update, context, target_id)


# ─────────────────────────────────────────────────────────────────────────────
#  VIP ASSIGNMENT
# ─────────────────────────────────────────────────────────────────────────────

async def uf_setvip_user(update: Update, context: ContextTypes.DEFAULT_TYPE,
                          target_id: int):
    if not _admin_check(update):
        return
    rows = []
    for rank, label in dum.VIP_LABELS.items():
        rows.append([InlineKeyboardButton(
            f"{'✅ ' if rank else '❌ '}Set {label}",
            callback_data=f"uf_dovip:{target_id}:{rank}"
        )])
    rows.append([InlineKeyboardButton("◀️ Back", callback_data=f"uf_profile:{target_id}")])
    await safe_edit_message(
        update,
        f"👑 <b>Set VIP for <code>{target_id}</code></b>",
        InlineKeyboardMarkup(rows), "HTML"
    )


# ─────────────────────────────────────────────────────────────────────────────
#  SEARCH
# ─────────────────────────────────────────────────────────────────────────────

async def uf_search_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _admin_check(update):
        return
    context.user_data["uf_state"] = "search"
    current = context.user_data.get("uf_search", "")
    hint = f"\nCurrent: <code>{current}</code>" if current else ""
    await safe_edit_message(
        update,
        f"🔍 <b>Search Users</b>{hint}\n\n"
        f"You can search by:\n"
        f"• Telegram User ID (numbers only)\n"
        f"• Username (partial match)\n"
        f"• Referral code\n"
        f"• Admin note keywords\n\n"
        f"Type your search query:",
        InlineKeyboardMarkup([[
            InlineKeyboardButton("🧹 Clear Search", callback_data="uf_clear_search"),
            InlineKeyboardButton("◀️ Cancel",        callback_data="uf_page:1"),
        ]]),
        "HTML"
    )


# ─────────────────────────────────────────────────────────────────────────────
#  BULK ACTIONS
# ─────────────────────────────────────────────────────────────────────────────

async def uf_bulk_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _admin_check(update):
        return
    filters = _filters(context)
    search  = context.user_data.get("uf_search", "")
    _, total = dum.get_users_filtered(filters, page=1, per_page=1, search=search)
    active_filters = _fmt_filters(filters, search)

    text = (
        f"⚡ <b>Bulk Actions</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Target: <b>{total} users</b>\n"
        f"Filters: <i>{active_filters}</i>\n\n"
        f"⚠️ Actions apply to ALL matching users."
    )

    rows = [
        [InlineKeyboardButton("📢 Broadcast Message",  callback_data="uf_bulk_broadcast")],
        [InlineKeyboardButton("💰 Give Balance",       callback_data="uf_bulk_action:give_balance"),
         InlineKeyboardButton("➖ Remove Balance",     callback_data="uf_bulk_action:remove_balance")],
        [InlineKeyboardButton("🚫 Ban All",            callback_data="uf_bulk_confirm:ban"),
         InlineKeyboardButton("✅ Unban All",          callback_data="uf_bulk_confirm:unban")],
        [InlineKeyboardButton("👑 Assign VIP",         callback_data="uf_bulk_vip"),
         InlineKeyboardButton("📝 Add Note to All",    callback_data="uf_bulk_action:add_note")],
        [InlineKeyboardButton("📥 Export CSV",         callback_data="uf_bulk_export")],
        [InlineKeyboardButton("◀️ Back",               callback_data="uf_page:1")],
    ]
    await safe_edit_message(update, text, InlineKeyboardMarkup(rows), "HTML")


async def uf_bulk_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE,
                           action: str):
    if not _admin_check(update):
        return
    filters = _filters(context)
    search  = context.user_data.get("uf_search", "")
    _, total = dum.get_users_filtered(filters, page=1, per_page=1, search=search)

    action_label = {
        "ban":   "🚫 BAN",
        "unban": "✅ UNBAN",
    }.get(action, action.upper())

    text = (
        f"⚠️ <b>Confirm Bulk Action</b>\n\n"
        f"Action: <b>{action_label}</b>\n"
        f"Affects: <b>{total} users</b>\n\n"
        f"This action <b>cannot be undone</b>. Are you sure?"
    )
    if action == "ban":
        rows = [
            [InlineKeyboardButton("✅ Yes, Ban All",    callback_data=f"uf_bulk_do:ban"),
             InlineKeyboardButton("❌ Cancel",          callback_data="uf_bulk_menu")],
        ]
    else:
        rows = [
            [InlineKeyboardButton("✅ Yes, Unban All",  callback_data=f"uf_bulk_do:unban"),
             InlineKeyboardButton("❌ Cancel",          callback_data="uf_bulk_menu")],
        ]
    await safe_edit_message(update, text, InlineKeyboardMarkup(rows), "HTML")


async def uf_bulk_do(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str):
    if not _admin_check(update):
        return
    filters = _filters(context)
    search  = context.user_data.get("uf_search", "")
    admin_id = update.effective_user.id

    all_users = dum.export_users_filtered(filters, search=search)
    user_ids = [u["user_id"] for u in all_users]

    if not user_ids:
        await safe_answer_callback(update, "No users match the current filters.", show_alert=True)
        return

    if action == "ban":
        count = dum.bulk_ban(user_ids, "Bulk admin action", admin_id)
        await safe_answer_callback(update, f"🚫 Banned {count} users", show_alert=True)
    elif action == "unban":
        count = dum.bulk_unban(user_ids, admin_id)
        await safe_answer_callback(update, f"✅ Unbanned {count} users", show_alert=True)

    await admin_users_advanced(update, context, 1)


async def uf_bulk_action_start(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                action: str):
    if not _admin_check(update):
        return
    filters = _filters(context)
    search  = context.user_data.get("uf_search", "")
    _, total = dum.get_users_filtered(filters, page=1, per_page=1, search=search)

    context.user_data["uf_bulk_action"] = action
    context.user_data["uf_state"] = f"bulk_{action}"

    prompts = {
        "give_balance":    f"💰 Enter amount to <b>give</b> to {total} users (e.g. 5.00):",
        "remove_balance":  f"➖ Enter amount to <b>remove</b> from {total} users (e.g. 3.00):",
        "add_note":        f"📝 Enter note to add to <b>{total} users</b>:",
    }
    await safe_edit_message(
        update,
        f"⚡ <b>Bulk: {action.replace('_', ' ').title()}</b>\n\n"
        f"{prompts.get(action, 'Enter value:')}",
        InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Cancel", callback_data="uf_bulk_menu")
        ]]),
        "HTML"
    )


async def uf_bulk_vip_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _admin_check(update):
        return
    filters = _filters(context)
    search  = context.user_data.get("uf_search", "")
    _, total = dum.get_users_filtered(filters, page=1, per_page=1, search=search)
    rows = []
    for rank, label in dum.VIP_LABELS.items():
        rows.append([InlineKeyboardButton(
            f"Set {label} for {total} users",
            callback_data=f"uf_bulk_dovip:{rank}"
        )])
    rows.append([InlineKeyboardButton("◀️ Cancel", callback_data="uf_bulk_menu")])
    await safe_edit_message(update, "👑 <b>Bulk Set VIP Rank</b>",
                             InlineKeyboardMarkup(rows), "HTML")


async def uf_bulk_dovip(update: Update, context: ContextTypes.DEFAULT_TYPE, rank: int):
    if not _admin_check(update):
        return
    filters = _filters(context)
    search  = context.user_data.get("uf_search", "")
    admin_id = update.effective_user.id
    all_users = dum.export_users_filtered(filters, search=search)
    user_ids = [u["user_id"] for u in all_users]
    count = dum.bulk_set_vip(user_ids, rank, admin_id)
    label = dum.get_vip_label(rank)
    await safe_answer_callback(update, f"👑 Set {label} for {count} users", show_alert=True)
    await admin_users_advanced(update, context, 1)


async def uf_bulk_export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _admin_check(update):
        return
    filters = _filters(context)
    search  = context.user_data.get("uf_search", "")
    await safe_answer_callback(update, "📥 Generating CSV…")

    all_users = dum.export_users_filtered(filters, search=search)
    # Add VIP rank to exported data
    for u in all_users:
        vip = dum.get_user_vip(u["user_id"])
        u["vip_rank"] = vip["vip_rank"] if vip else 0

    csv_text = dum.users_to_csv(all_users)
    bio = io.BytesIO(csv_text.encode("utf-8"))
    bio.name = f"users_export_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    bio.seek(0)

    try:
        await update.effective_message.reply_document(
            document=bio,
            filename=bio.name,
            caption=f"📥 Exported <b>{len(all_users)}</b> users\nFilters: {_fmt_filters(filters, search)}",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"CSV export error: {e}")
        await safe_answer_callback(update, "❌ Export failed", show_alert=True)


# ─────────────────────────────────────────────────────────────────────────────
#  MESSAGE HANDLER  (called from message_handlers.py for text inputs)
# ─────────────────────────────────────────────────────────────────────────────

async def uf_handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Intercept text messages for user-management states.
    Returns True if consumed (caller should return early).
    """
    if not is_admin(update.effective_user.id):
        return False

    state = context.user_data.get("uf_state")
    if not state:
        return False

    text = update.message.text.strip()
    admin = update.effective_user
    admin_name = admin.first_name or f"Admin#{admin.id}"

    # ── Search ───────────────────────────────────────────────────────────────
    if state == "search":
        context.user_data.pop("uf_state")
        context.user_data["uf_search"] = text
        context.user_data["uf_page"] = 1
        await admin_users_advanced(update, context, 1)
        return True

    # ── Add note ─────────────────────────────────────────────────────────────
    if state == "add_note":
        context.user_data.pop("uf_state")
        target_id = context.user_data.pop("uf_note_target", None)
        if not target_id:
            return False
        dum.add_admin_note(target_id, admin.id, admin_name, text)
        db.add_admin_log(admin.id, "add_note", f"Note for {target_id}: {text[:50]}", target_id)
        await update.message.reply_text("✅ Note added.", parse_mode="HTML")
        await uf_notes_page(update, context, target_id)
        return True

    # ── Edit note ────────────────────────────────────────────────────────────
    if state == "edit_note":
        context.user_data.pop("uf_state")
        note_id   = context.user_data.pop("uf_note_id", None)
        target_id = context.user_data.pop("uf_note_target", None)
        if not note_id or not target_id:
            return False
        dum.edit_admin_note(note_id, text)
        await update.message.reply_text("✅ Note updated.", parse_mode="HTML")
        await uf_notes_page(update, context, target_id)
        return True

    # ── Bulk: give/remove balance ─────────────────────────────────────────────
    if state in ("bulk_give_balance", "bulk_remove_balance"):
        context.user_data.pop("uf_state")
        try:
            amount = float(text.replace("+", "").replace(",", "."))
        except ValueError:
            await update.message.reply_text("❌ Invalid amount. Enter a number like 5.00")
            return True
        if state == "bulk_remove_balance":
            amount = -abs(amount)
        filters = _filters(context)
        search  = context.user_data.get("uf_search", "")
        all_users = dum.export_users_filtered(filters, search=search)
        user_ids = [u["user_id"] for u in all_users]
        count = dum.bulk_adjust_balance(user_ids, amount, admin.id)
        action_word = "given to" if amount >= 0 else "removed from"
        await update.message.reply_text(
            f"✅ <b>${abs(amount):.2f} {action_word} {count} users.</b>",
            parse_mode="HTML"
        )
        await admin_users_advanced(update, context, 1)
        return True

    # ── Bulk: add note ────────────────────────────────────────────────────────
    if state == "bulk_add_note":
        context.user_data.pop("uf_state")
        filters = _filters(context)
        search  = context.user_data.get("uf_search", "")
        all_users = dum.export_users_filtered(filters, search=search)
        user_ids = [u["user_id"] for u in all_users]
        count = dum.bulk_add_note(user_ids, text, admin.id, admin_name)
        await update.message.reply_text(
            f"✅ <b>Note added to {count} users.</b>", parse_mode="HTML"
        )
        await admin_users_advanced(update, context, 1)
        return True

    return False
