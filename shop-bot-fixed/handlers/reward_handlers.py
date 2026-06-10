"""
╔══════════════════════════════════════════════════════════╗
║   TELEGRAM SHOP BOT - REWARD LINKS & DAILY GIFT ADMIN   ║
╚══════════════════════════════════════════════════════════╝
"""

import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import database as db
from utils.helpers import (
    is_admin, safe_edit_message, safe_answer_callback,
    safe_float, safe_int, UserState
)
from keyboards.inline import cancel_keyboard, back_to_admin_keyboard

logger = logging.getLogger(__name__)


def _lang(ctx): return ctx.user_data.get("lang", "en")


# ─────────────────────────────────────────────
#  REWARD LINKS PANEL
# ─────────────────────────────────────────────

async def reward_links_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    links = db.get_all_reward_links()
    active = [l for l in links if l.get("is_active")]
    text = (
        "🎁 <b>Reward Links</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📊 Total Links: <b>{len(links)}</b>\n"
        f"✅ Active: <b>{len(active)}</b>\n\n"
        "Create special links that give users points when opened."
    )
    rows = []
    for link in links[:10]:
        status = "✅" if link.get("is_active") else "❌"
        uses = f"{link['used_count']}/{'∞' if link['max_uses'] == -1 else link['max_uses']}"
        rows.append([InlineKeyboardButton(
            f"{status} +{link['points']}pts — {uses} uses",
            callback_data=f"rl:detail:{link['id']}"
        )])
    rows.extend([
        [InlineKeyboardButton("➕ Create Reward Link", callback_data="rl:create")],
        [InlineKeyboardButton("◀️ Admin Panel", callback_data="admin")],
    ])
    await safe_edit_message(update, text, InlineKeyboardMarkup(rows), "HTML")


async def reward_link_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, link_id: int):
    with db.get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM reward_links WHERE id = ?", (link_id,))
        link = c.fetchone()
    if not link:
        await safe_answer_callback(update, "Link not found", show_alert=True)
        return
    link = dict(link)
    bot_username = context.bot.username
    tg_link = f"https://t.me/{bot_username}?start={link['token']}"
    status = "✅ Active" if link.get("is_active") else "❌ Inactive"
    uses = f"{link['used_count']} / {'∞' if link['max_uses'] == -1 else link['max_uses']}"
    expires = link.get("expires_at") or "Never"
    target = link.get("target_users") or "Everyone"
    text = (
        f"🎁 <b>Reward Link</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💰 Points: <b>{link['points']}</b>\n"
        f"🔢 Uses: <b>{uses}</b>\n"
        f"⏳ Expires: <b>{expires}</b>\n"
        f"👥 Target Users: <b>{target}</b>\n"
        f"Status: <b>{status}</b>\n\n"
        f"🔗 <b>Share Link:</b>\n"
        f"<code>{tg_link}</code>"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Copy Link", callback_data=f"rl:copy:{link_id}")],
        [InlineKeyboardButton("🗑️ Delete", callback_data=f"rl:delete:{link_id}"),
         InlineKeyboardButton("◀️ Back", callback_data="rl:panel")],
    ])
    await safe_edit_message(update, text, keyboard, "HTML")


async def reward_link_create_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["rl_step"] = "points"
    context.user_data["rl_data"] = {}
    await safe_edit_message(
        update,
        "🎁 <b>Create Reward Link</b>\n\nStep 1: How many points should this link give?\n(e.g. 5.00)",
        cancel_keyboard("rl:panel"), "HTML"
    )


async def reward_link_delete(update: Update, context: ContextTypes.DEFAULT_TYPE, link_id: int):
    db.delete_reward_link(link_id)
    db.add_admin_log(update.effective_user.id, "delete_reward_link", f"Reward link #{link_id}", link_id)
    await safe_answer_callback(update, "🗑️ Reward link deleted", show_alert=False)
    await reward_links_panel(update, context)


# ─────────────────────────────────────────────
#  DAILY GIFT PANEL
# ─────────────────────────────────────────────

async def daily_gift_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    enabled = db.get_setting("daily_gift_enabled", False)
    points = db.get_setting("daily_gift_points", 1.0)
    cooldown = db.get_setting("daily_gift_cooldown_hours", 24)

    status_icon = "✅ Enabled" if enabled else "❌ Disabled"
    text = (
        "🎁 <b>Daily Gift Control</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Status: <b>{status_icon}</b>\n"
        f"💰 Points per gift: <b>{points}</b>\n"
        f"⏳ Cooldown: <b>{cooldown} hours</b>\n\n"
        "When enabled, users can claim a daily reward from their profile."
    )
    toggle_label = "🔴 Disable Daily Gift" if enabled else "🟢 Enable Daily Gift"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(toggle_label, callback_data="dg:toggle")],
        [InlineKeyboardButton("💰 Set Points", callback_data="dg:edit:points"),
         InlineKeyboardButton("⏳ Set Cooldown", callback_data="dg:edit:cooldown")],
        [InlineKeyboardButton("◀️ Admin Panel", callback_data="admin")],
    ])
    await safe_edit_message(update, text, keyboard, "HTML")


async def toggle_daily_gift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current = db.get_setting("daily_gift_enabled", False)
    db.set_setting("daily_gift_enabled", not current)
    db.add_admin_log(update.effective_user.id, "toggle_daily_gift",
                     f"{'Enabled' if not current else 'Disabled'}")
    await safe_answer_callback(update,
        f"✅ Daily Gift {'enabled' if not current else 'disabled'}", show_alert=False)
    await daily_gift_panel(update, context)


async def daily_gift_edit_start(update: Update, context: ContextTypes.DEFAULT_TYPE, field: str):
    prompts = {
        "points": "💰 Enter new points amount for daily gift (e.g. 1.00):",
        "cooldown": "⏳ Enter cooldown in hours (e.g. 24 for daily, 12 for twice a day):",
    }
    context.user_data["dg_edit_field"] = field
    context.user_data["dg_editing"] = True
    await safe_edit_message(update, prompts.get(field, "Enter new value:"),
                             cancel_keyboard("dg:panel"), "HTML")
