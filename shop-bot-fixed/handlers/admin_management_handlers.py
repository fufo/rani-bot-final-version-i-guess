"""
╔══════════════════════════════════════════════════════════╗
║     TELEGRAM SHOP BOT - ADMIN MANAGEMENT PANEL           ║
║   Add/remove admins, permissions, owner protection       ║
╚══════════════════════════════════════════════════════════╝
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import database as db
from config import PRIMARY_ADMIN_ID
from utils.helpers import (
    safe_edit_message, safe_answer_callback, UserState,
    format_datetime, is_owner
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
#  ADMIN MANAGEMENT PANEL
# ─────────────────────────────────────────────

async def admin_management_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admins = db.get_all_admins()
    lines = []
    for a in admins:
        crown = "👑" if a["user_id"] == PRIMARY_ADMIN_ID else "🛡️"
        name = a.get("first_name") or f"User#{a['user_id']}"
        username = f"@{a['username']}" if a.get("username") else ""
        lines.append(f"{crown} <b>{name}</b> {username}\n   <code>{a['user_id']}</code>")

    text = (
        "👑 <b>Admin Management</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Total admins: <b>{len(admins)}</b>\n\n"
        + ("\n\n".join(lines) if lines else "No admins found.")
    )

    rows = []
    for a in admins:
        crown = "👑" if a["user_id"] == PRIMARY_ADMIN_ID else "🛡️"
        name = a.get("first_name") or f"User#{a['user_id']}"
        rows.append([InlineKeyboardButton(
            f"{crown} {name}",
            callback_data=f"adm:detail:{a['user_id']}"
        )])

    rows.extend([
        [InlineKeyboardButton("➕ Add Admin",  callback_data="adm:add"),
         InlineKeyboardButton("🔄 Refresh",   callback_data="cfg:admins")],
        [InlineKeyboardButton("◀️ Settings",   callback_data="admin_settings")],
    ])
    await safe_edit_message(update, text, InlineKeyboardMarkup(rows), "HTML")


# ─────────────────────────────────────────────
#  ADMIN DETAIL
# ─────────────────────────────────────────────

async def admin_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int):
    admins = db.get_all_admins()
    a = next((x for x in admins if x["user_id"] == target_id), None)
    if not a:
        await safe_answer_callback(update, "Admin not found", show_alert=True)
        return

    is_primary = target_id == PRIMARY_ADMIN_ID
    name = a.get("first_name") or f"User#{target_id}"
    username = f"@{a['username']}" if a.get("username") else "—"

    text = (
        f"{'👑' if is_primary else '🛡️'} <b>Admin Detail</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 Name: <b>{name}</b>\n"
        f"📛 Username: {username}\n"
        f"🆔 ID: <code>{target_id}</code>\n"
        f"🔑 Permissions: <b>{a.get('permissions', 'all')}</b>\n"
        f"📅 Added: <b>{format_datetime(a.get('added_at', ''))}</b>\n"
        f"{'👑 Primary Owner — cannot be removed' if is_primary else ''}"
    )

    rows = []
    if not is_primary:
        rows.append([InlineKeyboardButton(
            "🗑️ Remove Admin",
            callback_data=f"adm:remove:{target_id}"
        )])
    rows.append([InlineKeyboardButton("◀️ Back", callback_data="cfg:admins")])
    await safe_edit_message(update, text, InlineKeyboardMarkup(rows), "HTML")


# ─────────────────────────────────────────────
#  ADD ADMIN (start)
# ─────────────────────────────────────────────

async def add_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        await safe_answer_callback(update, "⛔ Only the owner can add admins", show_alert=True)
        return
    context.user_data[UserState.ADMIN_ADD_ADMIN] = True
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✖️ Cancel", callback_data="cfg:admins")
    ]])
    await safe_edit_message(
        update,
        "➕ <b>Add New Admin</b>\n\n"
        "Send the Telegram <b>User ID</b> of the new admin:\n\n"
        "<i>The user must have started the bot first.\n"
        "You can get someone's ID via @userinfobot</i>",
        keyboard, "HTML"
    )


# ─────────────────────────────────────────────
#  REMOVE ADMIN
# ─────────────────────────────────────────────

async def remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int):
    if not is_owner(update.effective_user.id):
        await safe_answer_callback(update, "⛔ Only the owner can remove admins", show_alert=True)
        return
    if target_id == PRIMARY_ADMIN_ID:
        await safe_answer_callback(update, "⛔ Cannot remove primary owner", show_alert=True)
        return
    success = db.remove_admin(target_id)
    if success:
        db.add_admin_log(update.effective_user.id, "remove_admin",
                         f"Removed admin {target_id}", target_id)
        await safe_answer_callback(update, "✅ Admin removed", show_alert=False)
    else:
        await safe_answer_callback(update, "❌ Failed to remove", show_alert=True)
    await admin_management_panel(update, context)
