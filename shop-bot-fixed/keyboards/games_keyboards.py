"""
╔══════════════════════════════════════════════════════════╗
║         TELEGRAM SHOP BOT - GAMES KEYBOARDS             ║
╚══════════════════════════════════════════════════════════╝
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from languages.strings import _


def games_menu_keyboard(lang: str = "en", enabled: dict = None) -> InlineKeyboardMarkup:
    if enabled is None:
        enabled = {"slots": True, "wheel": True, "coinflip": True}

    def btn(label, cb, game=None):
        if game and not enabled.get(game, True):
            return InlineKeyboardButton(f"🔒 {label}", callback_data=f"game:disabled:{game}")
        return InlineKeyboardButton(label, callback_data=cb)

    return InlineKeyboardMarkup([
        [btn("🎰 Slot Machine", "game:slots", "slots"),
         btn("🎡 Lucky Wheel",  "game:wheel", "wheel")],
        [btn("🪙 Coin Flip",    "game:coinflip", "coinflip"),
         InlineKeyboardButton("🎁 Daily Reward",  callback_data="game:daily")],
        [InlineKeyboardButton("🏆 Leaderboard",   callback_data="game:lb:points"),
         InlineKeyboardButton("📜 My History",    callback_data="game:history:1")],
        [InlineKeyboardButton("🏠 Home",          callback_data="home")],
    ])


def back_to_games() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Games Menu", callback_data="game:menu")]
    ])


def play_again_keyboard(game_cb: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Play Again",   callback_data=game_cb),
         InlineKeyboardButton("◀️ Games Menu",   callback_data="game:menu")],
    ])


def coinflip_choice_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🦅 Heads", callback_data="game:cf:heads"),
         InlineKeyboardButton("🦁 Tails", callback_data="game:cf:tails")],
        [InlineKeyboardButton("◀️ Games Menu", callback_data="game:menu")],
    ])


def leaderboard_keyboard(current_mode: str = "points") -> InlineKeyboardMarkup:
    def active(mode): return f"✅ " if mode == current_mode else ""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{active('points')}💵 Points Won",   callback_data="game:lb:points"),
         InlineKeyboardButton(f"{active('games')}🎲 Games Played",  callback_data="game:lb:games")],
        [InlineKeyboardButton(f"{active('winrate')}🏆 Win Rate",    callback_data="game:lb:winrate")],
        [InlineKeyboardButton("◀️ Games Menu", callback_data="game:menu")],
    ])


def history_keyboard(page: int, total_pages: int) -> InlineKeyboardMarkup:
    rows = []
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("◀️ Prev", callback_data=f"game:history:{page-1}"))
    nav.append(InlineKeyboardButton(f"📄 {page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav.append(InlineKeyboardButton("▶️ Next", callback_data=f"game:history:{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton("◀️ Games Menu", callback_data="game:menu")])
    return InlineKeyboardMarkup(rows)


# ─────────────────────────────────────────────
#  ADMIN KEYBOARDS
# ─────────────────────────────────────────────

def games_admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Economy Dashboard", callback_data="gcfg:dashboard"),
         InlineKeyboardButton("🌐 Global RTP",        callback_data="gcfg:global_rtp")],
        [InlineKeyboardButton("🔌 Enable/Disable",    callback_data="gcfg:toggle_games"),
         InlineKeyboardButton("🤖 Auto Economy",      callback_data="gcfg:eco_engine")],
        [InlineKeyboardButton("💰 Bet Limits",        callback_data="gcfg:bets"),
         InlineKeyboardButton("⏱ Cooldowns",          callback_data="gcfg:cooldowns")],
        [InlineKeyboardButton("🎰 Slot Probs",        callback_data="gcfg:slots"),
         InlineKeyboardButton("🪙 Coin Flip Prob",    callback_data="gcfg:coinflip")],
        [InlineKeyboardButton("🎡 Wheel Segments",    callback_data="gcfg:wheel"),
         InlineKeyboardButton("🎁 Daily Reward",      callback_data="gcfg:daily")],
        [InlineKeyboardButton("📈 Game Statistics",   callback_data="gcfg:stats"),
         InlineKeyboardButton("🗑️ Reset History",    callback_data="gcfg:reset_confirm")],
        [InlineKeyboardButton("◀️ Admin Panel",       callback_data="admin")],
    ])
