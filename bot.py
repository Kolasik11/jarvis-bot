import os
import telebot, sqlite3, re, threading, time, requests, random
from datetime import datetime
from telebot import types

TOKEN = os.environ.get("NOT_TOOWN", "")
bot = telebot.TeleBot(TOKEN)
BN = "J.A.R.V.I.S."
sec_mode = False
prot = False
MY_ID = None

BAD = ['хуй','хуя','хуе','пизд','бля','блять','ебал','ебат','заеб','нахуй','мудак','говно','сука','тварь','пидор','шлюха']

QA = {
'привет':['Здравствуйте!','Приветствую!'],
'как дела':['Всё отлично!','Работаю штатно!'],
'как ты':['В порядке!','Готов к работе!'],
'как жизнь':['Прекрасна!'],
'как настроение':['Отличное!'],
'как здоровье':['В норме!'],
'как серафимушка':['Серафимушка в порядке!','Всё хорошо!'],
'как серафима':['Серафима в порядке!'],
'как григорий':['Григорий в порядке!'],
'как гриша':['Гриша в порядке!'],
'серафимушка':['Прекрасный человек!'],
'григорий':['Надёжный человек!'],
'кто ты':['Я J.A.R.V.I.S.!'],
'что ты умеешь':['Задачи, заметки, слежу за чатами!'],
'спасибо':['Пожалуйста!','Рад помочь!'],
'пока':['До свидания!'],
'до свидания':['Всего доброго!'],
'ты крутой':['Спасибо!'],
'ты лучший':['Благодарю!'],
'извини':['Ничего страшного!'],
'что поесть':['Что-нибудь вкусное!'],
'я голоден':['Подкрепитесь!'],
'я устал':['Отдохните!'],
'хочу спать':['Сон важен!'],
'мне скучно':['Чем займёмся?'],
'мне грустно':['Всё будет хорошо!'],
'расскажи анекдот':['Почему программисты путают Хэллоуин и Рождество? Oct 31 == Dec 25!'],
'пошути':['Почему бот не пошёл в бар? Не было бар-кода!'],
'что такое любовь':['Прекрасное чувство!'],
'удачи':['И вам удачи!'],
'помоги':['Чем помочь?'],
'я тебя люблю':['Я вас тоже!'],
'ты мой друг':['Всегда рядом!'],
'я скучал':['Я тоже!'],
}

def ans(t):
    tl = t.lower().strip()
    for k, v in QA.items():
        if k in tl:
            return random.choice(v)
    return None

def db():
    conn = sqlite3.connect('jarvis.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS t (id INTEGER PRIMARY KEY, text TEXT, date TEXT, done INTEGER)')
    c.execute('CREATE TABLE IF NOT EXISTS n (id INTEGER PRIMARY KEY, text TEXT, date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS l (id INTEGER PRIMARY KEY, uid TEXT, un TEXT, fn TEXT, text TEXT, date TEXT, st INTEGER, cid TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS r (id INTEGER PRIMARY KEY, cid TEXT, uid TEXT, text TEXT, rt TEXT, done INTEGER)')
    c.execute('CREATE TABLE IF NOT EXISTS g (cid TEXT PRIMARY KEY, cn TEXT)')
    conn.commit()
    conn.close()

def smsg(uid, un, fn, txt, st=0, cid=None):
    conn = sqlite3.connect('jarvis.db')
    c = conn.cursor()
    c.execute("INSERT INTO l VALUES (NULL,?,?,?,?,?,?,?)", (str(uid), un or "нет", fn or "нет", txt or "стикер", datetime.now().strftime("%d.%m %H:%M"), st, str(cid) if cid else None))
    conn.commit()
    conn.close()

def atask(t):
    conn = sqlite3.connect('jarvis.db')
    c = conn.cursor()
    c.execute("INSERT INTO t (text,date,done) VALUES (?,?,0)", (t, datetime.now().strftime("%d.%m %H:%M")))
    conn.commit()
    conn.close()

def gtasks():
    conn = sqlite3.connect('jarvis.db')
    c = conn.cursor()
    c.execute("SELECT id,text FROM t WHERE done=0 ORDER BY id")
    r = c.fetchall()
    conn.close()
    return r

def cntt():
    conn = sqlite3.connect('jarvis.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM t WHERE done=0")
    n = c.fetchone()[0]
    conn.close()
    return n

def dtask(i):
    conn = sqlite3.connect('jarvis.db')
    c = conn.cursor()
    c.execute("UPDATE t SET done=1 WHERE id=?", (i,))
    a = c.rowcount
    conn.commit()
    conn.close()
    return a > 0

def delt(i):
    conn = sqlite3.connect('jarvis.db')
    c = conn.cursor()
    c.execute("DELETE FROM t WHERE id=?", (i,))
    a = c.rowcount
    conn.commit()
    conn.close()
    return a > 0

def clrt():
    conn = sqlite3.connect('jarvis.db')
    c = conn.cursor()
    c.execute("DELETE FROM t WHERE done=1")
    n = c.rowcount
    conn.commit()
    conn.close()
    return n

def anote(t):
    conn = sqlite3.connect('jarvis.db')
    c = conn.cursor()
    c.execute("INSERT INTO n (text,date) VALUES (?,?)", (t, datetime.now().strftime("%d.%m %H:%M")))
    conn.commit()
    conn.close()

def gnotes():
    conn = sqlite3.connect('jarvis.db')
    c = conn.cursor()
    c.execute("SELECT id,text,date FROM n ORDER BY id")
    r = c.fetchall()
    conn.close()
    return r

def deln(i):
    conn = sqlite3.connect('jarvis.db')
    c = conn.cursor()
    c.execute("DELETE FROM n WHERE id=?", (i,))
    a = c.rowcount
    conn.commit()
    conn.close()
    return a > 0

def clrn():
    conn = sqlite3.connect('jarvis.db')
    c = conn.cursor()
    c.execute("DELETE FROM n")
    n = c.rowcount
    conn.commit()
    conn.close()
    return n

def arem(cid, uid, t, rt):
    conn = sqlite3.connect('jarvis.db')
    c = conn.cursor()
    c.execute("INSERT INTO r (cid,uid,text,rt,done) VALUES (?,?,?,?,0)", (str(cid), str(uid), t, rt))
    conn.commit()
    conn.close()

def grems():
    conn = sqlite3.connect('jarvis.db')
    c = conn.cursor()
    c.execute("SELECT id,cid,text,rt FROM r WHERE done=0")
    r = c.fetchall()
    conn.close()
    return r

def drem(i):
    conn = sqlite3.connect('jarvis.db')
    c = conn.cursor()
    c.execute("UPDATE r SET done=1 WHERE id=?", (i,))
    conn.commit()
    conn.close()

def sgrp(cid, cn):
    conn = sqlite3.connect('jarvis.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO g VALUES (?,?)", (str(cid), cn))
    conn.commit()
    conn.close()

def ggrp():
    conn = sqlite3.connect('jarvis.db')
    c = conn.cursor()
    c.execute("SELECT cid,cn FROM g LIMIT 1")
    r = c.fetchone()
    conn.close()
    return r

def cstats(cid):
    conn = sqlite3.connect('jarvis.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM l WHERE cid=?", (str(cid),))
    t = c.fetchone()[0]
    c.execute("SELECT un,COUNT(*) FROM l WHERE cid=? GROUP BY uid ORDER BY COUNT(*) DESC", (str(cid),))
    u = c.fetchall()
    conn.close()
    return t, u

def wthr(city):
    try:
        r = requests.get("https://wttr.in/" + city + "?format=%C+%t+%w", timeout=10)
        return "🌤 " + city + ": " + r.text if r.status_code == 200 else "⚠ Ошибка"
    except:
        return "⚠ Ошибка сети"

def curr(cur):
    try:
        r = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=10)
        if r.status_code == 200:
            d = r.json()
            if cur.upper() in d['rates']:
                return "💵 1 USD = " + str(d['rates'][cur.upper()]) + " " + cur.upper()
        return "⚠ Не найдено"
    except:
        return "⚠ Ошибка сети"

def rcheck():
    while True:
        try:
            now = datetime.now().strftime("%d.%m %H:%M")
            for i, cid, t, rt in grems():
                if rt == now:
                    try:
                        bot.send_message(cid, "🔔 НАПОМИНАНИЕ!\n\n" + t)
                        drem(i)
                    except:
                        pass
            time.sleep(30)
        except:
            time.sleep(30)

def menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("📝 Заметки", callback_data="n"),
           types.InlineKeyboardButton("📋 Задачи", callback_data="t"))
    kb.add(types.InlineKeyboardButton("🛡️ Слежка", callback_data="p"),
           types.InlineKeyboardButton("📊 Анализ", callback_data="a"))
    kb.add(types.InlineKeyboardButton("⏰ Напоминания", callback_data="r"),
           types.InlineKeyboardButton("🌤 Полезное", callback_data="u"))
    kb.add(types.InlineKeyboardButton("🤖 Секретарь", callback_data="s"),
           types.InlineKeyboardButton("❓ Помощь", callback_data="h"))
    return kb

def back():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="m"))
    return kb

@bot.message_handler(commands=['start', 'menu'])
def st(m):
    global MY_ID
    if MY_ID is None:
        MY_ID = m.chat.id
    bot.send_message(m.chat.id, "🤖 *J.A.R.V.I.S.* — главное меню\n\nВыберите раздел:", parse_mode='Markdown', reply_markup=menu())

@bot.callback_query_handler(func=lambda call: True)
def cb(call):
    global sec_mode, prot
    d = call.data
    cid = call.message.chat.id
    mid = call.message.message_id
    if d == "m":
        bot.edit_message_text("🤖 *J.A.R.V.I.S.* — главное меню\n\nВыберите раздел:", cid, mid, parse_mode='Markdown', reply_markup=menu())
    elif d == "n":
        t = "📝 *ЗАМЕТКИ*\n\n• /note [текст] — создать\n• /notes — все заметки\n• /delnote N — удалить\n• /clearnotes — удалить все\n\n📊 Всего: " + str(len(gnotes()))
        bot.edit_message_text(t, cid, mid, parse_mode='Markdown', reply_markup=back())
    elif d == "t":
        t = "📋 *ЗАДАЧИ*\n\n• /add [текст] — добавить\n• /list — список\n• /done N — выполнить\n• /delete N — удалить\n• /clear — очистить\n\n📊 Активных: " + str(cntt())
        bot.edit_message_text(t, cid, mid, parse_mode='Markdown', reply_markup=back())
    elif d == "p":
        g = ggrp()
        s = "🔒 ВКЛ" if prot else "🔓 ВЫКЛ"
        t = "🛡️ *СЛЕЖКА ЗА ЧАТАМИ*\n\n• /setgroup — установить группу\n• /protect — активировать\n• /check — диагностика\n• /report 1313 — отчёт\n\n"
        if g:
            t += "📌 Группа: *" + g[1] + "*\n📌 Защита: " + s + "\n🔑 Отключить: 1717"
        else:
            t += "⚠ Группа не установлена"
        bot.edit_message_text(t, cid, mid, parse_mode='Markdown', reply_markup=back())
    elif d == "a":
        t = "📊 *АНАЛИЗ*\n\n📋 Задачи: *" + str(cntt()) + "*\n📝 Заметки: *" + str(len(gnotes())) + "*\n💬 Вопросов: *" + str(len(QA)) + "*\n🛡️ Защита: " + ("🔒 ВКЛ" if prot else "🔓 ВЫКЛ") + "\n🤖 Секретарь: " + ("✅ ВКЛ" if sec_mode else "❌ ВЫКЛ")
        bot.edit_message_text(t, cid, mid, parse_mode='Markdown', reply_markup=back())
    elif d == "r":
        t = "⏰ *НАПОМИНАНИЯ*\n\n• /remind 15:30 Текст\n• /timer [сек]\n\n📌 Пример:\n`/remind 18:00 Позвонить маме`"
        bot.edit_message_text(t, cid, mid, parse_mode='Markdown', reply_markup=back())
    elif d == "u":
        t = "🌤 *ПОЛЕЗНОЕ*\n\n• /weather [город] — погода\n• /currency [USD] — курс\n• /timer [сек] — таймер\n\n📌 Примеры:\n`/weather Москва`\n`/currency USD`"
        bot.edit_message_text(t, cid, mid, parse_mode='Markdown', reply_markup=back())
    elif d == "s":
        sec_mode = not sec_mode
        t = "🤖 *СЕКРЕТАРЬ*\n\nСтатус: *" + ("✅ ВКЛ" if sec_mode else "❌ ВЫКЛ") + "*\n\nОтвечает на вопросы автоматически."
        bot.edit_message_text(t, cid, mid, parse_mode='Markdown', reply_markup=back())
    elif d == "h":
        t = "❓ *ПОМОЩЬ*\n\n💬 *Спросите меня:*\n• «Как дела?»\n• «Как Серафимушка?»\n• «Как Григорий?»\n• «Расскажи анекдот»\n\n📌 Разделы: Заметки, Задачи, Слежка, Анализ, Напоминания, Полезное"
        bot.edit_message_text(t, cid, mid, parse_mode='Markdown', reply_markup=back())
    bot.answer_callback_query(call.id)

@bot.message_handler(commands=['help'])
def hlp(m):
    bot.reply_to(m, "📖 *ПОМОЩЬ*\n\n📝 /note /notes /delnote /clearnotes\n📋 /add /list /done /delete /clear\n⏰ /remind /timer\n🌤 /weather /currency\n🛡️ /setgroup /protect /check /report 1313\n🤖 /secretary /analysis /menu", parse_mode='Markdown')

@bot.message_handler(commands=['note'])
def nc(m):
    t = m.text.replace('/note','',1).strip()
    if t:
        anote(t)
        bot.reply_to(m, "📝 Сохранено: «" + t + "»")
    else:
        bot.reply_to(m, "⚠ /note Купить молоко")

@bot.message_handler(commands=['notes'])
def nsc(m):
    n = gnotes()
    if n:
        r = "📋 *Заметки:*\n\n"
        for i, t, d in n:
            r += "  " + str(i) + ". [" + d + "] " + t + "\n"
        bot.reply_to(m, r, parse_mode='Markdown')
    else:
        bot.reply_to(m, "📭 Нет заметок")

@bot.message_handler(commands=['delnote'])
def dnc(m):
    p = m.text.split()
    if len(p) < 2:
        bot.reply_to(m, "⚠ /delnote 3")
        return
    try:
        bot.reply_to(m, "🗑 Удалено" if deln(int(p[1])) else "⚠ Не найдено")
    except:
        bot.reply_to(m, "⚠ Введите число")

@bot.message_handler(commands=['clearnotes'])
def cnc(m):
    bot.reply_to(m, "🧹 Удалено " + str(clrn()))

@bot.message_handler(commands=['add'])
def ac(m):
    t = m.text.replace('/add','',1).strip()
    if t:
        atask(t)
        bot.reply_to(m, "🗂 Добавлено: «" + t + "»")
    else:
        bot.reply_to(m, "⚠ /add Купить хлеб")

@bot.message_handler(commands=['list'])
def lc(m):
    ts = gtasks()
    if ts:
        r = "📋 *Задачи:*\n\n"
        for i, t in ts:
            r += "  " + str(i) + ". " + t + "\n"
        bot.reply_to(m, r, parse_mode='Markdown')
    else:
        bot.reply_to(m, "🎉 Все выполнено!")

@bot.message_handler(commands=['done'])
def dc(m):
    p = m.text.split()
    if len(p) < 2:
        bot.reply_to(m, "⚠ /done 3")
        return
    try:
        bot.reply_to(m, "✔ Выполнено" if dtask(int(p[1])) else "⚠ Не найдено")
    except:
        bot.reply_to(m, "⚠ Введите число")

@bot.message_handler(commands=['delete'])
def dlc(m):
    p = m.text.split()
    if len(p) < 2:
        bot.reply_to(m, "⚠ /delete 3")
        return
    try:
        bot.reply_to(m, "🗑 Удалено" if delt(int(p[1])) else "⚠ Не найдено")
    except:
        bot.reply_to(m, "⚠ Введите число")

@bot.message_handler(commands=['clear'])
def cc(m):
    bot.reply_to(m, "🧹 Удалено " + str(clrt()))

@bot.message_handler(commands=['remind'])
def rc(m):
    p = m.text.split(maxsplit=2)
    if len(p) < 3:
        bot.reply_to(m, "⚠ /remind 15:30 Текст")
        return
    try:
        datetime.strptime(p[1], "%H:%M")
        rt = datetime.now().strftime('%d.%m') + " " + p[1]
        arem(m.chat.id, m.from_user.id, p[2], rt)
        bot.reply_to(m, "⏰ На " + rt + ": " + p[2])
    except:
        bot.reply_to(m, "⚠ Формат ЧЧ:ММ")

@bot.message_handler(commands=['weather'])
def wc(m):
    p = m.text.split()
    if len(p) < 2:
        bot.reply_to(m, "⚠ /weather Москва")
        return
    bot.reply_to(m, wthr(p[1]))

@bot.message_handler(commands=['currency'])
def crc(m):
    p = m.text.split()
    if len(p) < 2:
        bot.reply_to(m, "⚠ /currency USD")
        return
    bot.reply_to(m, curr(p[1]))

@bot.message_handler(commands=['timer'])
def tc(m):
    p = m.text.split()
    if len(p) < 2:
        bot.reply_to(m, "⚠ /timer 10")
        return
    try:
        s = int(p[1])
        bot.reply_to(m, "⏳ Таймер на " + str(s) + " сек")
        def c2():
            time.sleep(s)
            try:
                bot.send_message(m.chat.id, "⏰ Время вышло!")
            except:
                pass
        threading.Thread(target=c2, daemon=True).start()
    except:
        bot.reply_to(m, "⚠ Введите число")

@bot.message_handler(commands=['secretary'])
def sc(m):
    global sec_mode
    sec_mode = not sec_mode
    bot.reply_to(m, "📋 Секретарь " + ("✅ ВКЛ" if sec_mode else "❌ ВЫКЛ"))

@bot.message_handler(commands=['analysis'])
def anc(m):
    r = "📊 *АНАЛИЗ*\n\n📋 Задачи: " + str(cntt()) + "\n📝 Заметки: " + str(len(gnotes())) + "\n💬 Вопросов: " + str(len(QA)) + "\n🛡️ Защита: " + ("🔒 ВКЛ" if prot else "🔓 ВЫКЛ") + "\n🤖 Секретарь: " + ("✅ ВКЛ" if sec_mode else "❌ ВЫКЛ")
    bot.reply_to(m, r, parse_mode='Markdown')

@bot.message_handler(commands=['setgroup'])
def sgc(m):
    if m.chat.type in ['group', 'supergroup']:
        sgrp(str(m.chat.id), m.chat.title or "Группа")
        bot.reply_to(m, "✅ Группа сохранена\nТеперь /protect")
    else:
        bot.reply_to(m, "⚠ Работает в группе")

@bot.message_handler(commands=['protect'])
def pc(m):
    global prot
    g = ggrp()
    if not g:
        bot.reply_to(m, "⚠ Сначала /setgroup в группе")
        return
    prot = True
    bot.reply_to(m, "🛡️ *ЗАЩИТА ВКЛЮЧЕНА*\n\nГруппа: " + g[1] + "\n\n🔑 Отключить: 1717", parse_mode='Markdown')

@bot.message_handler(commands=['check'])
def chc(m):
    g = ggrp()
    if not g:
        bot.reply_to(m, "⚠ Группа не установлена")
        return
    t, u = cstats(g[0])
    r = "🔍 *ДИАГНОСТИКА*\n\n📌 Группа: " + g[1] + "\n📌 Защита: " + ("🔒 ВКЛ" if prot else "🔓 ВЫКЛ") + "\n📨 Сообщений: " + str(t)
    if u:
        r += "\n\n👥 *Топ:*\n"
        for un, cnt in u[:5]:
            r += "  • @" + (un or 'без un') + ": " + str(cnt) + "\n"
    bot.reply_to(m, r, parse_mode='Markdown')

@bot.message_handler(commands=['report'])
def rpc(m):
    p = m.text.split()
    if len(p) < 2 or p[1] != "1313":
        bot.reply_to(m, "⚠ Неверный пароль")
        return
    g = ggrp()
    if not g:
        bot.reply_to(m, "⚠ Группа не установлена")
        return
    t, u = cstats(g[0])
    bot.reply_to(m, "📋 *ОТЧЁТ*\n\n📌 " + g[1] + "\n📊 Всего: " + str(t) + "\n👥 Пользователей: " + str(len(u)), parse_mode='Markdown')

@bot.message_handler(content_types=['text', 'sticker'])
def allm(m):
    global prot, sec_mode, MY_ID
    if MY_ID is None:
        MY_ID = m.chat.id
    u = m.from_user
    cid = str(m.chat.id) if m.chat else None
    st = 1 if m.sticker else 0
    if m.text and m.text.strip() == "1717" and prot:
        prot = False
        bot.reply_to(m, "✅ Защита отключена")
        return
    txt = m.sticker.emoji if m.sticker else (m.text or "")
    smsg(u.id, u.username, u.first_name, txt, st, cid)
    if prot:
        g = ggrp()
        if g and str(cid) == g[0]:
            if not st and txt:
                bad = [w for w in BAD if w in txt.lower()]
                if bad:
                    try:
                        bot.send_message(MY_ID, "🔞 МАТ!\n@" + (u.username or u.first_name) + ": " + txt)
                    except:
                        pass
    if not st and m.text and not m.text.startswith('/'):
        tl = m.text.lower().strip()
        a = ans(tl)
        if a:
            bot.reply_to(m, BN + ": " + a)
            return
        if sec_mode and '?' in m.text:
            bot.reply_to(m, "📋 Принял запрос")
            return
        if 'добавь' in tl:
            t = re.sub(r'(добавь|запомни)\s*', '', m.text).strip()
            if t and len(t) > 2:
                atask(t)
                bot.reply_to(m, "🗂 Добавлено: «" + t + "»")

if __name__ == "__main__":
    db()
    threading.Thread(target=rcheck, daemon=True).start()
    try:
        bot.remove_webhook()
    except:
        pass
    print("🟢 J.A.R.V.I.S. запущен")
    while True:
        try:
            bot.polling(non_stop=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            print("⚠ " + str(e))
            time.sleep(5)
