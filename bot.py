import os, sqlite3, requests, telebot
from telebot import types

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
AI_KEY = os.getenv("AI_KEY")

if not TOKEN:
    raise RuntimeError("Нет токена!")

bot = telebot.TeleBot(TOKEN)
conn = sqlite3.connect('jarvis.db', check_same_thread=False)
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, text TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, text TEXT)")
conn.commit()

def menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("📝 Заметки", callback_data="notes"),
           types.InlineKeyboardButton("📋 Задачи", callback_data="tasks"))
    kb.add(types.InlineKeyboardButton("🌤 Погода", callback_data="weather"),
           types.InlineKeyboardButton("💵 Курс валют", callback_data="currency"))
    return kb

@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id, "🤖 J.A.R.V.I.S. к вашим услугам, сэр.\nВыберите раздел:", reply_markup=menu())

# --- ЗАМЕТКИ ---
@bot.message_handler(commands=['note'])
def add_note(m):
    text = m.text.replace('/note', '').strip()
    if text:
        cur.execute("INSERT INTO notes (text) VALUES (?)", (text,))
        conn.commit()
        bot.reply_to(m, f"📝 Заметка сохранена: {text}")

@bot.message_handler(commands=['notes'])
def show_notes(m):
    cur.execute("SELECT id, text FROM notes")
    rows = cur.fetchall()
    if rows:
        bot.reply_to(m, "📝 Ваши заметки:\n" + "\n".join(f"{r[0]}. {r[1]}" for r in rows))
    else:
        bot.reply_to(m, "📭 Заметок пока нет.")

# --- ЗАДАЧИ ---
@bot.message_handler(commands=['add'])
def add_task(m):
    text = m.text.replace('/add', '').strip()
    if text:
        cur.execute("INSERT INTO tasks (text) VALUES (?)", (text,))
        conn.commit()
        bot.reply_to(m, f"📋 Задача добавлена: {text}")

@bot.message_handler(commands=['list'])
def show_tasks(m):
    cur.execute("SELECT id, text FROM tasks")
    rows = cur.fetchall()
    if rows:
        bot.reply_to(m, "📋 Ваши задачи:\n" + "\n".join(f"{r[0]}. {r[1]}" for r in rows))
    else:
        bot.reply_to(m, "🎉 Задач нет.")

# --- КНОПКИ ---
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data == "notes":
        show_notes(call.message)
    elif call.data == "tasks":
        show_tasks(call.message)
    elif call.data == "weather":
        bot.send_message(call.message.chat.id, "Напишите: /weather Москва")
    elif call.data == "currency":
        bot.send_message(call.message.chat.id, "Напишите: /currency USD")
    bot.answer_callback_query(call.id)

# --- ПОГОДА И ВАЛЮТЫ ---
@bot.message_handler(commands=['weather'])
def weather_cmd(m):
    city = m.text.replace('/weather', '').strip()
    if not city:
        bot.reply_to(m, "Напишите: /weather Москва")
        return
    try:
        r = requests.get(f"https://wttr.in/{city}?format=3", timeout=10)
        bot.reply_to(m, r.text)
    except:
        bot.reply_to(m, "Ошибка погоды.")

@bot.message_handler(commands=['currency'])
def currency_cmd(m):
    cur_code = m.text.replace('/currency', '').strip().upper()
    if not cur_code:
        bot.reply_to(m, "Напишите: /currency USD")
        return
    try:
        r = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=10).json()
        rate = r['rates'].get(cur_code)
        if rate:
            bot.reply_to(m, f"💵 1 USD = {rate} {cur_code}")
        else:
            bot.reply_to(m, "Валюта не найдена.")
    except:
        bot.reply_to(m, "Ошибка курса.")

# --- ИИ ---
@bot.message_handler(content_types=['text'])
def chat(m):
    if m.text.lower() in ["привет", "как дела"]:
        bot.reply_to(m, "Здравствуйте, сэр! Все системы работают.")
        return
    
    if not AI_KEY:
        bot.reply_to(m, "Сэр, ключ AI_KEY не найден.")
        return

    try:
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", 
            headers={"Authorization": f"Bearer {AI_KEY}"},
            json={"model": "google/gemini-2.0-flash-exp:free", 
                  "messages": [{"role": "user", "content": m.text}]}, timeout=30)
        
        if res.status_code == 200:
            bot.reply_to(m, res.json()["choices"][0]["message"]["content"])
        else:
            bot.reply_to(m, f"Сэр, ИИ сейчас недоступен (лимит бесплатных запросов исчерпан).")
    except:
        bot.reply_to(m, "Сэр, ошибка связи с ИИ.")

if __name__ == "__main__":
    print("J.A.R.V.I.S. запущен")
    bot.infinity_polling()
