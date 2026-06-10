"""
╔══════════════════════════════════════════════════════════╗
║     TELEGRAM SHOP BOT - FORCE SUBSCRIBE MANAGER          ║
║   Multi-channel subscribe system, fully DB-driven        ║
╚══════════════════════════════════════════════════════════╝
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import database as db
from utils.helpers import safe_edit_message, safe_answer_callback, UserState

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
#  FORCE SUBSCRIBE PANEL
# ─────────────────────────────────────────────

async def force_subscribe_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    enabled = db.get_setting("force_subscribe", False)
    channels = db.get_force_channels(active_only=False)
    status = "✅ ON" if enabled else "❌ OFF"

    lines = []
    for ch in channels:
        icon = "🟢" if ch.get("is_active") else "🔴"
        lines.append(f"{icon} @{ch['username']}")

    ch_text = "\n".join(lines) if lines else "  No channels added yet."

    text = (
        "📌 <b>Force Subscribe Manager</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Status: <b>{status}</b>\n"
        f"Channels: <b>{len(channels)}</b>\n\n"
        f"<b>Channel List:</b>\n{ch_text}"
    )

    rows = [
        [InlineKeyboardButton(
            f"{'❌ Disable' if enabled else '✅ Enable'} Force Subscribe",
            callback_data="fs:toggle"
        )],
        [InlineKeyboardButton("➕ Add Channel",   callback_data="fs:add"),
         InlineKeyboardButton("🔄 Refresh",       callback_data="cfg:force_sub")],
    ]

    for ch in channels:
        icon = "🟢" if ch.get("is_active") else "🔴"
        rows.append([
            InlineKeyboardButton(
                f"{icon} @{ch['username']}",
                callback_data=f"fs:detail:{ch['id']}"
            )
        ])

    rows.append([InlineKeyboardButton("✏️ Edit Join Message", callback_data="stg:edit:join_message")])
    rows.append([InlineKeyboardButton("◀️ Settings",           callback_data="admin_settings")])

    await safe_edit_message(update, text, InlineKeyboardMarkup(rows), "HTML")


# ─────────────────────────────────────────────
#  CHANNEL DETAIL
# ─────────────────────────────────────────────

async def channel_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, channel_id: int):
    channels = db.get_force_channels(active_only=False)
    ch = next((c for c in channels if c["id"] == channel_id), None)
    if not ch:
        await safe_answer_callback(update, "Channel not found", show_alert=True)
        return

    icon = "🟢 Active" if ch.get("is_active") else "🔴 Inactive"
    text = (
        f"📡 <b>Channel Detail</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📛 Username: @{ch['username']}\n"
        f"🔗 Link: {ch.get('link', '—')}\n"
        f"📌 Status: <b>{icon}</b>"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "🔴 Deactivate" if ch.get("is_active") else "🟢 Activate",
            callback_data=f"fs:toggle_ch:{channel_id}"
        )],
        [InlineKeyboardButton("✏️ Edit Link",   callback_data=f"fs:edit_link:{channel_id}"),
         InlineKeyboardButton("🗑️ Remove",      callback_data=f"fs:remove:{channel_id}")],
        [InlineKeyboardButton("◀️ Back",        callback_data="cfg:force_sub")],
    ])
    await safe_edit_message(update, text, keyboard, "HTML")


# ─────────────────────────────────────────────
#  ADD CHANNEL (start)
# ─────────────────────────────────────────────

async def add_channel_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data[UserState.ADMIN_ADD_CHANNEL] = True
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✖️ Cancel", callback_data="cfg:force_sub")
    ]])
    await safe_edit_message(
        update,
        "📡 <b>Add Force Subscribe Channel</b>\n\n"
        "Send the channel username (with or without @):\n\n"
        "<i>Example: @mychannel or mychannel</i>",
        keyboard, "HTML"
    )


# ─────────────────────────────────────────────
#  TOGGLE GLOBAL FORCE SUBSCRIBE
# ─────────────────────────────────────────────

async def toggle_force_subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current = db.get_setting("force_subscribe", False)
    db.set_setting("force_subscribe", not current)
    new_status = "✅ Enabled" if not current else "❌ Disabled"
    db.add_admin_log(update.effective_user.id, "force_subscribe_toggle",
                     f"Force subscribe {new_status}")
    await safe_answer_callback(update, f"Force Subscribe {new_status}", show_alert=False)
    await force_subscribe_panel(update, context)


# ─────────────────────────────────────────────
#  TOGGLE INDIVIDUAL CHANNEL
# ─────────────────────────────────────────────

async def toggle_channel(update: Update, context: ContextTypes.DEFAULT_TYPE, channel_id: int):
    db.toggle_force_channel(channel_id)
    await safe_answer_callback(update, "✅ Updated", show_alert=False)
    await channel_detail(update, context, channel_id)


# ─────────────────────────────────────────────
#  REMOVE CHANNEL
# ─────────────────────────────────────────────

async def remove_channel(update: Update, context: ContextTypes.DEFAULT_TYPE, channel_id: int):
    db.remove_force_channel(channel_id)
    db.add_admin_log(update.effective_user.id, "remove_channel", f"Removed channel {channel_id}")
    await safe_answer_callback(update, "🗑️ Channel removed", show_alert=False)
    await force_subscribe_panel(update, context)


# ─────────────────────────────────────────────
#  CHECK SUBSCRIBE (user-facing)
# ─────────────────────────────────────────────

async def check_user_subscribed(bot, user_id: int) -> bool:
    """Check all active force-subscribe channels. Returns True if subscribed to all."""
    channels = db.get_force_channels(active_only=True)
    if not channels:
        return True
    for ch in channels:
        username = ch["username"].lstrip("@")
        try:
            member = await bot.get_chat_member(chat_id=f"@{username}", user_id=user_id)
            if member.status in ("left", "kicked", "banned"):
                return False
        except Exception as e:
            logger.warning(f"Subscribe check failed for @{username}: {e}")
    return True


def build_subscribe_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """Build a keyboard with join buttons for all active channels."""
    channels = db.get_force_channels(active_only=True)
    rows = []
    for ch in channels:
        link = ch.get("link") or f"https://t.me/{ch['username']}"
        rows.append([InlineKeyboardButton(
            f"📢 Join @{ch['username']}", url=link
        )])
    rows.append([InlineKeyboardButton("🔄 Check Again", callback_data="check_subscribe")])
    return InlineKeyboardMarkup(rows)
