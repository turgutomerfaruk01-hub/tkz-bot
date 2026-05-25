import os
import sqlite3
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# Token ve Kanal Ayarları
TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_1 = "@tkzcpmfreetoolbor"  # Kanal 1 @kullanıcıadı
CHANNEL_2 = "@kanal2_kullanici_adi"  # Kanal 2 @kullanıcıadı

logging.basicConfig(level=logging.INFO)

# Veritabanı
def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, ref_points INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

init_db()

# Katılım Kontrolü
async def check_sub(user_id, context):
    try:
        c1 = await context.bot.get_chat_member(chat_id=CHANNEL_1, user_id=user_id)
        c2 = await context.bot.get_chat_member(chat_id=CHANNEL_2, user_id=user_id)
        return c1.status in ['member', 'administrator', 'creator'] and c2.status in ['member', 'administrator', 'creator']
    except:
        return False

# Komutlar
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (id, ref_points) VALUES (?, ?)', (user_id, 0))
    
    if args and args[0].isdigit():
        referrer_id = int(args[0])
        if referrer_id != user_id:
            cursor.execute('UPDATE users SET ref_points = ref_points + 1 WHERE id = ?', (referrer_id,))
    conn.commit()
    conn.close()

    keyboard = [
        [InlineKeyboardButton("ANA KANAL", url="https://t.me/tkzcpmfreetoolbor")],
        [InlineKeyboardButton("SOHBET KANALI", url="https://t.me/+4-4aBzr4AnY2MDM0")],
        [InlineKeyboardButton("KATILDIM✅", callback_data='check_sub')]
    ]
    await update.message.reply_text("Hoş geldin! Botu kullanmak için kanallarımıza katıl:", reply_markup=InlineKeyboardMarkup(keyboard))

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    if query.data == 'check_sub':
        if await check_sub(user_id, context):
            keyboard = [[InlineKeyboardButton("CPM1", callback_data='menu_cpm1')], [InlineKeyboardButton("CPM2", callback_data='menu_cpm2')]]
            await query.edit_message_text("✅ Onaylandı! Menü:", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.message.reply_text("❌ Kanallara katılmadan devam edemezsin!")

    elif query.data.startswith('menu_'):
        keyboard = [
            [InlineKeyboardButton("GET COIN (2p)", callback_data='add_2')],
            [InlineKeyboardButton("GET MONEY (2p)", callback_data='add_2')],
            [InlineKeyboardButton("GET FREE ACCOUNT (2p)", callback_data='add_2')],
            [InlineKeyboardButton("GET SCRIPT (4p)", callback_data='add_4')],
            [InlineKeyboardButton("MY REF", callback_data='my_ref'), InlineKeyboardButton("MY REF LINK", callback_data='my_link')]
        ]
        await query.edit_message_text(f"Menü: {query.data.replace('menu_', '').upper()}", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith('add_'):
        points = int(query.data.split('_')[1])
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET ref_points = ref_points + ? WHERE id = ?', (points, user_id))
        conn.commit()
        conn.close()
        await query.message.reply_text(f"✅ {points} puan eklendi!")

    elif query.data == 'my_ref':
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT ref_points FROM users WHERE id = ?', (user_id,))
        p = cursor.fetchone()[0]
        conn.close()
        await query.message.reply_text(f"📊 Puanın: {p}")

    elif query.data == 'my_link':
        await query.message.reply_text(f"🔗 Linkin:\nhttps://t.me/TKZFRRET00LBOT?start={user_id}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_handler))
    print("Bot çalışıyor...")
    app.run_polling()
