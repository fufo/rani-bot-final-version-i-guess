"""
╔══════════════════════════════════════════════════════════╗
║   TELEGRAM SHOP BOT — NEW FEATURES                      ║
║   Flash Sale · Product of Day · Pending Orders          ║
║   Win-Back · Daily Stats · My Products                  ║
╚══════════════════════════════════════════════════════════╝
"""

import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import database as db
from utils.helpers import (
    is_admin, safe_edit_message, safe_answer_callback,
    format_price, UserState
)

logger = logging.getLogger(__name__)


def _lang(context): return context.user_data.get("lang", "en")


# ─────────────────────────────────────────────
#  MY PRODUCTS (user's purchase history with redownload)
# ─────────────────────────────────────────────

async def my_products_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    orders, total = db.get_user_orders(user.id, 1, 50)
    completed = [o for o in orders if o.get("status") == "completed" and o.get("file_id")]

    if not completed:
        await safe_edit_message(
            update,
            "🗂️ <b>My Products</b>\n\nYou haven't purchased any downloadable products yet.",
            InlineKeyboardMarkup([[InlineKeyboardButton("🛍️ Shop", callback_data="shop"),
                                   InlineKeyboardButton("🏠 Home", callback_data="home")]]),
            "HTML"
        )
        return

    rows = []
    for o in completed[:20]:
        name = (o.get("product_name") or "Product")[:30]
        rows.append([InlineKeyboardButton(
            f"📦 {name}",
            callback_data=f"redownload:{o['order_id']}"
        )])

    rows.append([InlineKeyboardButton("🏠 Home", callback_data="home")])
    await safe_edit_message(
        update,
        f"🗂️ <b>My Products</b>\n\n{len(completed)} downloadable purchase(s).\nTap to re-download:",
        InlineKeyboardMarkup(rows),
        "HTML"
    )


async def redownload_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, order_id: str):
    user = update.effective_user
    orders, _ = db.get_user_orders(user.id, 1, 200)
    order = next((o for o in orders if str(o.get("order_id")) == str(order_id)), None)

    if not order:
        await safe_answer_callback(update, "❌ Order not found.", show_alert=True)
        return

    if not order.get("file_id"):
        await safe_answer_callback(update, "❌ No file attached to this order.", show_alert=True)
        return

    file_type = order.get("file_type", "document")
    caption = f"📦 <b>{order.get('product_name', 'Product')}</b>\n🧾 Order: <code>{order_id}</code>"

    try:
        send_fn = {
            "photo":    context.bot.send_photo,
            "video":    context.bot.send_video,
            "audio":    context.bot.send_audio,
            "animation":context.bot.send_animation,
            "voice":    context.bot.send_voice,
        }.get(file_type, context.bot.send_document)

        await send_fn(chat_id=user.id, **{
            "photo" if file_type == "photo" else
            "video" if file_type == "video" else
            "audio" if file_type == "audio" else
            "animation" if file_type == "animation" else
            "voice" if file_type == "voice" else
            "document": order["file_id"]
        }, caption=caption, parse_mode="HTML")

        await safe_answer_callback(update, "✅ File sent!", show_alert=False)
    except Exception as e:
        await safe_answer_callback(update, f"❌ Could not send file: {str(e)[:60]}", show_alert=True)


# ─────────────────────────────────────────────
#  TRACK ORDER (user)
# ─────────────────────────────────────────────

async def track_order_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = _lang(context)
    context.user_data[UserState.AWAITING_TRACK_ORDER] = True
    await safe_edit_message(
        update,
        "🔍 <b>Track Order</b>\n\nEnter your Order ID:",
        InlineKeyboardMarkup([[InlineKeyboardButton("✖️ Cancel", callback_data="home")]]),
        "HTML"
    )


async def show_order_status(update: Update, context: ContextTypes.DEFAULT_TYPE, order_id: str):
    user = update.effective_user
    orders, _ = db.get_user_orders(user.id, 1, 200)
    order = next((o for o in orders if str(o.get("order_id")) == str(order_id).strip()), None)

    if not order:
        await update.message.reply_text(
            "❌ Order not found. Make sure the ID is correct.",
            parse_mode="HTML"
        )
        return

    status_map = {
        "completed": "✅ Completed",
        "pending":   "⏳ Pending",
        "cancelled": "❌ Cancelled",
    }
    status = status_map.get(order.get("status", ""), "❓ Unknown")
    delivered = order.get("delivered_at") or "—"
    created   = order.get("created_at", "—")[:16]

    text = (
        f"🔍 <b>Order Details</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🧾 ID: <code>{order_id}</code>\n"
        f"📦 Product: <b>{order.get('product_name', '—')}</b>\n"
        f"💰 Amount: <b>${order.get('amount', 0):.2f}</b>\n"
        f"💳 Method: <b>{order.get('payment_method', '—')}</b>\n"
        f"📅 Ordered: <b>{created}</b>\n"
        f"🚀 Status: <b>{status}</b>\n"
        f"📬 Delivered: <b>{delivered[:16] if delivered != '—' else '—'}</b>"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 My Orders", callback_data="orders:1"),
         InlineKeyboardButton("🏠 Home", callback_data="home")]
    ])
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=keyboard)


# ─────────────────────────────────────────────
#  FLASH SALE — Admin
# ─────────────────────────────────────────────

async def flash_sale_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await safe_answer_callback(update, "⛔ Access denied", show_alert=True)
        return

    sales = db.get_all_flash_sales_admin()
    active = [s for s in sales if s.get("is_live")]

    lines = []
    for s in sales[:10]:
        live = "🔴 LIVE" if s.get("is_live") else "⏸️"
        lines.append(f"{live} {s['product_name'][:25]} — {s['discount']}% off\n"
                     f"   ⏰ {s['starts_at'][:16]} → {s['ends_at'][:16]}")

    text = (
        f"⚡ <b>Flash Sales</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔴 Active: <b>{len(active)}</b>\n\n"
        + ("\n\n".join(lines) if lines else "No flash sales yet.")
    )

    rows = [
        [InlineKeyboardButton("➕ New Flash Sale", callback_data="fs:new")],
    ]
    for s in active:
        rows.append([InlineKeyboardButton(
            f"🛑 Cancel: {s['product_name'][:20]}",
            callback_data=f"fs:cancel:{s['id']}"
        )])
    rows.append([InlineKeyboardButton("◀️ Admin Panel", callback_data="admin")])

    await safe_edit_message(update, text, InlineKeyboardMarkup(rows), "HTML")


async def flash_sale_new_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    # Step 1: pick product
    products, _ = db.get_all_products_admin(1, 50)
    active_products = [p for p in products if p.get("is_active")]
    if not active_products:
        await safe_answer_callback(update, "❌ No active products found.", show_alert=True)
        return

    rows = [[InlineKeyboardButton(
        f"📦 {p['name'][:30]} — ${p['price']:.2f}",
        callback_data=f"fs:pick:{p['id']}"
    )] for p in active_products[:20]]
    rows.append([InlineKeyboardButton("✖️ Cancel", callback_data="fs:panel")])

    await safe_edit_message(
        update,
        "⚡ <b>New Flash Sale</b>\n\nStep 1: Choose a product:",
        InlineKeyboardMarkup(rows),
        "HTML"
    )


async def flash_sale_pick_product(update: Update, context: ContextTypes.DEFAULT_TYPE, product_id: int):
    context.user_data["fs_product_id"] = product_id
    context.user_data[UserState.ADMIN_FLASH_SALE_STEP] = "discount"
    product = db.get_product(product_id)
    await safe_edit_message(
        update,
        f"⚡ <b>Flash Sale</b> — {product['name']}\n\n"
        f"Step 2: Enter discount percentage (e.g. 20 for 20% off):",
        InlineKeyboardMarkup([[InlineKeyboardButton("✖️ Cancel", callback_data="fs:panel")]]),
        "HTML"
    )


async def flash_sale_save(admin_id: int, product_id: int, discount: float,
                          hours: float, context) -> str:
    """Create flash sale, returns confirmation text."""
    now = datetime.now()
    ends = now + timedelta(hours=hours)
    db.create_flash_sale(
        product_id=product_id,
        discount=discount,
        starts_at=now.strftime("%Y-%m-%d %H:%M:%S"),
        ends_at=ends.strftime("%Y-%m-%d %H:%M:%S"),
        admin_id=admin_id
    )
    db.add_admin_log(admin_id, "create_flash_sale",
                     f"Product #{product_id}, {discount}% off, {hours}h")
    product = db.get_product(product_id)
    return (
        f"⚡ <b>Flash Sale Created!</b>\n\n"
        f"📦 {product['name']}\n"
        f"💥 Discount: <b>{discount}%</b>\n"
        f"⏰ Ends: <b>{ends.strftime('%Y-%m-%d %H:%M')}</b>"
    )


async def flash_sale_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE, sale_id: int):
    db.cancel_flash_sale(sale_id)
    db.add_admin_log(update.effective_user.id, "cancel_flash_sale", f"Sale #{sale_id}")
    await safe_answer_callback(update, "✅ Flash sale cancelled", show_alert=False)
    await flash_sale_panel(update, context)


# ─────────────────────────────────────────────
#  FLASH SALE — User view
# ─────────────────────────────────────────────

async def flash_sales_user_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = _lang(context)
    sales = db.get_active_flash_sales()

    if not sales:
        await safe_edit_message(
            update,
            "⚡ <b>Flash Sales</b>\n\nNo active flash sales right now. Check back later!",
            InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="home")]]),
            "HTML"
        )
        return

    rows = []
    text_lines = ["⚡ <b>Flash Sales — Limited Time!</b>\n━━━━━━━━━━━━━━━━━━━━\n"]

    for s in sales:
        ends = datetime.strptime(s["ends_at"], "%Y-%m-%d %H:%M:%S")
        remaining = ends - datetime.now()
        h, rem = divmod(int(remaining.total_seconds()), 3600)
        m = rem // 60
        old_price = s["price"]
        new_price = old_price * (1 - s["discount"] / 100)
        text_lines.append(
            f"📦 <b>{s['name']}</b>\n"
            f"  💥 <b>{s['discount']}% OFF</b>  "
            f"~~${old_price:.2f}~~ → <b>${new_price:.2f}</b>\n"
            f"  ⏳ {h}h {m}m remaining"
        )
        rows.append([InlineKeyboardButton(
            f"📦 {s['name'][:30]} — ${new_price:.2f}",
            callback_data=f"product:{s['product_id']}"
        )])

    rows.append([InlineKeyboardButton("🏠 Home", callback_data="home")])
    await safe_edit_message(update, "\n\n".join(text_lines),
                             InlineKeyboardMarkup(rows), "HTML")


# ─────────────────────────────────────────────
#  PRODUCT OF THE DAY — Admin set
# ─────────────────────────────────────────────

async def set_product_of_day_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    products, _ = db.get_all_products_admin(1, 50)
    active = [p for p in products if p.get("is_active")]
    rows = [[InlineKeyboardButton(
        f"📦 {p['name'][:30]}",
        callback_data=f"pod:set:{p['id']}"
    )] for p in active[:20]]
    rows.append([InlineKeyboardButton("✖️ Cancel", callback_data="admin")])
    await safe_edit_message(
        update,
        "🌟 <b>Set Product of the Day</b>\n\nChoose a product:",
        InlineKeyboardMarkup(rows),
        "HTML"
    )


async def set_product_of_day_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                      product_id: int):
    db.set_product_of_day(product_id, update.effective_user.id)
    product = db.get_product(product_id)
    await safe_answer_callback(update, f"✅ {product['name']} set as Product of the Day!",
                                show_alert=False)
    await safe_edit_message(
        update,
        f"🌟 <b>Product of the Day Set!</b>\n\n📦 {product['name']}\n💰 ${product['price']:.2f}",
        InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Admin Panel", callback_data="admin")]]),
        "HTML"
    )


# ─────────────────────────────────────────────
#  PRODUCT OF THE DAY — User view
# ─────────────────────────────────────────────

async def product_of_day_user_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = _lang(context)
    product = db.get_product_of_day()

    if not product or not product.get("is_active"):
        await safe_edit_message(
            update,
            "🌟 <b>Product of the Day</b>\n\nNo featured product today. Check back tomorrow!",
            InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="home")]]),
            "HTML"
        )
        return

    sale = db.get_flash_sale_for_product(product["id"])
    price_line = f"💰 Price: <b>${product['price']:.2f}</b>"
    if sale:
        new_price = product["price"] * (1 - sale["discount"] / 100)
        price_line = (f"💰 Price: ~~${product['price']:.2f}~~ → "
                      f"<b>${new_price:.2f}</b> ⚡{sale['discount']}% OFF")

    stock = product.get("stock", -1)
    stock_text = "Unlimited" if stock == -1 else (str(stock) if stock > 0 else "❌ Out of Stock")
    text = (
        f"🌟 <b>Product of the Day</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📦 <b>{product['name']}</b>\n"
        f"{price_line}\n"
        f"📦 Stock: <b>{stock_text}</b>\n"
        + (f"\n📝 {product['description']}" if product.get("description") else "")
    )

    from keyboards.inline import product_detail_keyboard
    keyboard = product_detail_keyboard(
        product_id=product["id"], stock=stock,
        price=product["price"], price_stars=product.get("price_stars", 0),
        lang=lang, category_id=product.get("category_id")
    )
    await safe_edit_message(update, text, keyboard, "HTML")


# ─────────────────────────────────────────────
#  PENDING ORDERS PANEL (Admin)
# ─────────────────────────────────────────────

async def pending_orders_panel(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 1):
    if not is_admin(update.effective_user.id):
        await safe_answer_callback(update, "⛔ Access denied", show_alert=True)
        return

    orders, total = db.get_pending_orders_admin(page, 10)
    total_pages = max(1, (total + 9) // 10)

    if not orders:
        await safe_edit_message(
            update,
            "⏳ <b>Pending Orders</b>\n\n✅ No pending orders!",
            InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Admin Panel", callback_data="admin")]]),
            "HTML"
        )
        return

    rows = []
    for o in orders:
        name = (o.get("first_name") or f"User#{o['user_id']}")[:15]
        prod = (o.get("product_name") or "?")[:20]
        rows.append([InlineKeyboardButton(
            f"⏳ {prod} — {name} — ${o['amount']:.2f}",
            callback_data=f"po:detail:{o['order_id']}"
        )])

    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"po:list:{page-1}"))
    nav.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav.append(InlineKeyboardButton("▶️", callback_data=f"po:list:{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton("◀️ Admin Panel", callback_data="admin")])

    await safe_edit_message(
        update,
        f"⏳ <b>Pending Orders</b> ({total} total) — Page {page}/{total_pages}",
        InlineKeyboardMarkup(rows),
        "HTML"
    )


# ─────────────────────────────────────────────
#  DAILY STATS JOB
# ─────────────────────────────────────────────

async def send_daily_stats(context: ContextTypes.DEFAULT_TYPE):
    """Job: send daily stats to all admins every morning at 8:00 AM."""
    try:
        stats = db.get_statistics()
        admin_ids = db.get_admin_ids()

        text = (
            f"📊 <b>Daily Report — {datetime.now().strftime('%Y-%m-%d')}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👥 New Users Today: <b>{stats.get('new_users_today', 0)}</b>\n"
            f"🛒 Orders Today: <b>{stats.get('orders_today', 0)}</b>\n"
            f"💵 Revenue Today: <b>${format_price(stats.get('revenue_today', 0))}</b>\n\n"
            f"📦 Active Products: <b>{stats.get('active_products', 0)}</b>\n"
            f"💎 Pending Deposits: <b>{stats.get('pending_deposits', 0)}</b>\n"
            f"👥 Total Users: <b>{stats.get('total_users', 0):,}</b>\n"
            f"💰 Total Revenue: <b>${format_price(stats.get('total_revenue', 0))}</b>"
        )

        for admin_id in admin_ids:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=text,
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.warning(f"Could not send daily stats to admin {admin_id}: {e}")

    except Exception as e:
        logger.error(f"Daily stats job failed: {e}")


# ─────────────────────────────────────────────
#  WIN-BACK JOB
# ─────────────────────────────────────────────

async def send_winback_notifications(context: ContextTypes.DEFAULT_TYPE):
    """Job: notify users who haven't used the bot in 7 days."""
    try:
        inactive = db.get_inactive_users(days=7)
        winback_msg = db.get_setting(
            "winback_message",
            "👋 <b>We miss you!</b>\n\n"
            "Come back and check our latest products — new offers are waiting for you! 🎁"
        )
        sent = 0
        for user in inactive:
            try:
                await context.bot.send_message(
                    chat_id=user["user_id"],
                    text=winback_msg,
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🛍️ Shop Now", url=f"https://t.me/{context.bot.username}")
                    ]])
                )
                sent += 1
                import asyncio
                await asyncio.sleep(0.05)  # rate limit
            except Exception:
                pass

        if sent:
            admin_ids = db.get_admin_ids()
            for admin_id in admin_ids:
                try:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=f"📣 <b>Win-Back Campaign</b>\n\n✅ Sent to <b>{sent}</b> inactive users.",
                        parse_mode="HTML"
                    )
                except Exception:
                    pass

    except Exception as e:
        logger.error(f"Win-back job failed: {e}")
