import os
import sqlite3
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# Railway Variables kısmından BOT_TOKEN'ı çeker
TOKEN = os.getenv('BOT_TOKEN')

# Loglama ayarı (Hataları görmek için)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Veritabanı
def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, ref_points INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

init_db()

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
        [InlineKeyboardButton("CPM1", callback_data='menu_cpm1')],
        [InlineKeyboardButton("CPM2", callback_data='menu_cpm2')]
    ]
    await update.message.reply_text("Hoş geldin! Bir menü seç:", reply_markup=InlineKeyboardMarkup(keyboard))

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("GET COIN (2p)", callback_data='add_2')],
        [InlineKeyboardButton("GET MONEY (2p)", callback_data='add_2')],
        [InlineKeyboardButton("GET FREE ACCOUNT (2p)", callback_data='add_2')],
        [InlineKeyboardButton("GET SCRIPT (4p)", callback_data='add_4')],
        [InlineKeyboardButton("MY REF", callback_data='my_ref'), InlineKeyboardButton("MY REF LINK", callback_data='my_link')]
    ]
    await query.edit_message_text(f"Menü: {query.data.replace('menu_', '').upper()}", reply_markup=InlineKeyboardMarkup(keyboard))

async def points_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    
    if query.data.startswith('add_'):
        points = int(query.data.split('_')[1])
        cursor.execute('UPDATE users SET ref_points = ref_points + ? WHERE id = ?', (points, user_id))
        conn.commit()
        await query.message.reply_text(f"✅ Hesabına {points} puan eklendi!")
    
    elif query.data == 'my_ref':
        cursor.execute('SELECT ref_points FROM users WHERE id = ?', (user_id,))
        points = cursor.fetchone()[0]
        await query.message.reply_text(f"📊 Toplam referans puanın: {points}")
    
    elif query.data == 'my_link':
        await query.message.reply_text(f"🔗 Referans Linkin:\nhttps://t.me/TKZFRRET00LBOT?start={user_id}")
    
    conn.close()

if __name__ == '__main__':
    if not TOKEN:
        print("HATA: BOT_TOKEN değişkeni bulunamadı!")
    else:
        app = ApplicationBuilder().token(TOKEN).build()
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CallbackQueryHandler(menu_handler, pattern='menu_.*'))
        app.add_handler(CallbackQueryHandler(points_handler, pattern='add_.*|my_ref|my_link'))
        
        print("Bot başarıyla başlatıldı ve çalışıyor!")
        app.run_polling()
