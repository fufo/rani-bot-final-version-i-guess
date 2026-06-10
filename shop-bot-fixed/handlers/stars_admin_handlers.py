"""
╔══════════════════════════════════════════════════════════╗
║     TELEGRAM SHOP BOT - STARS SYSTEM ADMIN PANEL         ║
║   Telegram Stars packages, pricing & management          ║
╚══════════════════════════════════════════════════════════╝
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import ContextTypes

import database as db
from utils.helpers import safe_edit_message, safe_answer_callback, format_price, UserState

logger = logging.getLogger(__name__)


def _tog(val) -> str:
    return "✅ ON" if val else "❌ OFF"


# ─────────────────────────────────────────────
#  STARS ADMIN PANEL
# ─────────────────────────────────────────────

async def stars_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = db.get_all_settings()
    enabled = s.get("stars_enabled", True)
    rate    = s.get("stars_per_dollar", 50)
    bonus   = s.get("stars_bonus_pct", 0)
    packages = db.get_stars_packages(active_only=False)

    text = (
        "⭐ <b>Stars System</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Status: <b>{_tog(enabled)}</b>\n"
        f"⭐ Stars per $1: <b>{rate}</b>\n"
        f"🎁 Bonus %: <b>{bonus}%</b>\n"
        f"📦 Packages: <b>{len(packages)}</b>"
    )

    rows = [
        [InlineKeyboardButton(
            f"{'❌ Disable' if enabled else '✅ Enable'} Stars",
            callback_data="stars:toggle"
        )],
        [InlineKeyboardButton("⭐ Stars/$1 Rate",    callback_data="stars:edit:stars_per_dollar"),
         InlineKeyboardButton("🎁 Bonus %",          callback_data="stars:edit:stars_bonus_pct")],
        [InlineKeyboardButton("📦 Manage Packages",  callback_data="stars:packages"),
         InlineKeyboardButton("➕ Add Package",       callback_data="stars:add_pkg")],
        [InlineKeyboardButton("💱 Exchange Rate",     callback_data="stars:edit:stars_exchange_rate")],
        [InlineKeyboardButton("◀️ Settings",          callback_data="admin_settings")],
    ]
    await safe_edit_message(update, text, InlineKeyboardMarkup(rows), "HTML")


# ─────────────────────────────────────────────
#  PACKAGES LIST
# ─────────────────────────────────────────────

async def stars_packages_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    packages = db.get_stars_packages(active_only=False)
    text = (
        "📦 <b>Stars Packages</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Total packages: <b>{len(packages)}</b>\n"
        "Click a package to manage it:"
    )
    rows = []
    for pkg in packages:
        icon = "🟢" if pkg.get("is_active") else "🔴"
        bonus_txt = f" +{pkg['bonus_stars']}⭐" if pkg.get("bonus_stars") else ""
        rows.append([InlineKeyboardButton(
            f"{icon} {pkg['name']} — {pkg['stars']}⭐{bonus_txt} (${pkg['price_usd']:.2f})",
            callback_data=f"stars:pkg:{pkg['id']}"
        )])
    rows.extend([
        [InlineKeyboardButton("➕ Add Package",  callback_data="stars:add_pkg")],
        [InlineKeyboardButton("◀️ Back",         callback_data="cfg:stars")],
    ])
    await safe_edit_message(update, text, InlineKeyboardMarkup(rows), "HTML")


# ─────────────────────────────────────────────
#  PACKAGE DETAIL
# ─────────────────────────────────────────────

async def stars_package_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, pkg_id: int):
    pkg = db.get_stars_package(pkg_id)
    if not pkg:
        await safe_answer_callback(update, "Package not found", show_alert=True)
        return

    icon = "🟢 Active" if pkg.get("is_active") else "🔴 Inactive"
    text = (
        f"📦 <b>{pkg['name']}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"⭐ Stars: <b>{pkg['stars']}</b>\n"
        f"🎁 Bonus Stars: <b>{pkg.get('bonus_stars', 0)}</b>\n"
        f"💵 Price: <b>${pkg['price_usd']:.2f}</b>\n"
        f"Status: <b>{icon}</b>"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Edit Name",      callback_data=f"stars:pkg_edit:name:{pkg_id}"),
         InlineKeyboardButton("💵 Edit Price",     callback_data=f"stars:pkg_edit:price:{pkg_id}")],
        [InlineKeyboardButton("⭐ Edit Stars",      callback_data=f"stars:pkg_edit:stars:{pkg_id}"),
         InlineKeyboardButton("🎁 Edit Bonus",     callback_data=f"stars:pkg_edit:bonus:{pkg_id}")],
        [InlineKeyboardButton(
            "🔴 Deactivate" if pkg.get("is_active") else "🟢 Activate",
            callback_data=f"stars:pkg_toggle:{pkg_id}"
        )],
        [InlineKeyboardButton("🧪 Test Invoice",    callback_data=f"stars:test:{pkg_id}")],
        [InlineKeyboardButton("🗑️ Delete",         callback_data=f"stars:pkg_del:{pkg_id}")],
        [InlineKeyboardButton("◀️ Back",            callback_data="stars:packages")],
    ])
    await safe_edit_message(update, text, keyboard, "HTML")


# ─────────────────────────────────────────────
#  TOGGLE STARS SYSTEM
# ─────────────────────────────────────────────

async def toggle_stars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current = db.get_setting("stars_enabled", True)
    db.set_setting("stars_enabled", not current)
    status = "✅ Enabled" if not current else "❌ Disabled"
    db.add_admin_log(update.effective_user.id, "stars_toggle", f"Stars {status}")
    await safe_answer_callback(update, f"Stars System {status}", show_alert=False)
    await stars_panel(update, context)


# ─────────────────────────────────────────────
#  TOGGLE PACKAGE
# ─────────────────────────────────────────────

async def toggle_package(update: Update, context: ContextTypes.DEFAULT_TYPE, pkg_id: int):
    db.toggle_stars_package(pkg_id)
    await safe_answer_callback(update, "✅ Updated", show_alert=False)
    await stars_package_detail(update, context, pkg_id)


# ─────────────────────────────────────────────
#  DELETE PACKAGE
# ─────────────────────────────────────────────

async def delete_package(update: Update, context: ContextTypes.DEFAULT_TYPE, pkg_id: int):
    db.delete_stars_package(pkg_id)
    db.add_admin_log(update.effective_user.id, "delete_stars_package", f"Package {pkg_id}")
    await safe_answer_callback(update, "🗑️ Deleted", show_alert=False)
    await stars_packages_list(update, context)


# ─────────────────────────────────────────────
#  ADD PACKAGE (start wizard)
# ─────────────────────────────────────────────

async def add_package_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data[UserState.ADMIN_ADD_STARS_PKG] = True
    context.user_data["stars_pkg_step"] = "name"
    context.user_data["stars_pkg_data"] = {}
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✖️ Cancel", callback_data="stars:packages")
    ]])
    await safe_edit_message(
        update,
        "📦 <b>Add Stars Package</b>\n\nStep 1/4: Enter package name:\n<i>e.g. Starter Pack</i>",
        keyboard, "HTML"
    )


# ─────────────────────────────────────────────
#  EDIT PACKAGE FIELD (prompt)
# ─────────────────────────────────────────────

PKG_EDIT_LABELS = {
    "name":   "✏️ Enter new package name:",
    "price":  "💵 Enter new price in USD (e.g. 4.99):",
    "stars":  "⭐ Enter number of stars:",
    "bonus":  "🎁 Enter bonus stars (0 for none):",
}


async def edit_package_field_start(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                    field: str, pkg_id: int):
    prompt = PKG_EDIT_LABELS.get(field, f"Enter new {field}:")
    context.user_data[UserState.ADMIN_EDIT_STARS_PKG] = True
    context.user_data["editing_pkg_id"] = pkg_id
    context.user_data["editing_pkg_field"] = field
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✖️ Cancel", callback_data=f"stars:pkg:{pkg_id}")
    ]])
    await safe_edit_message(update, prompt, keyboard, "HTML")


# ─────────────────────────────────────────────
#  EDIT STARS SETTING (prompt)
# ─────────────────────────────────────────────

STARS_LABELS = {
    "stars_per_dollar":   "⭐ Enter stars per $1 (e.g. 50):",
    "stars_bonus_pct":    "🎁 Enter bonus percentage (e.g. 10 for 10%):",
    "stars_exchange_rate":"💱 Enter stars-to-balance exchange rate (stars per $1):",
}


async def edit_stars_setting_start(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str):
    prompt = STARS_LABELS.get(key, f"Enter new value for {key}:")
    current = db.get_setting(key, 0)
    context.user_data[UserState.ADMIN_EDIT_SETTING] = True
    context.user_data[UserState.ADMIN_EDIT_SETTING_KEY] = key
    context.user_data["_setting_back_cb"] = "cfg:stars"
    text = f"{prompt}\n\nCurrent: <code>{current}</code>"
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✖️ Cancel", callback_data="cfg:stars")
    ]])
    await safe_edit_message(update, text, keyboard, "HTML")


# ─────────────────────────────────────────────
#  TEST INVOICE (admin preview of Stars payment)
# ─────────────────────────────────────────────

async def test_stars_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE, pkg_id: int):
    pkg = db.get_stars_package(pkg_id)
    if not pkg:
        await safe_answer_callback(update, "Package not found", show_alert=True)
        return

    total_stars = pkg["stars"] + pkg.get("bonus_stars", 0)
    try:
        link = await context.bot.create_invoice_link(
            title=pkg["name"],
            description=f"Buy {total_stars} ⭐ Telegram Stars",
            payload=f"stars_pkg_{pkg_id}",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(pkg["name"], pkg["stars"])]
        )
        await safe_answer_callback(update, "✅ Invoice link created!", show_alert=False)
        try:
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text=(
                    f"🧪 <b>Test Invoice</b>\n\n"
                    f"Package: <b>{pkg['name']}</b>\n"
                    f"Stars: <b>{total_stars} ⭐</b>\n"
                    f"Price: <b>{pkg['stars']} XTR</b>\n\n"
                    f"🔗 Invoice Link:\n{link}"
                ),
                parse_mode="HTML"
            )
        except Exception:
            pass
    except Exception as e:
        await safe_answer_callback(update, f"❌ Error: {str(e)[:100]}", show_alert=True)
