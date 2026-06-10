"""
╔══════════════════════════════════════════════════════════╗
║     TELEGRAM SHOP BOT - REFERRAL ADMIN PANEL             ║
║   Full referral system management from inline panel      ║
╚══════════════════════════════════════════════════════════╝
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import database as db
from utils.helpers import safe_edit_message, safe_answer_callback, format_price, format_date

logger = logging.getLogger(__name__)


def _tog(val) -> str:
    return "✅ ON" if val else "❌ OFF"


# ─────────────────────────────────────────────
#  REFERRAL ADMIN PANEL
# ─────────────────────────────────────────────

async def referral_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = db.get_all_settings()
    enabled   = s.get("referral_enabled", True)
    bonus     = s.get("referral_bonus", 0.5)
    btype     = s.get("referral_bonus_type", "balance")
    s_bonus   = s.get("referral_stars_bonus", 0)
    min_inv   = s.get("referral_min_invites", 0)
    pb        = s.get("referral_purchase_bonus", 0.05)

    btype_label = "💰 Balance" if btype == "balance" else "⭐ Stars"
    stats = db.get_referral_stats()

    text = (
        "🔗 <b>Referral System</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Status: <b>{_tog(enabled)}</b>\n"
        f"Reward Type: <b>{btype_label}</b>\n"
        f"💰 Balance Bonus: <b>${format_price(float(bonus))}</b>\n"
        f"⭐ Stars Bonus: <b>{s_bonus}</b>\n"
        f"📊 Purchase Bonus: <b>{float(pb)*100:.1f}%</b>\n"
        f"👥 Min Invites: <b>{min_inv}</b>\n\n"
        f"📈 <b>Stats</b>\n"
        f"Total Referrals: <b>{stats['total_referrals']}</b>\n"
        f"Total Paid: <b>${format_price(float(stats['total_paid']))}</b>\n"
        f"Active Referrers: <b>{stats['active_referrers']}</b>"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            f"{'❌ Disable' if enabled else '✅ Enable'} Referrals",
            callback_data="ref:toggle"
        )],
        [InlineKeyboardButton("💰 Balance Bonus",   callback_data="ref:edit:referral_bonus"),
         InlineKeyboardButton("⭐ Stars Bonus",      callback_data="ref:edit:referral_stars_bonus")],
        [InlineKeyboardButton("💎 Reward Type",      callback_data="ref:reward_type"),
         InlineKeyboardButton("📊 Purchase %",       callback_data="ref:edit:referral_purchase_bonus")],
        [InlineKeyboardButton("👥 Min Invites",      callback_data="ref:edit:referral_min_invites")],
        [InlineKeyboardButton("🏆 Leaderboard",      callback_data="ref:leaderboard"),
         InlineKeyboardButton("📊 Statistics",       callback_data="ref:stats")],
        [InlineKeyboardButton("◀️ Settings",         callback_data="admin_settings")],
    ])
    await safe_edit_message(update, text, keyboard, "HTML")


# ─────────────────────────────────────────────
#  TOGGLE REFERRAL
# ─────────────────────────────────────────────

async def toggle_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current = db.get_setting("referral_enabled", True)
    db.set_setting("referral_enabled", not current)
    status = "✅ Enabled" if not current else "❌ Disabled"
    db.add_admin_log(update.effective_user.id, "referral_toggle", f"Referral {status}")
    await safe_answer_callback(update, f"Referral {status}", show_alert=False)
    await referral_panel(update, context)


# ─────────────────────────────────────────────
#  REWARD TYPE SELECTION
# ─────────────────────────────────────────────

async def referral_reward_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current = db.get_setting("referral_bonus_type", "balance")
    text = (
        "💎 <b>Referral Reward Type</b>\n\n"
        f"Current: <b>{'💰 Balance' if current == 'balance' else '⭐ Stars'}</b>\n\n"
        "Select which currency to reward referrers with:"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            f"{'✅ ' if current == 'balance' else ''}💰 Balance (USD)",
            callback_data="ref:set_type:balance"
        )],
        [InlineKeyboardButton(
            f"{'✅ ' if current == 'stars' else ''}⭐ Stars",
            callback_data="ref:set_type:stars"
        )],
        [InlineKeyboardButton("◀️ Back", callback_data="cfg:referral")],
    ])
    await safe_edit_message(update, text, keyboard, "HTML")


async def set_referral_reward_type(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                    reward_type: str):
    db.set_setting("referral_bonus_type", reward_type)
    db.add_admin_log(update.effective_user.id, "referral_reward_type", f"Type: {reward_type}")
    label = "💰 Balance" if reward_type == "balance" else "⭐ Stars"
    await safe_answer_callback(update, f"Reward type: {label}", show_alert=False)
    await referral_panel(update, context)


# ─────────────────────────────────────────────
#  LEADERBOARD
# ─────────────────────────────────────────────

async def referral_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from datetime import datetime
    from utils.formatting import RANK_MEDALS

    # All-time leaderboard
    leaders = db.get_referral_leaderboard(10)
    # Weekly leaderboard
    weekly  = db.get_weekly_top_inviters(3)

    # ── All-time
    if not leaders:
        all_time_text = "No referrals yet."
    else:
        lines = []
        for i, u in enumerate(leaders):
            medal   = RANK_MEDALS[i]
            name    = u.get("first_name") or f"User#{u['user_id']}"
            uname   = f" @{u['username']}" if u.get("username") else ""
            count   = u.get("referral_count", 0)
            earned  = float(u.get("total_earned") or 0)
            lines.append(
                f"{medal} <b>{name}</b>{uname}\n"
                f"   👥 {count} invites · 💰 ${format_price(earned)}"
            )
        all_time_text = "\n\n".join(lines)

    # ── Weekly
    week_str  = datetime.now().strftime("Week %W, %Y")
    w_medals  = ["🥇", "🥈", "🥉"]
    if weekly:
        wlines = []
        for i, u in enumerate(weekly):
            medal = w_medals[i] if i < 3 else "🏅"
            name  = u.get("first_name") or f"User#{u['user_id']}"
            cnt   = u.get("weekly_count", 0)
            wlines.append(f"{medal} <b>{name}</b> — {cnt} invites this week")
        weekly_text = "\n".join(wlines)
    else:
        weekly_text = "No invites yet this week."

    text = (
        "🏆 <b>Referral Leaderboard</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📅 <b>All-Time Top 10</b>\n"
        f"{all_time_text}\n\n"
        f"📆 <b>This Week ({week_str})</b>\n"
        f"{weekly_text}"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Refresh",         callback_data="ref:leaderboard"),
         InlineKeyboardButton("💸 Pay Weekly",      callback_data="ref:pay_weekly")],
        [InlineKeyboardButton("◀️ Back",            callback_data="cfg:referral")],
    ])
    await safe_edit_message(update, text, keyboard, "HTML")


async def pay_weekly_rewards_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin triggers weekly payout to top 3 inviters."""
    from datetime import datetime
    from utils.helpers import is_admin
    if not is_admin(update.effective_user.id):
        await safe_answer_callback(update, "⛔ Access denied", show_alert=True)
        return

    weekly = db.get_weekly_top_inviters(3)
    if not weekly:
        await safe_answer_callback(update, "No inviters this week yet.", show_alert=True)
        return

    # Reward tiers: 1st=$5, 2nd=$3, 3rd=$1
    WEEKLY_TIERS = [5.0, 3.0, 1.0]
    week_str = datetime.now().strftime("%Y-W%W")
    rewards = [(u["user_id"], WEEKLY_TIERS[i]) for i, u in enumerate(weekly[:3])]
    paid = db.pay_weekly_rewards(rewards, week_str)

    if paid == 0:
        await safe_answer_callback(update, "⚠️ Already paid for this week.", show_alert=True)
        return

    db.add_admin_log(
        update.effective_user.id, "weekly_rewards",
        f"Paid {paid} users for {week_str}"
    )

    # Notify winners
    tier_labels = ["🥇 1st", "🥈 2nd", "🥉 3rd"]
    for i, (uid, amt) in enumerate(rewards[:paid]):
        try:
            await context.bot.send_message(
                chat_id=uid,
                text=(
                    f"🎉 <b>Weekly Referral Reward!</b>\n\n"
                    f"{tier_labels[i]} place this week!\n"
                    f"💰 <b>+${amt:.2f}</b> added to your balance!\n\n"
                    f"Keep inviting friends to win again next week! 🚀"
                ),
                parse_mode="HTML"
            )
        except Exception:
            pass

    await safe_answer_callback(update, f"✅ Paid {paid} winners!", show_alert=True)
    await referral_leaderboard(update, context)


# ─────────────────────────────────────────────
#  DETAILED STATS
# ─────────────────────────────────────────────

async def referral_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = db.get_referral_stats()
    s = db.get_all_settings()
    text = (
        "📊 <b>Referral Statistics</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔗 Total Referrals: <b>{stats['total_referrals']}</b>\n"
        f"💰 Total Paid Out: <b>${format_price(float(stats['total_paid']))}</b>\n"
        f"👥 Active Referrers: <b>{stats['active_referrers']}</b>\n\n"
        f"⚙️ <b>Current Config</b>\n"
        f"Balance Bonus: <b>${s.get('referral_bonus', 0.5)}</b>\n"
        f"Stars Bonus: <b>{s.get('referral_stars_bonus', 0)} ⭐</b>\n"
        f"Purchase %: <b>{float(s.get('referral_purchase_bonus', 0.05))*100:.1f}%</b>\n"
        f"Min Invites: <b>{s.get('referral_min_invites', 0)}</b>"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Refresh",  callback_data="ref:stats")],
        [InlineKeyboardButton("◀️ Back",     callback_data="cfg:referral")],
    ])
    await safe_edit_message(update, text, keyboard, "HTML")


# ─────────────────────────────────────────────
#  EDIT REFERRAL SETTING (prompt)
# ─────────────────────────────────────────────

REF_LABELS = {
    "referral_bonus":           "💰 Enter balance bonus per referral (e.g. 0.50):",
    "referral_stars_bonus":     "⭐ Enter stars bonus per referral (e.g. 10):",
    "referral_purchase_bonus":  "📊 Enter purchase bonus as decimal (e.g. 0.05 = 5%):",
    "referral_min_invites":     "👥 Enter minimum invites required (0 = no minimum):",
}


async def edit_referral_start(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str):
    from utils.helpers import UserState
    prompt = REF_LABELS.get(key, f"Enter new value for {key}:")
    current = db.get_setting(key, 0)
    context.user_data[UserState.ADMIN_EDIT_SETTING] = True
    context.user_data[UserState.ADMIN_EDIT_SETTING_KEY] = key
    context.user_data["_setting_back_cb"] = "cfg:referral"
    text = f"{prompt}\n\nCurrent: <code>{current}</code>"
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✖️ Cancel", callback_data="cfg:referral")
    ]])
    await safe_edit_message(update, text, keyboard, "HTML")
