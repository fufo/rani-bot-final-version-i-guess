"""
╔══════════════════════════════════════════════════════════╗
║           TELEGRAM SHOP BOT - KEYBOARD BUILDERS          ║
╚══════════════════════════════════════════════════════════╝
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Dict, Optional

from languages.strings import _
from config import Emoji, PRODUCTS_PER_PAGE, CATEGORIES_PER_PAGE


def _nav_row(current_page: int, total_pages: int,
             base_cb: str, lang: str = "en") -> List[InlineKeyboardButton]:
    buttons = []
    if current_page > 1:
        buttons.append(InlineKeyboardButton(
            _("btn_prev", lang), callback_data=f"{base_cb}:{current_page - 1}"
        ))
    buttons.append(InlineKeyboardButton(
        f"📄 {current_page}/{total_pages}", callback_data="noop"
    ))
    if current_page < total_pages:
        buttons.append(InlineKeyboardButton(
            _("btn_next", lang), callback_data=f"{base_cb}:{current_page + 1}"
        ))
    return buttons


# ─────────────────────────────────────────────
#  MAIN MENU
# ─────────────────────────────────────────────

def main_menu_keyboard(lang: str = "en", is_admin: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(_("btn_shop", lang),       callback_data="shop"),
         InlineKeyboardButton(_("btn_my_balance", lang), callback_data="balance")],
        [InlineKeyboardButton(_("btn_my_orders", lang),  callback_data="orders:1"),
         InlineKeyboardButton(_("btn_my_profile", lang), callback_data="profile")],
        [InlineKeyboardButton(_("btn_search", lang),     callback_data="search"),
         InlineKeyboardButton(_("btn_referral", lang),   callback_data="referral")],
        [InlineKeyboardButton("⚡ Flash Sales",           callback_data="flash_sales"),
         InlineKeyboardButton("🌟 Product of the Day",   callback_data="pod:view")],
        [InlineKeyboardButton("🗂️ My Products",          callback_data="my_products"),
         InlineKeyboardButton("🔍 Track Order",          callback_data="track_order")],
        [InlineKeyboardButton("🎮 Games Center",          callback_data="game:menu"),
         InlineKeyboardButton(_("btn_support", lang),    callback_data="support")],
        [InlineKeyboardButton(_("btn_language", lang),   callback_data="language"),
         InlineKeyboardButton("📋 Terms of Service",          callback_data="tos")],
    ]
    if is_admin:
        rows.append([InlineKeyboardButton(f"{Emoji.ADMIN} Admin Panel", callback_data="admin")])
    return InlineKeyboardMarkup(rows)


# ─────────────────────────────────────────────
#  SHOP / CATEGORIES
# ─────────────────────────────────────────────

def categories_keyboard(categories: List[Dict], page: int, total_pages: int,
                         lang: str = "en") -> InlineKeyboardMarkup:
    rows = []
    for i in range(0, len(categories), 2):
        row = []
        for cat in categories[i:i+2]:
            emoji = cat.get("emoji", "📦")
            name = cat.get(f"name_{lang}") or cat.get("name", "Category")
            row.append(InlineKeyboardButton(
                f"{emoji} {name}", callback_data=f"cat:{cat['id']}:1"
            ))
        rows.append(row)
    if total_pages > 1:
        rows.append(_nav_row(page, total_pages, "cats_page", lang))
    rows.append([InlineKeyboardButton(_("btn_home", lang), callback_data="home")])
    return InlineKeyboardMarkup(rows)


def products_keyboard(products: List[Dict], category_id: int,
                      page: int, total_pages: int,
                      lang: str = "en") -> InlineKeyboardMarkup:
    rows = []
    for product in products:
        stock = product.get("stock", -1)
        status = "" if stock != 0 else " ❌"
        name = product.get(f"name_{lang}") or product.get("name", "Product")
        price = product.get("price", 0)
        rows.append([InlineKeyboardButton(
            f"📦 {name} — ${price:.2f}{status}",
            callback_data=f"product:{product['id']}"
        )])
    if total_pages > 1:
        rows.append(_nav_row(page, total_pages, f"cat:{category_id}", lang))
    rows.extend([
        [InlineKeyboardButton(f"{Emoji.BACK} Categories", callback_data="shop")],
        [InlineKeyboardButton(_("btn_home", lang), callback_data="home")],
    ])
    return InlineKeyboardMarkup(rows)


def product_detail_keyboard(product_id: int, stock: int, price: float,
                              price_stars: int, lang: str = "en",
                              category_id: int = None,
                              can_rate: bool = False) -> InlineKeyboardMarkup:
    rows = []
    if stock != 0:
        buy_row = [InlineKeyboardButton(
            f"💵 Buy ${price:.2f}", callback_data=f"buy:balance:{product_id}"
        )]
        # Stars are a payment method only for buying points, not products directly
        rows.append(buy_row)
    else:
        rows.append([InlineKeyboardButton("❌ Out of Stock", callback_data="noop")])

    if can_rate:
        rows.append([InlineKeyboardButton(
            "⭐ Rate this product", callback_data="my_ratings"
        )])

    back_cb = f"cat:{category_id}:1" if category_id else "shop"
    rows.extend([
        [InlineKeyboardButton(f"{Emoji.BACK} Back", callback_data=back_cb),
         InlineKeyboardButton(f"{Emoji.HOME} Home", callback_data="home")],
    ])
    return InlineKeyboardMarkup(rows)


# ─────────────────────────────────────────────
#  PURCHASE CONFIRMATION
# ─────────────────────────────────────────────

def purchase_confirm_keyboard(product_id: int, payment_method: str,
                               lang: str = "en",
                               coupon_applied: bool = False) -> InlineKeyboardMarkup:
    rows = []
    if not coupon_applied:
        rows.append([InlineKeyboardButton(
            _("btn_apply_coupon", lang),
            callback_data=f"coupon:{product_id}:{payment_method}"
        )])
    rows.extend([
        [InlineKeyboardButton(_("btn_confirm", lang),
                              callback_data=f"confirm_buy:{payment_method}:{product_id}"),
         InlineKeyboardButton(_("btn_cancel", lang),
                              callback_data=f"product:{product_id}")],
        [InlineKeyboardButton(_("btn_home", lang), callback_data="home")],
    ])
    return InlineKeyboardMarkup(rows)


# ─────────────────────────────────────────────
#  BALANCE / WALLET
# ─────────────────────────────────────────────

def balance_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(_("btn_deposit_usdt", lang),  callback_data="deposit:usdt"),
         InlineKeyboardButton(_("btn_deposit_stars", lang), callback_data="deposit:stars_menu")],
        [InlineKeyboardButton(_("btn_home", lang), callback_data="home")],
    ])


def deposit_usdt_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(_("btn_submit_tx", lang), callback_data="submit_tx")],
        [InlineKeyboardButton(_("btn_back", lang),      callback_data="balance")],
    ])


def stars_packages_keyboard(packages: List[Dict], lang: str = "en") -> InlineKeyboardMarkup:
    rows = []
    for pkg in packages:
        bonus = f" +{round(pkg.get('bonus_stars',0)/max(pkg['stars'],1)*pkg['price_usd'],4):.4f} bonus" if pkg.get("bonus_stars") else ""
        rows.append([InlineKeyboardButton(
            f"Pay {pkg['stars']}⭐ → 💰${pkg['price_usd']:.2f} Points{bonus}",
            callback_data=f"buy_stars_pkg:{pkg['id']}"
        )])
    rows.append([InlineKeyboardButton(_("btn_back", lang), callback_data="balance")])
    return InlineKeyboardMarkup(rows)


# ─────────────────────────────────────────────
#  ORDERS
# ─────────────────────────────────────────────

def orders_keyboard(orders: List[Dict], page: int, total_pages: int,
                    lang: str = "en") -> InlineKeyboardMarkup:
    rows = []
    for order in orders:
        status_e = {"completed": "✅", "pending": "⏳", "cancelled": "❌"}.get(
            order.get("status", ""), "❓"
        )
        rows.append([InlineKeyboardButton(
            f"{status_e} {order.get('product_name', 'Product')} — ${order.get('amount', 0):.2f}",
            callback_data=f"order_detail:{order['order_id']}"
        )])
    if total_pages > 1:
        rows.append(_nav_row(page, total_pages, "orders", lang))
    rows.append([InlineKeyboardButton(_("btn_home", lang), callback_data="home")])
    return InlineKeyboardMarkup(rows)


# ─────────────────────────────────────────────
#  LANGUAGE
# ─────────────────────────────────────────────

def language_keyboard(current_lang: str = "en") -> InlineKeyboardMarkup:
    flags = {"en": "🇬🇧 English", "ar": "🇸🇦 العربية", "fr": "🇫🇷 Français"}
    rows = []
    for code, label in flags.items():
        check = " ✓" if code == current_lang else ""
        rows.append([InlineKeyboardButton(
            f"{label}{check}", callback_data=f"setlang:{code}"
        )])
    rows.append([InlineKeyboardButton("◀️ Back", callback_data="home")])
    return InlineKeyboardMarkup(rows)


# ─────────────────────────────────────────────
#  FORCE SUBSCRIBE
# ─────────────────────────────────────────────

def subscribe_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """Build subscribe keyboard from DB channels."""
    import database as db
    channels = db.get_force_channels(active_only=True)
    rows = []
    for ch in channels:
        link = ch.get("link") or f"https://t.me/{ch['username']}"
        rows.append([InlineKeyboardButton(
            f"📢 Join @{ch['username']}", url=link
        )])
    join_msg = db.get_setting("join_message", "")
    rows.append([InlineKeyboardButton(
        _("btn_check_again", lang), callback_data="check_subscribe"
    )])
    return InlineKeyboardMarkup(rows)


# ─────────────────────────────────────────────
#  CAPTCHA
# ─────────────────────────────────────────────

def captcha_keyboard(answer: int) -> InlineKeyboardMarkup:
    import random
    options = {answer}
    while len(options) < 4:
        options.add(random.randint(max(1, answer - 10), answer + 10))
    options = list(options)
    random.shuffle(options)
    rows = []
    for i in range(0, 4, 2):
        row = [InlineKeyboardButton(str(options[i]), callback_data=f"captcha:{options[i]}")]
        if i + 1 < len(options):
            row.append(InlineKeyboardButton(str(options[i+1]), callback_data=f"captcha:{options[i+1]}"))
        rows.append(row)
    return InlineKeyboardMarkup(rows)


# ─────────────────────────────────────────────
#  REFERRAL
# ─────────────────────────────────────────────

def referral_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 My Referrals",  callback_data="referral_list")],
        [InlineKeyboardButton(_("btn_home", lang), callback_data="home")],
    ])


# ─────────────────────────────────────────────
#  SUPPORT
# ─────────────────────────────────────────────

def support_keyboard(support_username: str, lang: str = "en") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Contact Support",
                              url=f"https://t.me/{support_username.lstrip('@')}")],
        [InlineKeyboardButton(_("btn_home", lang), callback_data="home")],
    ])


# ─────────────────────────────────────────────
#  UTILITY
# ─────────────────────────────────────────────

def cancel_keyboard(back_cb: str, lang: str = "en") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(_("btn_cancel", lang), callback_data=back_cb)
    ]])


def back_to_admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("◀️ Admin Panel", callback_data="admin")
    ]])


def confirm_delete_keyboard(item_type: str, item_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Yes, Delete",
                              callback_data=f"confirm_delete:{item_type}:{item_id}"),
         InlineKeyboardButton("✖️ Cancel",
                              callback_data=f"admin_{item_type}s:1")],
    ])


# ─────────────────────────────────────────────
#  ADMIN PANEL KEYBOARDS
# ─────────────────────────────────────────────

def admin_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Statistics",    callback_data="admin_stats"),
         InlineKeyboardButton("👥 Users",         callback_data="admin_users:1")],
        [InlineKeyboardButton("📦 Products",      callback_data="admin_products:1"),
         InlineKeyboardButton("📂 Categories",    callback_data="admin_categories")],
        [InlineKeyboardButton("💰 Deposits",      callback_data="admin_deposits"),
         InlineKeyboardButton("📜 Orders",        callback_data="admin_orders:1")],
        [InlineKeyboardButton("🎟️ Coupons",      callback_data="admin_coupons"),
         InlineKeyboardButton("📢 Broadcast",     callback_data="admin_broadcast")],
        [InlineKeyboardButton("🎁 Reward Links",  callback_data="rl:panel"),
         InlineKeyboardButton("🎀 Daily Gift",    callback_data="dg:panel")],
        [InlineKeyboardButton("🚚 Deliveries",    callback_data="admin_failed_deliveries"),
         InlineKeyboardButton("🛡️ Error Logs",   callback_data="err:dashboard")],
        [InlineKeyboardButton("⚙️ Settings",      callback_data="admin_settings"),
         InlineKeyboardButton("📋 Admin Logs",    callback_data="admin_logs:1")],
        [InlineKeyboardButton("⚡ Flash Sales",    callback_data="fs:panel"),
         InlineKeyboardButton("🌟 Product of Day", callback_data="pod:admin")],
        [InlineKeyboardButton("⏳ Pending Orders",  callback_data="po:list:1"),
         InlineKeyboardButton("📣 Win-Back",        callback_data="admin_winback")],
        [InlineKeyboardButton("💾 Backup DB",       callback_data="admin_backup"),
         InlineKeyboardButton("📤 Export Users",    callback_data="admin_export")],
        [InlineKeyboardButton("📥 Take DB",         callback_data="admin_take_db"),
         InlineKeyboardButton("📤 Upload DB",       callback_data="admin_upload_db")],
        [InlineKeyboardButton("🎮 Games Center",    callback_data="games_admin")],
        [InlineKeyboardButton("📝 Edit File",         callback_data="admin_upload_file")],
        [InlineKeyboardButton("🏠 Home",          callback_data="home")],
    ])


def admin_stats_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Refresh",      callback_data="admin_stats")],
        [InlineKeyboardButton("◀️ Admin Panel",  callback_data="admin")],
    ])


def admin_products_keyboard(products: List[Dict], page: int,
                             total_pages: int) -> InlineKeyboardMarkup:
    rows = []
    for p in products:
        active = "✅" if p.get("is_active") else "❌"
        rows.append([InlineKeyboardButton(
            f"{active} {p['name']} — ${p.get('price', 0):.2f}",
            callback_data=f"admin_product:{p['id']}"
        )])
    rows.append([InlineKeyboardButton("➕ Add Product", callback_data="admin_add_product")])
    if total_pages > 1:
        nav = []
        if page > 1:
            nav.append(InlineKeyboardButton("◀️ Prev", callback_data=f"admin_products:{page-1}"))
        nav.append(InlineKeyboardButton(f"📄 {page}/{total_pages}", callback_data="noop"))
        if page < total_pages:
            nav.append(InlineKeyboardButton("▶️ Next", callback_data=f"admin_products:{page+1}"))
        rows.append(nav)
    rows.append([InlineKeyboardButton("◀️ Admin Panel", callback_data="admin")])
    return InlineKeyboardMarkup(rows)


def admin_product_detail_keyboard(product_id: int, is_active: bool) -> InlineKeyboardMarkup:
    toggle_label = "🔴 Deactivate" if is_active else "🟢 Activate"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Edit Name",    callback_data=f"admin_edit_product:name:{product_id}"),
         InlineKeyboardButton("💰 Edit Price",   callback_data=f"admin_edit_product:price:{product_id}")],
        [InlineKeyboardButton("📝 Edit Desc",    callback_data=f"admin_edit_product:desc:{product_id}"),
         InlineKeyboardButton("📦 Edit Stock",   callback_data=f"admin_edit_product:stock:{product_id}")],
        [InlineKeyboardButton("📁 Replace File", callback_data=f"admin_edit_product:file:{product_id}"),
         InlineKeyboardButton(toggle_label,      callback_data=f"admin_toggle_product:{product_id}")],
        [InlineKeyboardButton("🔗 Share Link",   callback_data=f"admin_product_share:{product_id}")],
        [InlineKeyboardButton("🗑️ Delete",       callback_data=f"admin_delete_product:{product_id}")],
        [InlineKeyboardButton("◀️ Products",     callback_data="admin_products:1")],
    ])


def admin_categories_keyboard(categories: List[Dict]) -> InlineKeyboardMarkup:
    rows = []
    for cat in categories:
        active = "✅" if cat.get("is_active") else "❌"
        rows.append([InlineKeyboardButton(
            f"{active} {cat.get('emoji','📦')} {cat['name']}",
            callback_data=f"admin_cat:{cat['id']}"
        )])
    rows.extend([
        [InlineKeyboardButton("➕ Add Category", callback_data="admin_add_category")],
        [InlineKeyboardButton("◀️ Admin Panel",  callback_data="admin")],
    ])
    return InlineKeyboardMarkup(rows)


def admin_users_keyboard(users: List[Dict], page: int,
                          total_pages: int) -> InlineKeyboardMarkup:
    rows = []
    for u in users:
        ban_icon = "🚫" if u.get("is_banned") else "✅"
        name = u.get("first_name") or f"User#{u['user_id']}"
        rows.append([InlineKeyboardButton(
            f"{ban_icon} {name} — ${u.get('balance', 0):.2f}",
            callback_data=f"admin_user:{u['user_id']}"
        )])
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("◀️ Prev", callback_data=f"admin_users:{page-1}"))
    nav.append(InlineKeyboardButton(f"📄 {page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav.append(InlineKeyboardButton("▶️ Next", callback_data=f"admin_users:{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton("🔍 Search by ID", callback_data="admin_user_search")])
    rows.append([InlineKeyboardButton("◀️ Admin Panel", callback_data="admin")])
    return InlineKeyboardMarkup(rows)


def admin_user_detail_keyboard(user_id: int, is_banned: bool) -> InlineKeyboardMarkup:
    ban_label = "✅ Unban" if is_banned else "🚫 Ban"
    ban_cb = f"admin_unban:{user_id}" if is_banned else f"admin_ban:{user_id}"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(ban_label,            callback_data=ban_cb),
         InlineKeyboardButton("💰 Adjust Balance",  callback_data=f"admin_adjust:{user_id}")],
        [InlineKeyboardButton("⭐ Adjust Stars",    callback_data=f"admin_adjust_stars:{user_id}"),
         InlineKeyboardButton("📜 View Orders",     callback_data=f"admin_user_orders:{user_id}")],
        [InlineKeyboardButton("◀️ Users",           callback_data="admin_users:1")],
    ])


def admin_settings_keyboard() -> InlineKeyboardMarkup:
    """Settings is now categorized — redirect to main settings panel."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 General",         callback_data="cfg:general"),
         InlineKeyboardButton("📌 Force Subscribe",  callback_data="cfg:force_sub")],
        [InlineKeyboardButton("💳 Payment",          callback_data="cfg:payment"),
         InlineKeyboardButton("⭐ Stars System",     callback_data="cfg:stars")],
        [InlineKeyboardButton("🔗 Referral",         callback_data="cfg:referral"),
         InlineKeyboardButton("🛡️ Security",        callback_data="cfg:security")],
        [InlineKeyboardButton("🔔 Notifications",    callback_data="cfg:notify"),
         InlineKeyboardButton("💬 Messages",         callback_data="cfg:messages")],
        [InlineKeyboardButton("🚀 Delivery",         callback_data="cfg:delivery"),
         InlineKeyboardButton("👑 Admins",           callback_data="cfg:admins")],
        [InlineKeyboardButton("◀️ Admin Panel",      callback_data="admin")],
    ])


def admin_deposits_keyboard(deposits: List[Dict]) -> InlineKeyboardMarkup:
    rows = []
    for dep in deposits:
        name = dep.get("first_name") or f"User#{dep['user_id']}"
        rows.append([InlineKeyboardButton(
            f"💎 {name} — ${dep['amount']:.2f} ({dep['method']})",
            callback_data=f"admin_dep:{dep['deposit_id']}"
        )])
    rows.append([InlineKeyboardButton("◀️ Admin Panel", callback_data="admin")])
    return InlineKeyboardMarkup(rows)


def admin_deposit_action_keyboard(deposit_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm",    callback_data=f"admin_dep_confirm:{deposit_id}"),
         InlineKeyboardButton("❌ Reject",     callback_data=f"admin_dep_reject:{deposit_id}")],
        [InlineKeyboardButton("◀️ Deposits",  callback_data="admin_deposits")],
    ])


def admin_coupons_keyboard(coupons: List[Dict]) -> InlineKeyboardMarkup:
    rows = []
    for c in coupons:
        active = "✅" if c.get("is_active") else "❌"
        rows.append([InlineKeyboardButton(
            f"{active} {c['code']} — {c['discount_value']}{'%' if c['discount_type']=='percentage' else '$'}",
            callback_data=f"admin_coupon:{c['id']}"
        )])
    rows.extend([
        [InlineKeyboardButton("➕ Add Coupon",  callback_data="admin_add_coupon")],
        [InlineKeyboardButton("◀️ Admin Panel", callback_data="admin")],
    ])
    return InlineKeyboardMarkup(rows)


def admin_logs_keyboard(page: int, total_pages: int) -> InlineKeyboardMarkup:
    rows = []
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("◀️ Prev", callback_data=f"admin_logs:{page-1}"))
    nav.append(InlineKeyboardButton(f"📄 {page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav.append(InlineKeyboardButton("▶️ Next", callback_data=f"admin_logs:{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton("◀️ Admin Panel", callback_data="admin")])
    return InlineKeyboardMarkup(rows)
