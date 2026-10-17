import os
import random
import sqlite3
import requests
import telebot
import logging
from telebot import types

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

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

QA = {"привет": "Здравствуйте, сэр!", "как дела": "Всё отлично, сэр."}

def menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("📝 Заметки", callback_data="notes"),
           types.InlineKeyboardButton("📋 Задачи", callback_data="tasks"))
    kb.add(types.InlineKeyboardButton("🌤 Погода", callback_data="weather"))
    return kb

@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id, "🤖 J.A.R.V.I.S. к вашим услугам, сэр.", reply_markup=menu())

@bot.message_handler(commands=['note'])
def note(m):
    text = m.text.replace('/note', '').strip()
    if text:
        cur.execute("INSERT INTO notes (text) VALUES (?)", (text,))
        conn.commit()
        bot.reply_to(m, f"📝 Заметка сохранена: {text}")

@bot.message_handler(commands=['notes'])
def notes(m):
    cur.execute("SELECT id, text FROM notes")
    rows = cur.fetchall()
    if rows:
        bot.reply_to(m, "Ваши заметки:\n" + "\n".join(f"{r[0]}. {r[1]}" for r in rows))
    else:
        bot.reply_to(m, "Заметок пока нет.")

@bot.message_handler(commands=['add'])
def add(m):
    text = m.text.replace('/add', '').strip()
    if text:
        cur.execute("INSERT INTO tasks (text) VALUES (?)", (text,))
        conn.commit()
        bot.reply_to(m, f"📋 Задача добавлена: {text}")

@bot.message_handler(commands=['list'])
def list_tasks(m):
    cur.execute("SELECT id, text FROM tasks")
    rows = cur.fetchall()
    if rows:
        bot.reply_to(m, "Ваши задачи:\n" + "\n".join(f"{r[0]}. {r[1]}" for r in rows))
    else:
        bot.reply_to(m, "Задач нет.")

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data == "notes":
        notes(call.message)
    elif call.data == "tasks":
        list_tasks(call.message)
    elif call.data == "weather":
        bot.reply_to(call.message, "Напишите: /weather Москва")
    bot.answer_callback_query(call.id)

@bot.message_handler(commands=['weather'])
def weather_cmd(m):
    city = m.text.replace('/weather', '').strip()
    if not city:
        bot.reply_to(m, "Укажите город: /weather Москва")
        return
    try:
        r = requests.get(f"https://wttr.in/{city}?format=3", timeout=10)
        bot.reply_to(m, r.text)
    except:
        bot.reply_to(m, "Ошибка погоды.")

@bot.message_handler(content_types=['text'])
def chat(m):
    text = m.text.lower()
    for k, v in QA.items():
        if k in text:
            bot.reply_to(m, v)
            return
    
    if not AI_KEY:
        bot.reply_to(m, "Сэр, ключ AI_KEY не найден в настройках Bothost.")
        return

    try:
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", 
            headers={"Authorization": f"Bearer {AI_KEY}"},
            json={"model": "google/gemini-2.0-flash-exp:free", 
                  "messages": [{"role": "user", "content": m.text}]}, timeout=30)
        
        if res.status_code == 200:
            ans = res.json()["choices"][0]["message"]["content"]
            bot.reply_to(m, ans)
        else:
            logging.error(f"OpenRouter Error: {res.status_code} - {res.text}")
            bot.reply_to(m, f"Сэр, ошибка ИИ (код {res.status_code}).")
    except Exception as e:
        logging.error(f"Request Error: {e}")
        bot.reply_to(m, "Сэр, ошибка связи с ИИ.")

if __name__ == "__main__":
    logging.info("J.A.R.V.I.S. запущен")
    bot.infinity_polling()
