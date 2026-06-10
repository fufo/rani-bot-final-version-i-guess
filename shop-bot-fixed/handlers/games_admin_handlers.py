"""
╔══════════════════════════════════════════════════════════╗
║         TELEGRAM SHOP BOT - GAMES ADMIN HANDLERS        ║
╚══════════════════════════════════════════════════════════╝
"""

import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import database as db
from utils.helpers import (
    is_admin, safe_edit_message, safe_answer_callback,
    safe_float, safe_int, UserState
)
from handlers.games_handlers import DEFAULT_WHEEL_SEGMENTS

logger = logging.getLogger(__name__)


def _gs(key, default):
    return db.get_setting(f"game_{key}", default)

def _gsf(key, default: float) -> float:
    """Get game setting as float safely."""
    val = db.get_setting(f"game_{key}", default)
    try:
        return float(val)
    except (TypeError, ValueError):
        return float(default)

def _ss(key, value):
    return db.set_setting(f"game_{key}", value)


# ─────────────────────────────────────────────
#  MAIN GAMES ADMIN PANEL
# ─────────────────────────────────────────────

async def games_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await safe_answer_callback(update, "⛔ Access denied", show_alert=True)
        return

    min_bet  = _gs("min_bet", 0.5)
    max_bet  = _gs("max_bet", 50.0)
    cd_cf    = _gs("coinflip_cooldown", 5)
    cd_sl    = _gs("slots_cooldown", 5)
    cd_wh    = _gs("wheel_cooldown", 5)
    dr_min   = _gs("daily_min", 5.0)
    dr_max   = _gs("daily_max", 50.0)

    text = (
        "🎮 <b>Games Admin Panel</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💰 Bet Range: <b>${min_bet} – ${max_bet}</b>\n"
        f"⏱ Cooldowns: CF={cd_cf}s | Slots={cd_sl}s | Wheel={cd_wh}s\n"
        f"🎁 Daily Reward: <b>${dr_min} – ${dr_max}</b>\n\n"
        "Select a section to configure:"
    )
    from keyboards.games_keyboards import games_admin_keyboard
    await safe_edit_message(update, text, games_admin_keyboard(), "HTML")


# ─────────────────────────────────────────────
#  BET LIMITS
# ─────────────────────────────────────────────

async def games_cfg_bets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    min_bet = _gs("min_bet", 0.5)
    max_bet = _gs("max_bet", 50.0)
    text = (
        "💰 <b>Bet Limits</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Min Bet: <b>${min_bet}</b>\n"
        f"Max Bet: <b>${max_bet}</b>\n\n"
        "Tap to edit:"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Min Bet: ${min_bet}", callback_data="gcfg:set:min_bet"),
         InlineKeyboardButton(f"Max Bet: ${max_bet}", callback_data="gcfg:set:max_bet")],
        [InlineKeyboardButton("◀️ Games Admin", callback_data="games_admin")],
    ])
    await safe_edit_message(update, text, kb, "HTML")


# ─────────────────────────────────────────────
#  COOLDOWNS
# ─────────────────────────────────────────────

async def games_cfg_cooldowns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cd_cf = _gs("coinflip_cooldown", 5)
    cd_sl = _gs("slots_cooldown", 5)
    cd_wh = _gs("wheel_cooldown", 5)
    text = (
        "⏱ <b>Game Cooldowns</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🪙 Coin Flip: <b>{cd_cf}s</b>\n"
        f"🎰 Slots:     <b>{cd_sl}s</b>\n"
        f"🎡 Wheel:     <b>{cd_wh}s</b>\n\n"
        "Tap to edit:"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🪙 Coin Flip: {cd_cf}s", callback_data="gcfg:set:coinflip_cooldown"),
         InlineKeyboardButton(f"🎰 Slots: {cd_sl}s",     callback_data="gcfg:set:slots_cooldown")],
        [InlineKeyboardButton(f"🎡 Wheel: {cd_wh}s",     callback_data="gcfg:set:wheel_cooldown")],
        [InlineKeyboardButton("◀️ Games Admin", callback_data="games_admin")],
    ])
    await safe_edit_message(update, text, kb, "HTML")


# ─────────────────────────────────────────────
#  SLOT MACHINE PROBABILITIES
# ─────────────────────────────────────────────

async def games_cfg_slots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loss  = _gs("slot_loss_prob",  78)
    small = _gs("slot_small_prob", 12)
    med   = _gs("slot_med_prob",   6)
    big   = _gs("slot_big_prob",   3)
    jkpt  = max(0, 100 - loss - small - med - big)

    total = loss + small + med + big + jkpt
    warn  = "" if total == 100 else f"\n⚠️ <b>Probs sum to {total}% (must be 100%)</b>"

    # Correct RTP: small=1.5x, med=2x, big=5x, jackpot=10x
    rtp = (small*1.5 + med*2.0 + big*5.0 + jkpt*10.0) / 100
    house = 1 - rtp

    text = (
        "🎰 <b>Slot Machine Probabilities</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"❌ Loss:          <b>{loss}%</b>\n"
        f"🍒 Small (1.5×): <b>{small}%</b>\n"
        f"🍉 Medium (2×):  <b>{med}%</b>\n"
        f"⭐ Big (5×):     <b>{big}%</b>\n"
        f"💎 Jackpot (10×):<b>{jkpt}%</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"📊 Total: <b>{total}%</b>\n"
        f"🎯 Player RTP: <b>{rtp*100:.1f}%</b>  |  🏦 House Edge: <b>{house*100:.1f}%</b>"
        f"{warn}\n\n"
        "Tap to edit:"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"❌ Loss: {loss}%",        callback_data="gcfg:set:slot_loss_prob"),
         InlineKeyboardButton(f"🍒 Small: {small}%",      callback_data="gcfg:set:slot_small_prob")],
        [InlineKeyboardButton(f"🍋 Medium: {med}%",       callback_data="gcfg:set:slot_med_prob"),
         InlineKeyboardButton(f"⭐ Big: {big}%",          callback_data="gcfg:set:slot_big_prob")],
        [InlineKeyboardButton("🔄 Refresh RTP Preview",   callback_data="gcfg:slots")],
        [InlineKeyboardButton("◀️ Games Admin",           callback_data="games_admin")],
    ])
    await safe_edit_message(update, text, kb, "HTML")


# ─────────────────────────────────────────────
#  COIN FLIP PROBABILITY
# ─────────────────────────────────────────────

async def games_cfg_coinflip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    h_prob = _gs("coinflip_heads_prob", 50)  # 50% = fair coin = 100% player RTP → house makes money via losing bets not odds
    t_prob = 100 - h_prob
    text = (
        "🪙 <b>Coin Flip Probabilities</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🦅 Heads: <b>{h_prob}%</b>\n"
        f"🦁 Tails: <b>{t_prob}%</b>\n\n"
        f"Payout: <b>2× bet</b>\n"
        f"RTP: <b>{h_prob}%</b>\n\n"
        "Tap to edit heads probability (tails = 100 - heads):"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🦅 Heads: {h_prob}%", callback_data="gcfg:set:coinflip_heads_prob")],
        [InlineKeyboardButton("◀️ Games Admin", callback_data="games_admin")],
    ])
    await safe_edit_message(update, text, kb, "HTML")


# ─────────────────────────────────────────────
#  LUCKY WHEEL SEGMENTS
# ─────────────────────────────────────────────

async def games_cfg_wheel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    segments = _gs("wheel_segments", DEFAULT_WHEEL_SEGMENTS) or DEFAULT_WHEEL_SEGMENTS
    total_weight = sum(s.get("weight", 10) for s in segments)

    lines = []
    for i, s in enumerate(segments):
        w    = s.get("weight", 10)
        prob = round(w / total_weight * 100, 1)
        lines.append(f"  {i+1}. {s['label']} — weight {w} ({prob}%)")

    text = (
        "🎡 <b>Lucky Wheel Segments</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        + "\n".join(lines) +
        "\n\n"
        "Add a new segment or edit existing ones:"
    )

    rows = []
    for i, s in enumerate(segments):
        rows.append([InlineKeyboardButton(
            f"✏️ {s['label']}",
            callback_data=f"gcfg:wheel_edit:{i}"
        )])
    rows.append([InlineKeyboardButton("➕ Add Segment",    callback_data="gcfg:wheel_add")])
    rows.append([InlineKeyboardButton("◀️ Games Admin",   callback_data="games_admin")])
    await safe_edit_message(update, text, InlineKeyboardMarkup(rows), "HTML")


async def games_cfg_wheel_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["game_admin_state"] = "wheel_add_label"
    text = (
        "🎡 <b>Add Wheel Segment</b>\n\n"
        "Send the label for the new segment.\n"
        "Examples: <code>+$30</code>  <code>💀 Bankrupt</code>  <code>🎁 Bonus</code>"
    )
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Cancel", callback_data="gcfg:wheel")]])
    await safe_edit_message(update, text, kb, "HTML")


async def games_cfg_wheel_edit(update: Update, context: ContextTypes.DEFAULT_TYPE, idx: int):
    segments = _gs("wheel_segments", DEFAULT_WHEEL_SEGMENTS) or DEFAULT_WHEEL_SEGMENTS
    if idx >= len(segments):
        await safe_answer_callback(update, "Segment not found", show_alert=True)
        return
    s = segments[idx]
    text = (
        f"✏️ <b>Edit Segment: {s['label']}</b>\n\n"
        f"Value: <b>{s['value']}</b>\n"
        f"Weight: <b>{s.get('weight', 10)}</b>\n\n"
        "Choose what to edit:"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Label",  callback_data=f"gcfg:wheel_field:{idx}:label"),
         InlineKeyboardButton("💰 Value",  callback_data=f"gcfg:wheel_field:{idx}:value")],
        [InlineKeyboardButton("⚖️ Weight", callback_data=f"gcfg:wheel_field:{idx}:weight"),
         InlineKeyboardButton("🗑️ Delete", callback_data=f"gcfg:wheel_del:{idx}")],
        [InlineKeyboardButton("◀️ Wheel",  callback_data="gcfg:wheel")],
    ])
    await safe_edit_message(update, text, kb, "HTML")


async def games_cfg_wheel_del(update: Update, context: ContextTypes.DEFAULT_TYPE, idx: int):
    segments = _gs("wheel_segments", DEFAULT_WHEEL_SEGMENTS) or DEFAULT_WHEEL_SEGMENTS
    if len(segments) <= 2:
        await safe_answer_callback(update, "❌ Minimum 2 segments required", show_alert=True)
        return
    removed = segments.pop(idx)
    _ss("wheel_segments", segments)
    db.add_admin_log(update.effective_user.id, "game_wheel_del",
                     f"Removed segment: {removed['label']}")
    await safe_answer_callback(update, f"✅ Removed: {removed['label']}")
    await games_cfg_wheel(update, context)


async def games_cfg_wheel_field(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                 idx: int, field: str):
    context.user_data["game_admin_state"] = f"wheel_edit:{idx}:{field}"
    labels = {"label": "label (text)", "value": "value (number, 0 = lose)", "weight": "weight (integer)"}
    text = (
        f"✏️ <b>Edit Wheel Segment</b>\n\n"
        f"Send new <b>{labels.get(field, field)}</b>:"
    )
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Cancel", callback_data="gcfg:wheel")]])
    await safe_edit_message(update, text, kb, "HTML")


# ─────────────────────────────────────────────
#  DAILY REWARD
# ─────────────────────────────────────────────

async def games_cfg_daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dr_min = _gs("daily_min", 5.0)
    dr_max = _gs("daily_max", 50.0)
    cd     = _gs("daily_cooldown_hours", 24)
    text = (
        "🎁 <b>Daily Reward Settings</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Min Reward: <b>${dr_min}</b>\n"
        f"Max Reward: <b>${dr_max}</b>\n"
        f"Cooldown:   <b>{cd} hours</b>\n\n"
        "Tap to edit:"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Min: ${dr_min}", callback_data="gcfg:set:daily_min"),
         InlineKeyboardButton(f"Max: ${dr_max}", callback_data="gcfg:set:daily_max")],
        [InlineKeyboardButton(f"⏱ Cooldown: {cd}h", callback_data="gcfg:set:daily_cooldown_hours")],
        [InlineKeyboardButton("◀️ Games Admin", callback_data="games_admin")],
    ])
    await safe_edit_message(update, text, kb, "HTML")


# ─────────────────────────────────────────────
#  GENERIC SETTING EDIT (await text input)
# ─────────────────────────────────────────────

SETTING_LABELS = {
    "min_bet":               ("Min Bet ($)", float),
    "max_bet":               ("Max Bet ($)", float),
    "coinflip_cooldown":     ("Coin Flip Cooldown (seconds)", int),
    "slots_cooldown":        ("Slots Cooldown (seconds)", int),
    "wheel_cooldown":        ("Wheel Cooldown (seconds)", int),
    "slot_loss_prob":        ("Slots Loss % (0-100)", float),
    "slot_small_prob":       ("Slots Small Win % (0-100)", float),
    "slot_med_prob":         ("Slots Medium Win % (0-100)", float),
    "slot_big_prob":         ("Slots Big Win % (0-100)", float),
    "coinflip_heads_prob":   ("Heads Win % (0-100)", float),
    "daily_min":             ("Daily Reward Min ($)", float),
    "daily_max":             ("Daily Reward Max ($)", float),
    "daily_cooldown_hours":  ("Daily Cooldown (hours)", int),
    # Economy / RTP
    "global_rtp":            ("Global Player RTP % (e.g. 40 = 60% house)", float),
    "rtp_min":               ("Minimum allowed RTP %", float),
    "rtp_max":               ("Maximum allowed RTP %", float),
    "eco_step":              ("Economy engine step size %", float),
    "eco_threshold":         ("Economy loss threshold (0 = any loss triggers)", float),
    # Bet-size scaling
    "bet_rtp_factor":        ("Bet RTP reduction factor (% per log2 unit, default 5)", float),
    "bet_scale_base":        ("Bet scale base reference point in $ (default 1.0)", float),
}

async def games_cfg_set_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str):
    label, typ = SETTING_LABELS.get(key, (key, float))
    current = _gs(key, "not set")
    context.user_data["game_admin_state"] = f"set:{key}"
    text = (
        f"⚙️ <b>Edit: {label}</b>\n\n"
        f"Current value: <b>{current}</b>\n\n"
        f"Send new value:"
    )
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Cancel", callback_data="games_admin")]])
    await safe_edit_message(update, text, kb, "HTML")


async def games_admin_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Handle text input for game admin settings. Returns True if consumed."""
    state = context.user_data.get("game_admin_state")
    if not state or not is_admin(update.effective_user.id):
        return False

    text = (update.message.text or "").strip()

    # ── Generic setting set ──
    if state.startswith("set:"):
        key = state[4:]
        _, typ = SETTING_LABELS.get(key, (key, float))
        context.user_data.pop("game_admin_state")
        try:
            val = typ(text)
        except ValueError:
            await update.message.reply_text(f"❌ Invalid value. Expected a number.")
            return True

        # Validation for probabilities
        if key.endswith("_prob") and not (0 <= val <= 100):
            await update.message.reply_text("❌ Probability must be 0–100.")
            return True

        # Extra slot prob validation: ensure total ≤ 100
        if key in ("slot_loss_prob", "slot_small_prob", "slot_med_prob", "slot_big_prob"):
            keys = ["slot_loss_prob", "slot_small_prob", "slot_med_prob", "slot_big_prob"]
            vals = {k: _gsf(k, d) for k, d in zip(keys, [65, 20, 10, 4])}
            vals[key] = val
            if sum(vals.values()) > 100:
                await update.message.reply_text(
                    f"❌ Total slot probabilities exceed 100% "
                    f"({sum(vals.values()):.1f}%). Adjust other values first."
                )
                return True

        _ss(key, val)
        db.add_admin_log(update.effective_user.id, "game_cfg", f"{key} = {val}")
        await update.message.reply_text(f"✅ {key} set to <b>{val}</b>", parse_mode="HTML")
        return True

    # ── Wheel segment: add label ──
    if state == "wheel_add_label":
        context.user_data["wheel_new_label"] = text
        context.user_data["game_admin_state"] = "wheel_add_value"
        await update.message.reply_text(
            "💰 Now send the <b>value</b> (number of points to add, 0 = lose turn):",
            parse_mode="HTML"
        )
        return True

    if state == "wheel_add_value":
        try:
            value = float(text)
        except ValueError:
            await update.message.reply_text("❌ Invalid number.")
            return True
        context.user_data["wheel_new_value"] = value
        context.user_data["game_admin_state"] = "wheel_add_weight"
        await update.message.reply_text(
            "⚖️ Now send the <b>weight</b> (integer, higher = more likely):",
            parse_mode="HTML"
        )
        return True

    if state == "wheel_add_weight":
        try:
            weight = int(text)
        except ValueError:
            await update.message.reply_text("❌ Invalid integer.")
            return True
        label  = context.user_data.pop("wheel_new_label", "?")
        value  = context.user_data.pop("wheel_new_value", 0)
        context.user_data.pop("game_admin_state")
        segments = _gs("wheel_segments", DEFAULT_WHEEL_SEGMENTS) or DEFAULT_WHEEL_SEGMENTS
        segments.append({"label": label, "value": value, "weight": weight})
        _ss("wheel_segments", segments)
        db.add_admin_log(update.effective_user.id, "game_wheel_add", f"{label} val={value} w={weight}")
        await update.message.reply_text(f"✅ Segment <b>{label}</b> added!", parse_mode="HTML")
        return True

    # ── Wheel segment: edit field ──
    if state.startswith("wheel_edit:"):
        _, idx_s, field = state.split(":")
        idx = int(idx_s)
        context.user_data.pop("game_admin_state")
        segments = _gs("wheel_segments", DEFAULT_WHEEL_SEGMENTS) or DEFAULT_WHEEL_SEGMENTS
        if idx >= len(segments):
            await update.message.reply_text("❌ Segment not found.")
            return True
        try:
            if field == "value":
                segments[idx][field] = float(text)
            elif field == "weight":
                segments[idx][field] = int(text)
            else:
                segments[idx][field] = text
        except ValueError:
            await update.message.reply_text("❌ Invalid value.")
            return True
        _ss("wheel_segments", segments)
        db.add_admin_log(update.effective_user.id, "game_wheel_edit", f"idx={idx} {field}={text}")
        await update.message.reply_text(f"✅ Segment updated!", parse_mode="HTML")
        return True

    return False


# ─────────────────────────────────────────────
#  ECONOMY DASHBOARD
# ─────────────────────────────────────────────

async def games_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await safe_answer_callback(update, "⛔ Access denied", show_alert=True)
        return

    snap    = db.get_economy_snapshot()
    adj     = db.safe_float_setting("game_eco_adjustment", 0.0)
    base    = db.safe_float_setting("game_global_rtp", 55.0)
    eco_on  = db.get_setting("game_eco_enabled", True)
    status  = db.get_setting("game_eco_status", "neutral")

    eff_rtp = min(70.0, max(10.0, base + adj))
    house   = 100 - eff_rtp

    total_bets  = snap.get("total_bets", 0)
    paid_out    = snap.get("total_paid_out", 0)
    collected   = snap.get("total_collected", 0)
    net         = snap.get("net_profit", 0)
    games_count = snap.get("total_games", 0)

    status_icons = {"profit": "🟢 Profit", "recovery": "🔴 Recovery Mode", "neutral": "🟡 Neutral", "disabled": "⚫ Manual"}
    status_str = status_icons.get(status, "🟡 Neutral")

    enabled_games = []
    for g in ["slots", "wheel", "coinflip"]:
        on = db.get_setting(f"game_{g}_enabled", True)
        enabled_games.append(f"{'✅' if on else '❌'} {g.title()}")

    from utils.helpers import format_price
    text = (
        "📊 <b>Games Economy Dashboard</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🎮 Total Games Played: <b>{games_count:,}</b>\n"
        f"💸 Total Bets: <b>${format_price(total_bets)}</b>\n"
        f"💵 Total Paid Out: <b>${format_price(paid_out)}</b>\n"
        f"💰 Total Collected: <b>${format_price(collected)}</b>\n"
        f"📈 Net Platform Profit: <b>${format_price(net)}</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🌐 Base Player RTP: <b>{base}%</b>\n"
        f"🤖 Eco Adjustment: <b>{adj:+.1f}%</b>\n"
        f"⚡ Effective Player RTP: <b>{eff_rtp:.1f}%</b>\n"
        f"🏦 House Edge: <b>{house:.1f}%</b>\n"
        f"🔄 Economy Engine: <b>{'ON' if eco_on else 'OFF'}</b>\n"
        f"📡 Economy Status: <b>{status_str}</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎲 Games:\n" + "\n".join(f"  {g}" for g in enabled_games)
    )
    from keyboards.games_keyboards import games_admin_keyboard
    await safe_edit_message(update, text, games_admin_keyboard(), "HTML")


# ─────────────────────────────────────────────
#  GLOBAL RTP CONTROL
# ─────────────────────────────────────────────

async def games_cfg_global_rtp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    base    = _gsf("global_rtp", 55.0)
    rtp_min = _gsf("rtp_min", 10.0)
    rtp_max = _gsf("rtp_max", 70.0)
    adj     = db.safe_float_setting("game_eco_adjustment", 0.0)
    eff     = min(rtp_max, max(rtp_min, base + adj))
    text = (
        "🌐 <b>Global RTP Control</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🎯 Base Player RTP: <b>{base}%</b>\n"
        f"🤖 Eco Adjustment: <b>{adj:+.1f}%</b>\n"
        f"⚡ Effective RTP: <b>{eff:.1f}%</b>\n"
        f"🏦 House Edge: <b>{100-eff:.1f}%</b>\n\n"
        f"📊 Min RTP: <b>{rtp_min}%</b>  |  Max RTP: <b>{rtp_max}%</b>\n\n"
        "<i>Base RTP = default player win rate before eco adjustment.\n"
        "60% house profit = 40% base RTP.</i>\n\n"
        "Tap to edit:"
    )
    factor     = _gs("bet_rtp_factor", 5.0)
    scale_base = _gs("bet_scale_base", 1.0)

    import math
    examples = []
    for b in [0.10, 0.50, 1.0, 5.0, 10.0, 50.0]:
        try:
            reduction = float(factor) * math.log2(1.0 + b / max(float(scale_base), 0.01))
            eff = max(float(rtp_min), min(float(rtp_max), float(base) + float(adj) - reduction))
        except (TypeError, ValueError):
            eff = float(base)
        examples.append(f"  ${b:.2f} bet → {eff:.1f}% RTP ({100-eff:.1f}% house)")

    text += "\n\n<b>Bet scaling preview:</b>\n" + "\n".join(examples)
    text += f"\n\n⚙️ Factor: <b>{factor}</b>  |  Scale base: <b>${scale_base}</b>"

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🎯 Base RTP: {base}%",    callback_data="gcfg:set:global_rtp"),
         InlineKeyboardButton(f"📉 Min: {rtp_min}%",      callback_data="gcfg:set:rtp_min")],
        [InlineKeyboardButton(f"📈 Max: {rtp_max}%",      callback_data="gcfg:set:rtp_max"),
         InlineKeyboardButton("🔄 Reset Adj to 0",        callback_data="gcfg:rtp_reset_adj")],
        [InlineKeyboardButton(f"📐 Factor: {factor}",     callback_data="gcfg:set:bet_rtp_factor"),
         InlineKeyboardButton(f"📏 Base: ${scale_base}",  callback_data="gcfg:set:bet_scale_base")],
        [InlineKeyboardButton("◀️ Games Admin",           callback_data="games_admin")],
    ])
    await safe_edit_message(update, text, kb, "HTML")


# ─────────────────────────────────────────────
#  ENABLE / DISABLE INDIVIDUAL GAMES
# ─────────────────────────────────────────────

async def games_cfg_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    games = [("slots", "🎰 Slot Machine"), ("wheel", "🎡 Lucky Wheel"), ("coinflip", "🪙 Coin Flip")]
    rows = []
    for key, label in games:
        on = db.get_setting(f"game_{key}_enabled", True)
        icon = "✅" if on else "❌"
        rows.append([InlineKeyboardButton(
            f"{icon} {label} — {'ON' if on else 'OFF'}",
            callback_data=f"gcfg:toggle:{key}"
        )])
    rows.append([InlineKeyboardButton("◀️ Games Admin", callback_data="games_admin")])

    text = (
        "🔌 <b>Enable / Disable Games</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Disabled games are hidden from users.\n"
        "Tap a game to toggle it on/off:"
    )
    await safe_edit_message(update, text, InlineKeyboardMarkup(rows), "HTML")


async def games_toggle_game(update: Update, context: ContextTypes.DEFAULT_TYPE, game: str):
    if not is_admin(update.effective_user.id):
        return
    current = db.get_setting(f"game_{game}_enabled", True)
    new_val = not current
    db.set_setting(f"game_{game}_enabled", new_val)
    db.add_admin_log(update.effective_user.id, "game_toggle",
                     f"{game} {'enabled' if new_val else 'disabled'}")
    await safe_answer_callback(update, f"{'✅ Enabled' if new_val else '❌ Disabled'}: {game}")
    await games_cfg_toggle(update, context)


# ─────────────────────────────────────────────
#  ECONOMY ENGINE CONFIGURATION
# ─────────────────────────────────────────────

async def games_cfg_eco_engine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    eco_on    = db.get_setting("game_eco_enabled", True)
    step      = _gs("eco_step", 1.0)
    threshold = _gs("eco_threshold", 0.0)
    adj       = db.safe_float_setting("game_eco_adjustment", 0.0)

    text = (
        "🤖 <b>Economy Protection Engine</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Status: <b>{'🟢 ON' if eco_on else '🔴 OFF'}</b>\n"
        f"Current Adjustment: <b>{adj:+.1f}%</b>\n\n"
        f"⚙️ Settings:\n"
        f"  Step Size: <b>{step}%</b> per trigger\n"
        f"  Loss Threshold: <b>${threshold}</b>\n\n"
        "<i>When platform recent profit drops below threshold,\n"
        "player RTP decreases by step% automatically.\n"
        "When profitable, it recovers gradually.</i>\n\n"
        "Tap to configure:"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            f"{'🔴 Disable' if eco_on else '🟢 Enable'} Engine",
            callback_data="gcfg:eco_toggle"
        )],
        [InlineKeyboardButton(f"📉 Step: {step}%",         callback_data="gcfg:set:eco_step"),
         InlineKeyboardButton(f"📊 Threshold: ${threshold}", callback_data="gcfg:set:eco_threshold")],
        [InlineKeyboardButton("🔄 Reset Adjustment to 0",  callback_data="gcfg:rtp_reset_adj")],
        [InlineKeyboardButton("◀️ Games Admin",            callback_data="games_admin")],
    ])
    await safe_edit_message(update, text, kb, "HTML")


async def games_eco_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    current = db.get_setting("game_eco_enabled", True)
    db.set_setting("game_eco_enabled", not current)
    db.add_admin_log(update.effective_user.id, "game_eco_toggle",
                     f"Economy engine {'disabled' if current else 'enabled'}")
    await safe_answer_callback(update, f"Economy engine {'disabled' if current else 'enabled'}")
    await games_cfg_eco_engine(update, context)


async def games_rtp_reset_adj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    db.set_setting("game_eco_adjustment", 0.0)
    db.add_admin_log(update.effective_user.id, "game_rtp_reset", "Eco adjustment reset to 0")
    await safe_answer_callback(update, "✅ Adjustment reset to 0")
    await games_cfg_eco_engine(update, context)
