import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from openai import OpenAI

# =============================
# ⚙️ زانیاری لە ENV (نەنووسە لە کۆد)
# =============================
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")

ADMIN_ID = 8186735286

# =============================
# 🤖 OpenAI
# =============================
client = OpenAI(api_key=OPENAI_KEY)

# =============================
# 📢 Forced Join Channels
# =============================
CHANNELS = [
    "chanaly_boot",
    "team_988",
    "my_d4ily"
]

# =============================
# 📦 داتای بەکارهێنەر (ساده)
# =============================
users = {}
LIMIT = 5  # فری = 5 جار

# =============================
# 🔒 پشکنینی جوین
# =============================
async def is_joined(bot, user_id):
    for ch in CHANNELS:
        try:
            member = await bot.get_chat_member(f"@{ch}", user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

# =============================
# 🧮 لیمیت
# =============================
def can_use(user_id):
    if user_id not in users:
        users[user_id] = {"count": 0, "vip": False}

    if users[user_id]["vip"]:
        return True

    if users[user_id]["count"] < LIMIT:
        users[user_id]["count"] += 1
        return True

    return False

# =============================
# 🏁 /start
# =============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not await is_joined(context.bot, user.id):
        buttons = []
        for ch in CHANNELS:
            buttons.append([InlineKeyboardButton(f"📢 @{ch}", url=f"https://t.me/{ch}")])
        buttons.append([InlineKeyboardButton("✅ جوین بووم", callback_data="check")])

        await update.message.reply_text(
            "🚫 تکایە سەرەتا ئەم جەناڵانە جوین بکە 👇",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    keyboard = [
        [InlineKeyboardButton("🤖 AI چات", callback_data="ai")],
        [InlineKeyboardButton("🆓 فری", callback_data="free")],
        [InlineKeyboardButton("💎 VIP", callback_data="vip")]
    ]

    await update.message.reply_text(
        "👋 بەخێربێیت بۆ بوتی AI\n\n"
        "هەموو شت بە دووگمە 👇",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =============================
# 🔘 دووگمەکان
# =============================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id

    if q.data == "check":
        if await is_joined(context.bot, uid):
            await q.message.reply_text("✅ سەرکەوتوو بوو! /start بکە")
        else:
            await q.message.reply_text("❌ هێشتا جوین نەبوویت")

    elif q.data == "ai":
        await q.message.reply_text("✍️ پرسیارت بنووسە")

    elif q.data == "free":
        count = users.get(uid, {}).get("count", 0)
        await q.message.reply_text(
            f"🆓 فری\n\n"
            f"تۆ {count}/{LIMIT} جار بەکارهێناوە"
        )

    elif q.data == "vip":
        await q.message.reply_text(
            "💎 بۆ VIP → پەیوەندی بکە بە ئەدمین"
        )

# =============================
# 🤖 AI چات
# =============================
async def ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if not can_use(uid):
        await update.message.reply_text(
            "⛔ لیمیت تەواو بوو\n"
            "بۆ بێ سنوور → VIP بکە"
        )
        return

    msg = update.message.text

    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": msg}]
        )
        await update.message.reply_text(res.choices[0].message.content)

    except:
        await update.message.reply_text("❌ هەڵە لە AI")

# =============================
# 👑 ئەدمین: VIP
# =============================
async def vip_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    uid = int(context.args[0])
    users.setdefault(uid, {"count": 0, "vip": False})
    users[uid]["vip"] = True
    await update.message.reply_text(f"✅ {uid} VIP کرا")

# =============================
# ▶️ RUN
# =============================
app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("vip", vip_cmd))
app.add_handler(CallbackQueryHandler(buttons))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_chat))

print("Bot is running...")
app.run_polling()