import os
import logging
from flask import Flask, request
import telebot
import google.generativeai as genai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing!")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is missing!")

bot = telebot.TeleBot(BOT_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-2.5-flash")

@app.route("/")
def home():
    return "Bot is alive!"

@app.route("/telegram-webhook", methods=["POST"])
def webhook():
    if request.headers.get("content-type") == "application/json":
        json_string = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "OK", 200
    return "Unsupported Media Type", 415

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_text = message.text
    logger.info(f"Message from {message.chat.id}: {user_text}")
    try:
        response = model.generate_content(user_text)
        reply = response.text if response.text else "I got no response."
        bot.reply_to(message, reply)
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        bot.reply_to(message, "Sorry, I'm having trouble. Try again!")

def set_webhook():
    if RENDER_URL:
        webhook_url = f"{RENDER_URL}/telegram-webhook"
        bot.remove_webhook()
        bot.set_webhook(url=webhook_url)
        logger.info(f"Webhook set: {webhook_url}")

if __name__ == "__main__":
    set_webhook()
    app.run(host="0.0.0.0", port=10000)
    
