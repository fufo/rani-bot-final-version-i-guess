"""
╔══════════════════════════════════════════════════════════╗
║       TELEGRAM SHOP BOT - DELIVERY SYSTEM                ║
║  Auto-retry, logs, purchase history restore              ║
╚══════════════════════════════════════════════════════════╝
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import database as db
from utils.helpers import (
    safe_edit_message, safe_answer_callback, send_product_file,
    is_admin, format_datetime
)
from utils.formatting import DIV_BOLD

logger = logging.getLogger(__name__)

MAX_DELIVERY_ATTEMPTS = 3


# ─────────────────────────────────────────────
#  SMART DELIVERY (with retry & logging)
# ─────────────────────────────────────────────

async def deliver_product(context: ContextTypes.DEFAULT_TYPE,
                           user_id: int, product: dict,
                           order_id: str, attempt: int = 1) -> bool:
    """
    Deliver a product to a user. Logs result.
    Returns True on success.
    """
    if not (product.get("file_id") or product.get("text_content")):
        return True  # Nothing to deliver

    name = product.get("name", "Product")
    caption = (
        f"📦 <b>{name}</b>\n"
        f"✅ Order: <code>{order_id}</code>\n"
        f"🛒 Thank you for your purchase!"
    )

    success = await send_product_file(context, user_id, product, caption=caption)

    db.log_delivery(
        order_id=order_id,
        user_id=user_id,
        product_id=product["id"],
        attempt=attempt,
        status="success" if success else "failed",
        error_msg="" if success else "Delivery failed"
    )

    if not success and attempt < MAX_DELIVERY_ATTEMPTS:
        logger.warning(
            f"Delivery attempt {attempt} failed for order {order_id}, "
            f"will retry (attempt {attempt + 1})"
        )
        import asyncio
        await asyncio.sleep(2 ** attempt)  # Exponential back-off
        return await deliver_product(context, user_id, product, order_id, attempt + 1)

    return success


# ─────────────────────────────────────────────
#  ADMIN: FAILED DELIVERIES PANEL
# ─────────────────────────────────────────────

async def failed_deliveries_panel(update: Update,
                                   context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        await safe_answer_callback(update, "⛔ Access denied", show_alert=True)
        return

    failed = db.get_failed_deliveries()
    if not failed:
        await safe_edit_message(
            update,
            "✅ <b>Failed Deliveries</b>\n\nNo failed deliveries. All good!",
            InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Back", callback_data="admin")
            ]]),
            "HTML"
        )
        return

    lines = []
    rows = []
    for item in failed[:10]:
        name = item.get("product_name", "?")
        uid = item.get("user_id")
        oid = item.get("order_id", "?")
        lines.append(f"• <code>{oid}</code> · {name[:20]} · uid <code>{uid}</code>")
        rows.append([InlineKeyboardButton(
            f"🔄 Resend: {name[:20]}",
            callback_data=f"delivery:resend:{oid}"
        )])

    rows.append([InlineKeyboardButton("◀️ Back", callback_data="admin")])

    text = (
        f"⚠️ <b>Failed Deliveries</b>\n{DIV_BOLD}\n\n"
        + "\n".join(lines)
    )
    await safe_edit_message(update, text, InlineKeyboardMarkup(rows), "HTML")


# ─────────────────────────────────────────────
#  ADMIN: RESEND DELIVERY
# ─────────────────────────────────────────────

async def resend_delivery(update: Update,
                           context: ContextTypes.DEFAULT_TYPE,
                           order_id: str) -> None:
    if not is_admin(update.effective_user.id):
        return

    with db.get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT o.*, p.file_id, p.file_type, p.text_content,
                   p.name, p.id as pid
            FROM orders o
            JOIN products p ON o.product_id = p.id
            WHERE o.order_id = ?
        """, (order_id,))
        row = c.fetchone()

    if not row:
        await safe_answer_callback(update, "❌ Order not found", show_alert=True)
        return

    order = dict(row)
    product = {
        "id": order["pid"],
        "name": order["name"],
        "file_id": order.get("file_id"),
        "file_type": order.get("file_type"),
        "text_content": order.get("text_content"),
    }

    success = await deliver_product(
        context, order["user_id"], product, order_id, attempt=1
    )

    msg = "✅ Re-delivered successfully!" if success else "❌ Re-delivery failed again."
    await safe_answer_callback(update, msg, show_alert=True)
    db.add_admin_log(
        update.effective_user.id,
        "resend_delivery",
        f"Order {order_id} — {'success' if success else 'failed'}"
    )
    await failed_deliveries_panel(update, context)


# ─────────────────────────────────────────────
#  USER: RESTORE PREVIOUS PURCHASE
# ─────────────────────────────────────────────

async def restore_purchase_handler(update: Update,
                                    context: ContextTypes.DEFAULT_TYPE,
                                    order_id: str) -> None:
    user = update.effective_user

    with db.get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT o.*, p.file_id, p.file_type, p.text_content,
                   p.name, p.id as pid
            FROM orders o
            JOIN products p ON o.product_id = p.id
            WHERE o.order_id = ? AND o.user_id = ? AND o.status = 'completed'
        """, (order_id, user.id))
        row = c.fetchone()

    if not row:
        await safe_answer_callback(update, "❌ Order not found.", show_alert=True)
        return

    order = dict(row)

    if not (order.get("file_id") or order.get("text_content")):
        await safe_answer_callback(
            update, "ℹ️ No file deliverable for this product.", show_alert=True
        )
        return

    product = {
        "id": order["pid"],
        "name": order["name"],
        "file_id": order.get("file_id"),
        "file_type": order.get("file_type"),
        "text_content": order.get("text_content"),
    }

    await safe_answer_callback(update, "📦 Resending your purchase...", show_alert=False)
    success = await deliver_product(context, user.id, product, order_id, attempt=1)
    if not success:
        await context.bot.send_message(
            chat_id=user.id,
            text="❌ Could not resend. Please contact support.",
            parse_mode="HTML"
        )
