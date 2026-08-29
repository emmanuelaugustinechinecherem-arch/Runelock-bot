import os
import logging
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, filters, CallbackContext
import google.generativeai as genai

# ========== LOGGING ==========
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== CONFIG ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://runelock-bot.onrender.com")
PORT = int(os.environ.get("PORT", 10000))

# ========== GEMINI AI SETUP ==========
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# ========== TELEGRAM SETUP ==========
bot = Bot(token=BOT_TOKEN)
dispatcher = Dispatcher(bot, None, workers=4)

# ========== FLASK APP ==========
app = Flask(__name__)

@app.route('/')
def health():
    """Fast response for cron-job.org to keep Render alive"""
    return "bot ok", 200

# ========== BOT COMMANDS ==========
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "🤖 *Runelock Bot* is online!\nPowered by Gemini AI. Send me anything!",
        parse_mode="Markdown"
    )

def handle_message(update: Update, context: CallbackContext):
    user_text = update.message.text
    bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        response = model.generate_content(
            user_text,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=500,
                temperature=0.7,
            )
        )
        reply = response.text if response.text else "I couldn't generate a response."
        update.message.reply_text(reply)
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        update.message.reply_text("⚠️ Sorry, I'm having trouble thinking right now. Try again!")

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# ========== WEBHOOK ENDPOINT ==========
@app.route('/telegram-webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "OK", 200

# ========== SET WEBHOOK ON STARTUP ==========
def setup_webhook():
    webhook_url = f"{RENDER_URL}/telegram-webhook"
    bot.set_webhook(webhook_url)
    logger.info(f"Webhook set: {webhook_url}")

# ========== RUN ==========
if __name__ == '__main__':
    setup_webhook()
    app.run(host='0.0.0.0', port=PORT)
    
