"""
╔══════════════════════════════════════════════════════════╗
║       TELEGRAM SHOP BOT - ERROR HANDLERS                 ║
║  Global exception handler + admin error dashboard        ║
╚══════════════════════════════════════════════════════════╝
"""

import logging
import traceback
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from utils.error_tracker import error_tracker
from utils.helpers import is_admin, safe_edit_message, safe_answer_callback
from utils.formatting import DIV_BOLD

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
#  GLOBAL ERROR HANDLER
# ─────────────────────────────────────────────

async def global_error_handler(update: object,
                                 context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Registered as application.add_error_handler.
    Records the error, logs it, and optionally notifies the primary admin.
    """
    err = context.error
    if err is None:
        return

    # Record in tracker
    ctx_str = "unknown"
    user_id = None
    if isinstance(update, Update):
        user_id = update.effective_user.id if update.effective_user else None
        if update.callback_query:
            ctx_str = f"callback:{update.callback_query.data or '?'}"
        elif update.message:
            ctx_str = "message"

    error_tracker.record(ctx_str, err, user_id)
    logger.error(f"Unhandled error [{ctx_str}]: {err}", exc_info=err)

    # Try to answer the query gracefully
    try:
        if isinstance(update, Update) and update.callback_query:
            await update.callback_query.answer("❌ Something went wrong", show_alert=False)
    except Exception:
        pass


# ─────────────────────────────────────────────
#  ADMIN: ERROR DASHBOARD
# ─────────────────────────────────────────────

async def error_dashboard(update: Update,
                           context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        await safe_answer_callback(update, "⛔ Access denied", show_alert=True)
        return

    total_unique = error_tracker.total_unique
    total_hits   = error_tracker.total_occurrences

    if total_unique == 0:
        text = (
            f"🛡️ <b>Error Tracker</b>\n{DIV_BOLD}\n\n"
            "✅ No errors recorded this session!"
        )
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("◀️ Admin Panel", callback_data="admin")
        ]])
        await safe_edit_message(update, text, keyboard, "HTML")
        return

    top = error_tracker.get_summary(10)
    lines = []
    for i, e in enumerate(top, 1):
        count = e["count"]
        etype = e["type"]
        ctx   = e["context"][:30]
        msg   = e["message"][:60]
        lines.append(
            f"{i}. <b>{etype}</b> ×{count}\n"
            f"   📍 {ctx}\n"
            f"   💬 <code>{msg}</code>\n"
            f"   🕐 Last: {e['last_seen']}"
        )

    text = (
        f"🛡️ <b>Error Dashboard</b>\n{DIV_BOLD}\n\n"
        f"📊 Unique errors: <b>{total_unique}</b>\n"
        f"🔢 Total occurrences: <b>{total_hits}</b>\n\n"
        "🔥 <b>Top Errors:</b>\n\n"
        + "\n\n".join(lines)
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🕐 Recent Timeline", callback_data="err:recent"),
         InlineKeyboardButton("🗑️ Clear All",       callback_data="err:clear")],
        [InlineKeyboardButton("🔄 Refresh",          callback_data="err:dashboard")],
        [InlineKeyboardButton("◀️ Admin Panel",      callback_data="admin")],
    ])
    await safe_edit_message(update, text, keyboard, "HTML")


async def error_recent(update: Update,
                        context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        return

    recent = error_tracker.get_recent(15)
    if not recent:
        await safe_answer_callback(update, "No recent errors", show_alert=False)
        return

    lines = []
    for e in recent:
        uid_str = f" · uid {e['user_id']}" if e.get("user_id") else ""
        lines.append(
            f"<code>{e['ts']}</code>{uid_str}\n"
            f"  <b>{e['type']}</b> in {e['context'][:25]}\n"
            f"  <code>{e['msg'][:80]}</code>"
        )

    text = f"🕐 <b>Recent Errors</b>\n{DIV_BOLD}\n\n" + "\n\n".join(lines)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Back", callback_data="err:dashboard")]
    ])
    await safe_edit_message(update, text, keyboard, "HTML")


async def error_clear(update: Update,
                       context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        return
    error_tracker.clear()
    import database as db
    db.add_admin_log(update.effective_user.id, "clear_errors", "Error tracker cleared")
    await safe_answer_callback(update, "🗑️ Error log cleared", show_alert=False)
    await error_dashboard(update, context)
