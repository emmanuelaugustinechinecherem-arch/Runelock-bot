import os
import logging
from flask import Flask, request
import telebot
import google.generativeai as genai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://runelock-bot.onrender.com")
PORT = int(os.environ.get("PORT", 10000))

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
bot = telebot.TeleBot(BOT_TOKEN)

app = Flask(__name__)

@app.route('/')
def health():
    return "bot ok", 200

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🤖 Runelock Bot is online!\nPowered by Gemini AI. Send me anything!")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    bot.send_chat_action(message.chat.id, "typing")
    try:
        response = model.generate_content(
            message.text,
            generation_config=genai.types.GenerationConfig(max_output_tokens=500, temperature=0.7)
        )
        reply = response.text if response.text else "I couldn't generate a response."
        bot.reply_to(message, reply)
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        bot.reply_to(message, "⚠️ Sorry, I'm having trouble right now. Try again!")

@app.route('/telegram-webhook', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

def setup_webhook():
    webhook_url = f"{RENDER_URL}/telegram-webhook"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    logger.info(f"Webhook set: {webhook_url}")

if __name__ == '__main__':
    setup_webhook()
    app.run(host='0.0.0.0', port=PORT)
    
