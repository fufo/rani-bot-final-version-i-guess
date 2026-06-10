# Changelog

## v3.1.0 — Premium Architecture Upgrade

### 🆕 New Modules

| File | Description |
|---|---|
| `utils/cache.py` | In-memory TTL cache — settings (2 min), products (1 min), users (15 s) |
| `utils/security.py` | Anti-duplicate-purchase locks, callback validation, admin action dedup |
| `utils/formatting.py` | Premium text builder — product cards, order receipts, stock/price badges |
| `utils/error_tracker.py` | In-session error deduplication, frequency counts, timeline view |
| `handlers/rating_handlers.py` | ⭐ Post-purchase rating prompt, 1–5 star UI, optional review text |
| `handlers/delivery_handlers.py` | Smart delivery: exponential retry (×3), delivery log, admin resend panel |
| `handlers/error_handlers.py` | Admin error dashboard, recent timeline, clear action |

### 🗄️ Database — New Tables (v3.1 migration, auto-applied on start)

- `product_ratings` — per-user/product rating (1–5 stars + optional review, unique)
- `delivery_logs` — per-attempt delivery record (success/fail, error msg)
- `referral_milestones` — permanent milestone rewards (1/3/5/10/25/50/100 invites)
- `weekly_rewards` — weekly leaderboard payouts (idempotent, deduplicated)

### ⚡ Performance

- `get_setting()` — cached 2 min (busted on `set_setting`)
- `get_categories()` — cached 1 min (busted on create/update/delete)
- `get_product()` — cached 1 min (busted on update/delete)
- Cache invalidation is automatic via `utils/cache.invalidate_product()` and `invalidate_settings()`

### 🔐 Security

- **Duplicate purchase guard** — per-(user, product) lock with 5 s TTL prevents double-tap race
- **Callback validation** — `is_valid_callback()` rejects empty or malformed payloads before routing
- **Admin dedup** — repeated destructive admin actions within 3 s are no-ops

### 🎨 UI/UX

- **Product pages** — show avg ⭐ rating, review count, stock badge, buy buttons side-by-side
- **Category view** — inline product preview list with stock indicators before showing buttons
- **Profile page** — rank badge, milestone progress bar, pending-ratings shortcut, My Orders button
- **Order detail** — Restore Download + Rate Product buttons where applicable
- **Admin logs** — icon-tagged actions, admin ID + timestamp on every entry

### 🔗 Referral System

- Visual **milestone progress bar** on user referral page (7 tiers: 1→100 invites)
- **Rank badge** system (Newcomer → Legend)
- Admin **weekly leaderboard** showing all-time + this-week inviters
- **Pay Weekly** button — one-click payout to top 3 with Telegram notification to winners
- Milestone rewards auto-awarded on each purchase that pushes invite count over threshold

### 📊 Admin

- **Error Dashboard** — top errors by frequency, recent timeline, clear button; wired into admin panel
- **Failed Deliveries** panel — list of failed deliveries with one-click resend
- **Enhanced stats** — rating avg, delivery success/fail counts, referral summary, weekly top inviters
- **User detail** — shows referral count, reviews given, language
- Admin panel has 🚚 Deliveries and 🛡️ Error Logs quick-access buttons

### ✅ Compatibility

All v3.0 features, callbacks, handlers, keyboards, and settings are fully preserved.
No existing functionality was removed or broken.
