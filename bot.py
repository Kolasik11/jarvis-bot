import os
import re
import time
import random
import sqlite3
import threading
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests
import telebot
from telebot import types

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("NOT_TOOWN", "")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-exp:free")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0") or "0")
TIMEZONE = os.getenv("BOT_TIMEZONE", "Europe/Moscow")
DB_PATH = os.getenv("JARVIS_DB_PATH", "jarvis.db")

BN = "J.A.R.V.I.S."
HISTORY_LIMIT = 12
MAX_MESSAGE_LENGTH = 3500
AI_TIMEOUT = 35

if not TOKEN:
    raise RuntimeError("Не задан токен. Установи TELEGRAM_BOT_TOKEN.")

bot = telebot.TeleBot(TOKEN, threaded=True)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("jarvis")

try:
    TZ = ZoneInfo(TIMEZONE)
except Exception:
    TZ = ZoneInfo("UTC")

BAD = ["хуй", "хуя", "хуе", "пизд", "бля", "блять", "ебал", "ебат", "заеб", "нахуй", "мудак", "говно", "сука", "тварь", "пидор", "шлюха"]

QA = {
    "привет": ["Здравствуйте, сэр.", "Приветствую, сэр."],
    "как дела": ["Работаю штатно, сэр.", "Все системы в порядке, сэр."],
    "как ты": ["Готов к работе, сэр."],
    "как жизнь": ["Стабильна, сэр."],
    "как настроение": ["Отличное. Чем могу помочь, сэр?"],
    "как здоровье": ["В норме, сэр."],
    "как серафимушка": ["Серафимушка в порядке!"],
    "как серафима": ["Серафима в порядке!"],
    "как григорий": ["Григорий в порядке!"],
    "как гриша": ["Гриша в порядке!"],
    "серафимушка": ["Прекрасный человек!"],
    "григорий": ["Надёжный человек!"],
    "кто ты": ["Я J.A.R.V.I.S., ваш личный ассистент, сэр."],
    "что ты умеешь": ["Управляю задачами и заметками, ставлю напоминания."],
    "спасибо": ["Всегда к вашим услугам, сэр."],
    "пока": ["До свидания, сэр."],
    "до свидания": ["Всего доброго, сэр."],
    "ты крутой": ["Благодарю, сэр."],
    "ты лучший": ["Приятно слышать, сэр."],
    "извини": ["Ничего страшного, сэр."],
    "что поесть": ["Могу предложить что-нибудь простое и вкусное, сэр."],
    "я голоден": ["Пора подкрепиться, сэр."],
    "я устал": ["Небольшой отдых может помочь, сэр."],
    "хочу спать": ["Сон важен, сэр."],
    "мне скучно": ["Можем сыграть в викторину, сэр."],
    "мне грустно": ["Мне жаль, что вам грустно, сэр."],
    "расскажи анекдот": ["Почему программисты путают Хэллоуин и Рождество? Потому что Oct 31 == Dec 25!"],
    "пошути": ["Почему бот не пошёл в бар? Не было бар-кода!"],
    "что такое любовь": ["Это чувство близости и заботы, сэр."],
    "удачи": ["И вам удачи, сэр."],
    "помоги": ["Конечно, сэр. Опишите задачу."],
    "я тебя люблю": ["Я рад быть полезным, сэр."],
    "ты мой друг": ["Я здесь, чтобы помочь вам, сэр."],
    "я скучал": ["С возвращением, сэр."]
}

def now_local():
    return datetime.now(TZ)

def db_connect():
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    return conn

def db():
    with db_connect() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, text TEXT NOT NULL, created_at TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0)")
        conn.execute("CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, text TEXT NOT NULL, created_at TEXT NOT NULL)")
        conn.execute("CREATE TABLE IF NOT EXISTS messages_log (id INTEGER PRIMARY KEY AUTOINCREMENT, uid TEXT, username TEXT, first_name TEXT, text TEXT, date TEXT, is_sticker INTEGER DEFAULT 0, chat_id TEXT)")
        conn.execute("CREATE TABLE IF NOT EXISTS reminders (id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id TEXT NOT NULL, user_id TEXT NOT NULL, text TEXT NOT NULL, due_at TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0)")
        conn.execute("CREATE TABLE IF NOT EXISTS groups_saved (chat_id TEXT PRIMARY KEY, chat_name TEXT)")
        conn.execute("CREATE TABLE IF NOT EXISTS chat_history (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, chat_id TEXT NOT NULL, role TEXT NOT NULL, content TEXT NOT NULL, created_at TEXT NOT NULL)")

def add_log(user, chat_id, text, is_sticker=False):
    try:
        with db_connect() as conn:
            conn.execute("INSERT INTO messages_log (uid,username,first_name,text,date,is_sticker,chat_id) VALUES (?,?,?,?,?,?,?)", (str(user.id), user.username or "нет", user.first_name or "нет", text[:2000], now_local().strftime("%d.%m.%Y %H:%M:%S"), int(is_sticker), str(chat_id)))
    except Exception:
        pass

def add_task(user_id, text):
    with db_connect() as conn:
        cur = conn.execute("INSERT INTO tasks(user_id,text,created_at,done) VALUES (?,?,?,0)", (str(user_id), text[:1000], now_local().isoformat()))
        return cur.lastrowid

def get_tasks(user_id):
    with db_connect() as conn:
        return conn.execute("SELECT id,text FROM tasks WHERE user_id=? AND done=0 ORDER BY id", (str(user_id),)).fetchall()

def count_tasks(user_id):
    with db_connect() as conn:
        return conn.execute("SELECT COUNT(*) FROM tasks WHERE user_id=? AND done=0", (str(user_id),)).fetchone()[0]

def finish_task(user_id, task_id):
    with db_connect() as conn:
        cur = conn.execute("UPDATE tasks SET done=1 WHERE id=? AND user_id=? AND done=0", (task_id, str(user_id)))
        return cur.rowcount > 0

def delete_task(user_id, task_id):
    with db_connect() as conn:
        cur = conn.execute("DELETE FROM tasks WHERE id=? AND user_id=?", (task_id, str(user_id)))
        return cur.rowcount > 0

def clear_finished_tasks(user_id):
    with db_connect() as conn:
        cur = conn.execute("DELETE FROM tasks WHERE user_id=? AND done=1", (str(user_id),))
        return cur.rowcount

def add_note(user_id, text):
    with db_connect() as conn:
        cur = conn.execute("INSERT INTO notes(user_id,text,created_at) VALUES (?,?,?)", (str(user_id), text[:2000], now_local().strftime("%d.%m.%Y %H:%M")))
        return cur.lastrowid

def get_notes(user_id):
    with db_connect() as conn:
        return conn.execute("SELECT id,text,created_at FROM notes WHERE user_id=? ORDER BY id", (str(user_id),)).fetchall()

def delete_note(user_id, note_id):
    with db_connect() as conn:
        cur = conn.execute("DELETE FROM notes WHERE id=? AND user_id=?", (note_id, str(user_id)))
        return cur.rowcount > 0

def clear_notes(user_id):
    with db_connect() as conn:
        cur = conn.execute("DELETE FROM notes WHERE user_id=?", (str(user_id),))
        return cur.rowcount

def add_reminder(chat_id, user_id, text, due_at):
    with db_connect() as conn:
        cur = conn.execute("INSERT INTO reminders(chat_id,user_id,text,due_at,done) VALUES (?,?,?,?,0)", (str(chat_id), str(user_id), text[:1000], due_at.isoformat()))
        return cur.lastrowid

def get_pending_reminders():
    with db_connect() as conn:
        return conn.execute("SELECT id,chat_id,user_id,text,due_at FROM reminders WHERE done=0").fetchall()

def mark_reminder_done(reminder_id):
    with db_connect() as conn:
        conn.execute("UPDATE reminders SET done=1 WHERE id=?", (reminder_id,))

def save_group(chat_id, title):
    with db_connect() as conn:
        conn.execute("INSERT OR REPLACE INTO groups_saved(chat_id,chat_name) VALUES (?,?)", (str(chat_id), title or "Группа"))

def get_group():
    with db_connect() as conn:
        return conn.execute("SELECT chat_id,chat_name FROM groups_saved ORDER BY rowid DESC LIMIT 1").fetchone()

def chat_stats(chat_id):
    with db_connect() as conn:
        total = conn.execute("SELECT COUNT(*) FROM messages_log WHERE chat_id=?", (str(chat_id),)).fetchone()[0]
        users = conn.execute("SELECT username,first_name,COUNT(*) AS n FROM messages_log WHERE chat_id=? GROUP BY uid ORDER BY n DESC LIMIT 10", (str(chat_id),)).fetchall()
        return total, users

def history_get(user_id, chat_id):
    with db_connect() as conn:
        rows = conn.execute("SELECT role,content FROM chat_history WHERE user_id=? AND chat_id=? ORDER BY id DESC LIMIT ?", (str(user_id), str(chat_id), HISTORY_LIMIT)).fetchall()
    return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]

def history_add(user_id, chat_id, role, content):
    with db_connect() as conn:
        conn.execute("INSERT INTO chat_history(user_id,chat_id,role,content,created_at) VALUES (?,?,?,?,?)", (str(user_id), str(chat_id), role, content[:4000], now_local().isoformat()))
        conn.execute("DELETE FROM chat_history WHERE user_id=? AND chat_id=? AND id NOT IN (SELECT id FROM chat_history WHERE user_id=? AND chat_id=? ORDER BY id DESC LIMIT 30)", (str(user_id), str(chat_id), str(user_id), str(chat_id)))

def history_clear(user_id, chat_id):
    with db_connect() as conn:
        cur = conn.execute("DELETE FROM chat_history WHERE user_id=? AND chat_id=?", (str(user_id), str(chat_id)))
        return cur.rowcount

def ask_ai(user_id, chat_id, text):
    if not OPENROUTER_KEY:
        return None
    messages = [{"role": "system", "content": "Ты J.A.R.V.I.S. — вежливый, умный личный ассистент. Обращайся к собеседнику «сэр». Отвечай на языке пользователя. Если не знаешь ответа, честно скажи об этом."}]
    messages.extend(history_get(user_id, chat_id))
    messages.append({"role": "user", "content": text[:4000]})
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers={"Authorization": "Bearer " + OPENROUTER_KEY, "Content-Type": "application/json"}, json={"model": OPENROUTER_MODEL, "messages": messages, "temperature": 0.7, "max_tokens": 700}, timeout=AI_TIMEOUT)
        if response.status_code != 200:
            return None
        data = response.json()
        answer = data["choices"][0]["message"]["content"]
        if not isinstance(answer, str) or not answer.strip():
            return None
        answer = answer.strip()
        history_add(user_id, chat_id, "user", text)
        history_add(user_id, chat_id, "assistant", answer)
        return answer
    except Exception:
        return None

def admin_only(message):
    if ADMIN_ID and message.from_user.id == ADMIN_ID:
        return True
    bot.reply_to(message, "⛔ Эта команда доступна только владельцу бота.")
    return False

def answer_long(message, text, **kwargs):
    text = str(text)
    for start in range(0, len(text), MAX_MESSAGE_LENGTH):
        bot.reply_to(message, text[start:start + MAX_MESSAGE_LENGTH], **kwargs)

def qa_answer(text):
    tl = text.lower().strip()
    for key, answers in QA.items():
        if key in tl:
            return random.choice(answers)
    return None

def weather(city):
    try:
        response = requests.get("https://wttr.in/" + requests.utils.quote(city) + "?format=%C+%t+%w", timeout=12)
        if response.status_code == 200:
            return f"🌤 {city}: {response.text.strip()}"
        return "⚠ Не удалось получить погоду."
    except requests.RequestException:
        return "⚠ Ошибка сети при получении погоды."

def currency(code):
    code = code.upper().strip()
    if not re.fullmatch(r"[A-Z]{3}", code):
        return "⚠ Укажите трёхбуквенный код валюты."
    try:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=12)
        response.raise_for_status()
        rates = response.json().get("rates", {})
        if code in rates:
            return f"💵 1 USD = {rates[code]} {code}"
        return "⚠ Валюта не найдена."
    except (requests.RequestException, ValueError):
        return "⚠ Ошибка при получении курса."

def reminder_worker():
    while True:
        try:
            current = now_local()
            for row in get_pending_reminders():
                try:
                    due = datetime.fromisoformat(row["due_at"])
                    if due.tzinfo is None:
                        due = due.replace(tzinfo=TZ)
                    if due <= current:
                        try:
                            bot.send_message(int(row["chat_id"]), "⏰ Напоминание!\n\n" + row["text"])
                        except Exception:
                            continue
                        mark_reminder_done(row["id"])
                except (ValueError, TypeError):
                    pass
            time.sleep(10)
        except Exception:
            time.sleep(10)

def main_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("📝 Заметки", callback_data="notes"), types.InlineKeyboardButton("📋 Задачи", callback_data="tasks"))
    kb.add(types.InlineKeyboardButton("⏰ Напоминания", callback_data="reminders"), types.InlineKeyboardButton("📊 Анализ", callback_data="analysis"))
    kb.add(types.InlineKeyboardButton("🧠 Память ИИ", callback_data="memory"), types.InlineKeyboardButton("🌤 Полезное", callback_data="useful"))
    kb.add(types.InlineKeyboardButton("❓ Помощь", callback_data="help"))
    return kb

def back_menu():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="menu"))
    return kb

@bot.message_handler(commands=["start", "menu"])
def start(message):
    bot.send_message(message.chat.id, "🤖 *J.A.R.V.I.S.* — главное меню\n\nВыберите раздел, сэр.", parse_mode="Markdown", reply_markup=main_menu())

@bot.message_handler(commands=["help"])
def help_command(message):
    text = ("📖 *Команды J.A.R.V.I.S.*\n\n"
            "📝 Заметки: `/note текст`, `/notes`, `/delnote ID`, `/clearnotes`\n"
            "📋 Задачи: `/add текст`, `/list`, `/done ID`, `/delete ID`, `/clear`\n"
            "⏰ Напоминания: `/remind ЧЧ:ММ текст`, `/remind_in минуты текст`, `/timer секунды`\n"
            "🌤 Полезное: `/weather город`, `/currency EUR`\n"
            "🧠 ИИ: `/reset` — очистить контекст\n"
            "📊 `/analysis` — статистика, `/menu` — меню")
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=["note"])
def note_command(message):
    value = message.text.partition(" ")[2].strip()
    if not value:
        bot.reply_to(message, "Использование: /note Купить молоко")
        return
    note_id = add_note(message.from_user.id, value)
    bot.reply_to(message, f"📝 Заметка #{note_id} сохранена.")

@bot.message_handler(commands=["notes"])
def notes_command(message):
    rows = get_notes(message.from_user.id)
    if not rows:
        bot.reply_to(message, "📭 У вас пока нет заметок.")
        return
    text = "📝 *Ваши заметки:*\n\n" + "\n".join(f"{r['id']}. [{r['created_at']}] {r['text']}" for r in rows)
    answer_long(message, text)

@bot.message_handler(commands=["delnote"])
def delete_note_command(message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].isdigit():
        bot.reply_to(message, "Использование: /delnote 3")
        return
    ok = delete_note(message.from_user.id, int(parts[1]))
    bot.reply_to(message, "🗑 Заметка удалена." if ok else "⚠ Заметка не найдена.")

@bot.message_handler(commands=["clearnotes"])
def clear_notes_command(message):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Да, удалить мои заметки", callback_data="confirm_clear_notes"), types.InlineKeyboardButton("Отмена", callback_data="menu"))
    bot.send_message(message.chat.id, "Удалить все ваши заметки?", reply_markup=kb)

@bot.message_handler(commands=["add"])
def add_task_command(message):
    value = message.text.partition(" ")[2].strip()
    if not value:
        bot.reply_to(message, "Использование: /add Купить хлеб")
        return
    task_id = add_task(message.from_user.id, value)
    bot.reply_to(message, f"📋 Задача #{task_id} добавлена.")

@bot.message_handler(commands=["list"])
def list_tasks_command(message):
    rows = get_tasks(message.from_user.id)
    if not rows:
        bot.reply_to(message, "🎉 Активных задач нет.")
        return
    answer_long(message, "📋 *Ваши задачи:*\n\n" + "\n".join(f"{r['id']}. {r['text']}" for r in rows))

@bot.message_handler(commands=["done"])
def done_task_command(message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].isdigit():
        bot.reply_to(message, "Использование: /done 3")
        return
    ok = finish_task(message.from_user.id, int(parts[1]))
    bot.reply_to(message, "✅ Задача выполнена." if ok else "⚠ Активная задача не найдена.")

@bot.message_handler(commands=["delete"])
def delete_task_command(message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].isdigit():
        bot.reply_to(message, "Использование: /delete 3")
        return
    ok = delete_task(message.from_user.id, int(parts[1]))
    bot.reply_to(message, "🗑 Задача удалена." if ok else "⚠ Задача не найдена.")

@bot.message_handler(commands=["clear"])
def clear_tasks_command(message):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Да, удалить выполненные", callback_data="confirm_clear_tasks"), types.InlineKeyboardButton("Отмена", callback_data="menu"))
    bot.send_message(message.chat.id, "Удалить все выполненные задачи?", reply_markup=kb)

@bot.message_handler(commands=["remind"])
def remind_command(message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.reply_to(message, "Использование: /remind 18:00 Позвонить маме")
        return
    try:
        target_time = datetime.strptime(parts[1], "%H:%M").time()
        now = now_local()
        due = now.replace(hour=target_time.hour, minute=target_time.minute, second=0, microsecond=0)
        if due <= now:
            due += timedelta(days=1)
        rid = add_reminder(message.chat.id, message.from_user.id, parts[2], due)
        bot.reply_to(message, f"⏰ Напоминание #{rid} установлено на {due.strftime('%d.%m.%Y %H:%M')}.")
    except ValueError:
        bot.reply_to(message, "⚠ Время должно быть в формате ЧЧ:ММ.")

@bot.message_handler(commands=["remind_in"])
def remind_in_command(message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3 or not parts[1].isdigit():
        bot.reply_to(message, "Использование: /remind_in 15 Позвонить маме")
        return
    minutes = int(parts[1])
    if not 1 <= minutes <= 525600:
        bot.reply_to(message, "Укажите количество минут от 1 до 525600.")
        return
    due = now_local() + timedelta(minutes=minutes)
    rid = add_reminder(message.chat.id, message.from_user.id, parts[2], due)
    bot.reply_to(message, f"⏰ Напоминание #{rid} установлено на {due.strftime('%d.%m.%Y %H:%M')}.")

@bot.message_handler(commands=["timer"])
def timer_command(message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].isdigit():
        bot.reply_to(message, "Использование: /timer 60")
        return
    seconds = int(parts[1])
    if not 1 <= seconds <= 86400:
        bot.reply_to(message, "Таймер должен быть от 1 до 86400 секунд.")
        return
    bot.reply_to(message, f"⏳ Таймер установлен на {seconds} сек.")
    def timer_job():
        time.sleep(seconds)
        try:
            bot.send_message(message.chat.id, "⏰ Время вышло!")
        except Exception:
            pass
    threading.Thread(target=timer_job, daemon=True).start()

@bot.message_handler(commands=["weather"])
def weather_command(message):
    city = message.text.partition(" ")[2].strip()
    if not city:
        bot.reply_to(message, "Использование: /weather Москва")
        return
    bot.reply_to(message, weather(city))

@bot.message_handler(commands=["currency"])
def currency_command(message):
    code = message.text.partition(" ")[2].strip()
    if not code:
        bot.reply_to(message, "Использование: /currency EUR")
        return
    bot.reply_to(message, currency(code))

@bot.message_handler(commands=["reset"])
def reset_command(message):
    count = history_clear(message.from_user.id, message.chat.id)
    bot.reply_to(message, f"🧠 Контекст этого чата очищен. Удалено сообщений: {count}.")
