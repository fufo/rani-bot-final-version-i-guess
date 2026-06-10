"""
╔══════════════════════════════════════════════════════════╗
║           TELEGRAM SHOP BOT - UTILITY FUNCTIONS          ║
╚══════════════════════════════════════════════════════════╝
"""

import time
import logging
from typing import Dict, Optional, Callable, Any
from datetime import datetime
from functools import wraps

from telegram import Update
from telegram.ext import ContextTypes

from config import PRIMARY_ADMIN_ID

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
#  ADMIN CHECK (DB-backed with cache)
# ─────────────────────────────────────────────

def is_admin(user_id: int) -> bool:
    """Check if user is admin — checks primary owner + DB admin list."""
    if user_id == PRIMARY_ADMIN_ID:
        return True
    try:
        import database as db
        return user_id in db.get_admin_ids()
    except Exception:
        return False


def is_owner(user_id: int) -> bool:
    """Check if user is the primary owner (cannot be removed)."""
    return user_id == PRIMARY_ADMIN_ID


# ─────────────────────────────────────────────
#  ANTI-SPAM / RATE LIMITER
# ─────────────────────────────────────────────

_rate_tracker: Dict[int, list] = {}
_last_action: Dict[int, float] = {}


def is_rate_limited(user_id: int, cooldown: int = 1, max_per_min: int = 30) -> bool:
    now = time.time()

    # Per-action cooldown
    if user_id in _last_action:
        if now - _last_action[user_id] < cooldown:
            return True
    _last_action[user_id] = now

    # Per-minute cap
    if user_id not in _rate_tracker:
        _rate_tracker[user_id] = []
    _rate_tracker[user_id] = [t for t in _rate_tracker[user_id] if now - t < 60]
    if len(_rate_tracker[user_id]) >= max_per_min:
        return True
    _rate_tracker[user_id].append(now)
    return False


# ─────────────────────────────────────────────
#  USER STATE MANAGER
# ─────────────────────────────────────────────

class UserState:
    AWAITING_SEARCH       = "awaiting_search"
    AWAITING_DEPOSIT_AMT  = "awaiting_deposit_amount"
    AWAITING_TX_HASH      = "awaiting_tx_hash"
    AWAITING_COUPON       = "awaiting_coupon"
    AWAITING_CAPTCHA      = "awaiting_captcha"
    CAPTCHA_ANSWER        = "captcha_answer"
    PENDING_PRODUCT_ID    = "pending_product_id"
    PENDING_PAYMENT       = "pending_payment_method"
    PENDING_COUPON        = "applied_coupon"
    PENDING_COUPON_DISC   = "coupon_discount"

    # Games
    GAME_AWAITING_BET     = "game_awaiting_bet"

    # Admin states — products
    ADMIN_ADD_PRODUCT     = "admin_add_product"
    ADMIN_EDIT_PRODUCT    = "admin_edit_product"
    ADMIN_PRODUCT_STEP    = "admin_product_step"
    ADMIN_PRODUCT_DATA    = "admin_product_data"

    # Admin states — categories
    ADMIN_ADD_CATEGORY    = "admin_add_category"

    # Admin states — users
    ADMIN_BAN_USER        = "admin_ban_user"
    ADMIN_ADJUST_BAL      = "admin_adjust_balance"
    ADMIN_ADD_ADMIN       = "admin_add_admin"
    ADMIN_SEARCH_USER     = "admin_search_user"

    # Admin states — broadcast
    ADMIN_BROADCAST       = "admin_broadcast"

    # Admin states — coupons
    ADMIN_ADD_COUPON      = "admin_add_coupon"

    # Admin states — settings
    ADMIN_EDIT_SETTING    = "admin_edit_setting"
    ADMIN_EDIT_SETTING_KEY= "admin_edit_setting_key"
    ADMIN_EDIT_WELCOME    = "admin_edit_welcome"

    # Admin states — force subscribe
    ADMIN_ADD_CHANNEL     = "admin_add_channel"

    # Admin states — user management / filtering
    UF_SEARCH             = "uf_search"
    UF_ADD_NOTE           = "uf_add_note"
    UF_EDIT_NOTE          = "uf_edit_note"
    UF_BULK_INPUT         = "uf_bulk_input"

    # Admin states — stars packages
    ADMIN_ADD_STARS_PKG   = "admin_add_stars_pkg"
    ADMIN_EDIT_STARS_PKG  = "admin_edit_stars_pkg"

    # Deposit confirmation
    ADMIN_DEPOSIT_CONFIRM = "admin_deposit_confirm"

    # Database upload
    ADMIN_UPLOAD_DB       = "admin_upload_db"

    # File edit (upload .py or any bot file to replace on server)
    ADMIN_UPLOAD_FILE     = "admin_upload_file"

    # Flash sale wizard
    ADMIN_FLASH_SALE_STEP = "admin_flash_sale_step"

    # Track order
    AWAITING_TRACK_ORDER  = "awaiting_track_order"


# ─────────────────────────────────────────────
#  TEXT FORMATTING
# ─────────────────────────────────────────────

def format_price(amount: float) -> str:
    return f"{amount:.2f}"


def format_date(date_str: str) -> str:
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d %b %Y")
    except Exception:
        return date_str or "—"


def format_datetime(date_str: str) -> str:
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d %b %Y %H:%M")
    except Exception:
        return date_str or "—"


def get_user_display_name(user) -> str:
    if hasattr(user, 'first_name'):
        name = user.first_name or ""
        if user.last_name:
            name += f" {user.last_name}"
        return name.strip() or f"User#{user.id}"
    name = user.get("first_name") or ""
    if user.get("last_name"):
        name += f" {user['last_name']}"
    return name.strip() or f"User#{user.get('user_id', '?')}"


def get_stock_display(stock: int, lang: str = "en") -> str:
    from languages.strings import _
    if stock == -1:
        return _("stock_unlimited", lang)
    if stock == 0:
        return _("out_of_stock", lang)
    return str(stock)


# ─────────────────────────────────────────────
#  CAPTCHA
# ─────────────────────────────────────────────

def generate_captcha() -> tuple:
    import random
    a = random.randint(1, 20)
    b = random.randint(1, 20)
    return {"a": a, "b": b}, a + b


# ─────────────────────────────────────────────
#  REFERRAL
# ─────────────────────────────────────────────

def build_referral_link(bot_username: str, referral_code: str) -> str:
    return f"https://t.me/{bot_username}?start=ref_{referral_code}"


def parse_start_payload(payload: str) -> Optional[str]:
    if payload and payload.startswith("ref_"):
        return payload[4:]
    return None


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


# ─────────────────────────────────────────────
#  DECORATORS
# ─────────────────────────────────────────────

def admin_only(func: Callable) -> Callable:
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if not is_admin(update.effective_user.id):
            if update.callback_query:
                await update.callback_query.answer("⛔ Admin only!", show_alert=True)
            else:
                await update.message.reply_text("⛔ Access denied.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper


# ─────────────────────────────────────────────
#  SAFE MESSAGE HELPERS
# ─────────────────────────────────────────────

async def safe_edit_message(update: Update, text: str,
                             reply_markup=None, parse_mode: str = "HTML") -> bool:
    try:
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=text, reply_markup=reply_markup, parse_mode=parse_mode
            )
        elif update.message:
            # Called from a text-message context (e.g. after a search input)
            await update.message.reply_text(
                text=text, reply_markup=reply_markup, parse_mode=parse_mode
            )
        return True
    except Exception as e:
        if "message is not modified" not in str(e).lower():
            logger.warning(f"edit_message: {e}")
    return False


async def safe_answer_callback(update: Update, text: str = "",
                                show_alert: bool = False) -> None:
    try:
        if update.callback_query:
            await update.callback_query.answer(text, show_alert=show_alert)
    except Exception:
        pass


# ─────────────────────────────────────────────
#  FILE TYPE DETECTION
# ─────────────────────────────────────────────

def detect_file_type(message) -> tuple:
    if message.document:
        return "document", message.document.file_id, message.document.file_name
    elif message.photo:
        return "photo", message.photo[-1].file_id, "photo.jpg"
    elif message.video:
        return "video", message.video.file_id, "video.mp4"
    elif message.audio:
        return "audio", message.audio.file_id, message.audio.file_name or "audio.mp3"
    elif message.animation:
        return "animation", message.animation.file_id, "animation.gif"
    elif message.voice:
        return "voice", message.voice.file_id, "voice.ogg"
    elif message.sticker:
        return "sticker", message.sticker.file_id, "sticker.webp"
    return None, None, None


async def send_product_file(context: ContextTypes.DEFAULT_TYPE,
                             chat_id: int, product: dict,
                             caption: str = "") -> bool:
    file_id = product.get("file_id")
    file_type = product.get("file_type", "document")
    text_content = product.get("text_content")

    # If product has text content, send it as a message
    if text_content:
        try:
            import re as _re
            def _linkify(text):
                """Convert bare URLs to HTML <a> links."""
                url_pattern = _re.compile(r"(https?://\S+|t\.me/\S+)")
                def make_link(m):
                    url = m.group(1)
                    if not url.startswith("http"):
                        url = "https://" + url
                    return '<a href="' + url + '">' + m.group(1) + '</a>'
                return url_pattern.sub(make_link, text)

            formatted_content = _linkify(text_content)
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"{caption}\n\n📄 <b>Product Content:</b>\n\n{formatted_content}",
                parse_mode="HTML",
                disable_web_page_preview=True
            )
            return True
        except Exception as e:
            logger.error(f"Text delivery error: {e}")
            return False

    if not file_id:
        return False
    try:
        if file_type == "photo":
            await context.bot.send_photo(chat_id=chat_id, photo=file_id,
                                          caption=caption, parse_mode="HTML")
        elif file_type == "video":
            await context.bot.send_video(chat_id=chat_id, video=file_id,
                                          caption=caption, parse_mode="HTML")
        elif file_type == "audio":
            await context.bot.send_audio(chat_id=chat_id, audio=file_id,
                                          caption=caption, parse_mode="HTML")
        elif file_type == "animation":
            await context.bot.send_animation(chat_id=chat_id, animation=file_id,
                                              caption=caption, parse_mode="HTML")
        elif file_type == "voice":
            await context.bot.send_voice(chat_id=chat_id, voice=file_id,
                                          caption=caption, parse_mode="HTML")
        else:
            await context.bot.send_document(chat_id=chat_id, document=file_id,
                                             caption=caption, parse_mode="HTML")
        return True
    except Exception as e:
        logger.error(f"File delivery error: {e}")
        return False
