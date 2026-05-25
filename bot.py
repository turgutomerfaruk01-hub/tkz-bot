import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# Token ve Username
TOKEN = '8552314108:AAHFaYY4FsDv-...' # Kendi tokenınızı kontrol edin

# Veritabanı kurulumu
def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (id INTEGER PRIMARY KEY, ref_points INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

init_db()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    
    # Yeni kullanıcıyı kaydet
    cursor.execute('INSERT OR IGNORE INTO users (id, ref_points) VALUES (?, ?)', (user_id, 0))
    
    # Referans sistemi (link ile gelindiyse puan ver)
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
    await query.edit_message_text(f"Seçiminiz: {query.data.replace('menu_', '').upper()}", reply_markup=InlineKeyboardMarkup(keyboard))

async def points_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    await query.answer()
    
    if query.data.startswith('add_'):
        points = int(query.data.split('_')[1])
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET ref_points = ref_points + ? WHERE id = ?', (points, user_id))
        conn.commit()
        conn.close()
        await query.message.reply_text(f"Başarılı! Hesabına {points} puan eklendi.")

    elif query.data == 'my_ref':
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT ref_points FROM users WHERE id = ?', (user_id,))
        result = cursor.fetchone()
        points = result[0] if result else 0
        conn.close()
        await query.message.reply_text(f"📊 Toplam referans puanın: {points}")

    elif query.data == 'my_link':
        link = f"t.me/TKZFRRET00LBOT?start={user_id}"
        await query.message.reply_text(f"🔗 Referans Linkin:\n{link}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu_handler, pattern='menu_.*'))
    app.add_handler(CallbackQueryHandler(points_handler, pattern='add_.*|my_ref|my_link'))
    
    print("Bot başarıyla başlatıldı ve çalışıyor!")
    app.run_polling()
