"""
╔══════════════════════════════════════════════════════════╗
║       TELEGRAM SHOP BOT - CALLBACK QUERY ROUTER          ║
╚══════════════════════════════════════════════════════════╝
"""

import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

import database as db
from config import PRIMARY_ADMIN_ID
from utils.security import is_valid_callback
from utils.helpers import (
    is_admin, is_owner, is_rate_limited, safe_int, safe_answer_callback,
    safe_edit_message, format_datetime, UserState
)
from languages.strings import _
from keyboards.inline import cancel_keyboard, back_to_admin_keyboard

logger = logging.getLogger(__name__)


def _lang(ctx): return ctx.user_data.get("lang", "en")


async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return

    user = update.effective_user
    data = query.data or ""

    # Validate callback data
    if not is_valid_callback(data):
        logger.warning(f"Invalid callback data: {data!r} from {user.id}")
        await query.answer("❌ Invalid request", show_alert=False)
        return

    # Rate limiting (skip for admins)
    if not is_admin(user.id):
        cooldown = db.get_setting("anti_spam_cooldown", 1)
        max_rpm  = db.get_setting("max_requests_minute", 30)
        if is_rate_limited(user.id, cooldown=int(cooldown), max_per_min=int(max_rpm)):
            await query.answer("⏳ Slow down!", show_alert=False)
            return

    # Load user language
    db_user = db.get_user(user.id)
    if db_user:
        context.user_data["lang"] = db_user.get("language", "en")
    lang = _lang(context)

    # Guard: banned
    if db_user and db_user.get("is_banned") and not is_admin(user.id):
        await query.answer("🚫 You are banned.", show_alert=True)
        return

    # Guard: maintenance
    if not db.get_setting("bot_status") and not is_admin(user.id):
        await query.answer("🔧 Maintenance mode", show_alert=True)
        return

    await query.answer()

    # ── Lazy imports to avoid circular deps ──────────────────────
    from handlers.user_handlers import (
        show_main_menu, shop_handler, category_handler, product_handler,
        buy_handler, confirm_buy_handler, apply_coupon_prompt,
        balance_handler, deposit_usdt_handler, orders_handler,
        profile_handler, search_handler, search_results_handler,
        referral_handler, language_handler, support_handler,
        check_subscribe_callback, captcha_callback,
        deposit_stars_menu_handler
    )
    from handlers.admin_handlers import (
        admin_panel, admin_stats, admin_products, admin_product_detail,
        admin_add_product_start, admin_add_product_category,
        admin_edit_product_field, admin_toggle_product,
        admin_delete_product_confirm, admin_categories, admin_add_category_start,
        admin_category_detail, admin_users, admin_user_detail,
        admin_ban_user, admin_unban_user, admin_adjust_balance, admin_adjust_stars,
        admin_deposits, admin_deposit_detail, admin_deposit_confirm, admin_deposit_reject,
        admin_coupons, admin_add_coupon_start, admin_coupon_detail,
        admin_broadcast_start, admin_logs, admin_backup, admin_export_users,
        admin_orders, admin_user_search_start,
        admin_take_database, admin_upload_database_start,
        admin_upload_file_start, admin_upload_file_receive
    )
    from handlers.settings_handlers import (
        settings_main, settings_general, settings_payment, settings_security,
        settings_notify, settings_messages, settings_delivery,
        toggle_setting, edit_setting_start
    )
    from handlers.force_subscribe_handlers import (
        force_subscribe_panel, channel_detail, add_channel_start,
        toggle_force_subscribe, toggle_channel, remove_channel
    )
    from handlers.referral_admin_handlers import (
        referral_panel, toggle_referral, referral_reward_type,
        set_referral_reward_type, referral_leaderboard, referral_stats,
        edit_referral_start
    )
    from handlers.stars_admin_handlers import (
        stars_panel, stars_packages_list, stars_package_detail,
        toggle_stars, toggle_package, delete_package, add_package_start,
        edit_package_field_start, edit_stars_setting_start, test_stars_invoice
    )
    from handlers.admin_management_handlers import (
        admin_management_panel, admin_detail, add_admin_start, remove_admin
    )
    from handlers.reward_handlers import (
        reward_links_panel, reward_link_detail, reward_link_create_start,
        reward_link_delete, daily_gift_panel, toggle_daily_gift, daily_gift_edit_start
    )
    from handlers.rating_handlers import (
        handle_rating_callback, handle_rating_submit, pending_ratings_handler
    )
    from handlers.delivery_handlers import (
        failed_deliveries_panel, resend_delivery
    )
    from handlers.error_handlers import (
        error_dashboard, error_recent, error_clear
    )
    from handlers.new_features_handlers import (
        my_products_handler, redownload_handler,
        track_order_handler,
        flash_sale_panel, flash_sale_new_start, flash_sale_pick_product,
        flash_sale_cancel, flash_sales_user_view,
        set_product_of_day_start, set_product_of_day_confirm,
        product_of_day_user_view,
        pending_orders_panel,
    )

    try:
        # ── NOOP ─────────────────────────────────────────────────
        if data == "noop":
            return

        # ── HOME ─────────────────────────────────────────────────
        elif data == "home":
            await show_main_menu(update, context)

        # ── SHOP ─────────────────────────────────────────────────
        elif data == "shop":
            await shop_handler(update, context)

        elif data.startswith("cats_page:"):
            page = safe_int(data.split(":")[1], 1)
            categories = db.get_categories(active_only=True)
            from config import CATEGORIES_PER_PAGE
            from keyboards.inline import categories_keyboard
            total_pages = max(1, (len(categories) + CATEGORIES_PER_PAGE - 1) // CATEGORIES_PER_PAGE)
            start = (page - 1) * CATEGORIES_PER_PAGE
            await safe_edit_message(update, _("select_category", lang),
                                     categories_keyboard(categories[start:start+CATEGORIES_PER_PAGE],
                                                         page, total_pages, lang), "HTML")

        elif data.startswith("cat:"):
            parts = data.split(":")
            cat_id = safe_int(parts[1])
            page = safe_int(parts[2]) if len(parts) > 2 else 1
            await category_handler(update, context, cat_id, page)

        elif data.startswith("product:"):
            await product_handler(update, context, safe_int(data.split(":")[1]))

        # ── PURCHASE ─────────────────────────────────────────────
        elif data.startswith("buy:"):
            parts = data.split(":")
            await buy_handler(update, context, parts[1], safe_int(parts[2]))

        elif data.startswith("confirm_buy:"):
            parts = data.split(":")
            await confirm_buy_handler(update, context, parts[1], safe_int(parts[2]))

        elif data.startswith("coupon:"):
            parts = data.split(":")
            await apply_coupon_prompt(update, context, safe_int(parts[1]), parts[2])

        # ── STARS PACKAGES (user-facing) ──────────────────────────
        elif data == "deposit:stars_menu":
            await deposit_stars_menu_handler(update, context)

        elif data.startswith("buy_stars_pkg:"):
            pkg_id = safe_int(data.split(":")[1])
            await _handle_buy_stars_package(update, context, pkg_id)

        # ── BALANCE / DEPOSITS ────────────────────────────────────
        elif data == "balance":
            await balance_handler(update, context)

        elif data == "deposit:usdt":
            await deposit_usdt_handler(update, context)

        elif data == "submit_tx":
            context.user_data[UserState.AWAITING_DEPOSIT_AMT] = True
            await safe_edit_message(update, _("ask_amount", lang),
                                     cancel_keyboard("balance", lang), "HTML")

        elif data == "deposit:stars":
            await deposit_stars_menu_handler(update, context)

        # ── ORDERS ───────────────────────────────────────────────
        elif data.startswith("orders:"):
            page = safe_int(data.split(":")[1], 1)
            await orders_handler(update, context, page)

        elif data.startswith("order_detail:"):
            order_id = data.split(":", 1)[1]
            await _show_order_detail(update, context, order_id)

        # ── PROFILE ──────────────────────────────────────────────
        elif data == "profile":
            await profile_handler(update, context)

        # ── SEARCH ───────────────────────────────────────────────
        elif data == "search":
            await search_handler(update, context)

        elif data.startswith("search_pg:"):
            parts = data.split(":")
            await search_results_handler(update, context, parts[1], safe_int(parts[2], 1))

        # ── DAILY GIFT CLAIM (user-facing) ───────────────────────
        elif data == "daily_gift:claim":
            success, msg, points = db.claim_daily_gift(user.id)
            if success:
                await query.answer(f"🎁 +{points:.2f} points claimed!", show_alert=True)
                from handlers.user_handlers import profile_handler
                await profile_handler(update, context)
            else:
                await query.answer(f"❌ {msg}", show_alert=True)

        # ── REFERRAL ─────────────────────────────────────────────
        elif data == "referral":
            await referral_handler(update, context)

        elif data == "referral_list":
            await _show_referral_list(update, context)

        # ── LANGUAGE ─────────────────────────────────────────────
        elif data == "language":
            await language_handler(update, context)

        elif data == "tos":
            from languages.strings import _
            from utils.helpers import safe_edit_message
            lang = context.user_data.get("lang", "en")
            tos_text = _("tos_text", lang)
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Back", callback_data="home")]])
            await safe_edit_message(update, tos_text, kb, "HTML")

        elif data.startswith("setlang:"):
            new_lang = data.split(":")[1]
            if new_lang in ("en", "ar", "fr"):
                db.update_user(user.id, language=new_lang)
                context.user_data["lang"] = new_lang
                from keyboards.inline import language_keyboard
                await safe_edit_message(update, _("language_changed", new_lang),
                                         language_keyboard(new_lang), "HTML")

        # ── SUPPORT ──────────────────────────────────────────────
        elif data == "support":
            await support_handler(update, context)

        # ── FORCE SUBSCRIBE ──────────────────────────────────────
        elif data == "check_subscribe":
            await check_subscribe_callback(update, context)

        # ── CAPTCHA ──────────────────────────────────────────────
        elif data.startswith("captcha:"):
            await captcha_callback(update, context, safe_int(data.split(":")[1]))

        # ════════════════════════════════════════════════════════
        #  ADMIN ROUTES (guard: is_admin)
        # ════════════════════════════════════════════════════════

        elif not is_admin(user.id):
            logger.debug(f"Non-admin tried: {data!r}")

        # ── GAMES CENTER ─────────────────────────────────────────
        elif data == "game:menu":
            from handlers.games_handlers import games_menu
            await games_menu(update, context)

        elif data == "game:daily":
            from handlers.games_handlers import daily_reward_handler
            await daily_reward_handler(update, context)

        elif data == "game:slots":
            from handlers.games_handlers import slots_menu
            await slots_menu(update, context)

        elif data == "game:wheel":
            from handlers.games_handlers import wheel_menu
            await wheel_menu(update, context)

        elif data == "game:coinflip":
            from handlers.games_handlers import coinflip_menu
            await coinflip_menu(update, context)

        elif data.startswith("game:cf:"):
            choice = data.split(":")[2]
            from handlers.games_handlers import coinflip_choose
            await coinflip_choose(update, context, choice)

        elif data.startswith("game:lb:"):
            mode = data.split(":")[2]
            from handlers.games_handlers import leaderboard_handler
            await leaderboard_handler(update, context, mode)

        elif data.startswith("game:history:"):
            page = safe_int(data.split(":")[2]) or 1
            from handlers.games_handlers import game_history_handler
            await game_history_handler(update, context, page)

        # ── GAMES ADMIN ──────────────────────────────────────────
        elif data == "games_admin":
            from handlers.games_admin_handlers import games_admin_panel
            await games_admin_panel(update, context)

        elif data == "gcfg:dashboard":
            from handlers.games_admin_handlers import games_dashboard
            await games_dashboard(update, context)

        elif data == "gcfg:global_rtp":
            from handlers.games_admin_handlers import games_cfg_global_rtp
            await games_cfg_global_rtp(update, context)

        elif data == "gcfg:toggle_games":
            from handlers.games_admin_handlers import games_cfg_toggle
            await games_cfg_toggle(update, context)

        elif data.startswith("gcfg:toggle:"):
            game = data.split(":")[2]
            from handlers.games_admin_handlers import games_toggle_game
            await games_toggle_game(update, context, game)

        elif data == "gcfg:eco_engine":
            from handlers.games_admin_handlers import games_cfg_eco_engine
            await games_cfg_eco_engine(update, context)

        elif data == "gcfg:eco_toggle":
            from handlers.games_admin_handlers import games_eco_toggle
            await games_eco_toggle(update, context)

        elif data == "gcfg:rtp_reset_adj":
            from handlers.games_admin_handlers import games_rtp_reset_adj
            await games_rtp_reset_adj(update, context)

        elif data == "game:disabled":
            await safe_answer_callback(update, "🔒 This game is currently disabled.", show_alert=True)

        elif data.startswith("game:disabled:"):
            await safe_answer_callback(update, "🔒 This game is currently disabled.", show_alert=True)

        elif data == "gcfg:bets":
            from handlers.games_admin_handlers import games_cfg_bets
            await games_cfg_bets(update, context)

        elif data == "gcfg:cooldowns":
            from handlers.games_admin_handlers import games_cfg_cooldowns
            await games_cfg_cooldowns(update, context)

        elif data == "gcfg:slots":
            from handlers.games_admin_handlers import games_cfg_slots
            await games_cfg_slots(update, context)

        elif data == "gcfg:coinflip":
            from handlers.games_admin_handlers import games_cfg_coinflip
            await games_cfg_coinflip(update, context)

        elif data == "gcfg:wheel":
            from handlers.games_admin_handlers import games_cfg_wheel
            await games_cfg_wheel(update, context)

        elif data == "gcfg:wheel_add":
            from handlers.games_admin_handlers import games_cfg_wheel_add
            await games_cfg_wheel_add(update, context)

        elif data.startswith("gcfg:wheel_edit:"):
            idx = safe_int(data.split(":")[2]) or 0
            from handlers.games_admin_handlers import games_cfg_wheel_edit
            await games_cfg_wheel_edit(update, context, idx)

        elif data.startswith("gcfg:wheel_del:"):
            idx = safe_int(data.split(":")[2]) or 0
            from handlers.games_admin_handlers import games_cfg_wheel_del
            await games_cfg_wheel_del(update, context, idx)

        elif data.startswith("gcfg:wheel_field:"):
            parts = data.split(":")
            idx = safe_int(parts[2]) or 0
            field = parts[3]
            from handlers.games_admin_handlers import games_cfg_wheel_field
            await games_cfg_wheel_field(update, context, idx, field)

        elif data == "gcfg:daily":
            from handlers.games_admin_handlers import games_cfg_daily
            await games_cfg_daily(update, context)

        elif data.startswith("gcfg:set:"):
            key = data[9:]
            from handlers.games_admin_handlers import games_cfg_set_prompt
            await games_cfg_set_prompt(update, context, key)

        elif data == "gcfg:stats":
            # Quick game stats for admin
            from utils.helpers import format_price
            with db.get_db() as conn:
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM games_history")
                total_games = c.fetchone()[0]
                c.execute("SELECT COALESCE(SUM(CASE WHEN profit>0 THEN 1 ELSE 0 END),0), COUNT(*) FROM games_history")
                wins, total = c.fetchone()
                c.execute("SELECT COALESCE(SUM(profit),0) FROM games_history WHERE profit>0")
                total_paid = c.fetchone()[0] or 0
                c.execute("SELECT COALESCE(SUM(ABS(profit)),0) FROM games_history WHERE profit<0")
                total_taken = c.fetchone()[0] or 0
            win_rate = round(wins/total*100, 1) if total else 0
            house_edge = round((total_taken - total_paid) / max(total_taken, 0.01) * 100, 2)
            text = (
                "📊 <b>Games Statistics</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🎮 Total Games: <b>{total_games:,}</b>\n"
                f"🏆 Win Rate: <b>{win_rate}%</b>\n"
                f"💵 Total Paid Out: <b>${format_price(total_paid)}</b>\n"
                f"💰 Total Collected: <b>${format_price(total_taken)}</b>\n"
                f"🏦 House Edge: <b>{house_edge}%</b>"
            )
            from keyboards.games_keyboards import games_admin_keyboard
            await safe_edit_message(update, text, games_admin_keyboard(), "HTML")

        elif data == "gcfg:reset_confirm":
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("⚠️ Yes, Reset ALL History", callback_data="gcfg:reset_do")],
                [InlineKeyboardButton("◀️ Cancel", callback_data="games_admin")],
            ])
            await safe_edit_message(
                update,
                "⚠️ <b>Reset Game History?</b>\n\nThis deletes ALL games_history and leaderboard_stats. Cannot be undone.",
                kb, "HTML"
            )

        elif data == "gcfg:reset_do":
            if not is_admin(update.effective_user.id):
                await safe_answer_callback(update, "⛔ Access denied", show_alert=True)
            else:
                with db.get_db() as conn:
                    conn.execute("DELETE FROM games_history")
                    conn.execute("DELETE FROM leaderboard_stats")
                db.add_admin_log(update.effective_user.id, "game_reset", "Reset all game history")
                await safe_answer_callback(update, "✅ Game history reset.")
                from handlers.games_admin_handlers import games_admin_panel
                await games_admin_panel(update, context)

        # ── ADMIN MAIN ───────────────────────────────────────────
        elif data == "admin":
            await admin_panel(update, context)

        elif data == "admin_stats":
            await admin_stats(update, context)

        # ── SETTINGS PANEL ───────────────────────────────────────
        elif data == "admin_settings":
            from keyboards.inline import admin_settings_keyboard
            text = "⚙️ <b>Bot Settings</b>\n━━━━━━━━━━━━━━━━\nSelect a category:"
            await safe_edit_message(update, text, admin_settings_keyboard(), "HTML")

        elif data.startswith("cfg:"):
            section = data.split(":")[1]
            if section == "general":
                await settings_general(update, context)
            elif section == "force_sub":
                await force_subscribe_panel(update, context)
            elif section == "payment":
                await settings_payment(update, context)
            elif section == "stars":
                await stars_panel(update, context)
            elif section == "referral":
                await referral_panel(update, context)
            elif section == "security":
                await settings_security(update, context)
            elif section == "notify":
                await settings_notify(update, context)
            elif section == "messages":
                await settings_messages(update, context)
            elif section == "delivery":
                await settings_delivery(update, context)
            elif section == "admins":
                await admin_management_panel(update, context)

        # ── SETTING TOGGLES ──────────────────────────────────────
        elif data.startswith("stg:toggle:"):
            key = data.split(":", 2)[2]
            await toggle_setting(update, context, key)

        elif data.startswith("stg:edit:"):
            key = data.split(":", 2)[2]
            await edit_setting_start(update, context, key)

        # ── FORCE SUBSCRIBE ──────────────────────────────────────
        elif data == "fs:toggle":
            await toggle_force_subscribe(update, context)

        elif data == "fs:add":
            await add_channel_start(update, context)

        elif data.startswith("fs:detail:"):
            channel_id = safe_int(data.split(":")[2])
            await channel_detail(update, context, channel_id)

        elif data.startswith("fs:toggle_ch:"):
            channel_id = safe_int(data.split(":")[2])
            await toggle_channel(update, context, channel_id)

        elif data.startswith("fs:remove:"):
            channel_id = safe_int(data.split(":")[2])
            await remove_channel(update, context, channel_id)

        elif data.startswith("fs:edit_link:"):
            channel_id = safe_int(data.split(":")[2])
            context.user_data["editing_channel_id"] = channel_id
            context.user_data["editing_channel_field"] = "link"
            await safe_edit_message(update,
                "🔗 Enter new channel link (e.g. https://t.me/mychannel):",
                cancel_keyboard(f"fs:detail:{channel_id}"), "HTML")

        # ── REFERRAL ADMIN ───────────────────────────────────────
        elif data == "ref:toggle":
            await toggle_referral(update, context)

        elif data == "ref:reward_type":
            await referral_reward_type(update, context)

        elif data.startswith("ref:set_type:"):
            rtype = data.split(":")[2]
            await set_referral_reward_type(update, context, rtype)

        elif data == "ref:leaderboard":
            await referral_leaderboard(update, context)
        elif data == "ref:pay_weekly":
            from handlers.referral_admin_handlers import pay_weekly_rewards_handler
            await pay_weekly_rewards_handler(update, context)

        elif data == "ref:stats":
            await referral_stats(update, context)

        elif data.startswith("ref:edit:"):
            key = data.split(":", 2)[2]
            await edit_referral_start(update, context, key)

        # ── STARS ADMIN ──────────────────────────────────────────
        elif data == "stars:toggle":
            await toggle_stars(update, context)

        elif data == "stars:packages":
            await stars_packages_list(update, context)

        elif data == "stars:add_pkg":
            await add_package_start(update, context)

        elif data.startswith("stars:pkg:"):
            pkg_id = safe_int(data.split(":")[2])
            await stars_package_detail(update, context, pkg_id)

        elif data.startswith("stars:pkg_toggle:"):
            pkg_id = safe_int(data.split(":")[2])
            await toggle_package(update, context, pkg_id)

        elif data.startswith("stars:pkg_del:"):
            pkg_id = safe_int(data.split(":")[2])
            await delete_package(update, context, pkg_id)

        elif data.startswith("stars:pkg_edit:"):
            parts = data.split(":")
            field = parts[2]
            pkg_id = safe_int(parts[3])
            await edit_package_field_start(update, context, field, pkg_id)

        elif data.startswith("stars:edit:"):
            key = data.split(":", 2)[2]
            await edit_stars_setting_start(update, context, key)

        elif data.startswith("stars:test:"):
            pkg_id = safe_int(data.split(":")[2])
            await test_stars_invoice(update, context, pkg_id)

        # ── ADMIN MANAGEMENT ─────────────────────────────────────
        elif data == "adm:add":
            await add_admin_start(update, context)

        elif data.startswith("adm:detail:"):
            target_id = safe_int(data.split(":")[2])
            await admin_detail(update, context, target_id)

        elif data.startswith("adm:remove:"):
            target_id = safe_int(data.split(":")[2])
            await remove_admin(update, context, target_id)

        # ── PRODUCTS ─────────────────────────────────────────────
        elif data.startswith("admin_products:"):
            await admin_products(update, context, safe_int(data.split(":")[1], 1))

        elif data.startswith("admin_product:"):
            await admin_product_detail(update, context, safe_int(data.split(":")[1]))

        elif data == "admin_add_product":
            await admin_add_product_start(update, context)

        elif data.startswith("ap_cat:"):
            await admin_add_product_category(update, context, safe_int(data.split(":")[1]))

        elif data.startswith("admin_edit_product:"):
            parts = data.split(":")
            await admin_edit_product_field(update, context, parts[1], safe_int(parts[2]))

        elif data.startswith("admin_toggle_product:"):
            await admin_toggle_product(update, context, safe_int(data.split(":")[1]))

        elif data.startswith("admin_delete_product:"):
            await admin_delete_product_confirm(update, context, safe_int(data.split(":")[1]))

        # ── CATEGORIES ───────────────────────────────────────────
        elif data == "admin_categories":
            # Clear any in-progress category wizard state
            context.user_data.pop(UserState.ADMIN_ADD_CATEGORY, None)
            context.user_data.pop("category_step", None)
            context.user_data.pop("category_data", None)
            await admin_categories(update, context)

        elif data == "admin_add_category":
            await admin_add_category_start(update, context)

        elif data.startswith("admin_cat:"):
            await admin_category_detail(update, context, safe_int(data.split(":")[1]))

        elif data.startswith("admin_toggle_cat:"):
            cat_id = safe_int(data.split(":")[1])
            cat = db.get_category(cat_id)
            if cat:
                db.update_category(cat_id, is_active=0 if cat.get("is_active") else 1)
            await admin_categories(update, context)

        elif data.startswith("admin_delete_cat:"):
            cat_id = safe_int(data.split(":")[1])
            db.delete_category(cat_id)
            await query.answer("🗑️ Category deleted", show_alert=False)
            await admin_categories(update, context)

        elif data.startswith("admin_edit_cat:"):
            parts = data.split(":")
            field = parts[1]
            cat_id = safe_int(parts[2])
            context.user_data["editing_cat_id"] = cat_id
            context.user_data["editing_cat_field"] = field
            label = "new name" if field == "name" else "new emoji"
            await safe_edit_message(update, f"✏️ Enter {label}:",
                                     cancel_keyboard("admin_categories"), "HTML")

        # ── USERS (Advanced Management) ───────────────────────────
        elif data.startswith("admin_users:"):
            # Route through the new advanced panel
            from handlers.user_mgmt_handlers import admin_users_advanced
            await admin_users_advanced(update, context, safe_int(data.split(":")[1], 1))

        elif data == "admin_users":
            from handlers.user_mgmt_handlers import admin_users_advanced
            await admin_users_advanced(update, context, 1)

        elif data == "admin_user_search":
            from handlers.user_mgmt_handlers import uf_search_start
            await uf_search_start(update, context)

        # ── User Filter / Management callbacks ────────────────────
        elif data.startswith("uf_page:"):
            from handlers.user_mgmt_handlers import admin_users_advanced
            await admin_users_advanced(update, context, safe_int(data.split(":")[1], 1))

        elif data.startswith("uf_profile:"):
            from handlers.user_mgmt_handlers import uf_user_profile
            await uf_user_profile(update, context, safe_int(data.split(":")[1]))

        elif data == "uf_filter_menu":
            from handlers.user_mgmt_handlers import uf_filter_menu
            await uf_filter_menu(update, context)

        elif data == "uf_presets":
            from handlers.user_mgmt_handlers import uf_presets
            await uf_presets(update, context)

        elif data.startswith("uf_preset:"):
            from handlers.user_mgmt_handlers import admin_users_advanced
            preset = data.split(":", 1)[1]
            context.user_data["uf_filters"] = {"preset": preset}
            await admin_users_advanced(update, context, 1)

        elif data == "uf_sort_menu":
            from handlers.user_mgmt_handlers import uf_sort_menu
            await uf_sort_menu(update, context)

        elif data.startswith("uf_setsort:"):
            from handlers.user_mgmt_handlers import admin_users_advanced
            context.user_data["uf_sort"] = data.split(":", 1)[1]
            await admin_users_advanced(update, context, 1)

        elif data == "uf_toggle_dir":
            from handlers.user_mgmt_handlers import admin_users_advanced
            cur = context.user_data.get("uf_sort_dir", "DESC")
            context.user_data["uf_sort_dir"] = "ASC" if cur == "DESC" else "DESC"
            await admin_users_advanced(update, context, 1)

        elif data.startswith("uf_fset:"):
            # Numeric filter input
            field = data.split(":", 1)[1]
            from handlers.user_mgmt_handlers import _admin_check
            if not _admin_check(update):
                return
            context.user_data["uf_state"] = f"fset_{field}"
            labels = {
                "balance_min":  "💰 Minimum balance (e.g. 10.00):",
                "balance_max":  "💰 Maximum balance:",
                "spent_min":    "💵 Minimum total spent:",
                "spent_max":    "💵 Maximum total spent:",
                "orders_min":   "🛒 Minimum order count:",
                "orders_max":   "🛒 Maximum order count:",
                "joined_after": "📅 Joined after (YYYY-MM-DD):",
                "joined_before":"📅 Joined before (YYYY-MM-DD):",
                "seen_after":   "🕐 Last seen after (YYYY-MM-DD):",
                "seen_before":  "🕐 Last seen before (YYYY-MM-DD):",
            }
            from keyboards.inline import cancel_keyboard
            await safe_edit_message(
                update,
                f"🔢 <b>Set Filter</b>\n\n{labels.get(field, 'Enter value:')}",
                cancel_keyboard("uf_filter_menu"), "HTML"
            )
            context.user_data["uf_pending_field"] = field

        elif data == "uf_lang_menu":
            from handlers.user_mgmt_handlers import uf_lang_menu
            await uf_lang_menu(update, context)

        elif data.startswith("uf_setlang:"):
            from handlers.user_mgmt_handlers import admin_users_advanced
            lang = data.split(":", 1)[1]
            if lang == "any":
                context.user_data.setdefault("uf_filters", {}).pop("language", None)
            else:
                context.user_data.setdefault("uf_filters", {})["language"] = lang
            await admin_users_advanced(update, context, 1)

        elif data == "uf_vip_filter":
            from handlers.user_mgmt_handlers import uf_vip_filter
            await uf_vip_filter(update, context)

        elif data.startswith("uf_setvip:"):
            from handlers.user_mgmt_handlers import admin_users_advanced
            rank = safe_int(data.split(":")[1], None)
            context.user_data.setdefault("uf_filters", {})["vip_rank"] = rank
            await admin_users_advanced(update, context, 1)

        elif data == "uf_ban_filter":
            from handlers.user_mgmt_handlers import uf_ban_filter
            await uf_ban_filter(update, context)

        elif data.startswith("uf_setban:"):
            from handlers.user_mgmt_handlers import admin_users_advanced
            val = data.split(":")[1]
            filters = context.user_data.setdefault("uf_filters", {})
            if val == "all":
                filters.pop("is_banned", None)
            else:
                filters["is_banned"] = (val == "1")
            await admin_users_advanced(update, context, 1)

        elif data.startswith("uf_toggle:"):
            field = data.split(":", 1)[1]
            filters = context.user_data.setdefault("uf_filters", {})
            filters[field] = not filters.get(field, False)
            from handlers.user_mgmt_handlers import uf_filter_menu
            await uf_filter_menu(update, context)

        elif data == "uf_clear_filters":
            from handlers.user_mgmt_handlers import _clear_filters, admin_users_advanced
            _clear_filters(context)
            await admin_users_advanced(update, context, 1)

        elif data == "uf_clear_search":
            context.user_data.pop("uf_search", None)
            context.user_data.pop("uf_state", None)
            from handlers.user_mgmt_handlers import admin_users_advanced
            await admin_users_advanced(update, context, 1)

        elif data == "uf_search_start":
            from handlers.user_mgmt_handlers import uf_search_start
            await uf_search_start(update, context)

        # ── Admin Notes ─────────────────────────────────────────────
        elif data.startswith("uf_notes:"):
            from handlers.user_mgmt_handlers import uf_notes_page
            await uf_notes_page(update, context, safe_int(data.split(":")[1]))

        elif data.startswith("uf_note_add:"):
            from handlers.user_mgmt_handlers import uf_note_add_start
            await uf_note_add_start(update, context, safe_int(data.split(":")[1]))

        elif data.startswith("uf_note_edit:"):
            from handlers.user_mgmt_handlers import uf_note_edit_start
            parts = data.split(":")
            await uf_note_edit_start(update, context,
                                      safe_int(parts[1]), safe_int(parts[2]))

        elif data.startswith("uf_note_del:"):
            from handlers.user_mgmt_handlers import uf_note_delete
            parts = data.split(":")
            await uf_note_delete(update, context,
                                  safe_int(parts[1]), safe_int(parts[2]))

        # ── VIP Assignment ──────────────────────────────────────────
        elif data.startswith("uf_setvip_user:"):
            from handlers.user_mgmt_handlers import uf_setvip_user
            await uf_setvip_user(update, context, safe_int(data.split(":")[1]))

        elif data.startswith("uf_dovip:"):
            parts = data.split(":")
            target_id = safe_int(parts[1])
            rank      = safe_int(parts[2])
            import database_user_mgmt as dum
            dum.set_user_vip(target_id, rank, update.effective_user.id)
            db.add_admin_log(update.effective_user.id, "set_vip",
                             f"VIP {rank} for {target_id}", target_id)
            await safe_answer_callback(update, f"👑 VIP set: {dum.get_vip_label(rank)}")
            from handlers.user_mgmt_handlers import uf_user_profile
            await uf_user_profile(update, context, target_id)

        # ── Bulk Actions ─────────────────────────────────────────────
        elif data == "uf_bulk_menu":
            from handlers.user_mgmt_handlers import uf_bulk_menu
            await uf_bulk_menu(update, context)

        elif data.startswith("uf_bulk_confirm:"):
            from handlers.user_mgmt_handlers import uf_bulk_confirm
            await uf_bulk_confirm(update, context, data.split(":", 1)[1])

        elif data.startswith("uf_bulk_do:"):
            from handlers.user_mgmt_handlers import uf_bulk_do
            await uf_bulk_do(update, context, data.split(":", 1)[1])

        elif data.startswith("uf_bulk_action:"):
            from handlers.user_mgmt_handlers import uf_bulk_action_start
            await uf_bulk_action_start(update, context, data.split(":", 1)[1])

        elif data == "uf_bulk_vip":
            from handlers.user_mgmt_handlers import uf_bulk_vip_menu
            await uf_bulk_vip_menu(update, context)

        elif data.startswith("uf_bulk_dovip:"):
            from handlers.user_mgmt_handlers import uf_bulk_dovip
            await uf_bulk_dovip(update, context, safe_int(data.split(":")[1], 0))

        elif data == "uf_bulk_broadcast":
            # Reuse the existing broadcast flow but scoped to filtered users
            context.user_data["bulk_broadcast_filters"] = _filters(context).copy()
            context.user_data["bulk_broadcast_search"]  = context.user_data.get("uf_search", "")
            context.user_data[UserState.ADMIN_BROADCAST] = True
            from keyboards.inline import cancel_keyboard
            await safe_edit_message(
                update,
                "📢 <b>Bulk Broadcast</b>\n\n"
                "This will send to ALL filtered users.\n\nType your message:",
                cancel_keyboard("uf_bulk_menu"), "HTML"
            )

        elif data == "uf_bulk_export":
            from handlers.user_mgmt_handlers import uf_bulk_export
            await uf_bulk_export(update, context)

        elif data.startswith("admin_user:"):
            await admin_user_detail(update, context, safe_int(data.split(":")[1]))

        elif data.startswith("admin_ban:"):
            await admin_ban_user(update, context, safe_int(data.split(":")[1]))

        elif data.startswith("admin_unban:"):
            await admin_unban_user(update, context, safe_int(data.split(":")[1]))

        elif data.startswith("admin_adjust:"):
            await admin_adjust_balance(update, context, safe_int(data.split(":")[1]))

        elif data.startswith("admin_adjust_stars:"):
            await admin_adjust_stars(update, context, safe_int(data.split(":")[1]))

        elif data.startswith("admin_user_orders:"):
            target_id = safe_int(data.split(":")[1])
            orders, _total = db.get_user_orders(target_id, 1, 10)
            lines = [f"• {o.get('product_name','?')} — ${o.get('amount',0):.2f} [{o.get('status','?')}]"
                     for o in orders]
            await safe_edit_message(update,
                f"📜 <b>Orders for {target_id}</b>\n\n" + ("\n".join(lines) or "No orders yet."),
                InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Back",
                    callback_data=f"admin_user:{target_id}")]]), "HTML")

        # ── DEPOSITS ─────────────────────────────────────────────
        elif data == "admin_deposits":
            await admin_deposits(update, context)

        elif data.startswith("admin_dep:"):
            await admin_deposit_detail(update, context, data.split(":", 1)[1])

        elif data.startswith("admin_dep_confirm:"):
            await admin_deposit_confirm(update, context, data.split(":", 1)[1])

        elif data.startswith("admin_dep_reject:"):
            await admin_deposit_reject(update, context, data.split(":", 1)[1])

        # ── ORDERS (admin) ────────────────────────────────────────
        elif data.startswith("admin_orders:"):
            page = safe_int(data.split(":")[1], 1)
            await admin_orders(update, context, page)

        elif data.startswith("admin_order_detail:"):
            order_id = data.split(":", 1)[1]
            await _show_admin_order_detail(update, context, order_id)

        # ── COUPONS ──────────────────────────────────────────────
        elif data == "admin_coupons":
            await admin_coupons(update, context)

        elif data == "admin_add_coupon":
            await admin_add_coupon_start(update, context)

        elif data.startswith("admin_coupon:"):
            await admin_coupon_detail(update, context, safe_int(data.split(":")[1]))

        elif data.startswith("admin_toggle_coupon:"):
            coupon_id = safe_int(data.split(":")[1])
            with db.get_db() as conn:
                c = conn.cursor()
                c.execute("SELECT is_active FROM coupons WHERE id=?", (coupon_id,))
                row = c.fetchone()
                if row:
                    conn.execute("UPDATE coupons SET is_active=? WHERE id=?",
                                 (0 if row[0] else 1, coupon_id))
            await admin_coupons(update, context)

        elif data.startswith("admin_delete_coupon:"):
            coupon_id = safe_int(data.split(":")[1])
            db.delete_coupon(coupon_id)
            db.add_admin_log(user.id, "delete_coupon", f"Coupon #{coupon_id}", coupon_id)
            await query.answer("🗑️ Coupon deleted", show_alert=False)
            await admin_coupons(update, context)

        elif data.startswith("coupon_type:"):
            coup_type = data.split(":")[1]
            context.user_data.setdefault("coupon_data", {})["discount_type"] = coup_type
            context.user_data["coupon_step"] = "value"
            type_label = "percentage (e.g. 20)" if coup_type == "percentage" else "fixed amount (e.g. 5.00)"
            await safe_edit_message(update, f"💰 Enter discount {type_label}:",
                                     cancel_keyboard("admin_coupons"), "HTML")

        # ── BROADCAST ────────────────────────────────────────────
        elif data == "admin_broadcast":
            await admin_broadcast_start(update, context)

        # ── LOGS ─────────────────────────────────────────────────
        elif data.startswith("admin_logs:"):
            await admin_logs(update, context, safe_int(data.split(":")[1], 1))

        # ── BACKUP / EXPORT ───────────────────────────────────────
        elif data == "admin_backup":
            await admin_backup(update, context)

        elif data == "admin_export":
            await admin_export_users(update, context)

        elif data == "admin_take_db":
            await admin_take_database(update, context)

        elif data == "admin_upload_db":
            await admin_upload_database_start(update, context)

        elif data == "admin_upload_file":
            await admin_upload_file_start(update, context)

        # ── NEW FEATURES — USER ───────────────────────────────────
        elif data == "my_products":
            await my_products_handler(update, context)

        elif data.startswith("redownload:"):
            await redownload_handler(update, context, data.split(":", 1)[1])

        elif data == "track_order":
            await track_order_handler(update, context)

        elif data == "flash_sales":
            await flash_sales_user_view(update, context)

        elif data == "pod:view":
            await product_of_day_user_view(update, context)

        # ── NEW FEATURES — ADMIN ──────────────────────────────────
        elif data == "fs:panel":
            await flash_sale_panel(update, context)

        elif data == "fs:new":
            await flash_sale_new_start(update, context)

        elif data.startswith("fs:pick:"):
            await flash_sale_pick_product(update, context, safe_int(data.split(":")[2]))

        elif data.startswith("fs:cancel:"):
            await flash_sale_cancel(update, context, safe_int(data.split(":")[2]))

        elif data == "pod:admin":
            await set_product_of_day_start(update, context)

        elif data.startswith("pod:set:"):
            await set_product_of_day_confirm(update, context, safe_int(data.split(":")[2]))

        elif data == "po:list:1" or data.startswith("po:list:"):
            page = safe_int(data.split(":")[2], 1)
            await pending_orders_panel(update, context, page)

        elif data.startswith("po:detail:"):
            order_id = data.split(":", 2)[2]
            await _show_pending_order_detail(update, context, order_id)

        elif data == "admin_winback":
            from handlers.new_features_handlers import send_winback_notifications
            await query.answer("📣 Win-back campaign started!", show_alert=True)
            await context.application.job_queue.run_once(
                send_winback_notifications, when=1
            )

        # ── CONFIRM DELETE ────────────────────────────────────────
        elif data.startswith("confirm_delete:"):
            parts = data.split(":")
            item_type = parts[1]
            item_id = safe_int(parts[2])
            if item_type == "product":
                db.delete_product(item_id)
                db.add_admin_log(user.id, "delete_product", f"Product #{item_id}", item_id)
                await query.answer("🗑️ Product deleted", show_alert=False)
                await admin_products(update, context)

        # ── PRODUCT SHARE LINK ────────────────────────────────────
        elif data.startswith("admin_product_share:"):
            product_id = safe_int(data.split(":")[1])
            product = db.get_product(product_id)
            if not product:
                await safe_answer_callback(update, "Product not found", show_alert=True)
                return
            token = db.get_or_create_product_share_token(product_id)
            bot_username = context.bot.username
            share_link = f"https://t.me/{bot_username}?start={token}"
            text = (
                f"🔗 <b>Share Link for:</b> {product['name']}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"Copy and share this link:\n\n"
                f"<code>{share_link}</code>\n\n"
                f"When a user opens this link, they will be taken directly to this product's page."
            )
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Back to Product",
                                      callback_data=f"admin_product:{product_id}")],
            ])
            await safe_edit_message(update, text, keyboard, "HTML")

        # ── REWARD LINKS ─────────────────────────────────────────
        elif data == "rl:panel":
            await reward_links_panel(update, context)

        elif data == "rl:create":
            await reward_link_create_start(update, context)

        elif data.startswith("rl:detail:"):
            link_id = safe_int(data.split(":")[2])
            await reward_link_detail(update, context, link_id)

        elif data.startswith("rl:delete:"):
            link_id = safe_int(data.split(":")[2])
            await reward_link_delete(update, context, link_id)

        elif data.startswith("rl:copy:"):
            link_id = safe_int(data.split(":")[2])
            with db.get_db() as conn:
                c = conn.cursor()
                c.execute("SELECT token FROM reward_links WHERE id = ?", (link_id,))
                row = c.fetchone()
            if row:
                bot_username = context.bot.username
                tg_link = f"https://t.me/{bot_username}?start={row['token']}"
                await query.answer(f"Link: {tg_link}", show_alert=True)
            else:
                await safe_answer_callback(update, "Link not found", show_alert=True)

        # ── DAILY GIFT ───────────────────────────────────────────
        elif data == "dg:panel":
            await daily_gift_panel(update, context)

        elif data == "dg:toggle":
            await toggle_daily_gift(update, context)

        elif data.startswith("dg:edit:"):
            field = data.split(":")[2]
            await daily_gift_edit_start(update, context, field)

        # ── RATINGS ──────────────────────────────────────────────

        elif data == "my_ratings":
            # Open the pending-ratings list (from profile)
            await pending_ratings_handler(update, context)

        elif data.startswith("rate_pick:"):
            # rate_pick:<product_id>:<order_id>
            # Show the star-picker WITHOUT submitting anything
            parts      = data.split(":", 2)
            product_id = safe_int(parts[1])
            order_id   = parts[2] if len(parts) > 2 else ""
            from handlers.rating_handlers import show_star_picker
            await show_star_picker(update, context, product_id, order_id)

        elif data.startswith("rate:"):
            # rate:<product_id>:<order_id>:<rating>  — rating MUST be 1-5
            parts      = data.split(":")
            product_id = safe_int(parts[1])
            order_id   = parts[2] if len(parts) > 2 else ""
            rating_val = safe_int(parts[3]) if len(parts) > 3 else 0
            if rating_val < 1 or rating_val > 5:
                # Bad data — show the picker again instead of crashing
                from handlers.rating_handlers import show_star_picker
                await show_star_picker(update, context, product_id, order_id)
            else:
                await handle_rating_callback(update, context, product_id, order_id, rating_val)

        elif data.startswith("rate_prompt:"):
            # Legacy / product-page "Rate this product" button → show picker
            parts      = data.split(":", 2)
            product_id = safe_int(parts[1])
            # No order_id known here — open pending list so user picks the right order
            await pending_ratings_handler(update, context)

        elif data.startswith("rate_submit:"):
            # rate_submit:<product_id>:<order_id>:<rating>  — Skip review button
            parts      = data.split(":")
            product_id = safe_int(parts[1])
            order_id   = parts[2]
            rating_val = safe_int(parts[3])
            await handle_rating_submit(update, context, product_id, order_id, rating_val)

        # ── ERROR DASHBOARD ──────────────────────────────────────
        elif data == "err:dashboard":
            await error_dashboard(update, context)
        elif data == "err:recent":
            await error_recent(update, context)
        elif data == "err:clear":
            await error_clear(update, context)

        # ── DELIVERY ─────────────────────────────────────────────
        elif data == "admin_failed_deliveries":
            await failed_deliveries_panel(update, context)

        elif data.startswith("delivery:resend:"):
            order_id = data.split(":", 2)[2]
            await resend_delivery(update, context, order_id)

        elif data.startswith("restore:"):
            order_id = data.split(":", 1)[1]
            from handlers.delivery_handlers import restore_purchase_handler
            await restore_purchase_handler(update, context, order_id)

        else:
            logger.debug(f"Unhandled callback: {data!r} from {user.id}")

    except Exception as e:
        from utils.error_tracker import error_tracker
        error_tracker.record(f"callback:{data[:40]}", e, user.id)
        logger.error(f"Callback error [{data}]: {e}", exc_info=True)
        try:
            await query.answer("❌ An error occurred", show_alert=False)
        except Exception:
            pass


# ─────────────────────────────────────────────
#  HELPER VIEWS
# ─────────────────────────────────────────────

async def _handle_buy_stars_package(update: Update, context: ContextTypes.DEFAULT_TYPE, pkg_id: int):
    """Generate and send an XTR invoice for a stars package."""
    from telegram import LabeledPrice
    pkg = db.get_stars_package(pkg_id)
    if not pkg or not pkg.get("is_active"):
        await safe_answer_callback(update, "❌ Package unavailable", show_alert=True)
        return
    if not db.get_setting("stars_enabled", True):
        await safe_answer_callback(update, "⭐ Stars system is disabled", show_alert=True)
        return

    total = pkg["stars"] + pkg.get("bonus_stars", 0)
    bonus_txt = f" (+{pkg['bonus_stars']}⭐ bonus)" if pkg.get("bonus_stars") else ""

    try:
        link = await context.bot.create_invoice_link(
            title=pkg["name"],
            description=f"Buy {total}⭐ Telegram Stars{bonus_txt}",
            payload=f"stars_pkg_{pkg_id}",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(pkg["name"], pkg["stars"])]
        )
        lang = _lang(context)
        await safe_edit_message(
            update,
            f"⭐ <b>{pkg['name']}</b>\n\n"
            f"You will receive: <b>{total} Stars</b>{bonus_txt}\n"
            f"Price: <b>{pkg['stars']} XTR</b>\n\n"
            f"Tap the button below to pay:",
            InlineKeyboardMarkup([
                [InlineKeyboardButton("⭐ Pay Now", url=link)],
                [InlineKeyboardButton("◀️ Back", callback_data="deposit:stars_menu")],
            ]),
            "HTML"
        )
    except Exception as e:
        logger.error(f"Stars invoice error: {e}")
        await safe_answer_callback(update, "❌ Failed to create invoice", show_alert=True)


async def _show_order_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, order_id: str):
    lang = _lang(context)
    with db.get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT o.*, p.file_id, p.file_type, p.name as pname
            FROM orders o LEFT JOIN products p ON o.product_id = p.id
            WHERE o.order_id = ?
        """, (order_id,))
        order = c.fetchone()
    if not order:
        await safe_edit_message(update, "❌ Order not found.",
                                 cancel_keyboard("orders:1", lang), "HTML")
        return
    order = dict(order)
    from utils.formatting import order_receipt
    text = order_receipt(order)

    # Build action buttons
    buttons = []
    # Show restore button if product has a deliverable file
    if order.get("file_id") and order.get("status") == "completed":
        buttons.append([InlineKeyboardButton(
            "📥 Restore Download", callback_data=f"restore:{order_id}"
        )])
    # Rate button if completed and not rated
    if order.get("status") == "completed" and order.get("product_id"):
        try:
            user_id = update.effective_user.id
            if db.can_rate_product(user_id, order["product_id"]):
                buttons.append([InlineKeyboardButton(
                    "⭐ Rate This Product",
                    callback_data=f"rate_pick:{order['product_id']}:{order_id}"
                )])
        except Exception:
            pass
    buttons.append([InlineKeyboardButton("◀️ My Orders", callback_data="orders:1")])

    await safe_edit_message(update, text, InlineKeyboardMarkup(buttons), "HTML")


async def _show_referral_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from utils.helpers import format_date
    user = update.effective_user
    lang = _lang(context)
    referrals = db.get_user_referrals(user.id)
    if not referrals:
        text = "👥 <b>My Referrals</b>\n\nNo referrals yet. Share your link to earn!"
    else:
        lines = [
            f"• {r.get('first_name') or 'User'} — joined {format_date(r.get('created_at', ''))}"
            for r in referrals[:20]
        ]
        text = f"👥 <b>My Referrals ({len(referrals)})</b>\n\n" + "\n".join(lines)
    await safe_edit_message(update, text,
                             InlineKeyboardMarkup([[
                                 InlineKeyboardButton("◀️ Back", callback_data="referral")
                             ]]), "HTML")


async def _show_pending_order_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, order_id: str):
    """Show pending order detail for admin with approve/cancel actions."""
    with db.get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT o.*, u.first_name, u.username, p.name as pname
            FROM orders o
            LEFT JOIN users u ON o.user_id = u.user_id
            LEFT JOIN products p ON o.product_id = p.id
            WHERE o.order_id = ?
        """, (order_id,))
        order = c.fetchone()
    if not order:
        await safe_edit_message(update, "❌ Order not found.",
                                 InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Back", callback_data="po:list:1")]]),
                                 "HTML")
        return
    order = dict(order)
    user_name = order.get("first_name") or f"User#{order['user_id']}"
    username_str = f" (@{order['username']})" if order.get("username") else ""
    status_map = {"completed": "✅ Completed", "pending": "⏳ Pending", "cancelled": "❌ Cancelled"}
    status = status_map.get(order.get("status", ""), "❓ Unknown")
    text = (
        f"⏳ <b>Pending Order Detail</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🧾 ID: <code>{order_id}</code>\n"
        f"👤 User: <b>{user_name}</b>{username_str}\n"
        f"📦 Product: <b>{order.get('pname') or order.get('product_name', '—')}</b>\n"
        f"💰 Amount: <b>${order.get('amount', 0):.2f}</b>\n"
        f"💳 Method: <b>{order.get('payment_method', '—')}</b>\n"
        f"📅 Created: <b>{str(order.get('created_at', '—'))[:16]}</b>\n"
        f"🚀 Status: <b>{status}</b>"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 View User", callback_data=f"admin_user:{order['user_id']}")],
        [InlineKeyboardButton("◀️ Pending Orders", callback_data="po:list:1")],
    ])
    await safe_edit_message(update, text, keyboard, "HTML")


async def _show_admin_order_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, order_id: str):
    """Show full order detail for admin (from admin_orders list)."""
    with db.get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT o.*, u.first_name, u.username, p.name as pname
            FROM orders o
            LEFT JOIN users u ON o.user_id = u.user_id
            LEFT JOIN products p ON o.product_id = p.id
            WHERE o.order_id = ?
        """, (order_id,))
        order = c.fetchone()
    if not order:
        await safe_edit_message(update, "❌ Order not found.",
                                 InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Back", callback_data="admin_orders:1")]]),
                                 "HTML")
        return
    order = dict(order)
    user_name = order.get("first_name") or f"User#{order['user_id']}"
    username_str = f" (@{order['username']})" if order.get("username") else ""
    status_map = {"completed": "✅ Completed", "pending": "⏳ Pending", "cancelled": "❌ Cancelled"}
    status = status_map.get(order.get("status", ""), "❓ Unknown")
    text = (
        f"📜 <b>Order Detail</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🧾 ID: <code>{order_id}</code>\n"
        f"👤 User: <b>{user_name}</b>{username_str}\n"
        f"📦 Product: <b>{order.get('pname') or order.get('product_name', '—')}</b>\n"
        f"💰 Amount: <b>${order.get('amount', 0):.2f}</b>\n"
        f"💳 Method: <b>{order.get('payment_method', '—')}</b>\n"
        f"📅 Created: <b>{str(order.get('created_at', '—'))[:16]}</b>\n"
        f"📬 Delivered: <b>{str(order.get('delivered_at', '—'))[:16] if order.get('delivered_at') else '—'}</b>\n"
        f"🚀 Status: <b>{status}</b>"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 View User", callback_data=f"admin_user:{order['user_id']}")],
        [InlineKeyboardButton("◀️ All Orders", callback_data="admin_orders:1")],
    ])
    await safe_edit_message(update, text, keyboard, "HTML")
