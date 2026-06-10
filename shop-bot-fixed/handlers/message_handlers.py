"""
╔══════════════════════════════════════════════════════════╗
║       TELEGRAM SHOP BOT - MESSAGE INPUT HANDLERS         ║
║  Handles all text/file input for wizard-style flows      ║
╚══════════════════════════════════════════════════════════╝
"""

import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

import database as db
from utils.helpers import (
    UserState, safe_float, safe_int, detect_file_type,
    is_admin, is_owner, get_user_display_name
)
from keyboards.inline import cancel_keyboard, back_to_admin_keyboard
from languages.strings import _

logger = logging.getLogger(__name__)


def _lang(ctx): return ctx.user_data.get("lang", "en")


# ─────────────────────────────────────────────
#  CENTRAL MESSAGE DISPATCHER
# ─────────────────────────────────────────────

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Central dispatcher for all text/file message inputs.
    Checks user_data state flags and routes accordingly.
    """
    user = update.effective_user
    if not user or not update.message:
        return

    ud = context.user_data
    text = (update.message.text or "").strip()

    # ── CAPTCHA INPUT (inline buttons handle this, but fallback) ──
    if ud.get(UserState.AWAITING_CAPTCHA):
        return

    # ─────────────────────────────────────────
    #  USER FLOWS
    # ─────────────────────────────────────────

    # ── RATING REVIEW TEXT ───────────────────────────────────────
    if ud.pop("awaiting_review_text", False):
        pending = ud.pop("pending_rating", {})
        rating  = pending.get("rating", 0)
        if pending and text and 1 <= rating <= 5:
            from handlers.rating_handlers import handle_rating_submit
            await handle_rating_submit(
                update, context,
                pending["product_id"], pending["order_id"],
                rating, review=text
            )
        elif pending and not text:
            # User sent something non-textual — just silently skip
            pass
        elif pending and not (1 <= rating <= 5):
            # Corrupted state — clear it silently
            logger.warning(f"Discarding review text: invalid stored rating={rating}")
        return

    # ── SEARCH INPUT ─────────────────────────────────────────────
    if ud.pop(UserState.AWAITING_SEARCH, False):
        if text:
            await _send_search_results(update, context, text, 1)
        return

    # ── DEPOSIT: AWAITING AMOUNT ──────────────────────────────────
    if ud.pop(UserState.AWAITING_DEPOSIT_AMT, False):
        min_dep = float(db.get_setting("min_deposit", 1.0))
        amount = safe_float(text)
        lang = _lang(context)
        if amount < min_dep:
            await update.message.reply_text(
                f"❌ Minimum deposit is <b>${min_dep:.2f}</b>. Enter a higher amount:",
                parse_mode="HTML"
            )
            ud[UserState.AWAITING_DEPOSIT_AMT] = True
            return
        ud["deposit_pending_amount"] = amount
        ud[UserState.AWAITING_TX_HASH] = True
        await update.message.reply_text(
            _("ask_tx_hash", lang), parse_mode="HTML"
        )
        return

    # ── DEPOSIT: AWAITING TX HASH ─────────────────────────────────
    if ud.pop(UserState.AWAITING_TX_HASH, False):
        amount = ud.pop("deposit_pending_amount", None)
        if not amount:
            await update.message.reply_text("❌ Session expired. Please start again.")
            return
        dep_id = db.create_deposit(user.id, amount, "USDT_TRC20", tx_hash=text)
        lang = _lang(context)
        await update.message.reply_text(
            _("deposit_submitted", lang, dep_id=dep_id),
            parse_mode="HTML"
        )
        # Notify all admins (DB-driven)
        admin_ids = db.get_admin_ids()
        for aid in admin_ids:
            try:
                await context.bot.send_message(
                    chat_id=aid,
                    text=(
                        f"💎 <b>New Deposit Request</b>\n\n"
                        f"👤 User: {get_user_display_name(user)} (<code>{user.id}</code>)\n"
                        f"💵 Amount: <b>${amount:.2f}</b>\n"
                        f"🔗 TX: <code>{text}</code>\n"
                        f"🆔 Deposit ID: <code>{dep_id}</code>"
                    ),
                    parse_mode="HTML"
                )
            except Exception:
                pass
        return

    # ── COUPON INPUT ──────────────────────────────────────────────
    if ud.pop(UserState.AWAITING_COUPON, False):
        product_id = ud.get(UserState.PENDING_PRODUCT_ID)
        payment_method = ud.get(UserState.PENDING_PAYMENT)
        lang = _lang(context)
        product = db.get_product(product_id) if product_id else None
        if not product:
            await update.message.reply_text("❌ Session expired.")
            return
        valid, msg, discount = db.validate_coupon(text.upper(), user.id, product["price"])
        if valid:
            ud[UserState.PENDING_COUPON] = text.upper()
            ud[UserState.PENDING_COUPON_DISC] = discount
            await update.message.reply_text(
                _("coupon_valid", lang, discount=f"{discount:.2f}"),
                parse_mode="HTML"
            )
            await _resend_purchase_confirm(update, context, payment_method, product_id)
        else:
            await update.message.reply_text(
                f"❌ {msg}. Try another code or press Back.",
                parse_mode="HTML"
            )
        return

    # ─────────────────────────────────────────
    #  GAMES: bet input
    # ─────────────────────────────────────────

    game_pending = ud.get(UserState.GAME_AWAITING_BET)
    if game_pending:
        try:
            bet = float(text.replace(",", "").replace("$", "").strip())
        except ValueError:
            await update.message.reply_text("❌ Please enter a valid number (e.g. 5 or 2.50)")
            return
        if game_pending == "slots":
            from handlers.games_handlers import slots_play
            await slots_play(update, context, bet)
        elif game_pending == "wheel":
            from handlers.games_handlers import wheel_play
            await wheel_play(update, context, bet)
        elif game_pending == "coinflip":
            from handlers.games_handlers import coinflip_play
            await coinflip_play(update, context, bet)
        return

    # ─────────────────────────────────────────
    #  ADMIN FLOWS
    # ─────────────────────────────────────────

    if not is_admin(user.id):
        # Check game admin state even for non-admin (shouldn't happen, just safety)
        return

    # ── GAMES ADMIN TEXT INPUT ───────────────────────────────────
    from handlers.games_admin_handlers import games_admin_text_input
    if await games_admin_text_input(update, context):
        return

    # ── USER MANAGEMENT FILTER STATES ────────────────────────────
    from handlers.user_mgmt_handlers import uf_handle_text_input
    if await uf_handle_text_input(update, context):
        return

    # ── Filter numeric field setter ───────────────────────────────
    uf_state = ud.get("uf_state", "")
    if uf_state.startswith("fset_"):
        ud.pop("uf_state")
        field = ud.pop("uf_pending_field", uf_state[5:])
        raw = text.strip()
        try:
            if "date" in field or field in ("joined_after", "joined_before", "seen_after", "seen_before"):
                # Accept YYYY-MM-DD
                val = raw
            else:
                val = float(raw)
            ud.setdefault("uf_filters", {})[field] = val
        except ValueError:
            await update.message.reply_text("❌ Invalid value. Please enter a number or date (YYYY-MM-DD).")
            return
        from handlers.user_mgmt_handlers import admin_users_advanced
        await admin_users_advanced(update, context, 1)
        return

    # ── ADMIN: SEARCH USER BY ID ──────────────────────────────────
    if ud.get(UserState.ADMIN_SEARCH_USER):
        ud.pop(UserState.ADMIN_SEARCH_USER)
        target_id = safe_int(text.strip())
        if not target_id:
            await update.message.reply_text(
                "❌ <b>Invalid ID.</b> Please enter a numeric Telegram User ID.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("◀️ Back to Users", callback_data="admin_users:1")
                ]])
            )
            return
        found_user = db.get_user(target_id)
        if not found_user:
            await update.message.reply_text(
                f"❌ <b>User not found.</b>\n\nNo user with ID <code>{target_id}</code> exists in the database.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔍 Search Again", callback_data="admin_user_search"),
                    InlineKeyboardButton("◀️ Users", callback_data="admin_users:1"),
                ]])
            )
            return
        # User found — show their detail page directly
        from handlers.admin_handlers import admin_user_detail
        # Fake a callback-style context so admin_user_detail can render
        # Instead, build the detail message inline
        name = found_user.get("first_name") or f"User#{target_id}"
        from utils.helpers import format_price, format_date
        from keyboards.inline import admin_user_detail_keyboard
        text_out = (
            f"👤 <b>User: {name}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🆔 ID: <code>{target_id}</code>\n"
            f"📛 Username: @{found_user.get('username') or '—'}\n"
            f"💰 Balance: <b>${format_price(found_user.get('balance', 0))}</b>\n"
            f"⭐ Stars: <b>{found_user.get('stars_balance', 0)}</b>\n"
            f"🛒 Orders: <b>{found_user.get('total_orders', 0)}</b>\n"
            f"💵 Spent: <b>${format_price(found_user.get('total_spent', 0))}</b>\n"
            f"📅 Joined: <b>{format_date(found_user.get('joined_at', ''))}</b>\n"
            f"Status: <b>{'🚫 Banned' if found_user.get('is_banned') else '✅ Active'}</b>"
        )
        await update.message.reply_text(
            text_out, parse_mode="HTML",
            reply_markup=admin_user_detail_keyboard(target_id, bool(found_user.get("is_banned")))
        )
        return

    # ── ADMIN: BAN USER REASON ────────────────────────────────────
    if ud.get(UserState.ADMIN_BAN_USER):
        ud.pop(UserState.ADMIN_BAN_USER)
        target_id = ud.pop("ban_target_id", None)
        if not target_id:
            return
        reason = text or "No reason provided"
        db.ban_user(target_id, reason)
        db.add_admin_log(user.id, "ban_user", f"Banned {target_id}: {reason}", target_id)
        try:
            await context.bot.send_message(
                chat_id=target_id,
                text=f"🚫 <b>You have been banned.</b>\nReason: {reason}",
                parse_mode="HTML"
            )
        except Exception:
            pass
        await update.message.reply_text(
            f"✅ User <code>{target_id}</code> banned.\nReason: {reason}",
            parse_mode="HTML"
        )
        return

    # ── ADMIN: ADJUST BALANCE / STARS ─────────────────────────────
    if ud.get(UserState.ADMIN_ADJUST_BAL):
        ud.pop(UserState.ADMIN_ADJUST_BAL)
        target_id = ud.pop("adjust_target_id", None)
        adj_type = ud.pop("adjust_type", "balance")
        if not target_id:
            return
        if adj_type == "stars":
            amount = safe_int(text.replace(",", ""))
            new_val = db.adjust_stars(target_id, amount)
            db.add_admin_log(user.id, "adjust_stars",
                             f"User {target_id}: {amount:+d} stars", target_id)
            await update.message.reply_text(
                f"✅ Stars adjusted.\n⭐ New balance: <b>{new_val}</b>", parse_mode="HTML"
            )
            notify = f"⭐ {'+'if amount>=0 else ''}{amount} stars"
        else:
            amount = safe_float(text.replace(",", "."))
            new_val = db.adjust_balance(target_id, amount)
            db.add_admin_log(user.id, "adjust_balance",
                             f"User {target_id}: {amount:+.2f} USD", target_id)
            await update.message.reply_text(
                f"✅ Balance adjusted.\n💰 New balance: <b>${new_val:.2f}</b>", parse_mode="HTML"
            )
            notify = f"💰 {'+'if amount>=0 else ''}${amount:.2f}"
        try:
            await context.bot.send_message(
                chat_id=target_id,
                text=f"💳 <b>Balance Updated</b>\n{notify} applied to your account.",
                parse_mode="HTML"
            )
        except Exception:
            pass
        return

    # ── ADMIN: SETTING EDIT ───────────────────────────────────────
    if ud.get(UserState.ADMIN_EDIT_SETTING):
        ud.pop(UserState.ADMIN_EDIT_SETTING)
        key = ud.pop(UserState.ADMIN_EDIT_SETTING_KEY, None)
        back_cb = ud.pop("_setting_back_cb", "admin_settings")
        if not key:
            return
        from handlers.settings_handlers import edit_setting_save
        result = await edit_setting_save(user.id, key, text)
        await update.message.reply_text(
            result, parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Back", callback_data=back_cb)
            ]])
        )
        return

    # ── ADMIN: ADD FORCE SUBSCRIBE CHANNEL ───────────────────────
    if ud.get(UserState.ADMIN_ADD_CHANNEL):
        ud.pop(UserState.ADMIN_ADD_CHANNEL)
        username = text.lstrip("@").strip()
        if not username:
            await update.message.reply_text("❌ Invalid username. Please try again.")
            return
        # Check if editing a channel field (link)
        ch_id = ud.pop("editing_channel_id", None)
        ch_field = ud.pop("editing_channel_field", None)
        if ch_id and ch_field == "link":
            db.update_force_channel(ch_id, link=text.strip())
            db.add_admin_log(user.id, "edit_channel_link", f"Channel #{ch_id} link updated")
            await update.message.reply_text("✅ Channel link updated!",
                                             reply_markup=InlineKeyboardMarkup([[
                                                 InlineKeyboardButton("◀️ Back",
                                                     callback_data=f"fs:detail:{ch_id}")
                                             ]]))
        else:
            ch_id = db.add_force_channel(username)
            db.add_admin_log(user.id, "add_force_channel", f"Added @{username}", ch_id)
            await update.message.reply_text(
                f"✅ Channel <b>@{username}</b> added to force subscribe list!",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("◀️ Force Subscribe", callback_data="cfg:force_sub")
                ]])
            )
        return

    # ── ADMIN: ADD ADMIN ─────────────────────────────────────────
    if ud.get(UserState.ADMIN_ADD_ADMIN):
        ud.pop(UserState.ADMIN_ADD_ADMIN)
        if not is_owner(user.id):
            await update.message.reply_text("⛔ Only the owner can add admins.")
            return
        new_admin_id = safe_int(text)
        if not new_admin_id:
            await update.message.reply_text("❌ Invalid user ID. Must be a number.")
            return
        new_user = db.get_user(new_admin_id)
        first_name = new_user.get("first_name", "Admin") if new_user else "Admin"
        username = new_user.get("username", "") if new_user else ""
        db.add_admin(
            user_id=new_admin_id,
            username=username,
            first_name=first_name,
            added_by=user.id
        )
        db.add_admin_log(user.id, "add_admin", f"Added admin {new_admin_id}", new_admin_id)
        try:
            await context.bot.send_message(
                chat_id=new_admin_id,
                text="🛡️ <b>You have been added as an admin!</b>\n\nUse /start to access the admin panel.",
                parse_mode="HTML"
            )
        except Exception:
            pass
        await update.message.reply_text(
            f"✅ User <code>{new_admin_id}</code> added as admin!",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Admin Management", callback_data="cfg:admins")
            ]])
        )
        return

    # ── ADMIN: EDIT CATEGORY FIELD ────────────────────────────────
    if ud.get("editing_cat_id") and ud.get("editing_cat_field"):
        cat_id = ud.pop("editing_cat_id")
        field = ud.pop("editing_cat_field")
        db.update_category(cat_id, **{field: text})
        db.add_admin_log(user.id, "edit_category", f"Cat #{cat_id} {field}={text}", cat_id)
        await update.message.reply_text(
            f"✅ Category {field} updated!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Categories", callback_data="admin_categories")
            ]])
        )
        return

    # ── ADMIN: STARS PACKAGE WIZARD ───────────────────────────────
    if ud.get(UserState.ADMIN_ADD_STARS_PKG):
        step = ud.get("stars_pkg_step", "name")
        data = ud.setdefault("stars_pkg_data", {})

        if step == "name":
            data["name"] = text
            ud["stars_pkg_step"] = "stars"
            await update.message.reply_text(
                "⭐ <b>Step 2/4:</b> Enter number of stars in this package:",
                parse_mode="HTML"
            )
        elif step == "stars":
            stars = safe_int(text)
            if stars <= 0:
                await update.message.reply_text("❌ Must be a positive number. Try again:")
                return
            data["stars"] = stars
            ud["stars_pkg_step"] = "price"
            await update.message.reply_text(
                "💵 <b>Step 3/4:</b> Enter price in USD (e.g. 4.99):",
                parse_mode="HTML"
            )
        elif step == "price":
            price = safe_float(text.replace(",", "."))
            if price <= 0:
                await update.message.reply_text("❌ Must be a positive number. Try again:")
                return
            data["price_usd"] = price
            ud["stars_pkg_step"] = "bonus"
            await update.message.reply_text(
                "🎁 <b>Step 4/4:</b> Enter bonus stars (0 for none):",
                parse_mode="HTML"
            )
        elif step == "bonus":
            data["bonus_stars"] = max(0, safe_int(text))
            pkg_id = db.create_stars_package(
                name=data["name"],
                stars=data["stars"],
                price_usd=data["price_usd"],
                bonus_stars=data.get("bonus_stars", 0)
            )
            db.add_admin_log(user.id, "add_stars_package", f"'{data['name']}' #{pkg_id}", pkg_id)
            ud.pop(UserState.ADMIN_ADD_STARS_PKG, None)
            ud.pop("stars_pkg_step", None)
            ud.pop("stars_pkg_data", None)
            total = data["stars"] + data.get("bonus_stars", 0)
            await update.message.reply_text(
                f"✅ <b>Package Created!</b>\n\n"
                f"📦 Name: <b>{data['name']}</b>\n"
                f"⭐ Stars: <b>{data['stars']}</b>"
                f" (+{data.get('bonus_stars',0)}🎁)\n"
                f"💵 Price: <b>${data['price_usd']:.2f}</b>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📦 Manage Packages", callback_data="stars:packages")
                ]])
            )
        return

    # ── ADMIN: EDIT STARS PACKAGE FIELD ──────────────────────────
    if ud.get(UserState.ADMIN_EDIT_STARS_PKG):
        ud.pop(UserState.ADMIN_EDIT_STARS_PKG)
        pkg_id = ud.pop("editing_pkg_id", None)
        field = ud.pop("editing_pkg_field", None)
        if not pkg_id or not field:
            return
        if field == "name":
            db.update_stars_package(pkg_id, name=text)
        elif field == "price":
            val = safe_float(text.replace(",", "."))
            if val <= 0:
                await update.message.reply_text("❌ Invalid price.")
                return
            db.update_stars_package(pkg_id, price_usd=val)
        elif field == "stars":
            val = safe_int(text)
            if val <= 0:
                await update.message.reply_text("❌ Invalid stars count.")
                return
            db.update_stars_package(pkg_id, stars=val)
        elif field == "bonus":
            db.update_stars_package(pkg_id, bonus_stars=max(0, safe_int(text)))
        db.add_admin_log(user.id, "edit_stars_pkg", f"Pkg #{pkg_id} {field}={text}", pkg_id)
        await update.message.reply_text(
            f"✅ Package updated!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Back", callback_data=f"stars:pkg:{pkg_id}")
            ]])
        )
        return

    # ── ADMIN: ADD PRODUCT WIZARD ─────────────────────────────────
    if ud.get(UserState.ADMIN_ADD_PRODUCT):
        step = ud.get(UserState.ADMIN_PRODUCT_STEP)
        data = ud.setdefault(UserState.ADMIN_PRODUCT_DATA, {})

        if step == "name":
            data["name"] = text
            ud[UserState.ADMIN_PRODUCT_STEP] = "price"
            await update.message.reply_text(
                "💰 <b>Enter product price</b> (e.g. 4.99):", parse_mode="HTML"
            )

        elif step == "price":
            price = safe_float(text)
            if price <= 0:
                await update.message.reply_text("❌ Invalid price. Enter a positive number:")
                return
            data["price"] = price
            ud[UserState.ADMIN_PRODUCT_STEP] = "price_stars"
            await update.message.reply_text(
                "⭐ <b>Enter Stars price</b> (0 to disable stars payment):", parse_mode="HTML"
            )

        elif step == "price_stars":
            data["price_stars"] = safe_int(text)
            ud[UserState.ADMIN_PRODUCT_STEP] = "stock"
            await update.message.reply_text(
                "📦 <b>Enter stock quantity</b> (-1 for unlimited):", parse_mode="HTML"
            )

        elif step == "stock":
            data["stock"] = safe_int(text, -1)
            ud[UserState.ADMIN_PRODUCT_STEP] = "description"
            await update.message.reply_text(
                "📝 <b>Enter product description</b> (or send - to skip):", parse_mode="HTML"
            )

        elif step == "description":
            data["description"] = "" if text == "-" else text
            ud[UserState.ADMIN_PRODUCT_STEP] = "text_content"
            await update.message.reply_text(
                "💬 <b>Enter product text content</b> (e.g. account credentials, license key, message)\n"
                "Or send <code>-</code> to skip and upload a file instead:",
                parse_mode="HTML"
            )

        elif step == "text_content":
            data["text_content"] = None if text == "-" else text
            if data["text_content"]:
                # Has text content — skip file step, create product now
                product_id = db.create_product(
                    category_id=data["category_id"],
                    name=data["name"],
                    price=data["price"],
                    description=data.get("description", ""),
                    price_stars=data.get("price_stars", 0),
                    stock=data.get("stock", -1),
                    text_content=data["text_content"]
                )
                db.add_admin_log(user.id, "add_product",
                                 f"Created '{data['name']}' (ID:{product_id})", product_id)
                ud.pop(UserState.ADMIN_ADD_PRODUCT, None)
                ud.pop(UserState.ADMIN_PRODUCT_STEP, None)
                ud.pop(UserState.ADMIN_PRODUCT_DATA, None)
                await update.message.reply_text(
                    f"✅ <b>Product Created!</b>\n\n"
                    f"📦 Name: <b>{data['name']}</b>\n"
                    f"💰 Price: <b>${data['price']:.2f}</b>\n"
                    f"🆔 ID: <b>{product_id}</b>\n"
                    f"💬 Delivery: <b>Text message</b>",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("📦 View Product",
                                             callback_data=f"admin_product:{product_id}"),
                        InlineKeyboardButton("➕ Add Another",
                                             callback_data="admin_add_product"),
                    ]])
                )
                return
            # No text content — proceed to file step
            ud[UserState.ADMIN_PRODUCT_STEP] = "file"
            await update.message.reply_text(
                "📁 <b>Send the product file</b> (document, photo, video, etc.)\n"
                "Or send <code>-</code> to create without a file:",
                parse_mode="HTML"
            )

        elif step == "file":
            file_type, file_id, file_name = None, None, None
            if text != "-":
                file_type, file_id, file_name = detect_file_type(update.message)
                if not file_id:
                    await update.message.reply_text(
                        "❌ Unsupported file type. Send a document, photo, video, or '-' to skip:"
                    )
                    return

            product_id = db.create_product(
                category_id=data["category_id"],
                name=data["name"],
                price=data["price"],
                description=data.get("description", ""),
                file_id=file_id, file_type=file_type, file_name=file_name,
                price_stars=data.get("price_stars", 0),
                stock=data.get("stock", -1),
                text_content=None
            )
            db.add_admin_log(user.id, "add_product",
                             f"Created '{data['name']}' (ID:{product_id})", product_id)
            ud.pop(UserState.ADMIN_ADD_PRODUCT, None)
            ud.pop(UserState.ADMIN_PRODUCT_STEP, None)
            ud.pop(UserState.ADMIN_PRODUCT_DATA, None)
            await update.message.reply_text(
                f"✅ <b>Product Created!</b>\n\n"
                f"📦 Name: <b>{data['name']}</b>\n"
                f"💰 Price: <b>${data['price']:.2f}</b>\n"
                f"🆔 ID: <b>{product_id}</b>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📦 View Product",
                                         callback_data=f"admin_product:{product_id}"),
                    InlineKeyboardButton("➕ Add Another",
                                         callback_data="admin_add_product"),
                ]])
            )
        return

    # ── ADMIN: EDIT PRODUCT FIELD ─────────────────────────────────
    if ud.get(UserState.ADMIN_EDIT_PRODUCT):
        ud.pop(UserState.ADMIN_EDIT_PRODUCT)
        product_id = ud.pop("edit_product_id", None)
        field = ud.pop("edit_product_field", None)
        if not product_id or not field:
            return

        if field == "file":
            file_type, file_id, file_name = detect_file_type(update.message)
            if file_id:
                db.update_product(product_id, file_id=file_id,
                                  file_type=file_type, file_name=file_name)
                await update.message.reply_text("✅ File updated!", parse_mode="HTML")
            else:
                await update.message.reply_text("❌ No valid file received.")
        elif field == "name":
            db.update_product(product_id, name=text)
            await update.message.reply_text(f"✅ Name updated: <b>{text}</b>", parse_mode="HTML")
        elif field == "price":
            price = safe_float(text)
            db.update_product(product_id, price=price)
            await update.message.reply_text(f"✅ Price updated: <b>${price:.2f}</b>", parse_mode="HTML")
        elif field == "desc":
            db.update_product(product_id, description=text)
            await update.message.reply_text("✅ Description updated.", parse_mode="HTML")
        elif field == "text_content":
            db.update_product(product_id, text_content=text)
            await update.message.reply_text("✅ Text content updated.", parse_mode="HTML")
        elif field == "stock":
            stock = safe_int(text, -1)
            db.update_product(product_id, stock=stock)
            await update.message.reply_text(f"✅ Stock updated: <b>{stock}</b>", parse_mode="HTML")

        db.add_admin_log(user.id, "edit_product",
                         f"Edited {field} for #{product_id}", product_id)
        return

    # ── ADMIN: ADD CATEGORY WIZARD ────────────────────────────────
    if ud.get(UserState.ADMIN_ADD_CATEGORY):
        step = ud.get("category_step", "name")
        cat_data = ud.setdefault("category_data", {})

        if step == "name":
            cat_data["name"] = text
            ud["category_step"] = "emoji"
            await update.message.reply_text(
                "😀 <b>Enter category emoji</b> (e.g. 🎮 or 📱):", parse_mode="HTML"
            )
        elif step == "emoji":
            cat_data["emoji"] = text or "📦"
            cat_id = db.create_category(name=cat_data["name"], emoji=cat_data["emoji"])
            db.add_admin_log(user.id, "add_category",
                             f"Created '{cat_data['name']}'", cat_id)
            ud.pop(UserState.ADMIN_ADD_CATEGORY, None)
            ud.pop("category_step", None)
            ud.pop("category_data", None)
            await update.message.reply_text(
                f"✅ <b>Category Created!</b>\n{cat_data['emoji']} {cat_data['name']}",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📂 Categories", callback_data="admin_categories")
                ]])
            )
        return

    # ── ADMIN: COUPON WIZARD ──────────────────────────────────────
    if ud.get("coupon_step"):
        step = ud.get("coupon_step")
        coup_data = ud.setdefault("coupon_data", {})

        if step == "code":
            coup_data["code"] = text.upper()
            ud["coupon_step"] = "type"
            await update.message.reply_text(
                "💰 <b>Discount type?</b>",
                reply_markup=_coupon_type_keyboard(), parse_mode="HTML"
            )
        elif step == "value":
            coup_data["value"] = safe_float(text)
            ud["coupon_step"] = "min"
            await update.message.reply_text(
                "📌 <b>Minimum purchase amount</b> (0 for none):", parse_mode="HTML"
            )
        elif step == "min":
            coup_data["min_purchase"] = safe_float(text)
            ud["coupon_step"] = "max_uses"
            await update.message.reply_text(
                "🔢 <b>Maximum uses</b> (-1 for unlimited):", parse_mode="HTML"
            )
        elif step == "max_uses":
            coup_data["max_uses"] = safe_int(text, -1)
            cid = db.create_coupon(
                code=coup_data["code"],
                discount_type=coup_data.get("discount_type", "percentage"),
                discount_value=coup_data["value"],
                min_purchase=coup_data.get("min_purchase", 0),
                max_uses=coup_data["max_uses"]
            )
            db.add_admin_log(user.id, "add_coupon", f"Created '{coup_data['code']}'", cid)
            ud.pop(UserState.ADMIN_ADD_COUPON, None)
            ud.pop("coupon_step", None)
            ud.pop("coupon_data", None)
            d_type = "%" if coup_data.get("discount_type") == "percentage" else "$"
            await update.message.reply_text(
                f"✅ <b>Coupon Created!</b>\n"
                f"🎟️ Code: <code>{coup_data['code']}</code>\n"
                f"💰 Discount: {coup_data['value']}{d_type}",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🎟️ Coupons", callback_data="admin_coupons")
                ]])
            )
        return

    # ── ADMIN: REWARD LINK WIZARD ─────────────────────────────────
    if ud.get("rl_step"):
        step = ud.get("rl_step")
        rl_data = ud.setdefault("rl_data", {})

        if step == "points":
            pts = safe_float(text)
            if pts <= 0:
                await update.message.reply_text("❌ Must be a positive number. Try again:")
                return
            rl_data["points"] = pts
            ud["rl_step"] = "max_uses"
            await update.message.reply_text(
                "🔢 <b>Step 2: Max uses</b>\n(-1 for unlimited, or a number like 100):",
                parse_mode="HTML"
            )
        elif step == "max_uses":
            rl_data["max_uses"] = safe_int(text, -1)
            ud["rl_step"] = "expires"
            await update.message.reply_text(
                "⏳ <b>Step 3: Expiry</b>\nEnter expiry date/time (e.g. 2026-12-31 23:59:59)\nOr send <code>-</code> for no expiry:",
                parse_mode="HTML"
            )
        elif step == "expires":
            if text.strip() == "-":
                rl_data["expires_at"] = None
            else:
                rl_data["expires_at"] = text.strip()
            ud["rl_step"] = "target_users"
            await update.message.reply_text(
                "👥 <b>Step 4: Target Users</b>\nEnter user IDs separated by commas (e.g. 123456,789012)\nOr send <code>-</code> for all users:",
                parse_mode="HTML"
            )
        elif step == "target_users":
            rl_data["target_users"] = None if text.strip() == "-" else text.strip()
            result = db.create_reward_link(
                points=rl_data["points"],
                max_uses=rl_data.get("max_uses", -1),
                expires_at=rl_data.get("expires_at"),
                target_users=rl_data.get("target_users"),
                created_by=user.id
            )
            ud.pop("rl_step", None)
            ud.pop("rl_data", None)
            bot_username = context.bot.username
            tg_link = f"https://t.me/{bot_username}?start={result['token']}"
            db.add_admin_log(user.id, "create_reward_link",
                             f"+{rl_data['points']}pts link #{result['id']}", result["id"])
            await update.message.reply_text(
                f"✅ <b>Reward Link Created!</b>\n\n"
                f"💰 Points: <b>{rl_data['points']}</b>\n"
                f"🔢 Max Uses: <b>{'∞' if rl_data.get('max_uses', -1) == -1 else rl_data['max_uses']}</b>\n"
                f"⏳ Expires: <b>{rl_data.get('expires_at') or 'Never'}</b>\n\n"
                f"🔗 <b>Share Link:</b>\n<code>{tg_link}</code>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🎁 Reward Links", callback_data="rl:panel")
                ]])
            )
        return

    # ── ADMIN: DAILY GIFT EDIT ────────────────────────────────────
    if ud.get("dg_editing"):
        ud.pop("dg_editing")
        field = ud.pop("dg_edit_field", None)
        if not field:
            return
        if field == "points":
            val = safe_float(text)
            if val <= 0:
                await update.message.reply_text("❌ Must be a positive number.")
                return
            db.set_setting("daily_gift_points", val)
            db.add_admin_log(user.id, "edit_daily_gift", f"Points set to {val}")
            await update.message.reply_text(
                f"✅ Daily gift points set to <b>{val}</b>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("◀️ Daily Gift", callback_data="dg:panel")
                ]])
            )
        elif field == "cooldown":
            val = safe_int(text, 24)
            if val <= 0:
                await update.message.reply_text("❌ Must be at least 1 hour.")
                return
            db.set_setting("daily_gift_cooldown_hours", val)
            db.add_admin_log(user.id, "edit_daily_gift", f"Cooldown set to {val}h")
            await update.message.reply_text(
                f"✅ Cooldown set to <b>{val} hours</b>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("◀️ Daily Gift", callback_data="dg:panel")
                ]])
            )
        return

    # ── ADMIN: UPLOAD DATABASE ─────────────────────────────────────
    if ud.get(UserState.ADMIN_UPLOAD_DB):
        from handlers.admin_handlers import admin_upload_database_receive
        await admin_upload_database_receive(update, context)
        return

    # ── ADMIN: EDIT BOT FILE ────────────────────────────────────────
    if ud.get(UserState.ADMIN_UPLOAD_FILE):
        from handlers.admin_handlers import admin_upload_file_receive
        await admin_upload_file_receive(update, context)
        return

    # ── ADMIN: FLASH SALE WIZARD ───────────────────────────────────
    if ud.get(UserState.ADMIN_FLASH_SALE_STEP):
        from handlers.new_features_handlers import flash_sale_save
        step = ud.get(UserState.ADMIN_FLASH_SALE_STEP)
        if step == "discount":
            try:
                discount = float(msg.text.strip().replace("%", ""))
                if not (1 <= discount <= 99):
                    raise ValueError
                ud["fs_discount"] = discount
                ud[UserState.ADMIN_FLASH_SALE_STEP] = "hours"
                await msg.reply_text(
                    f"⚡ Discount: <b>{discount}%</b>\n\nStep 3: How many hours should the sale last? (e.g. 24):",
                    parse_mode="HTML"
                )
            except ValueError:
                await msg.reply_text("❌ Enter a valid number between 1 and 99 (e.g. 20):")
        elif step == "hours":
            try:
                hours = float(msg.text.strip())
                if hours <= 0:
                    raise ValueError
                product_id = ud.pop("fs_product_id", None)
                discount = ud.pop("fs_discount", 0)
                ud.pop(UserState.ADMIN_FLASH_SALE_STEP, None)
                result = await flash_sale_save(user.id, product_id, discount, hours, context)
                await msg.reply_text(result, parse_mode="HTML")
            except ValueError:
                await msg.reply_text("❌ Enter a valid number of hours (e.g. 24):")
        return

    # ── USER: TRACK ORDER ──────────────────────────────────────────
    if ud.pop(UserState.AWAITING_TRACK_ORDER, False):
        from handlers.new_features_handlers import show_order_status
        await show_order_status(update, context, msg.text.strip())
        return

    # ── ADMIN: BROADCAST ──────────────────────────────────────────
    if ud.pop(UserState.ADMIN_BROADCAST, False):
        msg = update.message
        if msg.photo:
            message_data = {"type": "photo", "file_id": msg.photo[-1].file_id,
                            "caption": msg.caption or ""}
        elif msg.video:
            message_data = {"type": "video", "file_id": msg.video.file_id,
                            "caption": msg.caption or ""}
        elif msg.text:
            message_data = {"type": "text", "text": msg.text}
        else:
            await update.message.reply_text("❌ Unsupported message type for broadcast.")
            return
        await update.message.reply_text("📢 Broadcasting... Please wait.")
        await _do_broadcast(context, user.id, message_data)
        return


# ─────────────────────────────────────────────
#  BROADCAST EXECUTION
# ─────────────────────────────────────────────

async def _do_broadcast(context: ContextTypes.DEFAULT_TYPE,
                         admin_id: int, message_data: dict):
    """Send broadcast to all non-banned users."""
    users = db.get_all_users(active_only=True)
    sent, failed = 0, 0
    for u in users:
        if u.get("is_banned"):
            continue
        uid = u["user_id"]
        try:
            if message_data["type"] == "text":
                await context.bot.send_message(
                    chat_id=uid, text=message_data["text"],
                    parse_mode="HTML"
                )
            elif message_data["type"] == "photo":
                await context.bot.send_photo(
                    chat_id=uid, photo=message_data["file_id"],
                    caption=message_data.get("caption", ""), parse_mode="HTML"
                )
            elif message_data["type"] == "video":
                await context.bot.send_video(
                    chat_id=uid, video=message_data["file_id"],
                    caption=message_data.get("caption", ""), parse_mode="HTML"
                )
            sent += 1
        except Exception:
            failed += 1

    try:
        await context.bot.send_message(
            chat_id=admin_id,
            text=(
                f"📢 <b>Broadcast Complete!</b>\n\n"
                f"✅ Sent: <b>{sent}</b>\n"
                f"❌ Failed: <b>{failed}</b>\n"
                f"👥 Total: <b>{sent + failed}</b>"
            ),
            parse_mode="HTML"
        )
    except Exception:
        pass


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def _coupon_type_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("% Percentage", callback_data="coupon_type:percentage"),
         InlineKeyboardButton("$ Fixed Amount", callback_data="coupon_type:fixed")]
    ])


async def _resend_purchase_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                    payment_method: str, product_id: int):
    """Re-display purchase confirmation after coupon applied."""
    lang = _lang(context)
    product = db.get_product(product_id)
    if not product:
        return
    name = product.get(f"name_{lang}") or product.get("name", "Product")
    price = product["price"]
    discount = context.user_data.get(UserState.PENDING_COUPON_DISC, 0.0)
    coupon_code = context.user_data.get(UserState.PENDING_COUPON, "None")
    final_price = max(0, price - discount)
    from keyboards.inline import purchase_confirm_keyboard
    text = _(
        "purchase_confirm", lang,
        name=name,
        price=f"{price:.2f}",
        coupon=coupon_code,
        final=f"{final_price:.2f}"
    )
    await update.message.reply_text(
        text, parse_mode="HTML",
        reply_markup=purchase_confirm_keyboard(
            product_id, payment_method, lang, coupon_applied=True
        )
    )


async def _send_search_results(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                 query: str, page: int):
    """Send search results as a new message."""
    lang = _lang(context)
    from config import PRODUCTS_PER_PAGE
    products, total = db.search_products(query, page, PRODUCTS_PER_PAGE)
    total_pages = max(1, (total + PRODUCTS_PER_PAGE - 1) // PRODUCTS_PER_PAGE)

    if not products:
        await update.message.reply_text(
            _("no_results", lang, query=query), parse_mode="HTML"
        )
        return

    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
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

    await update.message.reply_text(
        f"{_('search_results', lang, query=query)}\n{total} result(s)",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(rows)
    )

    