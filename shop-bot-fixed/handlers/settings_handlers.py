"""
╔══════════════════════════════════════════════════════════╗
║     TELEGRAM SHOP BOT - DYNAMIC SETTINGS PANEL           ║
║   Full inline admin settings — no config.py editing      ║
╚══════════════════════════════════════════════════════════╝
"""

import logging
from typing import List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import database as db
from config import Emoji
from utils.helpers import safe_edit_message, safe_answer_callback, UserState, is_owner

logger = logging.getLogger(__name__)


def _tog(val) -> str:
    return "✅ ON" if val else "❌ OFF"


# ─────────────────────────────────────────────
#  MAIN SETTINGS MENU
# ─────────────────────────────────────────────

async def settings_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "⚙️ <b>Bot Settings</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Select a category to configure:"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 General",        callback_data="cfg:general"),
         InlineKeyboardButton("📌 Force Subscribe", callback_data="cfg:force_sub")],
        [InlineKeyboardButton("💳 Payment",        callback_data="cfg:payment"),
         InlineKeyboardButton("⭐ Stars System",   callback_data="cfg:stars")],
        [InlineKeyboardButton("🔗 Referral",       callback_data="cfg:referral"),
         InlineKeyboardButton("🛡️ Security",      callback_data="cfg:security")],
        [InlineKeyboardButton("🔔 Notifications",  callback_data="cfg:notify"),
         InlineKeyboardButton("💬 Messages",       callback_data="cfg:messages")],
        [InlineKeyboardButton("🚀 Delivery",       callback_data="cfg:delivery"),
         InlineKeyboardButton("👑 Admins",         callback_data="cfg:admins")],
        [InlineKeyboardButton("◀️ Admin Panel",    callback_data="admin")],
    ])
    await safe_edit_message(update, text, keyboard, "HTML")


# ─────────────────────────────────────────────
#  GENERAL SETTINGS
# ─────────────────────────────────────────────

async def settings_general(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = db.get_all_settings()
    bot_name = s.get("bot_name", "Premium Shop Bot")
    status = _tog(s.get("bot_status", True))
    product_link = s.get("product_link", "")
    text = (
        "🌐 <b>General Settings</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🤖 Bot Status: <b>{status}</b>\n"
        f"📛 Bot Name: <b>{bot_name}</b>\n"
        f"💬 Support: <b>{s.get('support_username', '—')}</b>\n"
        f"🌍 Currency: <b>{s.get('currency', 'USD')}</b>\n"
        f"🔗 Product Link: <b>{product_link[:60] if product_link else '—'}</b>"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🤖 Bot: {status}", callback_data="stg:toggle:bot_status")],
        [InlineKeyboardButton("📛 Bot Name",        callback_data="stg:edit:bot_name"),
         InlineKeyboardButton("💬 Support User",    callback_data="stg:edit:support_username")],
        [InlineKeyboardButton("🌍 Currency",        callback_data="stg:edit:currency"),
         InlineKeyboardButton("💱 Symbol",          callback_data="stg:edit:currency_symbol")],
        [InlineKeyboardButton("🔧 Maintenance Msg", callback_data="stg:edit:maintenance_msg")],
        [InlineKeyboardButton("🔗 Product Link",    callback_data="stg:edit:product_link")],
        [InlineKeyboardButton("◀️ Settings",        callback_data="admin_settings")],
    ])
    await safe_edit_message(update, text, keyboard, "HTML")


# ─────────────────────────────────────────────
#  PAYMENT SETTINGS
# ─────────────────────────────────────────────

async def settings_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = db.get_all_settings()
    auto_del = _tog(s.get("auto_delivery", True))
    text = (
        "💳 <b>Payment Settings</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💎 USDT Wallet:\n<code>{s.get('usdt_wallet', '—')}</code>\n\n"
        f"📡 Network: <b>{s.get('usdt_network', 'TRC20')}</b>\n"
        f"📥 Min Deposit: <b>${s.get('min_deposit', 1.0)}</b>\n"
        f"📤 Min Withdrawal: <b>${s.get('min_withdrawal', 5.0)}</b>\n"
        f"🚀 Auto Delivery: <b>{auto_del}</b>"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 USDT Wallet",     callback_data="stg:edit:usdt_wallet")],
        [InlineKeyboardButton("📥 Min Deposit",     callback_data="stg:edit:min_deposit"),
         InlineKeyboardButton("📤 Min Withdrawal",  callback_data="stg:edit:min_withdrawal")],
        [InlineKeyboardButton(f"🚀 Auto Delivery: {auto_del}", callback_data="stg:toggle:auto_delivery")],
        [InlineKeyboardButton("📋 Payment Instructions", callback_data="stg:edit:payment_instructions")],
        [InlineKeyboardButton("◀️ Settings",        callback_data="admin_settings")],
    ])
    await safe_edit_message(update, text, keyboard, "HTML")


# ─────────────────────────────────────────────
#  SECURITY SETTINGS
# ─────────────────────────────────────────────

async def settings_security(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = db.get_all_settings()
    captcha = _tog(s.get("captcha_enabled", False))
    text = (
        "🛡️ <b>Security Settings</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🤖 Captcha: <b>{captcha}</b>\n"
        f"⏱ Anti-Spam Cooldown: <b>{s.get('anti_spam_cooldown', 1)}s</b>\n"
        f"📊 Max Req/min: <b>{s.get('max_requests_minute', 30)}</b>"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🤖 Captcha: {captcha}", callback_data="stg:toggle:captcha_enabled")],
        [InlineKeyboardButton("⏱ Cooldown (s)",    callback_data="stg:edit:anti_spam_cooldown"),
         InlineKeyboardButton("📊 Max Req/min",    callback_data="stg:edit:max_requests_minute")],
        [InlineKeyboardButton("◀️ Settings",        callback_data="admin_settings")],
    ])
    await safe_edit_message(update, text, keyboard, "HTML")


# ─────────────────────────────────────────────
#  NOTIFICATION SETTINGS
# ─────────────────────────────────────────────

async def settings_notify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = db.get_all_settings()
    login_n = _tog(s.get("login_notify", True))
    order_l = _tog(s.get("order_logs", True))
    text = (
        "🔔 <b>Notification Settings</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔔 Login Notify: <b>{login_n}</b>\n"
        f"📋 Order Logs: <b>{order_l}</b>"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🔔 Login Notify: {login_n}", callback_data="stg:toggle:login_notify")],
        [InlineKeyboardButton(f"📋 Order Logs: {order_l}",   callback_data="stg:toggle:order_logs")],
        [InlineKeyboardButton("◀️ Settings",                  callback_data="admin_settings")],
    ])
    await safe_edit_message(update, text, keyboard, "HTML")


# ─────────────────────────────────────────────
#  MESSAGES SETTINGS
# ─────────────────────────────────────────────

async def settings_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "💬 <b>Messages & Texts</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Edit the bot's key messages:"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👋 Welcome Message",      callback_data="stg:edit:welcome_message")],
        [InlineKeyboardButton("🎉 Join Message",         callback_data="stg:edit:join_message")],
        [InlineKeyboardButton("📋 Terms of Service",     callback_data="stg:edit:terms_message")],
        [InlineKeyboardButton("💳 Payment Instructions", callback_data="stg:edit:payment_instructions")],
        [InlineKeyboardButton("🔧 Maintenance Message",  callback_data="stg:edit:maintenance_msg")],
        [InlineKeyboardButton("◀️ Settings",             callback_data="admin_settings")],
    ])
    await safe_edit_message(update, text, keyboard, "HTML")


# ─────────────────────────────────────────────
#  DELIVERY SETTINGS
# ─────────────────────────────────────────────

async def settings_delivery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = db.get_all_settings()
    auto_del  = _tog(s.get("auto_delivery", True))
    prod_del  = _tog(s.get("product_auto_delete", False))
    ratings_e = _tog(s.get("ratings_enabled", True))
    max_retry = s.get("delivery_max_retries", 3)
    text = (
        "🚀 <b>Delivery Settings</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🚀 Auto Delivery:       <b>{auto_del}</b>\n"
        f"🗑️ Auto-Delete After:   <b>{prod_del}</b>\n"
        f"🔁 Max Retry Attempts:  <b>{max_retry}</b>\n"
        f"⭐ Ratings Enabled:     <b>{ratings_e}</b>\n"
        f"👥 Required Referrals:  <b>{s.get('required_referrals', 0)}</b>"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🚀 Auto Delivery: {auto_del}",
                              callback_data="stg:toggle:auto_delivery")],
        [InlineKeyboardButton(f"🗑️ Auto-Delete: {prod_del}",
                              callback_data="stg:toggle:product_auto_delete")],
        [InlineKeyboardButton(f"⭐ Ratings: {ratings_e}",
                              callback_data="stg:toggle:ratings_enabled")],
        [InlineKeyboardButton("🔁 Max Retries",       callback_data="stg:edit:delivery_max_retries"),
         InlineKeyboardButton("👥 Required Referrals", callback_data="stg:edit:required_referrals")],
        [InlineKeyboardButton("◀️ Settings",           callback_data="admin_settings")],
    ])
    await safe_edit_message(update, text, keyboard, "HTML")


# ─────────────────────────────────────────────
#  TOGGLE SETTING
# ─────────────────────────────────────────────

async def toggle_setting(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str):
    current = db.get_setting(key)
    new_val = not bool(current)
    db.set_setting(key, new_val)
    status = "✅ ON" if new_val else "❌ OFF"
    db.add_admin_log(update.effective_user.id, "toggle_setting", f"{key} → {status}")
    await safe_answer_callback(update, f"{key}: {status}", show_alert=False)
    # Re-render the appropriate category panel
    await _refresh_after_toggle(update, context, key)


async def _refresh_after_toggle(update, context, key: str):
    payment_keys = {"auto_delivery", "product_auto_delete"}
    security_keys = {"captcha_enabled"}
    notify_keys   = {"login_notify", "order_logs"}
    general_keys  = {"bot_status"}
    delivery_keys = {"auto_delivery", "product_auto_delete", "ratings_enabled"}
    if key in payment_keys or key in delivery_keys:
        await settings_delivery(update, context)
    elif key in security_keys:
        await settings_security(update, context)
    elif key in notify_keys:
        await settings_notify(update, context)
    elif key in general_keys:
        await settings_general(update, context)
    else:
        await settings_main(update, context)


# ─────────────────────────────────────────────
#  EDIT SETTING (prompt for new value)
# ─────────────────────────────────────────────

SETTING_LABELS = {
    "bot_name":             "📛 Enter new bot name:",
    "support_username":     "💬 Enter support username (e.g. @support_user):",
    "currency":             "🌍 Enter currency code (e.g. USD, EUR):",
    "currency_symbol":      "💱 Enter currency symbol (e.g. $ or €):",
    "maintenance_msg":      "🔧 Enter maintenance message:",
    "usdt_wallet":          "💎 Enter USDT TRC20 wallet address:",
    "min_deposit":          "📥 Enter minimum deposit amount (number):",
    "min_withdrawal":       "📤 Enter minimum withdrawal amount (number):",
    "anti_spam_cooldown":   "⏱ Enter cooldown in seconds (number):",
    "max_requests_minute":  "📊 Enter max requests per minute (number):",
    "welcome_message":      "👋 Enter new welcome message (supports HTML):",
    "join_message":         "🎉 Enter join message:",
    "terms_message":        "📋 Enter terms of service text:",
    "payment_instructions": "💳 Enter payment instructions:",
    "required_referrals":   "👥 Enter required referrals (0 = none):",
    "bonus_rewards":        "🎁 Enter bonus reward amount:",
    "delivery_max_retries": "🔁 Enter max delivery retry attempts (1-5):",
    "weekly_reward_1st":    "🥇 Weekly reward for 1st place ($):",
    "weekly_reward_2nd":    "🥈 Weekly reward for 2nd place ($):",
    "weekly_reward_3rd":    "🥉 Weekly reward for 3rd place ($):",
    "product_link":         "🔗 Enter the product URL (e.g. https://example.com/product/123):",
}

SETTING_BACK = {
    "bot_name":             "cfg:general",
    "support_username":     "cfg:general",
    "currency":             "cfg:general",
    "currency_symbol":      "cfg:general",
    "maintenance_msg":      "cfg:general",
    "product_link":         "cfg:general",
    "usdt_wallet":          "cfg:payment",
    "min_deposit":          "cfg:payment",
    "min_withdrawal":       "cfg:payment",
    "payment_instructions": "cfg:payment",
    "anti_spam_cooldown":   "cfg:security",
    "max_requests_minute":  "cfg:security",
    "welcome_message":      "cfg:messages",
    "join_message":         "cfg:messages",
    "terms_message":        "cfg:messages",
    "required_referrals":   "cfg:delivery",
    "bonus_rewards":        "cfg:delivery",
    "delivery_max_retries": "cfg:delivery",
    "weekly_reward_1st":    "cfg:referral",
    "weekly_reward_2nd":    "cfg:referral",
    "weekly_reward_3rd":    "cfg:referral",
}


async def edit_setting_start(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str):
    prompt = SETTING_LABELS.get(key, f"✏️ Enter new value for <code>{key}</code>:")
    current = db.get_setting(key, "")
    back_cb = SETTING_BACK.get(key, "admin_settings")
    context.user_data[UserState.ADMIN_EDIT_SETTING] = True
    context.user_data[UserState.ADMIN_EDIT_SETTING_KEY] = key
    text = (
        f"{prompt}\n\n"
        f"Current value:\n<code>{str(current)[:200]}</code>"
    )
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✖️ Cancel", callback_data=back_cb)
    ]])
    await safe_edit_message(update, text, keyboard, "HTML")


async def edit_setting_save(user_id: int, key: str, value_str: str) -> str:
    """Save a setting from text input. Returns confirmation message."""
    # Determine type from current value
    current = db.get_setting(key)
    if isinstance(current, bool):
        val = value_str.lower() in ("1", "true", "yes", "on")
    elif isinstance(current, int):
        try:
            val = int(value_str)
        except ValueError:
            return "❌ Invalid number. Please enter an integer."
    elif isinstance(current, float):
        try:
            val = float(value_str.replace(",", "."))
        except ValueError:
            return "❌ Invalid number. Please enter a decimal number."
    else:
        val = value_str.strip()
    db.set_setting(key, val)
    db.add_admin_log(user_id, "edit_setting", f"{key} = {str(val)[:100]}")
    return f"✅ <b>{key}</b> updated successfully!"
