import telebot
import os

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
print("Токен прочитан. Длина:", len(TOKEN) if TOKEN else 0)

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Я работаю!")

print("Бот запускается...")
bot.infinity_polling()
