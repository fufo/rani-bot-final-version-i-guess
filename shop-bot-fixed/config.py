"""
╔══════════════════════════════════════════════════════════╗
║           TELEGRAM SHOP BOT - CONFIGURATION              ║
║   Only BOT_TOKEN lives here. All other settings are      ║
║   managed dynamically from the Telegram Admin Panel.     ║
╚══════════════════════════════════════════════════════════╝
"""

import os

# ─────────────────────────────────────────────
#  BOT TOKEN — edit this or set env var
# ─────────────────────────────────────────────
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "8319709304:AAFtcuTuLiQ4MRIciV9Map05abuWOx2v5L4")

# ─────────────────────────────────────────────
#  PRIMARY OWNER — cannot be removed via panel
# ─────────────────────────────────────────────
PRIMARY_ADMIN_ID: int = int(os.getenv("PRIMARY_ADMIN_ID", "6905398066"))

# ─────────────────────────────────────────────
#  DATABASE
# ─────────────────────────────────────────────
DATABASE_PATH: str = os.getenv("DATABASE_PATH", "shop.db")

# ─────────────────────────────────────────────
#  BOT META
# ─────────────────────────────────────────────
BOT_VERSION: str = "3.1.0"
BOT_NAME: str = "Premium Shop Bot"

# ─────────────────────────────────────────────
#  PAGINATION (UI constants, not critical)
# ─────────────────────────────────────────────
PRODUCTS_PER_PAGE: int = 6
CATEGORIES_PER_PAGE: int = 8
ORDERS_PER_PAGE: int = 5
USERS_PER_PAGE: int = 10

# ─────────────────────────────────────────────
#  DEFAULT SETTINGS  (seeded into DB on first run)
#  All of these become live-editable from the admin panel
# ─────────────────────────────────────────────
DEFAULT_SETTINGS = {
    # General
    "bot_status":           True,
    "bot_name":             "Premium Shop Bot",
    "maintenance_msg":      "🔧 Bot is under maintenance. Please try again later.",
    "welcome_message":      "👋 Welcome to <b>{bot_name}</b>!\n\n🛒 Browse premium digital products\n💎 Fast • Secure • Automatic Delivery\n\nUse the buttons below to get started.",
    "join_message":         "🎉 <b>Welcome to {bot_name}!</b>\n\nYou've successfully joined. Explore our products!",
    "terms_message":        "📋 <b>Terms of Service</b>\n\nBy using this bot you agree to our terms...",
    "payment_instructions": "💳 Send the exact amount to the address shown.\nAfter sending, submit your transaction hash.",

    # Support
    "support_username":     "@support",

    # Force Subscribe
    "force_subscribe":      False,

    # Security
    "captcha_enabled":      False,
    "anti_spam_cooldown":   1,
    "max_requests_minute":  30,

    # Notifications
    "login_notify":         True,
    "order_logs":           True,

    # Payment / Wallet
    "usdt_wallet":          "YOUR_USDT_TRC20_WALLET",
    "usdt_network":         "TRC20",
    "min_deposit":          1.0,
    "min_withdrawal":       5.0,
    "currency":             "USD",
    "currency_symbol":      "$",

    # Stars
    "stars_enabled":        True,
    "stars_per_dollar":     50,
    "stars_exchange_rate":  50,
    "stars_bonus_pct":      0,

    # Referral
    "referral_enabled":     True,
    "referral_bonus":       0.5,
    "referral_bonus_type":  "balance",
    "referral_stars_bonus": 10,
    "referral_min_invites": 0,
    "referral_purchase_bonus": 0.05,

    # Products
    "auto_delivery":        True,
    "product_auto_delete":  False,
    "required_referrals":   0,
    "bonus_rewards":        0.0,

    # Daily Gift
    "daily_gift_enabled":       False,
    "daily_gift_points":        1.0,
    "daily_gift_cooldown_hours": 24,
}

# ─────────────────────────────────────────────
#  SUPPORTED FILE TYPES
# ─────────────────────────────────────────────
SUPPORTED_FILE_TYPES = {
    "document":  ["zip", "apk", "txt", "pdf", "exe", "rar", "7z", "csv", "json", "xml"],
    "photo":     ["jpg", "jpeg", "png", "webp", "gif"],
    "video":     ["mp4", "mov", "avi", "mkv"],
    "audio":     ["mp3", "ogg", "wav", "flac"],
    "animation": ["gif", "mp4"],
    "text":      ["txt"],
}


# ─────────────────────────────────────────────
#  EMOJIS (UI constants)
# ─────────────────────────────────────────────
class Emoji:
    SHOP       = "🛒"
    PRODUCT    = "📦"
    CATEGORY   = "📂"
    CART       = "🛍️"
    BALANCE    = "💰"
    WALLET     = "👛"
    STARS      = "⭐"
    USDT       = "💎"
    ADMIN      = "👑"
    SETTINGS   = "⚙️"
    STATS      = "📊"
    USERS      = "👥"
    BAN        = "🚫"
    UNBAN      = "✅"
    BROADCAST  = "📢"
    LOG        = "📋"
    SEARCH     = "🔍"
    ORDER      = "📜"
    REFERRAL   = "🔗"
    COUPON     = "🎟️"
    PROFILE    = "👤"
    SUPPORT    = "💬"
    BACK       = "◀️"
    NEXT       = "▶️"
    HOME       = "🏠"
    ADD        = "➕"
    DELETE     = "🗑️"
    EDIT       = "✏️"
    CHECK      = "✔️"
    CROSS      = "✖️"
    ON         = "✅"
    OFF        = "❌"
    TOGGLE_ON  = "🟢"
    TOGGLE_OFF = "🔴"
    FIRE       = "🔥"
    DIAMOND    = "💎"
    CROWN      = "👑"
    LOCK       = "🔒"
    UNLOCK     = "🔓"
    MONEY      = "💵"
    GIFT       = "🎁"
    BACKUP     = "💾"
    NOTIFY     = "🔔"
    SUCCESS    = "✅"
    ERROR      = "❌"
    WARNING    = "⚠️"
    INFO       = "ℹ️"
    LOADING    = "⏳"
    REFRESH    = "🔄"
    LANGUAGE   = "🌐"
    PAYMENT    = "💳"
    DELIVERY   = "🚀"
    SUBSCRIBE  = "📌"
    CAPTCHA    = "🤖"
    HISTORY    = "📅"
    EXPORT     = "📤"
    TRENDING   = "📈"
    SHIELD     = "🛡️"
    KEY        = "🔑"
    CHANNEL    = "📡"
    PACKAGE    = "🎁"
    CHART      = "📈"
    LEADERBOARD= "🏆"
