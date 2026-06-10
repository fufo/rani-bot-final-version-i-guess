"""
╔══════════════════════════════════════════════════════════╗
║         TELEGRAM SHOP BOT - GAMES CENTER HANDLERS       ║
╚══════════════════════════════════════════════════════════╝
"""

import logging
import random
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import database as db
from utils.helpers import (
    is_admin, safe_edit_message, safe_answer_callback,
    safe_float, safe_int, format_price, UserState
)

logger = logging.getLogger(__name__)

def _lang(ctx): return ctx.user_data.get("lang", "en")


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def _get_game_setting(key, default):
    return db.get_setting(f"game_{key}", default)

def _get_game_float(key, default: float) -> float:
    """Get game setting as float safely."""
    val = db.get_setting(f"game_{key}", default)
    try:
        return float(val)
    except (TypeError, ValueError):
        return float(default)

def _cooldown_ok(user_id: int, game: str) -> tuple[bool, int]:
    """Returns (is_ok, seconds_remaining)."""
    cd_seconds = int(_get_game_setting(f"{game}_cooldown", 5))
    last = db.get_game_last_play(user_id, game)
    if not last:
        return True, 0
    elapsed = (datetime.now() - last).total_seconds()
    remaining = cd_seconds - elapsed
    if remaining <= 0:
        return True, 0
    return False, int(remaining) + 1


# ─────────────────────────────────────────────
#  ECONOMY ENGINE HELPERS
# ─────────────────────────────────────────────

def _is_game_enabled(game: str) -> bool:
    return bool(db.get_setting(f"game_{game}_enabled", True))

def _apply_rtp_to_slot_loss(base_loss_prob: float, game_type: str = "slots",
                             bet: float = 0.0) -> float:
    """Adjust slot loss probability based on effective RTP + bet size."""
    effective_player_rtp = db.get_effective_rtp(game_type, bet)
    return max(0.0, min(99.0, 100.0 - effective_player_rtp))

def _apply_rtp_to_coinflip(game_type: str = "coinflip", bet: float = 0.0) -> float:
    """Return adjusted win probability based on effective RTP + bet size."""
    return db.get_effective_rtp(game_type, bet)

def _apply_rtp_to_wheel(segments: list, game_type: str = "wheel",
                        bet: float = 0.0) -> list:
    """Adjust wheel lose-segment weight based on effective RTP + bet size."""
    effective_player_rtp = db.get_effective_rtp(game_type, bet)
    lose_weight = max(1, int((100 - effective_player_rtp) / 5))
    adjusted = []
    for s in segments:
        if s.get("multiplier", s.get("value", 1)) == 0:
            adjusted.append({**s, "weight": lose_weight})
        else:
            adjusted.append(s)
    return adjusted


# ─────────────────────────────────────────────
#  GAMES MENU
# ─────────────────────────────────────────────

async def games_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = _lang(context)
    db_user = db.get_user(user.id)
    balance = db_user.get("balance", 0) if db_user else 0
    stats   = db.get_game_stats(user.id) or {}

    wins   = stats.get("total_wins", 0)
    losses = stats.get("total_losses", 0)
    total  = wins + losses
    rate   = f"{round(wins/total*100)}%" if total else "—"

    text = (
        "🎮 <b>Games Center</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💰 Balance: <b>${format_price(balance)}</b>\n\n"
        f"🎲 Games Played: <b>{total}</b>\n"
        f"🏆 Win Rate: <b>{rate}</b>\n"
        f"💵 Points Won: <b>${format_price(stats.get('total_points_won', 0))}</b>\n\n"
        "Choose a game:"
    )
    from keyboards.games_keyboards import games_menu_keyboard
    enabled = {
        "slots":    _is_game_enabled("slots"),
        "wheel":    _is_game_enabled("wheel"),
        "coinflip": _is_game_enabled("coinflip"),
    }
    await safe_edit_message(update, text, games_menu_keyboard(lang, enabled), "HTML")


# ─────────────────────────────────────────────
#  DAILY REWARD
# ─────────────────────────────────────────────

async def daily_reward_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = _lang(context)

    claimed, reward, next_claim = db.claim_daily_reward(user.id)
    from keyboards.games_keyboards import games_menu_keyboard, back_to_games

    if not claimed:
        hours = int((next_claim - datetime.now()).total_seconds() // 3600)
        mins  = int(((next_claim - datetime.now()).total_seconds() % 3600) // 60)
        text = (
            "⏰ <b>Daily Reward</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"You already claimed today's reward!\n\n"
            f"⏳ Next claim in: <b>{hours}h {mins}m</b>"
        )
        await safe_edit_message(update, text, back_to_games(), "HTML")
        return

    db_user = db.get_user(user.id)
    new_bal = db_user.get("balance", 0) if db_user else 0

    text = (
        "🎁 <b>Daily Reward Claimed!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✨ You received: <b>${format_price(reward)}</b> points!\n"
        f"💰 New Balance: <b>${format_price(new_bal)}</b>\n\n"
        f"Come back tomorrow for another reward!"
    )
    await safe_edit_message(update, text, back_to_games(), "HTML")


# ─────────────────────────────────────────────
#  COIN FLIP
# ─────────────────────────────────────────────

async def coinflip_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_game_enabled("coinflip"):
        await safe_answer_callback(update, "🪙 Coin Flip is currently disabled.", show_alert=True)
        return
    user = update.effective_user
    db_user = db.get_user(user.id)
    balance = db_user.get("balance", 0) if db_user else 0

    min_bet = _get_game_float("min_bet", 0.5)
    max_bet = _get_game_float("max_bet", 50.0)

    text = (
        "🪙 <b>Coin Flip</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💰 Balance: <b>${format_price(balance)}</b>\n"
        f"📊 Bet range: <b>${min_bet:.2f} – ${max_bet:.2f}</b>\n\n"
        f"Win: <b>2× your bet</b>\n\n"
        "Choose your side first, then enter your bet:"
    )
    from keyboards.games_keyboards import coinflip_choice_keyboard
    await safe_edit_message(update, text, coinflip_choice_keyboard(), "HTML")


async def coinflip_choose(update: Update, context: ContextTypes.DEFAULT_TYPE, choice: str):
    """User picked heads or tails — store choice and ask for bet."""
    context.user_data["cf_choice"] = choice
    context.user_data[UserState.GAME_AWAITING_BET] = "coinflip"
    db_user = db.get_user(update.effective_user.id)
    balance = db_user.get("balance", 0) if db_user else 0
    min_bet = _get_game_float("min_bet", 0.5)
    max_bet = _get_game_float("max_bet", 50.0)

    icon = "🦅" if choice == "heads" else "🦁"
    text = (
        f"🪙 <b>Coin Flip — {icon} {choice.title()}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💰 Balance: <b>${format_price(balance)}</b>\n"
        f"📊 Bet range: <b>${min_bet:.2f} – ${max_bet:.2f}</b>\n\n"
        "💬 <b>Type your bet amount:</b>"
    )
    from keyboards.games_keyboards import back_to_games
    await safe_edit_message(update, text, back_to_games(), "HTML")


async def coinflip_play(update: Update, context: ContextTypes.DEFAULT_TYPE, bet: float):
    """Execute the coin flip with the given bet."""
    user   = update.effective_user
    choice = context.user_data.pop("cf_choice", "heads")
    context.user_data.pop(UserState.GAME_AWAITING_BET, None)

    ok, cd = _cooldown_ok(user.id, "coinflip")
    if not ok:
        await _send_cooldown(update, context, cd)
        return

    min_bet = _get_game_float("min_bet", 0.5)
    max_bet = _get_game_float("max_bet", 50.0)

    if bet < min_bet or bet > max_bet:
        from keyboards.games_keyboards import back_to_games
        await safe_edit_message(
            update,
            f"❌ Bet must be between ${min_bet:.2f} and ${max_bet:.2f}.",
            back_to_games(), "HTML"
        )
        return

    if not db.atomic_deduct_balance(user.id, bet):
        await _send_broke(update, context, bet)
        return

    # Determine outcome using economy-adjusted probability + bet scaling
    heads_prob = _apply_rtp_to_coinflip("coinflip", bet) / 100
    result = "heads" if random.random() < heads_prob else "tails"
    won = (result == choice)

    if won:
        winnings = round(bet * 2, 4)
        new_bal_win = db.adjust_balance(user.id, winnings)
        profit = round(winnings - bet, 4)
    else:
        new_bal_win = None
        profit = -bet

    db.record_game(user.id, "coinflip", bet, profit, result=result)
    db.run_economy_engine()

    icon = "🦅" if result == "heads" else "🦁"
    your_icon = "🦅" if choice == "heads" else "🦁"
    db_user  = db.get_user(user.id)
    new_bal  = (new_bal_win if new_bal_win is not None
                else (db_user.get("balance", 0) if db_user else 0))

    if won:
        text = (
            f"🪙 <b>Coin Flip</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Your pick: {your_icon} {choice.title()}\n"
            f"Result:    {icon} {result.title()}\n\n"
            f"🎉 <b>YOU WIN!</b>\n"
            f"🎲 Bet ${format_price(bet)} → Won ${format_price(winnings)} (2×)\n"
            f"💵 Profit: <b>+${format_price(profit)}</b>\n"
            f"💰 New Balance: <b>${format_price(new_bal)}</b>"
        )
    else:
        # Check if player is now broke
        if new_bal <= 0:
            await _send_broke(update, context, 0)
            return
        text = (
            f"🪙 <b>Coin Flip</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Your pick: {your_icon} {choice.title()}\n"
            f"Result:    {icon} {result.title()}\n\n"
            f"😔 <b>Better luck next time!</b>\n"
            f"💸 Lost: <b>${format_price(bet)}</b>\n"
            f"💰 New Balance: <b>${format_price(new_bal)}</b>"
        )

    from keyboards.games_keyboards import play_again_keyboard
    await safe_edit_message(update, text, play_again_keyboard("game:coinflip"), "HTML")


# ─────────────────────────────────────────────
#  SLOT MACHINE
# ─────────────────────────────────────────────

SLOT_SYMBOLS = ["🍒", "🍋", "🍉", "⭐", "💎"]
SLOT_WEIGHTS  = [40, 30, 18, 9, 3]   # default weights (higher = more frequent)

async def slots_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_game_enabled("slots"):
        await safe_answer_callback(update, "🎰 Slot Machine is currently disabled.", show_alert=True)
        return
    user = update.effective_user
    db_user = db.get_user(user.id)
    balance = db_user.get("balance", 0) if db_user else 0
    min_bet = _get_game_float("min_bet", 0.5)
    max_bet = _get_game_float("max_bet", 50.0)

    text = (
        "🎰 <b>Slot Machine</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💰 Balance: <b>${format_price(balance)}</b>\n"
        f"📊 Bet range: <b>${min_bet:.2f} – ${max_bet:.2f}</b>\n\n"
        "🍒 🍉 ⭐ 💎\n\n"
        "<b>Payouts (3 of a kind):</b>\n"
        "  🍒 🍒 🍒 = <b>1.5×</b> bet\n"
        "  🍉 🍉 🍉 = <b>2×</b> bet\n"
        "  ⭐ ⭐ ⭐ = <b>5×</b> bet\n"
        "  💎 💎 💎 = <b>10×</b> bet 🎊\n\n"
        "💬 <b>Type your bet to spin:</b>"
    )
    context.user_data[UserState.GAME_AWAITING_BET] = "slots"
    from keyboards.games_keyboards import back_to_games
    await safe_edit_message(update, text, back_to_games(), "HTML")


async def slots_play(update: Update, context: ContextTypes.DEFAULT_TYPE, bet: float):
    user = update.effective_user
    context.user_data.pop(UserState.GAME_AWAITING_BET, None)

    ok, cd = _cooldown_ok(user.id, "slots")
    if not ok:
        await _send_cooldown(update, context, cd)
        return

    min_bet = _get_game_float("min_bet", 0.5)
    max_bet = _get_game_float("max_bet", 50.0)

    if bet < min_bet or bet > max_bet:
        from keyboards.games_keyboards import back_to_games
        await safe_edit_message(
            update,
            f"❌ Bet must be between ${min_bet:.2f} and ${max_bet:.2f}.",
            back_to_games(), "HTML"
        )
        return

    if not db.atomic_deduct_balance(user.id, bet):
        await _send_broke(update, context, bet)
        return

    # Send "spinning" animation
    from keyboards.games_keyboards import back_to_games
    await safe_edit_message(update, "🎰 Spinning...\n\n[ 🎲 | 🎲 | 🎲 ]", back_to_games(), "HTML")
    await asyncio.sleep(1)

    # Determine outcome via configurable probabilities + economy engine
    # Slot RTP: loss=78%→small(1.5x)=12%→med(2x)=6%→big(5x)=3%→jackpot(10x)=1%
    # E[return] = 1.5×12 + 2×6 + 5×3 + 10×1 = 18+12+15+10 = 55% player RTP
    base_loss    = _get_game_float("slot_loss_prob", 78)
    loss_prob    = _apply_rtp_to_slot_loss(base_loss, "slots", bet)
    small_prob   = _get_game_float("slot_small_prob", 12)
    med_prob     = _get_game_float("slot_med_prob", 6)
    big_prob     = _get_game_float("slot_big_prob", 3)
    # Scale win probs proportionally so they still sum with loss_prob to 100
    win_total_base = small_prob + med_prob + big_prob + max(0, 100 - base_loss - small_prob - med_prob - big_prob)
    win_available  = 100 - loss_prob
    if win_total_base > 0:
        scale = win_available / win_total_base
        small_prob = small_prob * scale
        med_prob   = med_prob   * scale
        big_prob   = big_prob   * scale

    roll = random.uniform(0, 100)
    if roll < loss_prob:
        outcome = "loss"
    elif roll < loss_prob + small_prob:
        outcome = "small"
    elif roll < loss_prob + small_prob + med_prob:
        outcome = "medium"
    elif roll < loss_prob + small_prob + med_prob + big_prob:
        outcome = "big"
    else:
        outcome = "jackpot"

    # Pick reels matching outcome
    if outcome == "jackpot":
        reels = ["💎", "💎", "💎"]
        multiplier = 10         # 10× bet  (1% chance)
    elif outcome == "big":
        reels = ["⭐", "⭐", "⭐"]
        multiplier = 5          # 5× bet   (3% chance)
    elif outcome == "medium":
        reels = ["🍉", "🍉", "🍉"]
        multiplier = 2          # 2× bet   (6% chance)
    elif outcome == "small":
        reels = ["🍒", "🍒", "🍒"]
        multiplier = 1.5        # 1.5× bet (12% chance)
    else:
        # Loss: ensure NOT 3 of a kind
        weights = _get_game_setting("slot_weights", SLOT_WEIGHTS) or SLOT_WEIGHTS
        while True:
            reels = random.choices(SLOT_SYMBOLS, weights=weights, k=3)
            if not (reels[0] == reels[1] == reels[2]):
                break
        multiplier = 0

    if multiplier > 0:
        winnings = round(bet * multiplier, 4)
        new_bal  = db.adjust_balance(user.id, winnings)
        profit   = round(winnings - bet, 4)
    else:
        winnings = 0
        db_user  = db.get_user(user.id)
        new_bal  = db_user.get("balance", 0) if db_user else 0
        profit   = -bet

    db.record_game(user.id, "slots", bet, profit, result="|".join(reels))
    db.run_economy_engine()

    # If player is now broke, show top-up popup
    if new_bal <= 0 and multiplier == 0:
        await _send_broke(update, context, 0)
        return

    reel_str = f"[ {reels[0]} | {reels[1]} | {reels[2]} ]"

    if outcome == "jackpot":
        header = "💎 <b>JACKPOT! 10×!</b> 🎊"
    elif outcome == "big":
        header = "⭐ <b>Big Win! 5×!</b> 🎉"
    elif multiplier > 0:
        header = "🎉 <b>You Win!</b>"
    else:
        header = "😔 <b>No Match — Try Again!</b>"

    profit_str = f"+${format_price(profit)}" if profit > 0 else f"-${format_price(abs(profit))}"
    if multiplier > 0:
        finance_line = f"🎲 Bet ${format_price(bet)} → Won ${format_price(winnings)} ({multiplier}×)\n💵 Profit: <b>{profit_str}</b>"
    else:
        finance_line = f"💸 Lost: <b>${format_price(bet)}</b>"
    text = (
        f"🎰 <b>Slot Machine</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{reel_str}\n\n"
        f"{header}\n"
        f"{finance_line}\n"
        f"💰 Balance: <b>${format_price(new_bal)}</b>"
    )

    from keyboards.games_keyboards import play_again_keyboard
    await safe_edit_message(update, text, play_again_keyboard("game:slots"), "HTML")


# ─────────────────────────────────────────────
#  LUCKY WHEEL
# ─────────────────────────────────────────────

# Wheel RTP math:
# E[return] = 1.5×12% + 3×5% + 6×2% + 10×1% + 0×80% = 0.18+0.15+0.12+0.10 = 0.55
# → Player RTP 55%  |  House edge 45%
DEFAULT_WHEEL_SEGMENTS = [
    {"label": "😈 Lose", "multiplier": 0.0,  "weight": 80},
    {"label": "1.5×",    "multiplier": 1.5,  "weight": 12},
    {"label": "3×",      "multiplier": 3.0,  "weight": 5},
    {"label": "6×",      "multiplier": 6.0,  "weight": 2},
    {"label": "💎 10×",  "multiplier": 10.0, "weight": 1},
]

async def wheel_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_game_enabled("wheel"):
        await safe_answer_callback(update, "🎡 Lucky Wheel is currently disabled.", show_alert=True)
        return
    user = update.effective_user
    db_user = db.get_user(user.id)
    balance = db_user.get("balance", 0) if db_user else 0
    min_bet = _get_game_float("min_bet", 0.5)
    max_bet = _get_game_float("max_bet", 50.0)

    segments = _get_game_setting("wheel_segments", DEFAULT_WHEEL_SEGMENTS) or DEFAULT_WHEEL_SEGMENTS
    seg_labels = "  " + "\n  ".join(s["label"] for s in segments)

    text = (
        "🎡 <b>Lucky Wheel</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💰 Balance: <b>${format_price(balance)}</b>\n"
        f"📊 Bet range: <b>${min_bet:.2f} – ${max_bet:.2f}</b>\n\n"
        "<b>Possible multipliers:</b>\n"
        f"{seg_labels}\n\n"
        "💬 <b>Type your bet amount to spin:</b>"
    )
    context.user_data[UserState.GAME_AWAITING_BET] = "wheel"
    from keyboards.games_keyboards import back_to_games
    await safe_edit_message(update, text, back_to_games(), "HTML")


async def wheel_play(update: Update, context: ContextTypes.DEFAULT_TYPE, bet: float):
    user = update.effective_user
    context.user_data.pop(UserState.GAME_AWAITING_BET, None)

    ok, cd = _cooldown_ok(user.id, "wheel")
    if not ok:
        await _send_cooldown(update, context, cd)
        return

    min_bet = _get_game_float("min_bet", 0.5)
    max_bet = _get_game_float("max_bet", 50.0)

    if bet < min_bet or bet > max_bet:
        from keyboards.games_keyboards import back_to_games
        await safe_edit_message(
            update,
            f"❌ Bet must be between ${min_bet:.2f} and ${max_bet:.2f}.",
            back_to_games(), "HTML"
        )
        return

    if not db.atomic_deduct_balance(user.id, bet):
        await _send_broke(update, context, bet)
        return

    # Animate
    from keyboards.games_keyboards import back_to_games
    frames = ["🎡 Spinning...   ◐", "🎡 Spinning...   ◓", "🎡 Spinning...   ◑", "🎡 Spinning...   ◒"]
    for frame in frames:
        await safe_edit_message(update, frame, back_to_games(), "HTML")
        await asyncio.sleep(0.4)

    raw_segs  = _get_game_setting("wheel_segments", DEFAULT_WHEEL_SEGMENTS) or DEFAULT_WHEEL_SEGMENTS
    segments  = _apply_rtp_to_wheel(raw_segs, "wheel", bet)
    weights   = [s.get("weight", 10) for s in segments]
    segment   = random.choices(segments, weights=weights, k=1)[0]

    multiplier = float(segment.get("multiplier", segment.get("value", 0)))
    is_loss    = multiplier == 0

    if not is_loss:
        # Winnings = bet × multiplier (bet already deducted, so credit full winnings)
        winnings = round(bet * multiplier, 4)
        new_bal  = db.adjust_balance(user.id, winnings)
        profit   = round(winnings - bet, 4)
    else:
        # Bet already deducted by atomic_deduct_balance — just fetch new balance
        db_user = db.get_user(user.id)
        new_bal = db_user.get("balance", 0) if db_user else 0
        profit  = -bet

    db.record_game(user.id, "wheel", bet, profit, result=segment["label"])
    db.run_economy_engine()

    if not is_loss:
        text = (
            f"🎡 <b>Lucky Wheel</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🎯 Landed on: <b>{segment['label']}</b>\n"
            f"🎲 Bet: <b>${format_price(bet)}</b>  ×  {multiplier}\n\n"
            f"🎉 <b>You Win!</b>\n"
            f"💵 Winnings: <b>${format_price(winnings)}</b>  "
            f"(+${format_price(profit)} profit)\n"
            f"💰 New Balance: <b>${format_price(new_bal)}</b>"
        )
    else:
        # Check if balance now 0 — show top-up popup
        db_user2 = db.get_user(user.id)
        cur_bal  = db_user2.get("balance", 0) if db_user2 else 0
        if cur_bal <= 0:
            await _send_broke(update, context, 0)
            return
        text = (
            f"🎡 <b>Lucky Wheel</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🎯 Landed on: <b>{segment['label']}</b>\n\n"
            f"😔 <b>Lose Turn!</b>\n"
            f"💸 Lost: <b>${format_price(bet)}</b>\n"
            f"💰 New Balance: <b>${format_price(new_bal)}</b>"
        )

    from keyboards.games_keyboards import play_again_keyboard
    await safe_edit_message(update, text, play_again_keyboard("game:wheel"), "HTML")


# ─────────────────────────────────────────────
#  LEADERBOARD
# ─────────────────────────────────────────────

async def leaderboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE,
                               mode: str = "points"):
    leaders = db.get_game_leaderboard(mode, limit=10)
    medals = ["🥇", "🥈", "🥉"] + ["🏅"] * 7

    if mode == "points":
        title = "💵 Top Points Won"
        def fmt(u): return f"${format_price(u.get('total_points_won', 0))}"
    elif mode == "games":
        title = "🎲 Most Games Played"
        def fmt(u):
            w = u.get("total_wins", 0)
            l = u.get("total_losses", 0)
            return f"{w+l} games"
    else:  # winrate
        title = "🏆 Best Win Rate"
        def fmt(u):
            w = u.get("total_wins", 0)
            l = u.get("total_losses", 0)
            t = w + l
            return f"{round(w/t*100)}%" if t >= 5 else "—"

    lines = []
    for i, u in enumerate(leaders):
        name = u.get("first_name") or f"User#{u['user_id']}"
        lines.append(f"  {medals[i]} <b>{name}</b> — {fmt(u)}")

    text = (
        f"🏆 <b>Leaderboard</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>{title}</b>\n\n"
        + ("\n".join(lines) if lines else "  No data yet") +
        "\n\n<i>Min 5 games to appear in win rate rankings</i>"
    )
    from keyboards.games_keyboards import leaderboard_keyboard
    await safe_edit_message(update, text, leaderboard_keyboard(mode), "HTML")


# ─────────────────────────────────────────────
#  GAME HISTORY
# ─────────────────────────────────────────────

async def game_history_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 1):
    user = update.effective_user
    per_page = 8
    history, total = db.get_game_history(user.id, page, per_page)
    total_pages = max(1, (total + per_page - 1) // per_page)

    if not history:
        text = (
            "📜 <b>Game History</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "No games played yet. Start playing!"
        )
    else:
        lines = []
        game_icons = {"slots": "🎰", "coinflip": "🪙", "wheel": "🎡"}
        for h in history:
            icon  = game_icons.get(h["game_type"], "🎮")
            won   = h["profit"] > 0
            sign  = "+" if won else ""
            emoji = "✅" if won else "❌"
            dt    = str(h.get("played_at", ""))[:16]
            lines.append(
                f"{emoji} {icon} <b>{h['game_type'].title()}</b> "
                f"bet ${format_price(h['bet'])} → "
                f"{sign}${format_price(abs(h['profit']))}  "
                f"<i>{dt}</i>"
            )
        text = (
            f"📜 <b>Game History</b> (Page {page}/{total_pages})\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            + "\n".join(lines)
        )

    from keyboards.games_keyboards import history_keyboard
    await safe_edit_message(update, text, history_keyboard(page, total_pages), "HTML")


# ─────────────────────────────────────────────
#  HELPERS (private)
# ─────────────────────────────────────────────

async def _send_cooldown(update, context, seconds_remaining):
    from keyboards.games_keyboards import back_to_games
    await safe_edit_message(
        update,
        f"⏳ <b>Slow down!</b>\n\nPlease wait <b>{seconds_remaining}s</b> before playing again.",
        back_to_games(), "HTML"
    )


async def _send_broke(update, context, bet):
    db_user = db.get_user(update.effective_user.id)
    balance = db_user.get("balance", 0) if db_user else 0
    packages = db.get_stars_packages(active_only=True)
    short = sorted(packages, key=lambda p: p["price_usd"])[:3] if packages else []

    rows = []
    for pkg in short:
        rows.append([InlineKeyboardButton(
            f"Pay {pkg['stars']}⭐ → 💰${pkg['price_usd']:.2f} Points",
            callback_data=f"buy_stars_pkg:{pkg['id']}"
        )])
    rows.append([InlineKeyboardButton("◀️ Back to Games", callback_data="game:menu")])

    text = (
        f"❌ <b>Insufficient Balance</b>\n\n"
        f"💰 You have: <b>${format_price(balance)}</b>\n"
        f"💸 You need: <b>${format_price(bet)}</b>\n\n"
        f"⭐ Top up with Telegram Stars:"
    )
    await safe_edit_message(update, text, InlineKeyboardMarkup(rows), "HTML")
