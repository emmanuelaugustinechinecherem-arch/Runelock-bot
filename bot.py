import os
import time
import telebot
import google.generativeai as genai

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    raise SystemExit("Missing TELEGRAM_TOKEN or GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-3.7-flash")

bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode="Markdown")

@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "Bot is online. Send any message.")

@bot.message_handler(func=lambda m: True)
def chat(message):
    bot.send_chat_action(message.chat.id, "typing")
    try:
        response = model.generate_content(message.text)
        text = response.text if response and getattr(response, "text", None) else "No reply."
        if len(text) > 4000:
            for i in range(0, len(text), 4000):
                bot.reply_to(message, text[i:i+4000])
        else:
            bot.reply_to(message, text)
    except Exception as e:
        print("AI error:", e)
        bot.reply_to(message, "AI error: " + str(e))

if __name__ == "__main__":
    bot.remove_webhook()
    time.sleep(2)
    while True:
        try:
            print("Bot polling...")
            bot.infinity_polling(timeout=60, long_polling_timeout=60, skip_pending=True)
        except Exception as e:
            print("Conflict or error:", e)
            print("Retrying in 5 seconds...")
            time.sleep(5)
