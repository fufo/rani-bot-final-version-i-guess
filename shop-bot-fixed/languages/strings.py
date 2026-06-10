"""
╔══════════════════════════════════════════════════════════╗
║         TELEGRAM SHOP BOT - LANGUAGE SYSTEM             ║
║        Arabic / English / French Support                 ║
╚══════════════════════════════════════════════════════════╝
"""

from typing import Dict, Any

STRINGS: Dict[str, Dict[str, str]] = {

    # ── GENERAL ──────────────────────────────────────────────────
    "btn_back":         {"en": "◀️ Back",          "ar": "◀️ رجوع",           "fr": "◀️ Retour"},
    "btn_home":         {"en": "🏠 Home",           "ar": "🏠 الرئيسية",       "fr": "🏠 Accueil"},
    "btn_cancel":       {"en": "✖️ Cancel",         "ar": "✖️ إلغاء",          "fr": "✖️ Annuler"},
    "btn_confirm":      {"en": "✅ Confirm",        "ar": "✅ تأكيد",           "fr": "✅ Confirmer"},
    "btn_refresh":      {"en": "🔄 Refresh",        "ar": "🔄 تحديث",          "fr": "🔄 Actualiser"},
    "btn_next":         {"en": "▶️ Next",           "ar": "▶️ التالي",         "fr": "▶️ Suivant"},
    "btn_prev":         {"en": "◀️ Prev",           "ar": "◀️ السابق",         "fr": "◀️ Précédent"},
    "btn_close":        {"en": "❌ Close",          "ar": "❌ إغلاق",           "fr": "❌ Fermer"},
    "btn_save":         {"en": "💾 Save",           "ar": "💾 حفظ",            "fr": "💾 Enregistrer"},
    "btn_delete":       {"en": "🗑️ Delete",        "ar": "🗑️ حذف",           "fr": "🗑️ Supprimer"},
    "btn_edit":         {"en": "✏️ Edit",           "ar": "✏️ تعديل",          "fr": "✏️ Modifier"},
    "btn_yes":          {"en": "✅ Yes",            "ar": "✅ نعم",             "fr": "✅ Oui"},
    "btn_no":           {"en": "❌ No",             "ar": "❌ لا",              "fr": "❌ Non"},

    # ── MAIN MENU ────────────────────────────────────────────────
    "main_menu_title":  {
        "en": "🏠 <b>Main Menu</b>",
        "ar": "🏠 <b>القائمة الرئيسية</b>",
        "fr": "🏠 <b>Menu Principal</b>"
    },
    "btn_shop":         {"en": "🛒 Shop",           "ar": "🛒 المتجر",          "fr": "🛒 Boutique"},
    "btn_my_balance":   {"en": "💰 My Balance",     "ar": "💰 رصيدي",           "fr": "💰 Mon Solde"},
    "btn_my_orders":    {"en": "📜 My Orders",      "ar": "📜 طلباتي",          "fr": "📜 Mes Commandes"},
    "btn_my_profile":   {"en": "👤 My Profile",     "ar": "👤 ملفي",            "fr": "👤 Mon Profil"},
    "btn_search":       {"en": "🔍 Search",         "ar": "🔍 بحث",             "fr": "🔍 Recherche"},
    "btn_referral":     {"en": "🔗 Referral",       "ar": "🔗 الإحالة",         "fr": "🔗 Parrainage"},
    "btn_support":      {"en": "💬 Support",        "ar": "💬 الدعم",           "fr": "💬 Support"},
    "btn_language":     {"en": "🌐 Language",       "ar": "🌐 اللغة",           "fr": "🌐 Langue"},
    "btn_games":        {"en": "🎮 Games Center",   "ar": "🎮 مركز الألعاب",    "fr": "🎮 Centre de Jeux"},
    "btn_tos":          {"en": "📋 Terms of Service","ar": "📋 شروط الخدمة",    "fr": "📋 Conditions d'utilisation"},
    "btn_flash_sales":  {"en": "⚡ Flash Sales",    "ar": "⚡ تخفيضات سريعة",   "fr": "⚡ Ventes Flash"},
    "btn_pod":          {"en": "🌟 Product of Day", "ar": "🌟 منتج اليوم",      "fr": "🌟 Produit du Jour"},
    "btn_track_order":  {"en": "🔍 Track Order",    "ar": "🔍 تتبع الطلب",      "fr": "🔍 Suivre Commande"},
    "btn_my_products":  {"en": "🗂️ My Products",   "ar": "🗂️ منتجاتي",        "fr": "🗂️ Mes Produits"},

    # ── SHOP / PRODUCTS ──────────────────────────────────────────
    "shop_title":       {
        "en": "🛒 <b>Shop</b>\nBrowse our premium digital products",
        "ar": "🛒 <b>المتجر</b>\nتصفح منتجاتنا الرقمية المميزة",
        "fr": "🛒 <b>Boutique</b>\nParcourez nos produits numériques premium"
    },
    "select_category":  {
        "en": "📂 <b>Select a category</b> to browse products:",
        "ar": "📂 <b>اختر فئة</b> لتصفح المنتجات:",
        "fr": "📂 <b>Sélectionnez une catégorie</b> pour parcourir les produits:"
    },
    "no_categories":    {
        "en": "📭 No categories available yet.",
        "ar": "📭 لا توجد فئات متاحة حتى الآن.",
        "fr": "📭 Aucune catégorie disponible pour l'instant."
    },
    "no_products":      {
        "en": "📭 No products in this category yet.",
        "ar": "📭 لا توجد منتجات في هذه الفئة حتى الآن.",
        "fr": "📭 Aucun produit dans cette catégorie pour l'instant."
    },
    "product_detail":   {
        "en": (
            "📦 <b>{name}</b>\n\n"
            "{description}\n\n"
            "💰 Price: <b>${price}</b>\n"
            "📦 Stock: <b>{stock}</b>\n"
            "🔥 Sold: <b>{total_sold}</b>"
        ),
        "ar": (
            "📦 <b>{name}</b>\n\n"
            "{description}\n\n"
            "💰 السعر: <b>${price}</b>\n"
            "📦 المخزون: <b>{stock}</b>\n"
            "🔥 مباع: <b>{total_sold}</b>"
        ),
        "fr": (
            "📦 <b>{name}</b>\n\n"
            "{description}\n\n"
            "💰 Prix: <b>${price}</b>\n"
            "📦 Stock: <b>{stock}</b>\n"
            "🔥 Vendu: <b>{total_sold}</b>"
        ),
    },
    "stock_unlimited":  {"en": "Unlimited",        "ar": "غير محدود",           "fr": "Illimité"},
    "out_of_stock":     {"en": "❌ Out of Stock",  "ar": "❌ نفذ المخزون",      "fr": "❌ Rupture de stock"},
    "btn_buy_usd":      {"en": "💵 Buy with Balance","ar": "💵 شراء بالرصيد",  "fr": "💵 Acheter avec le solde"},

    # ── BALANCE / WALLET ─────────────────────────────────────────
    "balance_title":    {
        "en": (
            "💰 <b>My Wallet</b>\n\n"
            "💵 Balance: <b>${balance}</b>\n"
            "📊 Total Spent: <b>${spent}</b>\n"
            "📦 Total Orders: <b>{orders}</b>"
        ),
        "ar": (
            "💰 <b>محفظتي</b>\n\n"
            "💵 الرصيد: <b>${balance}</b>\n"
            "📊 إجمالي الإنفاق: <b>${spent}</b>\n"
            "📦 إجمالي الطلبات: <b>{orders}</b>"
        ),
        "fr": (
            "💰 <b>Mon Portefeuille</b>\n\n"
            "💵 Solde: <b>${balance}</b>\n"
            "📊 Total Dépensé: <b>${spent}</b>\n"
            "📦 Total Commandes: <b>{orders}</b>"
        ),
    },
    "btn_deposit_usdt": {"en": "💎 Deposit USDT",  "ar": "💎 إيداع USDT",       "fr": "💎 Dépôt USDT"},
    "btn_deposit_stars":{"en": "⭐ Buy Points",    "ar": "⭐ شراء نقاط",        "fr": "⭐ Acheter des points"},
    "deposit_usdt_info":{
        "en": (
            "💎 <b>USDT Deposit</b> (TRC20)\n\n"
            "📋 <b>Wallet Address:</b>\n<code>{wallet}</code>\n\n"
            "📌 <b>Minimum:</b> ${min_deposit}\n"
            "⚡ After sending, tap below and enter your TX hash.\n\n"
            "⚠️ Only send USDT on TRC20 network!"
        ),
        "ar": (
            "💎 <b>إيداع USDT</b> (TRC20)\n\n"
            "📋 <b>عنوان المحفظة:</b>\n<code>{wallet}</code>\n\n"
            "📌 <b>الحد الأدنى:</b> ${min_deposit}\n"
            "⚡ بعد الإرسال، اضغط أدناه وأدخل هاش المعاملة.\n\n"
            "⚠️ أرسل USDT على شبكة TRC20 فقط!"
        ),
        "fr": (
            "💎 <b>Dépôt USDT</b> (TRC20)\n\n"
            "📋 <b>Adresse du portefeuille:</b>\n<code>{wallet}</code>\n\n"
            "📌 <b>Minimum:</b> ${min_deposit}\n"
            "⚡ Après l'envoi, appuyez ci-dessous et entrez votre hash TX.\n\n"
            "⚠️ Envoyez uniquement USDT sur le réseau TRC20!"
        ),
    },
    "btn_submit_tx":    {"en": "📤 Submit TX Hash", "ar": "📤 إرسال هاش المعاملة","fr": "📤 Soumettre hash TX"},
    "ask_amount":       {"en": "💵 Enter deposit amount (USD):","ar": "💵 أدخل مبلغ الإيداع (دولار):","fr": "💵 Entrez le montant du dépôt (USD):"},
    "ask_tx_hash":      {"en": "📋 Enter your TRC20 transaction hash:","ar": "📋 أدخل هاش معاملتك TRC20:","fr": "📋 Entrez votre hash de transaction TRC20:"},
    "deposit_submitted":{
        "en": "✅ <b>Deposit submitted!</b>\nWe'll verify and credit your account shortly.\n\nDeposit ID: <code>{dep_id}</code>",
        "ar": "✅ <b>تم تقديم الإيداع!</b>\nسنتحقق ونضيف الرصيد لحسابك قريبًا.\n\nرقم الإيداع: <code>{dep_id}</code>",
        "fr": "✅ <b>Dépôt soumis!</b>\nNous vérifierons et créditerons votre compte sous peu.\n\nID de dépôt: <code>{dep_id}</code>",
    },

    # ── PURCHASE FLOW ────────────────────────────────────────────
    "insufficient_balance": {
        "en": "❌ <b>Insufficient balance!</b>\nYou need <b>${needed}</b> but have <b>${have}</b>.",
        "ar": "❌ <b>رصيد غير كافٍ!</b>\nتحتاج <b>${needed}</b> لكن لديك <b>${have}</b>.",
        "fr": "❌ <b>Solde insuffisant!</b>\nVous avez besoin de <b>${needed}</b> mais vous avez <b>${have}</b>.",
    },
    "purchase_confirm": {
        "en": "🛒 <b>Confirm Purchase</b>\n\n📦 Product: <b>{name}</b>\n💰 Price: <b>${price}</b>\n\n🎟️ Coupon: <b>{coupon}</b>\n💵 Final Price: <b>${final}</b>",
        "ar": "🛒 <b>تأكيد الشراء</b>\n\n📦 المنتج: <b>{name}</b>\n💰 السعر: <b>${price}</b>\n\n🎟️ القسيمة: <b>{coupon}</b>\n💵 السعر النهائي: <b>${final}</b>",
        "fr": "🛒 <b>Confirmer l'achat</b>\n\n📦 Produit: <b>{name}</b>\n💰 Prix: <b>${price}</b>\n\n🎟️ Coupon: <b>{coupon}</b>\n💵 Prix final: <b>${final}</b>",
    },
    "btn_apply_coupon":  {"en": "🎟️ Apply Coupon",  "ar": "🎟️ تطبيق قسيمة",    "fr": "🎟️ Appliquer Coupon"},
    "ask_coupon_code":   {"en": "🎟️ Enter coupon code:","ar": "🎟️ أدخل كود القسيمة:","fr": "🎟️ Entrez le code coupon:"},
    "coupon_valid":      {"en": "✅ Coupon applied! Saving <b>${discount}</b>","ar": "✅ تم تطبيق القسيمة! توفير <b>${discount}</b>","fr": "✅ Coupon appliqué! Économie de <b>${discount}</b>"},
    "coupon_invalid":    {"en": "❌ Invalid or expired coupon code.","ar": "❌ كود القسيمة غير صالح أو منتهي الصلاحية.","fr": "❌ Code coupon invalide ou expiré."},
    "purchase_success":  {
        "en": "✅ <b>Purchase Successful!</b>\n\n🚀 Your product is being delivered below 👇\n\nOrder ID: <code>{order_id}</code>",
        "ar": "✅ <b>تمت عملية الشراء بنجاح!</b>\n\n🚀 منتجك يتم تسليمه أدناه 👇\n\nرقم الطلب: <code>{order_id}</code>",
        "fr": "✅ <b>Achat réussi!</b>\n\n🚀 Votre produit est livré ci-dessous 👇\n\nID de commande: <code>{order_id}</code>",
    },

    # ── ORDERS ───────────────────────────────────────────────────
    "orders_title":     {
        "en": "📜 <b>My Order History</b>",
        "ar": "📜 <b>سجل طلباتي</b>",
        "fr": "📜 <b>Historique de mes commandes</b>",
    },
    "no_orders":        {
        "en": "📭 You haven't placed any orders yet.",
        "ar": "📭 لم تقم بأي طلبات حتى الآن.",
        "fr": "📭 Vous n'avez encore passé aucune commande.",
    },
    "order_item":       {
        "en": "📦 <b>{name}</b>\n💵 ${amount} • {status} • {date}",
        "ar": "📦 <b>{name}</b>\n💵 ${amount} • {status} • {date}",
        "fr": "📦 <b>{name}</b>\n💵 ${amount} • {status} • {date}",
    },

    # ── PROFILE ──────────────────────────────────────────────────
    "profile_title":    {
        "en": (
            "👤 <b>My Profile</b>\n\n"
            "🆔 ID: <code>{user_id}</code>\n"
            "👤 Name: <b>{name}</b>\n"
            "📅 Joined: <b>{joined}</b>\n"
            "💰 Balance: <b>${balance}</b>\n"
            "📦 Orders: <b>{orders}</b>\n"
            "🔗 Referrals: <b>{referrals}</b>\n"
            "🌐 Language: <b>{language}</b>"
        ),
        "ar": (
            "👤 <b>ملفي الشخصي</b>\n\n"
            "🆔 المعرف: <code>{user_id}</code>\n"
            "👤 الاسم: <b>{name}</b>\n"
            "📅 تاريخ الانضمام: <b>{joined}</b>\n"
            "💰 الرصيد: <b>${balance}</b>\n"
            "📦 الطلبات: <b>{orders}</b>\n"
            "🔗 الإحالات: <b>{referrals}</b>\n"
            "🌐 اللغة: <b>{language}</b>"
        ),
        "fr": (
            "👤 <b>Mon Profil</b>\n\n"
            "🆔 ID: <code>{user_id}</code>\n"
            "👤 Nom: <b>{name}</b>\n"
            "📅 Inscrit: <b>{joined}</b>\n"
            "💰 Solde: <b>${balance}</b>\n"
            "📦 Commandes: <b>{orders}</b>\n"
            "🔗 Parrainages: <b>{referrals}</b>\n"
            "🌐 Langue: <b>{language}</b>"
        ),
    },

    # ── REFERRAL ─────────────────────────────────────────────────
    "referral_title":   {
        "en": (
            "🔗 <b>Referral Program</b>\n\n"
            "💵 Earn <b>${bonus}</b> for each friend you invite!\n"
            "🔗 Your referral link:\n{link}\n\n"
            "👥 Total referrals: <b>{count}</b>\n"
            "💰 Total earned: <b>${earned}</b>"
        ),
        "ar": (
            "🔗 <b>برنامج الإحالة</b>\n\n"
            "💵 اكسب <b>${bonus}</b> لكل صديق تدعوه!\n"
            "🔗 رابط الإحالة الخاص بك:\n{link}\n\n"
            "👥 إجمالي الإحالات: <b>{count}</b>\n"
            "💰 إجمالي الأرباح: <b>${earned}</b>"
        ),
        "fr": (
            "🔗 <b>Programme de Parrainage</b>\n\n"
            "💵 Gagnez <b>${bonus}</b> pour chaque ami invité!\n"
            "🔗 Votre lien de parrainage:\n{link}\n\n"
            "👥 Total parrainages: <b>{count}</b>\n"
            "💰 Total gagné: <b>${earned}</b>"
        ),
    },

    # ── SEARCH ───────────────────────────────────────────────────
    "search_prompt":    {"en": "🔍 Enter search term:","ar": "🔍 أدخل كلمة البحث:","fr": "🔍 Entrez le terme de recherche:"},
    "search_results":   {"en": "🔍 Results for: <b>{query}</b>","ar": "🔍 نتائج لـ: <b>{query}</b>","fr": "🔍 Résultats pour: <b>{query}</b>"},
    "no_results":       {"en": "🔍 No products found for <b>{query}</b>.","ar": "🔍 لا توجد منتجات لـ <b>{query}</b>.","fr": "🔍 Aucun produit trouvé pour <b>{query}</b>."},

    # ── GAMES CENTER ─────────────────────────────────────────────
    "games_menu_title": {
        "en": "🎮 <b>Games Center</b>\n━━━━━━━━━━━━━━━━━━━━━━━━\n\nChoose a game to play:",
        "ar": "🎮 <b>مركز الألعاب</b>\n━━━━━━━━━━━━━━━━━━━━━━━━\n\nاختر لعبة للعب:",
        "fr": "🎮 <b>Centre de Jeux</b>\n━━━━━━━━━━━━━━━━━━━━━━━━\n\nChoisissez un jeu:"
    },
    "btn_slots":        {"en": "🎰 Slot Machine",  "ar": "🎰 ماكينة القمار",    "fr": "🎰 Machine à Sous"},
    "btn_wheel":        {"en": "🎡 Lucky Wheel",   "ar": "🎡 العجلة المحظوظة",  "fr": "🎡 Roue de la Fortune"},
    "btn_coinflip":     {"en": "🪙 Coin Flip",     "ar": "🪙 قلب العملة",       "fr": "🪙 Pile ou Face"},
    "btn_daily_reward": {"en": "🎁 Daily Reward",  "ar": "🎁 المكافأة اليومية", "fr": "🎁 Récompense Quotidienne"},
    "btn_leaderboard":  {"en": "🏆 Leaderboard",   "ar": "🏆 لوحة المتصدرين",  "fr": "🏆 Classement"},
    "btn_game_history": {"en": "📜 My History",    "ar": "📜 سجلي",             "fr": "📜 Mon Historique"},
    "game_disabled":    {"en": "🔒 This game is currently disabled.","ar": "🔒 هذه اللعبة معطلة حالياً.","fr": "🔒 Ce jeu est actuellement désactivé."},
    "game_cooldown":    {"en": "⏳ Please wait <b>{seconds}s</b> before playing again.","ar": "⏳ انتظر <b>{seconds}ث</b> قبل اللعب مجدداً.","fr": "⏳ Attendez <b>{seconds}s</b> avant de rejouer."},
    "game_broke":       {
        "en": "❌ <b>Insufficient Balance</b>\n\nYou need at least <b>${min_bet}</b> to play.\n\n⭐ Top up with Telegram Stars:",
        "ar": "❌ <b>رصيد غير كافٍ</b>\n\nتحتاج على الأقل <b>${min_bet}</b> للعب.\n\n⭐ أعد شحن رصيدك بنجوم تيليغرام:",
        "fr": "❌ <b>Solde insuffisant</b>\n\nVous avez besoin d'au moins <b>${min_bet}</b> pour jouer.\n\n⭐ Rechargez avec des étoiles Telegram:",
    },
    "daily_claimed":    {
        "en": "🎁 <b>Daily Reward Claimed!</b>\n\n✨ You received: <b>${reward}</b> points!\n💰 New Balance: <b>${balance}</b>\n\nCome back tomorrow!",
        "ar": "🎁 <b>تم استلام المكافأة اليومية!</b>\n\n✨ حصلت على: <b>${reward}</b> نقطة!\n💰 الرصيد الجديد: <b>${balance}</b>\n\nعد غداً!",
        "fr": "🎁 <b>Récompense quotidienne réclamée!</b>\n\n✨ Vous avez reçu: <b>${reward}</b> points!\n💰 Nouveau solde: <b>${balance}</b>\n\nRevenez demain!",
    },
    "daily_already":    {
        "en": "⏰ <b>Already Claimed</b>\n\nYou already claimed today's reward!\n⏳ Next claim in: <b>{hours}h {mins}m</b>",
        "ar": "⏰ <b>تم الاستلام مسبقاً</b>\n\nلقد استلمت مكافأة اليوم!\n⏳ المكافأة القادمة خلال: <b>{hours}س {mins}د</b>",
        "fr": "⏰ <b>Déjà réclamé</b>\n\nVous avez déjà réclamé la récompense d'aujourd'hui!\n⏳ Prochaine réclamation dans: <b>{hours}h {mins}m</b>",
    },

    # ── FORCE SUBSCRIBE ──────────────────────────────────────────
    "subscribe_required": {
        "en": (
            "📌 <b>Subscription Required</b>\n\n"
            "You must join our channel to use this bot.\n"
            "Press the button below to join, then press <b>Check Again</b>."
        ),
        "ar": (
            "📌 <b>الاشتراك مطلوب</b>\n\n"
            "يجب عليك الانضمام إلى قناتنا لاستخدام هذا البوت.\n"
            "اضغط على الزر أدناه للانضمام، ثم اضغط <b>تحقق مجددًا</b>."
        ),
        "fr": (
            "📌 <b>Abonnement Requis</b>\n\n"
            "Vous devez rejoindre notre chaîne pour utiliser ce bot.\n"
            "Appuyez sur le bouton ci-dessous pour rejoindre, puis appuyez sur <b>Vérifier à nouveau</b>."
        ),
    },
    "btn_join_channel": {"en": "📢 Join Channel",  "ar": "📢 انضم للقناة",      "fr": "📢 Rejoindre la chaîne"},
    "btn_check_again":  {"en": "🔄 Check Again",   "ar": "🔄 تحقق مجددًا",     "fr": "🔄 Vérifier à nouveau"},
    "not_subscribed":   {
        "en": "❌ You haven't joined the channel yet. Please join and try again.",
        "ar": "❌ لم تنضم إلى القناة بعد. الرجاء الانضمام والمحاولة مجددًا.",
        "fr": "❌ Vous n'avez pas encore rejoint la chaîne. Rejoignez et réessayez.",
    },

    # ── CAPTCHA ──────────────────────────────────────────────────
    "captcha_question": {
        "en": "🤖 <b>CAPTCHA Verification</b>\n\nWhat is {a} + {b}?",
        "ar": "🤖 <b>التحقق من الهوية</b>\n\nما هو {a} + {b}؟",
        "fr": "🤖 <b>Vérification CAPTCHA</b>\n\nCombien font {a} + {b}?",
    },
    "captcha_wrong":    {"en": "❌ Wrong! Try again.","ar": "❌ خطأ! حاول مجددًا.","fr": "❌ Faux! Réessayez."},
    "captcha_passed":   {"en": "✅ Verified! Welcome.","ar": "✅ تم التحقق! مرحبًا.","fr": "✅ Vérifié! Bienvenue."},

    # ── LANGUAGE SELECTION ───────────────────────────────────────
    "select_language":  {
        "en": "🌐 <b>Select Language</b>",
        "ar": "🌐 <b>اختر اللغة</b>",
        "fr": "🌐 <b>Sélectionner la langue</b>",
    },
    "language_changed": {
        "en": "✅ Language changed to <b>English</b>",
        "ar": "✅ تم تغيير اللغة إلى <b>العربية</b>",
        "fr": "✅ Langue changée en <b>Français</b>",
    },

    # ── TERMS OF SERVICE ─────────────────────────────────────────
    "tos_text": {
        "en": (
            "📋 <b>Terms of Service</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "By using this bot you agree to:\n\n"
            "1. All sales are final. No refunds after delivery.\n"
            "2. You must be 18+ to use this service.\n"
            "3. Do not abuse or attempt to exploit the bot.\n"
            "4. Points and balances have no real-world cash value.\n"
            "5. We reserve the right to ban accounts that violate these terms.\n"
            "6. Game outcomes are random and final.\n\n"
            "<i>Last updated: 2025. Contact support for questions.</i>"
        ),
        "ar": (
            "📋 <b>شروط الخدمة</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "باستخدام هذا البوت فإنك توافق على:\n\n"
            "1. جميع المبيعات نهائية ولا يوجد استرداد بعد التسليم.\n"
            "2. يجب أن يكون عمرك 18 سنة أو أكثر.\n"
            "3. لا تسيء استخدام البوت أو تحاول استغلاله.\n"
            "4. النقاط والأرصدة ليس لها قيمة نقدية حقيقية.\n"
            "5. نحتفظ بالحق في حظر الحسابات التي تنتهك هذه الشروط.\n"
            "6. نتائج الألعاب عشوائية ونهائية."
        ),
        "fr": (
            "📋 <b>Conditions d'utilisation</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "En utilisant ce bot vous acceptez:\n\n"
            "1. Toutes les ventes sont finales, pas de remboursement après livraison.\n"
            "2. Vous devez avoir 18 ans ou plus.\n"
            "3. Ne pas abuser ou exploiter le bot.\n"
            "4. Les points n'ont pas de valeur monétaire réelle.\n"
            "5. Nous nous réservons le droit de bannir les comptes qui violent ces conditions.\n"
            "6. Les résultats des jeux sont aléatoires et définitifs."
        )
    },

    # ── SYSTEM MESSAGES ──────────────────────────────────────────
    "bot_offline":      {
        "en": "🔧 Bot is currently under maintenance. Please try again later.",
        "ar": "🔧 البوت في صيانة حاليًا. يرجى المحاولة لاحقًا.",
        "fr": "🔧 Le bot est actuellement en maintenance. Veuillez réessayer plus tard.",
    },
    "user_banned":      {
        "en": "🚫 You have been banned from using this bot.\nReason: {reason}",
        "ar": "🚫 تم حظرك من استخدام هذا البوت.\nالسبب: {reason}",
        "fr": "🚫 Vous avez été banni de ce bot.\nRaison: {reason}",
    },
    "error_generic":    {"en": "❌ An error occurred. Please try again.","ar": "❌ حدث خطأ. يرجى المحاولة مجددًا.","fr": "❌ Une erreur s'est produite. Veuillez réessayer."},
    "error_not_found":  {"en": "❌ Item not found.","ar": "❌ العنصر غير موجود.","fr": "❌ Élément introuvable."},
    "error_cooldown":   {"en": "⏳ Please wait before trying again.","ar": "⏳ يرجى الانتظار قبل المحاولة مجددًا.","fr": "⏳ Veuillez attendre avant de réessayer."},

    # ── ADMIN PANEL ──────────────────────────────────────────────
    "admin_panel":      {
        "en": (
            "👑 <b>Admin Panel</b>\n\n"
            "👥 Users: <b>{users}</b>\n"
            "📦 Orders: <b>{orders}</b>\n"
            "💰 Revenue: <b>${revenue}</b>\n"
            "⏳ Pending Deposits: <b>{deposits}</b>"
        ),
        "ar": (
            "👑 <b>لوحة الإدارة</b>\n\n"
            "👥 المستخدمون: <b>{users}</b>\n"
            "📦 الطلبات: <b>{orders}</b>\n"
            "💰 الإيرادات: <b>${revenue}</b>\n"
            "⏳ الإيداعات المعلقة: <b>{deposits}</b>"
        ),
        "fr": (
            "👑 <b>Panneau Admin</b>\n\n"
            "👥 Utilisateurs: <b>{users}</b>\n"
            "📦 Commandes: <b>{orders}</b>\n"
            "💰 Revenus: <b>${revenue}</b>\n"
            "⏳ Dépôts en attente: <b>{deposits}</b>"
        ),
    },
    "admin_users_list": {
        "en": "👥 <b>Users</b> (Page {page}/{total_pages})\nTotal: {total}",
        "ar": "👥 <b>المستخدمون</b> (صفحة {page}/{total_pages})\nالإجمالي: {total}",
        "fr": "👥 <b>Utilisateurs</b> (Page {page}/{total_pages})\nTotal: {total}",
    },
    "admin_products_list": {
        "en": "📦 <b>Products</b> (Page {page}/{total_pages})",
        "ar": "📦 <b>المنتجات</b> (صفحة {page}/{total_pages})",
        "fr": "📦 <b>Produits</b> (Page {page}/{total_pages})",
    },
    "admin_orders_list": {
        "en": "📜 <b>Orders</b> (Page {page}/{total_pages})\nTotal: {total}",
        "ar": "📜 <b>الطلبات</b> (صفحة {page}/{total_pages})\nالإجمالي: {total}",
        "fr": "📜 <b>Commandes</b> (Page {page}/{total_pages})\nTotal: {total}",
    },
    "admin_deposits_pending": {
        "en": "💎 <b>Pending Deposits</b>",
        "ar": "💎 <b>الإيداعات المعلقة</b>",
        "fr": "💎 <b>Dépôts en attente</b>",
    },
    "admin_confirm_ban": {
        "en": "⚠️ Ban user <code>{user_id}</code>?",
        "ar": "⚠️ حظر المستخدم <code>{user_id}</code>؟",
        "fr": "⚠️ Bannir l'utilisateur <code>{user_id}</code>?",
    },
    "admin_confirm_unban": {
        "en": "✅ Unban user <code>{user_id}</code>?",
        "ar": "✅ رفع حظر المستخدم <code>{user_id}</code>؟",
        "fr": "✅ Débannir l'utilisateur <code>{user_id}</code>?",
    },
    "admin_adjust_balance": {
        "en": "💰 Enter new balance for user <code>{user_id}</code>:",
        "ar": "💰 أدخل الرصيد الجديد للمستخدم <code>{user_id}</code>:",
        "fr": "💰 Entrez le nouveau solde pour l'utilisateur <code>{user_id}</code>:",
    },
    "admin_broadcast_prompt": {
        "en": "📢 <b>Broadcast</b>\n\nSend a message to all users.\nType your message:",
        "ar": "📢 <b>بث جماعي</b>\n\nأرسل رسالة لجميع المستخدمين.\nاكتب رسالتك:",
        "fr": "📢 <b>Diffusion</b>\n\nEnvoyez un message à tous les utilisateurs.\nTapez votre message:",
    },
    "admin_broadcast_done": {
        "en": "✅ Broadcast sent to <b>{count}</b> users.",
        "ar": "✅ تم إرسال البث إلى <b>{count}</b> مستخدم.",
        "fr": "✅ Diffusion envoyée à <b>{count}</b> utilisateurs.",
    },
    "admin_add_product_name": {
        "en": "📦 Enter product name (English):",
        "ar": "📦 أدخل اسم المنتج (بالإنجليزية):",
        "fr": "📦 Entrez le nom du produit (en anglais):",
    },
    "admin_add_product_price": {
        "en": "💰 Enter product price ($):",
        "ar": "💰 أدخل سعر المنتج ($):",
        "fr": "💰 Entrez le prix du produit ($):",
    },
    "admin_add_product_stock": {
        "en": "📦 Enter stock quantity (0 = unlimited):",
        "ar": "📦 أدخل كمية المخزون (0 = غير محدود):",
        "fr": "📦 Entrez la quantité en stock (0 = illimité):",
    },
    "admin_add_product_content": {
        "en": "📝 Enter product content/delivery text:",
        "ar": "📝 أدخل محتوى المنتج/نص التسليم:",
        "fr": "📝 Entrez le contenu du produit/texte de livraison:",
    },
    "admin_product_added": {
        "en": "✅ Product <b>{name}</b> added successfully!",
        "ar": "✅ تمت إضافة المنتج <b>{name}</b> بنجاح!",
        "fr": "✅ Produit <b>{name}</b> ajouté avec succès!",
    },
    "admin_coupon_added": {
        "en": "✅ Coupon <b>{code}</b> created!\nDiscount: {discount}\nUses: {uses}",
        "ar": "✅ تم إنشاء القسيمة <b>{code}</b>!\nالخصم: {discount}\nالاستخدامات: {uses}",
        "fr": "✅ Coupon <b>{code}</b> créé!\nRéduction: {discount}\nUtilisations: {uses}",
    },
    "admin_settings_title": {
        "en": "⚙️ <b>Bot Settings</b>",
        "ar": "⚙️ <b>إعدادات البوت</b>",
        "fr": "⚙️ <b>Paramètres du Bot</b>",
    },
    "admin_games_title": {
        "en": "🎮 <b>Games Admin Panel</b>",
        "ar": "🎮 <b>لوحة إدارة الألعاب</b>",
        "fr": "🎮 <b>Panneau Admin des Jeux</b>",
    },
    "admin_games_dashboard": {
        "en": "📊 <b>Economy Dashboard</b>",
        "ar": "📊 <b>لوحة الاقتصاد</b>",
        "fr": "📊 <b>Tableau de Bord Économique</b>",
    },

    # ── SUPPORT ──────────────────────────────────────────────────
    "support_title":    {
        "en": "💬 <b>Support</b>\n\nContact us for help with your orders or account.",
        "ar": "💬 <b>الدعم</b>\n\nتواصل معنا للمساعدة في طلباتك أو حسابك.",
        "fr": "💬 <b>Support</b>\n\nContactez-nous pour de l'aide avec vos commandes ou votre compte.",
    },
    "btn_open_ticket":  {"en": "🎫 Open Ticket",   "ar": "🎫 فتح تذكرة",        "fr": "🎫 Ouvrir un ticket"},
    "btn_contact_admin":{"en": "👤 Contact Admin",  "ar": "👤 تواصل مع المشرف",  "fr": "👤 Contacter l'admin"},
}


# ─────────────────────────────────────────────
#  TRANSLATION FUNCTION
# ─────────────────────────────────────────────

def _(key: str, lang: str = "en", **kwargs) -> str:
    lang = lang if lang in ("en", "ar", "fr") else "en"
    translations = STRINGS.get(key, {})
    if not translations:
        return f"[{key}]"
    text = translations.get(lang) or translations.get("en", f"[{key}]")
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, ValueError):
            pass
    return text


def get_language_name(lang_code: str) -> str:
    names = {"en": "🇬🇧 English", "ar": "🇸🇦 العربية", "fr": "🇫🇷 Français"}
    return names.get(lang_code, "🌐 Unknown")


AVAILABLE_LANGUAGES = ["en", "ar", "fr"]
