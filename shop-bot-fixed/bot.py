"""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║          ██████╗  ██████╗ ████████╗                             ║
║          ██╔══██╗██╔═══██╗╚══██╔══╝                            ║
║          ██████╔╝██║   ██║   ██║                                ║
║          ██╔══██╗██║   ██║   ██║                                ║
║          ██████╔╝╚██████╔╝   ██║                                ║
║          ╚═════╝  ╚═════╝    ╚═╝                                ║
║                                                                  ║
║        PREMIUM TELEGRAM SHOP BOT  v3.0.0                        ║
║        Multi-Language | Auto Delivery | Full Admin               ║
║        Dynamic settings — all controlled from Telegram           ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝

ENTRY POINT — registers all handlers and starts the bot.

Architecture:
  bot.py                       ← Entry point
  config.py                    ← BOT_TOKEN + PRIMARY_ADMIN_ID only
  database.py                  ← SQLite3 full DB layer (v3)
  languages/strings.py         ← Multi-language strings
  keyboards/inline.py          ← All InlineKeyboardMarkup builders
  utils/helpers.py             ← Shared utilities, decorators, state
  handlers/
    user_handlers.py           ← /start, shop, balance, orders, profile
    admin_handlers.py          ← Admin panel, products, users, stats
    settings_handlers.py       ← Dynamic settings panel (new)
    force_subscribe_handlers.py← Multi-channel force subscribe (new)
    referral_admin_handlers.py ← Referral admin panel (new)
    stars_admin_handlers.py    ← Stars system panel (new)
    admin_management_handlers.py← Admin add/remove panel (new)
    message_handlers.py        ← Text/file input wizard flows
    callback_router.py         ← Central callback dispatcher
"""

import asyncio
import logging
import sys
from telegram import Update, BotCommand
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, PreCheckoutQueryHandler
)
from telegram.error import NetworkError, TimedOut, RetryAfter

import database as db
from config import BOT_TOKEN, BOT_VERSION, PRIMARY_ADMIN_ID
from handlers.callback_router import callback_router
from handlers.user_handlers import start_handler
from handlers.message_handlers import message_handler

# ─────────────────────────────────────────────
#  LOGGING SETUP
# ─────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ],
)

for noisy in ("httpx", "httpcore", "telegram.ext.updater"):
    logging.getLogger(noisy).setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
#  STARS PAYMENT HANDLERS
# ─────────────────────────────────────────────

async def pre_checkout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Approve all Stars pre-checkout queries."""
    query = update.pre_checkout_query
    if not query:
        return
    try:
        await query.answer(ok=True)
        logger.info(f"Pre-checkout approved for user {query.from_user.id} payload={query.invoice_payload}")
    except Exception as e:
        logger.error(f"Pre-checkout error: {e}")
        try:
            await query.answer(ok=False, error_message="Payment processing error. Please try again.")
        except Exception:
            pass


async def successful_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle completed Stars payment — credit stars to user and notify."""
    user = update.effective_user
    payment = update.message.successful_payment
    if not payment:
        return

    payload = payment.invoice_payload
    total_amount = payment.total_amount  # Amount in Stars (XTR)
    logger.info(f"Stars payment: user={user.id} payload={payload} amount={total_amount}")

    # Ensure user exists in DB (they may have paid without going through /start)
    db.get_or_create_user(
        user_id=user.id,
        username=user.username or "",
        first_name=user.first_name or "",
        last_name=user.last_name or "",
    )

    # Determine which package was purchased
    pkg_id = None
    if payload.startswith("stars_pkg_"):
        try:
            pkg_id = int(payload.split("_")[-1])
        except ValueError:
            pass

    if pkg_id:
        pkg = db.get_stars_package(pkg_id)
        if pkg:
            # Credit bot points (balance) equal to the package's USD value
            points_credited = pkg["price_usd"]
            bonus_points = round(pkg.get("bonus_stars", 0) / max(pkg["stars"], 1) * points_credited, 4) if pkg.get("bonus_stars") else 0
            total_points = round(points_credited + bonus_points, 4)
            new_balance = db.adjust_balance(user.id, total_points)
            bonus_note = f"\n🎁 +${bonus_points:.4f} bonus points!" if bonus_points else ""

            await update.message.reply_text(
                f"✅ <b>Payment Successful!</b>\n\n"
                f"💰 <b>${total_points:.4f} Points</b> added to your balance!{bonus_note}\n\n"
                f"📦 Package: <b>{pkg['name']}</b>\n"
                f"💳 Paid: <b>{total_amount} XTR</b>\n"
                f"💰 New Balance: <b>${new_balance:.4f}</b>",
                parse_mode="HTML"
            )

            # Create order record
            order_id = db.create_order(
                user_id=user.id,
                product_id=None,
                amount=total_points,
                payment_method="Telegram Stars",
                product_name=f"Points Package: {pkg['name']}"
            )
            db.complete_order(order_id)

            # Log the event
            db.add_admin_log(user.id, "stars_purchase",
                             f"Pkg: {pkg['name']}, Points: ${total_points}", pkg_id)

            # Notify admins
            if db.get_setting("order_logs", True):
                admin_ids = db.get_admin_ids()
                for aid in admin_ids:
                    try:
                        await context.bot.send_message(
                            chat_id=aid,
                            text=(
                                f"⭐ <b>Stars → Points Purchase!</b>\n\n"
                                f"👤 User: {user.first_name} (<code>{user.id}</code>)\n"
                                f"📦 Package: <b>{pkg['name']}</b>\n"
                                f"💰 Points Added: <b>${total_points:.4f}</b>\n"
                                f"💳 Paid: <b>{total_amount} XTR</b>"
                            ),
                            parse_mode="HTML"
                        )
                    except Exception:
                        pass
        else:
            # Unknown package — fallback: credit raw XTR amount as points at exchange rate
            rate = db.get_setting("stars_exchange_rate", 50) or 50
            points = round(total_amount / rate, 4)
            db.adjust_balance(user.id, points)
            await update.message.reply_text(
                f"✅ <b>Payment Successful!</b>\n💰 <b>${points:.4f} Points</b> added!",
                parse_mode="HTML"
            )
    else:
        # Generic Stars payment — credit points at exchange rate
        rate = db.get_setting("stars_exchange_rate", 50) or 50
        points = round(total_amount / rate, 4)
        db.adjust_balance(user.id, points)
        await update.message.reply_text(
            f"✅ <b>Payment Successful!</b>\n💰 <b>${points:.4f} Points</b> added!",
            parse_mode="HTML"
        )


# ─────────────────────────────────────────────
#  ERROR HANDLER
# ─────────────────────────────────────────────

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """
    Global error handler — delegates to error_tracker module
    and still notifies the primary admin on critical errors.
    """
    from handlers.error_handlers import global_error_handler
    await global_error_handler(update, context)

    error = context.error
    if error is None:
        return

    if isinstance(error, (NetworkError, TimedOut)):
        logger.warning(f"Network/Timeout: {error}")
        return

    if isinstance(error, RetryAfter):
        logger.warning(f"Rate limited — retry after {error.retry_after}s")
        await asyncio.sleep(error.retry_after)
        return

    logger.error(f"Unhandled exception: {error}", exc_info=context.error)

    try:
        admin_ids = db.get_admin_ids()
        update_str = ""
        if isinstance(update, Update):
            if update.effective_user:
                update_str = f"👤 User: <code>{update.effective_user.id}</code>"
            if update.callback_query:
                update_str += f"\n📌 CB: <code>{(update.callback_query.data or '')[:80]}</code>"
        if admin_ids:
            await context.bot.send_message(
                chat_id=admin_ids[0],
                text=(
                    f"⚠️ <b>Bot Error</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"<b>{type(error).__name__}</b>\n"
                    f"<code>{str(error)[:200]}</code>\n\n"
                    f"{update_str}\n\n"
                    f"📊 /err_dashboard for details"
                ),
                parse_mode="HTML"
            )
    except Exception:
        pass


# ─────────────────────────────────────────────
#  POST INIT
# ─────────────────────────────────────────────

async def post_init(application: Application):
    """Called after bot starts. Initialises DB, sets commands, notifies admin."""

    db.init_database()
    db._run_v31_migrations()
    # ── User Management Extension ──────────────────────
    from database_user_mgmt import init_user_mgmt_tables
    init_user_mgmt_tables()
    # ── Games Center Extension ─────────────────────────
    db.init_games_tables()
    logger.info("✅ Database v3.1 initialized")

    commands = [
        BotCommand("start", "🏠 Start the bot"),
    ]
    await application.bot.set_my_commands(commands)
    logger.info("✅ Bot commands set")

    bot_name = db.get_setting("bot_name", "Premium Shop Bot")

    # Register scheduled jobs
    await setup_jobs(application)

    try:
        await application.bot.send_message(
            chat_id=PRIMARY_ADMIN_ID,
            text=(
                f"🚀 <b>{bot_name} v{BOT_VERSION} Started!</b>\n\n"
                f"✅ Database: OK\n"
                f"✅ Handlers: Registered\n"
                f"⭐ Stars System: {'ON' if db.get_setting('stars_enabled', True) else 'OFF'}\n"
                f"📌 Force Subscribe: {'ON' if db.get_setting('force_subscribe', False) else 'OFF'}\n"
                f"🔗 Referrals: {'ON' if db.get_setting('referral_enabled', True) else 'OFF'}\n\n"
                f"🤖 Bot is now running."
            ),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.warning(f"Could not notify primary admin: {e}")

    logger.info(f"🚀 {bot_name} v{BOT_VERSION} is live")


# ─────────────────────────────────────────────
#  SCHEDULED JOBS
# ─────────────────────────────────────────────

async def setup_jobs(application):
    """Register recurring jobs."""
    from handlers.new_features_handlers import send_daily_stats, send_winback_notifications
    import datetime as dt

    jq = application.job_queue
    if jq is None:
        logger.warning("JobQueue not available — scheduled jobs disabled.")
        return

    # Daily stats: every day at 08:00 UTC
    jq.run_daily(
        send_daily_stats,
        time=dt.time(hour=8, minute=0, tzinfo=dt.timezone.utc),
        name="daily_stats"
    )

    # Win-back: every Sunday at 10:00 UTC
    jq.run_daily(
        send_winback_notifications,
        time=dt.time(hour=10, minute=0, tzinfo=dt.timezone.utc),
        days=(6,),  # Sunday
        name="win_back"
    )

    logger.info("✅ Scheduled jobs registered: daily_stats, win_back")


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

def main():
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.critical("❌ BOT_TOKEN not configured!")
        sys.exit(1)

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # /start command
    app.add_handler(CommandHandler("start", start_handler))

    # /err_dashboard command (admin only — same handler as the callback)
    async def err_dashboard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        from handlers.error_handlers import error_dashboard
        await error_dashboard(update, context)

    app.add_handler(CommandHandler("err_dashboard", err_dashboard_cmd))

    # All inline button presses
    app.add_handler(CallbackQueryHandler(callback_router))

    # Stars pre-checkout (must be before message handlers)
    app.add_handler(PreCheckoutQueryHandler(pre_checkout_handler))

    # Text input (search, wizard steps, settings editing)
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        message_handler
    ))

    # File/media input (product uploads, broadcasts)
    app.add_handler(MessageHandler(
        filters.Document.ALL
        | filters.PHOTO
        | filters.VIDEO
        | filters.AUDIO
        | filters.ANIMATION
        | filters.VOICE,
        message_handler
    ))

    # Successful Stars payments
    app.add_handler(MessageHandler(
        filters.SUCCESSFUL_PAYMENT,
        successful_payment_handler
    ))

    # Global error handler
    app.add_error_handler(error_handler)

    logger.info("📡 Starting polling...")
    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,
        poll_interval=0,
        timeout=30,
    )


if __name__ == "__main__":
    main()
