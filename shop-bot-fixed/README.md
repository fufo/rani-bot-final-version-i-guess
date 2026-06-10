# 🤖 Rani Shop Bot — Complete Documentation

> A full-featured Telegram shop bot with digital product delivery, wallet system, games center, referral program, and dynamic economy engine.

---

## 📑 Table of Contents

1. [How It Works](#how-it-works)
2. [User Panel — Every Button Explained](#user-panel)
3. [Admin Panel — Every Button Explained](#admin-panel)
4. [Games Center](#games-center)
5. [Economy Engine](#economy-engine)
6. [Glossary — Difficult Terms](#glossary)
7. [Settings Reference](#settings-reference)

---

## How It Works

Users interact with the bot entirely through **inline buttons** (tappable buttons inside the chat). No commands needed except `/start`.

**Flow for a typical purchase:**
1. User sends `/start` → sees Main Menu
2. Taps 🛒 Shop → picks a category → picks a product
3. Taps 💵 Buy with Balance → confirms → receives product instantly
4. If no balance: bot suggests buying points with ⭐ Telegram Stars

**Points (balance)** are the internal currency. Users get points by:
- Paying with Telegram Stars (⭐)
- Depositing USDT (crypto)
- Referral bonuses
- Daily rewards
- Winning games

---

## User Panel

### 🏠 Main Menu

The first screen every user sees. Contains:

| Button | What it does |
|--------|-------------|
| 🛒 **Shop** | Opens the product catalog |
| 💰 **My Balance** | Shows your wallet — balance, total spent, total orders |
| 📜 **My Orders** | History of all your purchases |
| 👤 **My Profile** | Your ID, name, join date, balance, referral count |
| 🔍 **Search** | Search for products by name |
| 🔗 **Referral** | Your referral link + earnings |
| ⚡ **Flash Sales** | Time-limited discounted products |
| 🌟 **Product of Day** | Admin-featured daily product |
| 🗂️ **My Products** | Products you've purchased |
| 🔍 **Track Order** | Enter an order ID to check its status |
| 🎮 **Games Center** | Opens the games hub |
| 💬 **Support** | Contact admin / open a ticket |
| 🌐 **Language** | Switch between English / Arabic / French |
| 📋 **Terms of Service** | Bot rules and conditions |

---

### 🛒 Shop

**Categories page** → tap a category → see products in that category.

Each **product card** shows:
- Name, description
- Price in points ($)
- Stock available
- Total sold count

**Product buttons:**
| Button | What it does |
|--------|-------------|
| 💵 **Buy with Balance** | Purchase using your points balance |
| 🎟️ **Apply Coupon** | Enter a discount coupon code before buying |
| ◀️ **Back** | Go back to the category |

**Confirm purchase screen** shows:
- Product name, original price, coupon discount, final price
- Tap ✅ Confirm to complete the purchase
- Product content is sent immediately after payment

---

### 💰 My Balance (Wallet)

Shows your current balance, total spent, and total orders.

**Wallet buttons:**
| Button | What it does |
|--------|-------------|
| 💎 **Deposit USDT** | Add funds by sending USDT (TRC20 crypto) |
| ⭐ **Buy Points** | Pay with Telegram Stars to get points — packages shown |

**USDT Deposit flow:**
1. Tap 💎 Deposit USDT
2. Copy the wallet address shown
3. Send USDT on TRC20 network
4. Tap 📤 Submit TX Hash
5. Enter the transaction hash
6. Wait for admin to confirm — balance credited automatically

**Buy Points with Stars flow:**
1. Tap ⭐ Buy Points
2. See available packages (e.g. "Pay 10⭐ → 💰$5.00 Points")
3. Tap a package → Telegram's Stars payment opens
4. Pay → points added to your balance instantly

---

### 🔗 Referral Program

Your unique referral link. Share it with friends — when they join and use the bot, you earn a bonus.

| Button | What it does |
|--------|-------------|
| 📋 **Copy Link** | Copies your referral link |
| 👥 **My Referrals** | List of people you referred |
| ◀️ **Back** | Return to main menu |

**Referral bonus** = configured by admin (default shown in the referral screen).

---

### 🎮 Games Center

See [Games Center section](#games-center) for full details.

---

### 👤 My Profile

Shows:
- Your Telegram ID (unique number)
- Display name
- Join date
- Current balance
- Total orders placed
- Total referrals made
- Current language setting

---

### 📜 My Orders

Paginated list of all your orders. Each entry shows:
- Product name
- Amount paid
- Status (pending / completed / cancelled)
- Date

---

### 💬 Support

Contact the bot admin for help. Options depend on admin configuration — usually a direct message link or ticket system.

---

## Admin Panel

Access: Only users with admin status. Tap 🔑 Admin Panel from main menu (only visible to admins).

The admin panel shows a live summary:
- Total users
- Total orders
- Total revenue
- Pending deposits

---

### 📊 Stats (🔄 Refresh)

Live dashboard showing user count, order count, revenue, and active deposits.

---

### 👥 Users

Browse all registered users. Each user entry shows ID, username, balance, join date.

**User management buttons (inside a user's profile):**
| Button | What it does |
|--------|-------------|
| 💰 **Adjust Balance** | Add or subtract points from user |
| ⭐ **Adjust Stars** | Modify user's stars balance |
| 🚫 **Ban / Unban** | Block or restore user access |
| 📝 **Add Note** | Write an admin note on the user |
| 📜 **View Orders** | See this user's order history |
| 🎫 **View Tickets** | See this user's support tickets |
| 📢 **Message User** | Send a direct message to this user |

**User filter system (🔍 Search / filter icon):**
| Button | What it does |
|--------|-------------|
| 🔍 **Search** | Search by username or ID |
| ⚡ **Quick Presets** | One-tap filters: New Users, High Spenders, Inactive, etc. |
| 🔃 **Sort** | Sort by balance, join date, orders, last seen, etc. |
| 💰 **Balance Range** | Filter users by min/max balance |
| 🛒 **Order Count** | Filter by number of orders |
| 💵 **Spent Range** | Filter by total amount spent |
| 📅 **Join Date** | Filter by when they joined |
| 🕐 **Last Active** | Filter by last activity date |
| ✅/🚫 **Ban Status** | Show only active or banned users |
| 🌍 **Language** | Filter by user's language |
| 👑 **VIP Rank** | Filter by VIP tier |
| 🧹 **Clear Filters** | Remove all active filters |

**Bulk actions (after filtering):**
| Button | What it does |
|--------|-------------|
| 📢 **Broadcast Message** | Send message to all filtered users |
| 💰 **Give Balance** | Add points to all filtered users |
| ➖ **Remove Balance** | Deduct points from all filtered users |
| 📝 **Add Note to All** | Add the same note to all filtered users |
| 👑 **Assign VIP** | Set VIP rank for all filtered users |
| 🚫/✅ **Ban All / Unban All** | Mass ban or unban |
| 📥 **Export CSV** | Download user data as a spreadsheet |

---

### 📦 Products

Browse and manage all products.

**Product list buttons:**
| Button | What it does |
|--------|-------------|
| ➕ **Add Product** | Create a new product (wizard: name → price → stock → content) |
| 📂 **Categories** | Manage product categories |
| ◀️/▶️ | Paginate through products |

**Inside a product:**
| Button | What it does |
|--------|-------------|
| ✏️ **Edit Name** | Change product name |
| ✏️ **Edit Price** | Change product price |
| ✏️ **Edit Stock** | Change available quantity |
| ✏️ **Edit Content** | Change the delivery text sent to buyer |
| ✏️ **Edit Description** | Change the product description |
| 🔄 **Toggle Active** | Enable or disable the product (hidden from shop when off) |
| 🗑️ **Delete** | Permanently remove product |

---

### 📂 Categories

| Button | What it does |
|--------|-------------|
| ➕ **Add Category** | Create a new category with name and emoji |
| ✏️ **Edit** | Rename category |
| 🗑️ **Delete** | Remove category (moves products to uncategorized) |

---

### 📜 Orders

All orders across all users, paginated.

| Button | What it does |
|--------|-------------|
| ✅ **Mark Complete** | Mark pending order as completed |
| ❌ **Cancel** | Cancel an order and refund user |
| 🔁 **Redeliver** | Resend the product content to the user |
| ⏳ **Pending Orders** | Filter to show only pending (undelivered) orders |

---

### 🎟️ Coupons

Discount codes users can apply at checkout.

| Button | What it does |
|--------|-------------|
| ➕ **Add Coupon** | Create new coupon: code → type (fixed/%) → discount → max uses |
| $ **Fixed Amount** | Coupon gives flat $X off |
| % **Percentage** | Coupon gives X% off |
| 🔄 **Toggle** | Enable or disable a coupon |
| 🗑️ **Delete** | Remove a coupon permanently |

---

### 💎 Deposits

Pending USDT deposits waiting for admin approval.

| Button | What it does |
|--------|-------------|
| ✅ **Confirm** | Verify the deposit and credit user's balance |
| ❌ **Reject** | Reject the deposit with a reason |

---

### 📢 Broadcast

Send a message to all users or a filtered group.

| Button | What it does |
|--------|-------------|
| 📢 **Broadcast** | Type a message → sends to all active users |
| 📣 **Win-Back** | Send re-engagement message to inactive users |

---

### 🔗 Referral Settings (`cfg:referral`)

| Button | What it does |
|--------|-------------|
| 💰 **Balance Bonus** | Set how many points the referrer earns per invite |
| 📊 **Purchase %** | Set % of referred user's purchases that go to referrer |
| ⭐ **Stars Bonus** | Bonus stars for referral (legacy) |
| 👥 **Min Invites** | Minimum referrals needed to unlock bonus |
| 💎 **Reward Type** | Set whether reward is balance or stars |
| 💸 **Pay Weekly** | Trigger weekly referral payout |
| 🔄 **Refresh** | Reload referral stats |

---

### 🌟 Product of Day (`pod:admin`)

Featured product shown on the main menu.

| Button | What it does |
|--------|-------------|
| ✏️ **Set Product** | Choose which product to feature today |
| 🗑️ **Remove** | Clear the featured product |

---

### ⚡ Flash Sales (`fs:panel`)

Time-limited sales with discounted prices.

| Button | What it does |
|--------|-------------|
| ➕ **New Flash Sale** | Create: pick product → discount % → duration |
| 🔄 **Toggle** | Enable/disable a flash sale |
| 🗑️ **Delete** | Remove a flash sale |

---

### 🎁 Daily Gift (`dg:panel`)

Free daily reward users can claim once per day.

| Button | What it does |
|--------|-------------|
| 💰 **Set Points** | Set how many points daily gift gives |
| ⏳ **Set Cooldown** | Set hours between claims (default 24) |

---

### 🎁 Reward Links (`rl:panel`)

Special one-time links that give users a reward when clicked.

| Button | What it does |
|--------|-------------|
| ➕ **Create Reward Link** | Create a link: set reward amount → get a share link |
| 🗑️ **Delete** | Remove a reward link |

---

### 👑 Admins (`cfg:admins`)

| Button | What it does |
|--------|-------------|
| ➕ **Add Admin** | Enter user ID to grant admin access |
| 🗑️ **Remove** | Revoke admin access from a user |

---

### ⭐ Stars System (`cfg:stars`)

Controls how Telegram Stars are used to buy points.

| Button | What it does |
|--------|-------------|
| ⭐ **Stars/$1 Rate** | How many stars = $1 of points |
| 🎁 **Bonus %** | Extra points % given on stars purchase |
| 💱 **Exchange Rate** | Stars-to-points conversion rate |
| ➕ **Add Package** | Create a new stars purchase package |

---

### 📌 Force Subscribe (`cfg:force_sub`)

Require users to join a Telegram channel before using the bot.

| Button | What it does |
|--------|-------------|
| ➕ **Add Channel** | Add a channel users must join |
| 🗑️ **Remove** | Remove a required channel |
| 🔄 **Toggle** | Enable/disable force subscribe |

---

### ⚙️ Settings (`admin_settings` / `cfg:general` etc.)

Main settings are split into sections:

| Section | What it controls |
|---------|-----------------|
| 🌐 **General** (`cfg:general`) | Bot name, currency, welcome message, join message, maintenance mode |
| 💳 **Payment** (`cfg:payment`) | USDT wallet address, min deposit, min withdrawal, payment instructions |
| 🚀 **Delivery** (`cfg:delivery`) | Max delivery retries, product link template |
| 🔔 **Notifications** (`cfg:notify`) | Order logs, deposit notifications |
| 🔗 **Referral** (`cfg:referral`) | All referral settings (see above) |
| 🛡️ **Security** (`cfg:security`) | CAPTCHA on/off, anti-spam cooldown, max requests per minute |
| 💬 **Messages** (`cfg:messages`) | Welcome message, terms message, support username |
| ⭐ **Stars System** (`cfg:stars`) | Stars packages and exchange rate |
| 📌 **Force Subscribe** (`cfg:force_sub`) | Required channel membership |

**Individual settings inside each section:**
Each setting has a button showing its current value. Tap it → type new value → saved instantly.

---

### 🗄️ Database (`admin_take_db` / `admin_upload_db`)

| Button | What it does |
|--------|-------------|
| 📥 **Take DB** | Download the current `shop.db` database file |
| 📤 **Upload DB** | Replace the database with an uploaded `.db` file |
| 💾 **Backup DB** | Create a timestamped backup of the database |

---

### 📋 Admin Logs (`admin_logs:1`)

Record of all admin actions (balance adjustments, bans, product changes, etc.) with timestamp, admin ID, and details.

---

### 🛡️ Error Dashboard (`/err_dashboard`)

| Button | What it does |
|--------|-------------|
| 🛡️ **Error Logs** | List of recent bot errors with user ID and traceback |
| 🕐 **Recent Timeline** | Timeline view of errors |
| 🗑️ **Clear All** | Delete all stored error logs |

---

### 🚚 Deliveries (`admin_failed_deliveries`)

Failed product deliveries that need manual resending.

| Button | What it does |
|--------|-------------|
| 🔁 **Redeliver** | Retry sending the product to the user |
| ❌ **Mark Failed** | Mark as permanently failed |

---

## Games Center

### 🎮 Games Menu

| Button | What it does |
|--------|-------------|
| 🎰 **Slot Machine** | 3-reel slot game — bet points, match symbols to win |
| 🎡 **Lucky Wheel** | Spin a wheel — land on multipliers or lose |
| 🪙 **Coin Flip** | Pick heads or tails — win 2× your bet |
| 🎁 **Daily Reward** | Claim free points once every 24 hours |
| 🏆 **Leaderboard** | Top 10 players by points won, games played, or win rate |
| 📜 **My History** | Your personal game history with results |
| 🏠 **Home** | Return to main menu |

Disabled games show 🔒 — tapping them shows an alert.

---

### 🎰 Slot Machine

**How to play:**
1. Type your bet amount (between min and max bet)
2. Reels spin and land on 3 symbols
3. Match 3 of a kind to win

**Payouts:**
| Combination | Multiplier |
|-------------|-----------|
| 🍒 🍒 🍒 | 1.5× bet |
| 🍉 🍉 🍉 | 2× bet |
| ⭐ ⭐ ⭐ | 5× bet |
| 💎 💎 💎 | 10× bet (JACKPOT) |
| No match | Lose bet |

Default probabilities: 78% lose, 12% small win, 6% medium, 3% big, 1% jackpot.

---

### 🎡 Lucky Wheel

**How to play:**
1. Type your bet amount
2. Wheel spins and lands on a segment
3. Win = bet × multiplier shown; Lose = lose your bet

**Default segments:**
| Segment | Multiplier | Probability |
|---------|-----------|-------------|
| 😈 Lose | 0× | ~80% |
| 1.5× | 1.5× bet | ~12% |
| 3× | 3× bet | ~5% |
| 6× | 6× bet | ~2% |
| 💎 10× | 10× bet | ~1% |

Admin can add, remove, or reweight any segment.

---

### 🪙 Coin Flip

**How to play:**
1. Tap 🦅 Heads or 🦁 Tails
2. Type your bet amount
3. Coin flips — correct pick = 2× your bet

Win probability adjusts based on bet size (bigger bet = slightly lower chance due to house edge scaling).

---

### 🎁 Daily Reward

Tap once per 24 hours to claim free points. Amount is random between admin-set min and max. Streak bonus: every 7 consecutive days gives +50% reward.

---

### 🏆 Leaderboard

Three views:
| Button | What it shows |
|--------|--------------|
| 💵 **Points Won** | Top players by total winnings |
| 🎲 **Games Played** | Top players by total games |
| 🏆 **Win Rate** | Best win percentage (min 5 games to qualify) |

---

### 📜 Game History

Paginated list of your last games. Each row shows:
- Game type icon
- Bet amount
- Result (win/loss amount)
- Date and time

---

## Admin — Games Panel (`games_admin`)

### 📊 Economy Dashboard (`gcfg:dashboard`)

Full financial overview of the games system:
- Total games played
- Total bets collected
- Total paid out to winners
- Net platform profit/loss
- Current effective RTP (player win rate)
- House edge
- Economy engine status
- Which games are enabled

---

### 🌐 Global RTP (`gcfg:global_rtp`)

**RTP** = Return To Player = % of each bet the player gets back on average.

- **Base RTP**: Default win rate for all games (default 55% — players get back 55¢ per $1)
- **Min RTP**: Minimum allowed — economy engine won't go below this
- **Max RTP**: Maximum allowed — economy engine won't go above this
- **Eco Adjustment**: Current auto-adjustment applied by the economy engine
- **Effective RTP**: Base + Eco Adjustment (what's actually running)
- **House Edge**: 100% − Effective RTP (what the house keeps)

**Bet scaling preview**: Shows how RTP decreases as bet size increases (bigger bets = lower player win chance).

| Button | What it does |
|--------|-------------|
| 🎯 **Base RTP** | Set the default player win rate |
| 📉 **Min** | Set minimum RTP floor |
| 📈 **Max** | Set maximum RTP ceiling |
| 🔄 **Reset Adj to 0** | Reset economy engine's auto-adjustment |
| 📐 **Factor** | How steeply RTP drops with bigger bets |
| 📏 **Base** | Reference bet size for scaling calculation |

---

### 🔌 Enable/Disable Games (`gcfg:toggle_games`)

Toggle each game on/off individually. Disabled games are hidden from users with a 🔒 lock. Tap any game to flip its state.

---

### 🤖 Auto Economy (`gcfg:eco_engine`)

**Economy Protection Engine** — automatically adjusts player win rates based on platform profit/loss.

| When platform is... | Engine does... |
|--------------------|---------------|
| Losing money (recent games unprofitable) | Gradually reduces player RTP (makes winning harder) |
| Breaking even | Holds current RTP |
| Profitable | Slowly recovers RTP toward base value |

**Settings:**
| Button | What it does |
|--------|-------------|
| 🟢/🔴 **Enable/Disable Engine** | Turn auto-adjustment on or off |
| 📉 **Step** | How many % to adjust per trigger (default 1%) |
| 📊 **Threshold** | Profit level that triggers adjustment (default 0 = any loss) |
| 🔄 **Reset Adjustment** | Set eco adjustment back to 0 |

---

### 💰 Bet Limits (`gcfg:bets`)

| Button | What it does |
|--------|-------------|
| **Min Bet** | Minimum allowed bet (recommended: $0.10) |
| **Max Bet** | Maximum allowed bet (recommended: $10.00) |

---

### ⏱ Cooldowns (`gcfg:cooldowns`)

Seconds users must wait between plays for each game. Prevents spam.

| Button | What it does |
|--------|-------------|
| 🪙 **Coin Flip** | Cooldown between coin flips |
| 🎰 **Slots** | Cooldown between slot spins |
| 🎡 **Wheel** | Cooldown between wheel spins |

---

### 🎰 Slot Machine Probs (`gcfg:slots`)

Configure slot machine outcome probabilities. Must sum to 100%.

| Setting | Default | Meaning |
|---------|---------|---------|
| Loss % | 78% | Probability of no match (lose bet) |
| Small Win % | 12% | 🍒 match — pays 1.5× bet |
| Medium Win % | 6% | 🍉 match — pays 2× bet |
| Big Win % | 3% | ⭐ match — pays 5× bet |
| Jackpot % | 1% | 💎 match — pays 10× bet |

Live RTP preview shown after any change.

---

### 🪙 Coin Flip Prob (`gcfg:coinflip`)

Set the base win probability for coin flip. Default 50% (fair coin). Adjust to favor house slightly if needed. Shown with live RTP calculation.

---

### 🎡 Wheel Segments (`gcfg:wheel`)

Full wheel segment manager.

| Button | What it does |
|--------|-------------|
| ✏️ **[Segment name]** | Edit that segment's label, value multiplier, or weight |
| ➕ **Add Segment** | Add a new wheel segment (label → multiplier → weight) |
| 🗑️ **Delete** (inside segment) | Remove a segment (minimum 2 required) |

**Weight** = relative probability. Higher weight = appears more often. A segment with weight 80 vs one with weight 20 appears 4× more often.

**Multiplier** = how much the bet is multiplied on win. 0 = lose turn.

---

### 🎁 Daily Reward Settings (`gcfg:daily`)

| Button | What it does |
|--------|-------------|
| **Min Reward** | Minimum points given daily (recommended: $0.10) |
| **Max Reward** | Maximum points given daily (recommended: $1.00) |
| **Cooldown** | Hours between claims (default 24) |

---

### 📈 Game Statistics (`gcfg:stats`)

Live snapshot of game economy:
- Total games played
- Win rate across all games
- Total paid out to winners
- Total collected from losers
- House edge (profit %)

---

### 🗑️ Reset History (`gcfg:reset_confirm`)

⚠️ **Dangerous** — deletes all game history and leaderboard stats permanently. Requires confirmation.

---

## Economy Engine

### How Bet Scaling Works

The bigger the bet, the lower the player's win chance. This uses a logarithmic formula:

```
RTP reduction = Factor × log2(1 + bet / scale_base)
```

**With defaults (Factor=5, Base=$1):**

| Bet | Player RTP | House Edge |
|-----|-----------|-----------|
| $0.10 | ~54% | ~46% |
| $0.50 | ~52% | ~48% |
| $1.00 | ~50% | ~50% |
| $5.00 | ~42% | ~58% |
| $10.00 | ~38% | ~62% |

This means small bets are relatively fair, but large bets strongly favor the house.

### How Auto-Economy Works

Every time a game is played:
1. Engine checks last 100 games' net profit
2. If platform is losing: reduces player RTP by `step`% (makes games harder)
3. If platform is profitable: slowly recovers RTP toward base
4. All changes are smooth and clamped within min/max limits

---

## Glossary

| Term | Meaning |
|------|---------|
| **Points / Balance** | Internal bot currency. Shown as $ amounts. Used to buy products and place game bets. |
| **Stars (XTR)** | Telegram's native currency. Used as a payment method to buy points. NOT stored in the bot. |
| **RTP** | Return To Player. The % of each bet a player gets back on average. 55% RTP = player gets 55¢ back per $1 bet. |
| **House Edge** | 100% − RTP. What the platform keeps. 45% house edge = platform keeps 45¢ per $1 bet. |
| **Multiplier** | In games, how much your bet is multiplied if you win. 2× means you get double your bet back. |
| **Eco Adjustment** | The economy engine's automatic RTP modification. Negative = harder for players, positive = easier. |
| **Weight** | In the Lucky Wheel, the relative probability of landing on a segment. Higher = more likely. |
| **TX Hash** | Transaction Hash. A unique ID for a crypto transaction. Used to verify USDT deposits. |
| **TRC20** | A blockchain network (Tron) used for USDT transfers. You must use TRC20, not ERC20. |
| **Referral** | A user who joined using your invite link. You earn a bonus when they join. |
| **VIP** | A special tier some users earn. Can have custom benefits configured by admin. |
| **Coupon** | A discount code. Can be fixed ($X off) or percentage (X% off). |
| **Force Subscribe** | A setting that requires users to join a Telegram channel before they can use the bot. |
| **CAPTCHA** | A math question shown to new users to verify they're human. |
| **Cooldown** | A waiting period enforced between actions to prevent spam. |
| **Broadcast** | Sending a message to all (or filtered) users at once. |
| **Leaderboard** | Top players ranked by various game statistics. |
| **Daily Reward** | Free points claimable once per 24 hours. |
| **Streak** | Consecutive days of claiming daily reward. Every 7 days gives a +50% bonus. |
| **Jackpot** | The highest slot machine payout (💎 💎 💎 = 10× bet). |
| **CSV Export** | Downloading user data as a spreadsheet file (comma-separated values). |
| **Admin Log** | A record of every admin action taken in the bot. |
| **Error Dashboard** | Admin view of all bot errors with details for debugging. |
| **Economy Engine** | Automated system that adjusts game difficulty based on platform profitability. |
| **Bet Scaling** | The mechanism that reduces player win chance as bet size increases. |

---

## Settings Reference

All game settings and their defaults:

| Setting Key | Default | Description |
|-------------|---------|-------------|
| `game_min_bet` | $0.10 | Minimum bet per game |
| `game_max_bet` | $10.00 | Maximum bet per game |
| `game_slots_cooldown` | 5s | Wait between slot spins |
| `game_coinflip_cooldown` | 5s | Wait between coin flips |
| `game_wheel_cooldown` | 5s | Wait between wheel spins |
| `game_slot_loss_prob` | 78% | Slot machine loss probability |
| `game_slot_small_prob` | 12% | Slot small win (1.5×) probability |
| `game_slot_med_prob` | 6% | Slot medium win (2×) probability |
| `game_slot_big_prob` | 3% | Slot big win (5×) probability |
| `game_coinflip_heads_prob` | 50% | Coin flip heads probability |
| `game_global_rtp` | 55% | Base player RTP across all games |
| `game_rtp_min` | 10% | Minimum RTP (floor) |
| `game_rtp_max` | 70% | Maximum RTP (ceiling) |
| `game_eco_enabled` | true | Economy engine on/off |
| `game_eco_step` | 1% | Engine adjustment step per trigger |
| `game_eco_threshold` | 0 | Loss threshold that triggers adjustment |
| `game_bet_rtp_factor` | 5 | Bet scaling steepness |
| `game_bet_scale_base` | $1.00 | Bet scaling reference point |
| `game_daily_min` | $0.10 | Minimum daily reward |
| `game_daily_max` | $1.00 | Maximum daily reward |
| `game_daily_cooldown_hours` | 24 | Hours between daily claims |
| `game_slots_enabled` | true | Slot machine on/off |
| `game_wheel_enabled` | true | Lucky wheel on/off |
| `game_coinflip_enabled` | true | Coin flip on/off |
