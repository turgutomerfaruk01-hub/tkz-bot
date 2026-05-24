import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ===================== AYARLAR =====================
BOT_TOKEN = "8552314108:AAHFaYY4FsDv-c538afaztJjQ_sxWlMJA8c"
BOT_USERNAME = "TKZFRRETOOLBOT"  # @ olmadan
# ===================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_FILE = "bot_data.db"

# Ürün maliyetleri (referans puanı)
COSTS = {
    "GET_COIN":         2,
    "GET_MONEY":        2,
    "GET_FREE_ACCOUNT": 2,
    "GET_SCRIPT":       4,
}

ITEM_LABELS = {
    "GET_COIN":         "💰 GET COIN",
    "GET_MONEY":        "💵 GET MONEY",
    "GET_FREE_ACCOUNT": "🎁 GET FREE ACCOUNT",
    "GET_SCRIPT":       "📜 GET SCRIPT",
}

ITEM_EMOJI = {
    "GET_COIN":         "🪙",
    "GET_MONEY":        "💵",
    "GET_FREE_ACCOUNT": "🎁",
    "GET_SCRIPT":       "📜",
}


# ─────────────────── VERİTABANI ───────────────────
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id     INTEGER PRIMARY KEY,
            username    TEXT,
            ref_points  INTEGER DEFAULT 0,
            referred_by INTEGER DEFAULT NULL
        )
    """)
    conn.commit()
    conn.close()


def get_user(user_id: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row


def register_user(user_id: int, username: str, referred_by: int = None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT OR IGNORE INTO users (user_id, username, ref_points, referred_by) VALUES (?,?,0,?)",
        (user_id, username, referred_by),
    )
    conn.commit()
    conn.close()


def add_ref_point(user_id: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET ref_points = ref_points + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def get_ref_points(user_id: int) -> int:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT ref_points FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0


def spend_ref_points(user_id: int, amount: int) -> bool:
    points = get_ref_points(user_id)
    if points < amount:
        return False
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET ref_points = ref_points - ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()
    return True


# ─────────────────── KLAVYELER ────────────────────
def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("CPM1", callback_data="menu_CPM1"),
            InlineKeyboardButton("CPM2", callback_data="menu_CPM2"),
        ]
    ])


def cpm_keyboard(menu: str):
    """CPM1 / CPM2 ana menüsü - ürünler + ref butonları"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 GET COIN — 2 puan",         callback_data=f"{menu}|info|GET_COIN")],
        [InlineKeyboardButton("💵 GET MONEY — 2 puan",        callback_data=f"{menu}|info|GET_MONEY")],
        [InlineKeyboardButton("🎁 GET FREE ACCOUNT — 2 puan", callback_data=f"{menu}|info|GET_FREE_ACCOUNT")],
        [InlineKeyboardButton("📜 GET SCRIPT — 4 puan",       callback_data=f"{menu}|info|GET_SCRIPT")],
        [
            InlineKeyboardButton("👥 MY REFERANS",      callback_data=f"{menu}|MY_REF"),
            InlineKeyboardButton("🔗 MY REFERANS LİNK", callback_data=f"{menu}|MY_REF_LINK"),
        ],
        [InlineKeyboardButton("⬅️ Geri", callback_data="back_main")],
    ])


def item_detail_keyboard(menu: str, item: str):
    """Ürün detay ekranı — GET butonu + Geri"""
    cost = COSTS[item]
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"✅ GET ({cost} puan harca)", callback_data=f"{menu}|buy|{item}")],
        [InlineKeyboardButton("⬅️ Geri", callback_data=f"menu_{menu}")],
    ])


def back_to_cpm_keyboard(menu: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Geri", callback_data=f"menu_{menu}")]
    ])


# ─────────────────── KOMUTLAR ────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name

    referred_by = None
    if context.args:
        try:
            ref_id = int(context.args[0].replace("ref_", ""))
            if ref_id != user_id:
                referred_by = ref_id
        except ValueError:
            pass

    existing = get_user(user_id)

    if not existing:
        register_user(user_id, username, referred_by)
        if referred_by and get_user(referred_by):
            add_ref_point(referred_by)
            try:
                await context.bot.send_message(
                    chat_id=referred_by,
                    text=(
                        f"🎉 Tebrikler! Referans linkinizle yeni bir kullanıcı katıldı.\n"
                        f"➕ +1 Referans puanı kazandınız!\n"
                        f"Toplam puanınız: {get_ref_points(referred_by)} 🏆"
                    ),
                )
            except Exception:
                pass
    else:
        register_user(user_id, username)

    await update.message.reply_text(
        f"👋 Hoş geldin, {user.first_name}!\n\n"
        "Lütfen bir menü seç:",
        reply_markup=main_menu_keyboard(),
    )


async def myref_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    points = get_ref_points(user_id)
    await update.message.reply_text(
        f"👥 *Referans Puanlarınız*\n\n🏆 Toplam Puan: *{points}*",
        parse_mode="Markdown",
    )


async def myreflink_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    link = f"https://t.me/{BOT_USERNAME}?start=ref_{user_id}"
    await update.message.reply_text(
        f"🔗 *Referans Linkiniz:*\n\n`{link}`\n\n"
        "Bu linki paylaşarak her yeni kullanıcı için 1 puan kazanırsınız!",
        parse_mode="Markdown",
    )


# ─────────────────── CALLBACK ────────────────────
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    # ── Ana menüye dön ──
    if data == "back_main":
        await query.edit_message_text(
            "Lütfen bir menü seç:", reply_markup=main_menu_keyboard()
        )
        return

    # ── CPM menüsü aç ──
    if data in ("menu_CPM1", "menu_CPM2"):
        menu = data[5:]   # "CPM1" veya "CPM2"
        points = get_ref_points(user_id)
        await query.edit_message_text(
            f"📋 *{menu} Menüsü*\n"
            f"💼 Mevcut puanınız: *{points}* 🏆\n\n"
            "Bir seçenek seç:",
            parse_mode="Markdown",
            reply_markup=cpm_keyboard(menu),
        )
        return

    # ── Pipe ile ayrılmış yeni format: MENU|eylem|item ──
    parts = data.split("|")
    if len(parts) < 2:
        return

    menu = parts[0]    # CPM1 / CPM2
    action = parts[1]  # info / buy / MY_REF / MY_REF_LINK

    # ── Ürün bilgi ekranı (GET butonu burada çıkar) ──
    if action == "info" and len(parts) == 3:
        item = parts[2]
        cost = COSTS[item]
        label = ITEM_LABELS[item]
        points = get_ref_points(user_id)
        await query.edit_message_text(
            f"{ITEM_EMOJI[item]} *{label}*\n\n"
            f"💸 Gerekli puan: *{cost}*\n"
            f"🏆 Mevcut puanınız: *{points}*\n\n"
            f"Satın almak için aşağıdaki GET butonuna bas!",
            parse_mode="Markdown",
            reply_markup=item_detail_keyboard(menu, item),
        )
        return

    # ── Satın alma ──
    if action == "buy" and len(parts) == 3:
        item = parts[2]
        cost = COSTS[item]
        label = ITEM_LABELS[item]
        if spend_ref_points(user_id, cost):
            await query.edit_message_text(
                f"✅ *{label}* başarıyla alındı!\n"
                f"💸 {cost} referans puanı harcandı.\n\n"
                f"Kalan puanınız: {get_ref_points(user_id)} 🏆",
                parse_mode="Markdown",
                reply_markup=back_to_cpm_keyboard(menu),
            )
        else:
            await query.edit_message_text(
                f"❌ *Yetersiz referans puanı!*\n\n"
                f"{label} için *{cost} puan* gerekli.\n"
                f"Mevcut puanınız: {get_ref_points(user_id)} 🏆\n\n"
                f"🔗 Referans linkinizi paylaşarak puan kazanın!",
                parse_mode="Markdown",
                reply_markup=back_to_cpm_keyboard(menu),
            )
        return

    # ── MY REFERANS ──
    if action == "MY_REF":
        points = get_ref_points(user_id)
        await query.edit_message_text(
            f"👥 *Referans Puanlarınız*\n\n"
            f"🏆 Toplam Puan: *{points}*\n\n"
            f"Puan kazanmak için referans linkinizi paylaşın!",
            parse_mode="Markdown",
            reply_markup=back_to_cpm_keyboard(menu),
        )
        return

    # ── MY REFERANS LİNK ──
    if action == "MY_REF_LINK":
        link = f"https://t.me/{BOT_USERNAME}?start=ref_{user_id}"
        await query.edit_message_text(
            f"🔗 *Referans Linkiniz:*\n\n`{link}`\n\n"
            f"Bu linki paylaşarak her yeni kullanıcı için *1 puan* kazanırsınız!\n\n"
            f"📌 Puan maliyetleri:\n"
            f"• GET COIN / MONEY / FREE ACCOUNT → 2 puan\n"
            f"• GET SCRIPT → 4 puan",
            parse_mode="Markdown",
            reply_markup=back_to_cpm_keyboard(menu),
        )
        return


# ─────────────────── MAIN ────────────────────────
def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("myref", myref_cmd))
    app.add_handler(CommandHandler("myreflink", myreflink_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("Bot başlatıldı...")
    app.run_polling()


if __name__ == "__main__":
    main()
