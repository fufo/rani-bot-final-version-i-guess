"""
╔══════════════════════════════════════════════════════════╗
║         TELEGRAM SHOP BOT - USER HANDLERS               ║
╚══════════════════════════════════════════════════════════╝
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import database as db
from config import Emoji, PRODUCTS_PER_PAGE, ORDERS_PER_PAGE
from languages.strings import _
from keyboards.inline import (
    main_menu_keyboard, balance_keyboard, deposit_usdt_keyboard,
    subscribe_keyboard, captcha_keyboard, language_keyboard,
    categories_keyboard, products_keyboard, product_detail_keyboard,
    purchase_confirm_keyboard, orders_keyboard, referral_keyboard,
    support_keyboard, cancel_keyboard, stars_packages_keyboard
)
from utils.helpers import (
    is_admin, is_rate_limited, generate_captcha, build_referral_link,
    parse_start_payload, format_price, format_date, get_user_display_name,
    get_stock_display, safe_edit_message, safe_answer_callback,
    send_product_file, UserState, detect_file_type
)

from utils.security import acquire_purchase_lock, release_purchase_lock
from utils.formatting import (
    product_card, order_receipt, fmt_price, fmt_stars, stock_badge,
    DIV_BOLD, toggle_badge, referral_rank_badge, get_next_milestone,
    get_achieved_milestone, MILESTONES
)

logger = logging.getLogger(__name__)


def _lang(context: ContextTypes.DEFAULT_TYPE) -> str:
    return context.user_data.get("lang", "en")


# ─────────────────────────────────────────────
#  SUBSCRIBE CHECK (multi-channel, DB-driven)
# ─────────────────────────────────────────────

async def check_subscribe(bot, user_id: int) -> bool:
    from handlers.force_subscribe_handlers import check_user_subscribed
    return await check_user_subscribed(bot, user_id)


# ─────────────────────────────────────────────
#  /start COMMAND
# ─────────────────────────────────────────────

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return

    referral_code = None
    deep_link_token = None
    if context.args:
        payload = context.args[0]
        if payload.startswith("prod") or payload.startswith("r_"):
            deep_link_token = payload
        else:
            referral_code = parse_start_payload(payload)

    db_user = db.get_or_create_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        referral_code=referral_code
    )

    lang = db_user.get("language", "en")
    context.user_data["lang"] = lang

    # Ban check
    if db_user.get("is_banned"):
        reason = db_user.get("ban_reason") or "No reason"
        await update.message.reply_text(
            _("user_banned", lang, reason=reason), parse_mode="HTML"
        )
        return

    # Maintenance check
    if not db.get_setting("bot_status") and not is_admin(user.id):
        msg = db.get_setting("maintenance_msg") or _("bot_offline", lang)
        await update.message.reply_text(msg, parse_mode="HTML")
        return

    # Captcha check
    if db.get_setting("captcha_enabled") and not db_user.get("captcha_passed") and not is_admin(user.id):
        a, answer = generate_captcha()
        context.user_data[UserState.AWAITING_CAPTCHA] = True
        context.user_data[UserState.CAPTCHA_ANSWER] = answer
        await update.message.reply_text(
            _("captcha_question", lang, a=a["a"], b=a["b"]),
            parse_mode="HTML",
            reply_markup=captcha_keyboard(answer)
        )
        return

    # Force subscribe check (multi-channel, DB-driven)
    if db.get_setting("force_subscribe") and not is_admin(user.id):
        subscribed = await check_subscribe(context.bot, user.id)
        if not subscribed:
            join_msg = db.get_setting("join_message") or _("subscribe_required", lang)
            try:
                join_msg = join_msg.format(
                    bot_name=db.get_setting("bot_name", "Premium Shop Bot")
                )
            except Exception:
                pass
            await update.message.reply_text(
                join_msg,
                parse_mode="HTML",
                reply_markup=subscribe_keyboard(lang)
            )
            return

    # ── Handle deep link tokens (after all access checks) ────────
    if deep_link_token:
        if deep_link_token.startswith("r_"):
            success, msg, points = db.claim_reward_link(deep_link_token, user.id)
            if success:
                await update.message.reply_text(
                    f"🎁 <b>Reward Claimed!</b>\n\n"
                    f"✅ <b>+{points:.2f}</b> points added to your balance!",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("💰 My Balance", callback_data="balance"),
                        InlineKeyboardButton("🏠 Home", callback_data="home"),
                    ]])
                )
            else:
                await update.message.reply_text(
                    f"❌ <b>Cannot Claim Reward</b>\n\n{msg}",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🏠 Home", callback_data="home")
                    ]])
                )
            return
        elif deep_link_token.startswith("prod"):
            product = db.get_product_by_share_token(deep_link_token)
            if product:
                await _open_product_from_share_link(update, context, product)
                return
            # Token not found — fall through to normal menu

    # Login notification — only for users who joined in the last 60 seconds
    if db.get_setting("login_notify") and not is_admin(user.id):
        joined_at = db_user.get("joined_at", "")
        try:
            from datetime import datetime, timedelta
            joined_dt = datetime.strptime(joined_at, "%Y-%m-%d %H:%M:%S")
            is_new = (datetime.utcnow() - joined_dt) < timedelta(seconds=60)
        except Exception:
            is_new = False
        if is_new:
            admin_ids = db.get_admin_ids()
            for admin_id in admin_ids:
                try:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=(
                            f"🔔 <b>New User Joined!</b>\n\n"
                            f"👤 Name: {get_user_display_name(user)}\n"
                            f"🆔 ID: <code>{user.id}</code>\n"
                            f"📛 Username: @{user.username or 'none'}"
                        ),
                        parse_mode="HTML"
                    )
                except Exception:
                    pass

    await show_main_menu(update, context, send_new=True)


# ─────────────────────────────────────────────
#  MAIN MENU
# ─────────────────────────────────────────────

async def _open_product_from_share_link(update, context, product):
    """Open a product page directly from a share link."""
    lang = context.user_data.get("lang", "en")
    from keyboards.inline import product_detail_keyboard
    p_name = product.get(f"name_{lang}") or product.get("name", "Product")
    p_desc = product.get(f"description_{lang}") or product.get("description", "")
    price = product.get("price", 0)
    stock = product.get("stock", -1)
    cat = product.get("category_name", "")
    cat_emoji = product.get("category_emoji", "📦")
    stock_text = "Unlimited" if stock == -1 else (str(stock) if stock > 0 else "Out of Stock")
    text = (
        f"{cat_emoji} <b>{p_name}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📂 Category: <b>{cat}</b>\n"
        f"💰 Price: <b>${price:.2f}</b>\n"
        f"📦 Stock: <b>{stock_text}</b>\n"
    )
    if p_desc:
        text += f"\n📝 {p_desc}"
    keyboard = product_detail_keyboard(product["id"], stock, price,
                                        product.get("price_stars", 0), lang,
                                        product.get("category_id"))
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=keyboard)


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE,
                          send_new: bool = False):
    user = update.effective_user
    lang = _lang(context)
    bot_name = db.get_setting("bot_name", "Premium Shop Bot")
    welcome = db.get_setting("welcome_message") or _("main_menu_title", lang)
    try:
        welcome = welcome.format(
            bot_name=bot_name,
            name=get_user_display_name(user)
        )
    except Exception:
        pass

    keyboard = main_menu_keyboard(lang, is_admin=is_admin(user.id))

    if send_new or not update.callback_query:
        await update.message.reply_text(welcome, parse_mode="HTML", reply_markup=keyboard)
    else:
        await safe_edit_message(update, welcome, keyboard)


# ─────────────────────────────────────────────
#  SHOP / CATEGORIES
# ─────────────────────────────────────────────

async def shop_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = _lang(context)
    categories = db.get_categories(active_only=True)
    if not categories:
        await safe_edit_message(update, _("no_categories", lang),
                                 InlineKeyboardMarkup([[
                                     InlineKeyboardButton(_("btn_home", lang), callback_data="home")
                                 ]]))
        return
    from config import CATEGORIES_PER_PAGE
    total_pages = max(1, (len(categories) + CATEGORIES_PER_PAGE - 1) // CATEGORIES_PER_PAGE)
    await safe_edit_message(update, _("select_category", lang),
                             categories_keyboard(categories, 1, total_pages, lang), "HTML")


async def category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE,
                            cat_id: int, page: int = 1):
    lang = _lang(context)
    products, total = db.get_products_by_category(cat_id, page, PRODUCTS_PER_PAGE)
    cat = db.get_category(cat_id)
    if not cat:
        await safe_edit_message(update, _("error_not_found", lang))
        return
    cat_name  = cat.get(f"name_{lang}") or cat.get("name", "Category")
    emoji     = cat.get("emoji", "📦")
    total_pages = max(1, (total + PRODUCTS_PER_PAGE - 1) // PRODUCTS_PER_PAGE)

    if not products:
        text = (
            f"{emoji} <b>{cat_name}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            + _("no_products", lang)
        )
    else:
        # Inline product summary list
        lines = []
        for p in products:
            pname  = p.get(f"name_{lang}") or p.get("name", "Product")
            price  = p.get("price", 0)
            stock  = p.get("stock", -1)
            stock_icon = "✅" if stock != 0 else "❌"
            lines.append(f"  {stock_icon} <b>{pname}</b> — ${price:.2f}")
        products_preview = "\n".join(lines)
        text = (
            f"{emoji} <b>{cat_name}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>{total} product{'s' if total != 1 else ''} · Page {page}/{total_pages}</i>\n\n"
            f"{products_preview}"
        )

    await safe_edit_message(update, text,
                             products_keyboard(products, cat_id, page, total_pages, lang), "HTML")


# ─────────────────────────────────────────────
#  PRODUCT DETAIL
# ─────────────────────────────────────────────

async def product_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, product_id: int):
    lang = _lang(context)
    product = db.get_product(product_id)
    if not product:
        await safe_answer_callback(update, _("error_not_found", lang), show_alert=True)
        return

    # Enrich with rating data
    try:
        rating_data = db.get_product_rating(product_id)
        product["avg_rating"] = rating_data.get("avg_rating")
        product["rating_count"] = rating_data.get("count", 0)
    except Exception:
        product["avg_rating"] = None
        product["rating_count"] = 0

    stock = product.get("stock", -1)
    text = product_card(product, lang)

    # Check if user can rate this product
    user = update.effective_user
    can_rate = False
    try:
        can_rate = db.can_rate_product(user.id, product_id) if user else False
    except Exception:
        pass

    keyboard = product_detail_keyboard(
        product_id=product_id, stock=stock,
        price=product["price"], price_stars=product.get("price_stars", 0),
        lang=lang, category_id=product.get("category_id"),
        can_rate=can_rate
    )
    await safe_edit_message(update, text, keyboard, "HTML")



# ─────────────────────────────────────────────
#  PURCHASE FLOW
# ─────────────────────────────────────────────

async def buy_handler(update: Update, context: ContextTypes.DEFAULT_TYPE,
                       payment_method: str, product_id: int):
    user = update.effective_user
    lang = _lang(context)
    db_user = db.get_user(user.id)
    product = db.get_product(product_id)
    if not product:
        await safe_answer_callback(update, _("error_not_found", lang), show_alert=True)
        return
    if product.get("stock") == 0:
        await safe_answer_callback(update, _("out_of_stock", lang), show_alert=True)
        return

    # Required referrals check
    req_refs = db.get_setting("required_referrals", 0)
    if req_refs and req_refs > 0:
        user_refs = db.get_user_referrals(user.id)
        if len(user_refs) < req_refs:
            await safe_answer_callback(
                update,
                f"⚠️ You need {req_refs} referrals to purchase. You have {len(user_refs)}.",
                show_alert=True
            )
            return

    price = product["price"]
    price_stars = product.get("price_stars", 0)
    coupon_code = context.user_data.get(UserState.PENDING_COUPON)
    discount = context.user_data.get(UserState.PENDING_COUPON_DISC, 0.0)
    final_price = max(0, price - discount) if payment_method == "balance" else price_stars

    context.user_data[UserState.PENDING_PRODUCT_ID] = product_id
    context.user_data[UserState.PENDING_PAYMENT] = payment_method

    name = product.get(f"name_{lang}") or product.get("name", "Product")
    text = _(
        "purchase_confirm", lang,
        name=name, price=format_price(price),
        coupon=coupon_code or "None",
        final=format_price(final_price) if payment_method == "balance" else f"{final_price} ⭐"
    )
    await safe_edit_message(update, text,
                             purchase_confirm_keyboard(product_id, payment_method, lang,
                                                        coupon_applied=bool(coupon_code)), "HTML")


async def confirm_buy_handler(update: Update, context: ContextTypes.DEFAULT_TYPE,
                               payment_method: str, product_id: int):
    user = update.effective_user
    lang = _lang(context)
    db_user = db.get_user(user.id)
    product = db.get_product(product_id)
    if not product:
        await safe_answer_callback(update, _("error_not_found", lang), show_alert=True)
        return
    if product.get("stock") == 0:
        await safe_answer_callback(update, _("out_of_stock", lang), show_alert=True)
        return

    # Duplicate-purchase guard — prevents double-tap race conditions
    if not acquire_purchase_lock(user.id, product_id):
        await safe_answer_callback(update, "⏳ Please wait, processing previous request...", show_alert=True)
        return

    price = product["price"]
    price_stars = product.get("price_stars", 0)
    discount = context.user_data.get(UserState.PENDING_COUPON_DISC, 0.0)
    coupon_code = context.user_data.get(UserState.PENDING_COUPON)
    name = product.get(f"name_{lang}") or product.get("name", "Product")

    if payment_method == "balance":
        final_price = max(0.0, price - discount)
        # Atomic deduct — prevents race condition where two simultaneous
        # requests both pass the balance check and both deduct.
        if not db.atomic_deduct_balance(user.id, final_price):
            # Re-fetch to show the real current balance in the error
            fresh = db.get_user(user.id)
            have = fresh["balance"] if fresh else 0

            # Suggest buying points with Stars instead of a plain error
            packages = db.get_stars_packages(active_only=True)
            short = sorted(packages, key=lambda p: p["price_usd"])[:3] if packages else []

            text = (
                f"❌ <b>Insufficient Balance</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"💰 You need: <b>${format_price(final_price)}</b>\n"
                f"💳 You have: <b>${format_price(have)}</b>\n"
                f"📉 Missing:  <b>${format_price(max(0, final_price - have))}</b>\n\n"
                f"⭐ <b>Top up with Telegram Stars!</b>\n"
                f"Pay with Stars and get points instantly:"
            )

            rows = []
            for pkg in short:
                bonus = f" +{round(pkg.get('bonus_stars',0)/max(pkg['stars'],1)*pkg['price_usd'],2):.2f} bonus" if pkg.get("bonus_stars") else ""
                rows.append([InlineKeyboardButton(
                    f"Pay {pkg['stars']}⭐ → 💰${pkg['price_usd']:.2f} Points{bonus}",
                    callback_data=f"buy_stars_pkg:{pkg['id']}"
                )])

            rows.append([InlineKeyboardButton("📦 See All Packages", callback_data="deposit:stars_menu")])
            rows.append([InlineKeyboardButton("◀️ Back", callback_data=f"prod:{product_id}")])

            await safe_answer_callback(update, "", show_alert=False)
            await safe_edit_message(update, text, InlineKeyboardMarkup(rows), "HTML")
            return
        payment_label = "USD Balance"
    else:
        return

    order_id = db.create_order(
        user_id=user.id, product_id=product_id,
        amount=final_price if payment_method == "balance" else price,
        payment_method=payment_label, product_name=name
    )
    db.complete_order(order_id)

    if coupon_code:
        db.use_coupon(coupon_code, user.id, order_id)
        context.user_data.pop(UserState.PENDING_COUPON, None)
        context.user_data.pop(UserState.PENDING_COUPON_DISC, None)

    # Safe buyer info
    buyer_first_name = user.first_name or "N/A"
    buyer_username = user.username
    username_display = f"@{buyer_username}" if buyer_username else "N/A"

    # Fetch support username for the button
    support_username = db.get_setting("support_username", "@support")
    support_url = f"https://t.me/{support_username.lstrip('@')}"

    # Buyer sees: simple confirmation + support button
    buyer_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Contact Support", url=support_url)],
        [InlineKeyboardButton(_("btn_home", lang), callback_data="home")],
    ])
    await safe_edit_message(
        update,
        _("purchase_success", lang, order_id=order_id),
        buyer_keyboard,
        "HTML"
    )

    # Auto delivery — with retry logic and delivery logging
    has_deliverable = db.get_setting("auto_delivery", True) and (
        bool(product.get("file_id")) or bool(product.get("text_content"))
    )

    if has_deliverable:
        from handlers.delivery_handlers import deliver_product
        await deliver_product(context, user.id, product, order_id)

    # Check and award referral milestones
    try:
        from database import check_and_award_milestones
        new_milestones = check_and_award_milestones(user.id)
        for m in new_milestones:
            try:
                await context.bot.send_message(
                    chat_id=user.id,
                    text=(
                        f"🎉 <b>Milestone Unlocked!</b>\n\n"
                        f"🏆 {m['title']}\n"
                        f"💰 Bonus: <b>+${m['reward']:.2f}</b> added to your balance!"
                    ),
                    parse_mode="HTML"
                )
            except Exception:
                pass
    except Exception:
        pass

    # Prompt rating (delayed, async)
    try:
        from handlers.rating_handlers import prompt_rating
        import asyncio
        asyncio.create_task(
            _delayed_rating_prompt(context, user.id, product_id, name, order_id)
        )
    except Exception:
        pass

    # Notify admins (if order_logs enabled) — full buyer + order details
    if db.get_setting("order_logs", True):
        admin_ids = db.get_admin_ids()
        for admin_id in admin_ids:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=(
                        f"🛒 <b>New Order!</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
                        f"👤 <b>Buyer Information:</b>\n"
                        f"  • <b>Name:</b> {buyer_first_name}\n"
                        f"  • <b>Username:</b> {username_display}\n"
                        f"  • <b>User ID:</b> <code>{user.id}</code>\n\n"
                        f"📦 <b>Order Details:</b>\n"
                        f"  • <b>Product:</b> {name}\n"
                        f"  • <b>Amount:</b> ${final_price:.2f}\n"
                        f"  • <b>Method:</b> {payment_label}\n"
                        f"  • <b>Order ID:</b> <code>{order_id}</code>"
                    ),
                    parse_mode="HTML"
                )
            except Exception:
                pass

    # Release duplicate-purchase lock
    release_purchase_lock(user.id, product_id)
    db.add_admin_log(user.id, "purchase", f"Product: {name}, Method: {payment_label}", product_id)


# ─────────────────────────────────────────────
#  COUPON
# ─────────────────────────────────────────────

async def apply_coupon_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE,
                               product_id: int, payment_method: str):
    lang = _lang(context)
    context.user_data[UserState.AWAITING_COUPON] = True
    context.user_data[UserState.PENDING_PRODUCT_ID] = product_id
    context.user_data[UserState.PENDING_PAYMENT] = payment_method
    await safe_edit_message(update, _("ask_coupon_code", lang),
                             cancel_keyboard(f"product:{product_id}", lang))


# ─────────────────────────────────────────────
#  BALANCE / WALLET
# ─────────────────────────────────────────────

async def balance_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = _lang(context)
    db_user = db.get_user(user.id)
    text = _(
        "balance_title", lang,
        balance=format_price(db_user.get("balance", 0)),
        spent=format_price(db_user.get("total_spent", 0)),
        orders=db_user.get("total_orders", 0)
    )
    await safe_edit_message(update, text, balance_keyboard(lang), "HTML")


async def deposit_usdt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = _lang(context)
    wallet = db.get_setting("usdt_wallet", "—")
    min_dep = db.get_setting("min_deposit", 1.0)
    instructions = db.get_setting("payment_instructions", "")
    text = _(
        "deposit_usdt_info", lang,
        wallet=wallet, min_deposit=min_dep
    )
    if instructions:
        text += f"\n\n📋 {instructions}"
    await safe_edit_message(update, text, deposit_usdt_keyboard(lang), "HTML")


async def deposit_stars_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = _lang(context)
    if not db.get_setting("stars_enabled", True):
        await safe_answer_callback(update, "⭐ Stars system is currently disabled", show_alert=True)
        return
    packages = db.get_stars_packages(active_only=True)
    if not packages:
        await safe_edit_message(
            update,
            "⭐ <b>Buy Points with Stars</b>\n\nNo packages available right now.",
            InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Back", callback_data="balance")]]),
            "HTML"
        )
        return
    text = (
        "⭐ <b>Buy Points with Stars</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Pay with Telegram ⭐ Stars to receive 💰 bot points.\n"
        "Points are added to your balance and used to buy products.\n\n"
        "Choose a package:"
    )
    await safe_edit_message(update, text, stars_packages_keyboard(packages, lang), "HTML")




# ─────────────────────────────────────────────
#  ORDERS HISTORY
# ─────────────────────────────────────────────

async def orders_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 1):
    user = update.effective_user
    lang = _lang(context)
    orders, total = db.get_user_orders(user.id, page, ORDERS_PER_PAGE)
    total_pages = max(1, (total + ORDERS_PER_PAGE - 1) // ORDERS_PER_PAGE)
    if not orders:
        await safe_edit_message(
            update, _("no_orders", lang),
            InlineKeyboardMarkup([[
                InlineKeyboardButton(_("btn_home", lang), callback_data="home")
            ]]), "HTML"
        )
        return
    text = f"{_('orders_title', lang)}\n\n📊 {total} total orders"
    await safe_edit_message(update, text, orders_keyboard(orders, page, total_pages, lang), "HTML")


# ─────────────────────────────────────────────
#  PROFILE
# ─────────────────────────────────────────────

async def profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = _lang(context)
    db_user = db.get_user(user.id)
    if not db_user:
        await safe_answer_callback(update, "❌ Profile not found. Try /start first.", show_alert=True)
        return

    referrals = db.get_user_referrals(user.id)
    ref_count = len(referrals)
    lang_names = {"en": "English", "ar": "العربية", "fr": "Français"}
    lang_display = lang_names.get(lang, lang)

    # Rank badge
    rank_badge = referral_rank_badge(ref_count)

    # Milestone progress
    next_m = get_next_milestone(ref_count)
    milestone_line = ""
    if next_m:
        remaining = next_m["count"] - ref_count
        filled = min(ref_count, next_m["count"])
        bar = "█" * filled + "░" * (next_m["count"] - filled)
        bar = bar[:10]  # max 10 chars display
        milestone_line = (
            f"\n🎯 <b>Next Milestone:</b> {next_m['title']}\n"
            f"[{bar}] {ref_count}/{next_m['count']} · +${next_m['reward']:.2f} reward"
        )

    # Pending ratings count
    try:
        pending_ratings = len(db.get_user_pending_ratings(user.id))
    except Exception:
        pending_ratings = 0

    text = (
        f"👤 <b>My Profile</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📛 <b>{get_user_display_name(user)}</b>  {rank_badge}\n"
        f"🆔 <code>{user.id}</code> · 🌍 {lang_display}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Balance: <b>${format_price(db_user.get('balance', 0) or 0)}</b>\n\n"
        f"🛒 Orders:  <b>{db_user.get('total_orders', 0) or 0}</b>\n"
        f"🔗 Referrals: <b>{ref_count}</b>\n"
        f"📅 Joined: <b>{format_date(db_user.get('joined_at', '') or '')}</b>"
        f"{milestone_line}"
    )

    # Build keyboard
    profile_rows = [
        [InlineKeyboardButton("🔗 Referral Link",  callback_data="referral"),
         InlineKeyboardButton("🛒 My Orders",      callback_data="orders:1")],
    ]
    if pending_ratings > 0:
        profile_rows.append([InlineKeyboardButton(
            f"⭐ Rate Purchases ({pending_ratings})", callback_data="my_ratings"
        )])

    daily_gift_enabled = db.get_setting("daily_gift_enabled", False)
    if daily_gift_enabled:
        can_claim, next_time = db.can_claim_daily_gift(user.id)
        if can_claim:
            profile_rows.append([InlineKeyboardButton("🎁 Claim Daily Gift", callback_data="daily_gift:claim")])
        else:
            profile_rows.append([InlineKeyboardButton(f"⏳ Next Gift: {next_time}", callback_data="noop")])

    profile_rows.append([InlineKeyboardButton("🏠 Home", callback_data="home")])
    keyboard = InlineKeyboardMarkup(profile_rows)
    await safe_edit_message(update, text, keyboard, "HTML")


# ─────────────────────────────────────────────
#  SEARCH
# ─────────────────────────────────────────────

async def search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = _lang(context)
    context.user_data[UserState.AWAITING_SEARCH] = True
    await safe_edit_message(update, _("search_prompt", lang),
                             cancel_keyboard("home", lang))


async def search_results_handler(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                   query: str, page: int = 1):
    lang = _lang(context)
    products, total = db.search_products(query, page, PRODUCTS_PER_PAGE)
    total_pages = max(1, (total + PRODUCTS_PER_PAGE - 1) // PRODUCTS_PER_PAGE)
    if not products:
        await safe_edit_message(update, _("no_results", lang, query=query),
                                 cancel_keyboard("home", lang), "HTML")
        return
    rows = []
    for product in products:
        p_name = product.get(f"name_{lang}") or product.get("name", "Product")
        rows.append([InlineKeyboardButton(
            f"📦 {p_name} — ${product.get('price', 0):.2f}",
            callback_data=f"product:{product['id']}"
        )])
    if total_pages > 1:
        nav = []
        if page > 1:
            nav.append(InlineKeyboardButton("◀️", callback_data=f"search_pg:{query}:{page-1}"))
        nav.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop"))
        if page < total_pages:
            nav.append(InlineKeyboardButton("▶️", callback_data=f"search_pg:{query}:{page+1}"))
        rows.append(nav)
    rows.append([InlineKeyboardButton("🏠 Home", callback_data="home")])
    await safe_edit_message(update,
                             f"{_('search_results', lang, query=query)}\n{total} result(s)",
                             InlineKeyboardMarkup(rows), "HTML")


# ─────────────────────────────────────────────
#  REFERRAL
# ─────────────────────────────────────────────

async def referral_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = _lang(context)
    db_user = db.get_user(user.id)
    referrals = db.get_user_referrals(user.id)
    total_earned = sum(r.get("bonus_paid", 0) for r in referrals)
    bonus = db.get_setting("referral_bonus", 0.5)

    ref_link = ""
    try:
        bot_info = await context.bot.get_me()
        ref_link = build_referral_link(bot_info.username, db_user.get("referral_code", ""))
    except Exception:
        ref_link = f"https://t.me/bot?start=ref_{db_user.get('referral_code', '')}"

    enabled = db.get_setting("referral_enabled", True)
    if not enabled:
        await safe_edit_message(
            update,
            "🔗 <b>Referral Program</b>\n\nReferral program is currently inactive.",
            InlineKeyboardMarkup([[InlineKeyboardButton(_("btn_home", lang), callback_data="home")]]),
            "HTML"
        )
        return

    count = len(referrals)
    rank_badge = referral_rank_badge(count)
    next_m = get_next_milestone(count)
    achieved = get_achieved_milestone(count)

    milestone_text = ""
    if next_m:
        remaining = next_m["count"] - count
        bar_filled = count % next_m["count"] if next_m["count"] > 1 else count
        bar_total  = next_m["count"]
        bar = "█" * min(bar_filled, 10) + "░" * max(0, 10 - bar_filled)
        milestone_text = (
            f"\n\n🎯 <b>Next Milestone:</b> {next_m['title']}\n"
            f"[{bar}] {count}/{next_m['count']}\n"
            f"Reward: 💰 +${next_m['reward']:.2f} · {remaining} more to go!"
        )
    elif achieved:
        milestone_text = f"\n\n🏆 <b>All milestones achieved!</b> You're legendary."

    text = _(
        "referral_title", lang,
        bonus=format_price(float(bonus)),
        link=ref_link,
        count=count,
        earned=format_price(float(total_earned))
    )
    text += f"\n\n{rank_badge}" + milestone_text
    await safe_edit_message(update, text, referral_keyboard(lang), "HTML")


# ─────────────────────────────────────────────
#  LANGUAGE
# ─────────────────────────────────────────────

async def language_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = _lang(context)
    await safe_edit_message(update, _("select_language", lang),
                             language_keyboard(lang), "HTML")


# ─────────────────────────────────────────────
#  SUPPORT
# ─────────────────────────────────────────────

async def support_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = _lang(context)
    support_username = db.get_setting("support_username", "@support")
    await safe_edit_message(
        update,
        f"💬 <b>Support</b>\n\nContact us: {support_username}",
        support_keyboard(support_username, lang), "HTML"
    )


# ─────────────────────────────────────────────
#  FORCE SUBSCRIBE CHECK (callback)
# ─────────────────────────────────────────────

async def check_subscribe_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = _lang(context)
    subscribed = await check_subscribe(context.bot, user.id)
    if subscribed:
        await safe_answer_callback(update, "✅ Verified!", show_alert=False)
        await show_main_menu(update, context)
    else:
        await safe_answer_callback(update, _("not_subscribed", lang), show_alert=True)


# ─────────────────────────────────────────────
#  CAPTCHA
# ─────────────────────────────────────────────

async def captcha_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, chosen: int):
    lang = _lang(context)
    correct = context.user_data.get(UserState.CAPTCHA_ANSWER)
    if chosen == correct:
        context.user_data.pop(UserState.AWAITING_CAPTCHA, None)
        context.user_data.pop(UserState.CAPTCHA_ANSWER, None)
        db.update_user(update.effective_user.id, captcha_passed=1)
        await safe_answer_callback(update, _("captcha_passed", lang), show_alert=False)
        await show_main_menu(update, context)
    else:
        await safe_answer_callback(update, _("captcha_wrong", lang), show_alert=True)


# ─────────────────────────────────────────────
#  HELPER: DELAYED RATING PROMPT
# ─────────────────────────────────────────────

async def _delayed_rating_prompt(context, user_id: int, product_id: int,
                                  product_name: str, order_id: str):
    """Send rating prompt 3 seconds after purchase confirmation."""
    import asyncio
    await asyncio.sleep(3)
    from handlers.rating_handlers import prompt_rating
    await prompt_rating(context, user_id, product_id, product_name, order_id)
