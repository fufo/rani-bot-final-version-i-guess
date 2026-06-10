"""
╔══════════════════════════════════════════════════════════╗
║       TELEGRAM SHOP BOT - RATING / REVIEW SYSTEM         ║
║  Users rate purchased products; shown on product pages   ║
╚══════════════════════════════════════════════════════════╝
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import database as db
from utils.helpers import safe_edit_message, safe_answer_callback
from utils.formatting import DIV_BOLD

logger = logging.getLogger(__name__)

STAR_LABELS = {1: "😞 Poor", 2: "😕 Fair", 3: "😐 OK", 4: "😊 Good", 5: "🤩 Excellent"}

# ─────────────────────────────────────────────
#  SHARED: STAR SELECTION KEYBOARD
# ─────────────────────────────────────────────

def _star_keyboard(product_id: int, order_id: str) -> InlineKeyboardMarkup:
    """Keyboard shown when user needs to pick a star rating (1–5 only)."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("1 ⭐", callback_data=f"rate:{product_id}:{order_id}:1"),
            InlineKeyboardButton("2 ⭐", callback_data=f"rate:{product_id}:{order_id}:2"),
            InlineKeyboardButton("3 ⭐", callback_data=f"rate:{product_id}:{order_id}:3"),
        ],
        [
            InlineKeyboardButton("4 ⭐", callback_data=f"rate:{product_id}:{order_id}:4"),
            InlineKeyboardButton("5 ⭐", callback_data=f"rate:{product_id}:{order_id}:5"),
        ],
        [InlineKeyboardButton("⏭️ Skip", callback_data="home")],
    ])


# ─────────────────────────────────────────────
#  PROMPT USER TO RATE (called post-purchase)
# ─────────────────────────────────────────────

async def prompt_rating(context: ContextTypes.DEFAULT_TYPE,
                         user_id: int, product_id: int,
                         product_name: str, order_id: str) -> None:
    """Send a new rating prompt message after a purchase completes."""
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                f"⭐ <b>Rate Your Purchase</b>\n"
                f"{DIV_BOLD}\n\n"
                f"How was <b>{product_name}</b>?\n"
                f"Tap a star to rate:"
            ),
            parse_mode="HTML",
            reply_markup=_star_keyboard(product_id, order_id),
        )
    except Exception as e:
        logger.warning(f"Rating prompt failed for {user_id}: {e}")


# ─────────────────────────────────────────────
#  SHOW STAR PICKER (from pending-ratings list)
# ─────────────────────────────────────────────

async def show_star_picker(update: Update,
                            context: ContextTypes.DEFAULT_TYPE,
                            product_id: int, order_id: str,
                            product_name: str = "") -> None:
    """
    Edit the current message to show the star-picker.
    Called when rating=0 (user clicked 'Rate' from profile/order detail).
    """
    # Clear any stale pending_rating so a leftover review-text state can't fire
    context.user_data.pop("pending_rating", None)
    context.user_data.pop("awaiting_review_text", None)

    label = f" <b>{product_name}</b>" if product_name else ""
    await safe_edit_message(
        update,
        f"⭐ <b>Rate Your Purchase</b>{label}\n"
        f"{DIV_BOLD}\n\n"
        f"Tap a star to rate:",
        _star_keyboard(product_id, order_id),
        "HTML",
    )


# ─────────────────────────────────────────────
#  HANDLE STAR SELECTION (rating 1–5)
# ─────────────────────────────────────────────

async def handle_rating_callback(update: Update,
                                  context: ContextTypes.DEFAULT_TYPE,
                                  product_id: int, order_id: str,
                                  rating: int) -> None:
    """
    Called when user taps a star button (rating must be 1–5).
    Saves the choice and asks for an optional text review.
    """
    if rating < 1 or rating > 5:
        # Defensive: should never reach here, but guard anyway
        logger.warning(f"handle_rating_callback called with invalid rating={rating}")
        await safe_answer_callback(update, "⭐ Please tap a star (1–5).", show_alert=False)
        return

    label     = STAR_LABELS.get(rating, "")
    stars_str = "⭐" * rating + "☆" * (5 - rating)

    # Store for the optional review-text step
    context.user_data["pending_rating"] = {
        "product_id": product_id,
        "order_id":   order_id,
        "rating":     rating,
    }
    context.user_data["awaiting_review_text"] = True

    await safe_edit_message(
        update,
        f"✅ <b>You rated:</b> {stars_str}  {label}\n\n"
        f"💬 <i>Optional:</i> Type a short review below,\n"
        f"or tap <b>Skip</b> to submit now:",
        InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "⏭️ Skip — submit now",
                callback_data=f"rate_submit:{product_id}:{order_id}:{rating}",
            )
        ]]),
        "HTML",
    )


# ─────────────────────────────────────────────
#  SUBMIT RATING (with or without review text)
# ─────────────────────────────────────────────

async def handle_rating_submit(update: Update,
                                context: ContextTypes.DEFAULT_TYPE,
                                product_id: int, order_id: str,
                                rating: int, review: str = "") -> None:
    """Validate rating (1–5), write to DB, show confirmation."""
    # Clear pending state regardless of outcome
    context.user_data.pop("pending_rating", None)
    context.user_data.pop("awaiting_review_text", None)

    user = update.effective_user

    # Hard guard — never write an invalid rating
    if rating < 1 or rating > 5:
        logger.error(f"handle_rating_submit blocked invalid rating={rating} "
                     f"from user={user.id} product={product_id}")
        await safe_answer_callback(
            update, "❌ Invalid rating. Please tap a star (1–5).", show_alert=True
        )
        return

    if not db.can_rate_product(user.id, product_id):
        await safe_answer_callback(
            update, "❌ You can't rate this product (already rated or not purchased).",
            show_alert=True
        )
        return

    db.add_rating(user.id, product_id, order_id, rating, review)

    from utils.cache import invalidate_product
    invalidate_product(product_id)

    stars_str = "⭐" * rating + "☆" * (5 - rating)
    await safe_edit_message(
        update,
        f"🎉 <b>Thanks for your review!</b>\n\n"
        f"{stars_str}  {STAR_LABELS.get(rating, '')}\n\n"
        f"Your feedback helps improve the store.",
        InlineKeyboardMarkup([[
            InlineKeyboardButton("🏠 Home", callback_data="home")
        ]]),
        "HTML",
    )


# ─────────────────────────────────────────────
#  PENDING RATINGS PAGE
# ─────────────────────────────────────────────

async def pending_ratings_handler(update: Update,
                                   context: ContextTypes.DEFAULT_TYPE) -> None:
    user    = update.effective_user
    pending = db.get_user_pending_ratings(user.id)

    if not pending:
        await safe_edit_message(
            update,
            "⭐ <b>Rate Products</b>\n\n"
            "No pending ratings — buy something to leave a review!",
            InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 Home", callback_data="home")
            ]]),
            "HTML",
        )
        return

    rows = []
    for item in pending[:5]:
        name = item.get("product_name") or item.get("name", "Product")
        # Use :0 as a sentinel that means "show picker", NOT "submit rating 0"
        rows.append([InlineKeyboardButton(
            f"⭐ Rate: {name[:28]}",
            callback_data=f"rate_pick:{item['product_id']}:{item['order_id']}",
        )])
    rows.append([InlineKeyboardButton("🏠 Home", callback_data="home")])

    await safe_edit_message(
        update,
        f"⭐ <b>Rate Your Purchases</b>\n{DIV_BOLD}\n\n"
        f"You have <b>{len(pending)}</b> unrated purchase(s):",
        InlineKeyboardMarkup(rows),
        "HTML",
    )
