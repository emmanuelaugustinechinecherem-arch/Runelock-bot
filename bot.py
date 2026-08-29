import os
import threading
import logging
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai

# --- CONFIGURATION ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

GEMINI_MODEL = "gemini-1.5-flash"
PORT = int(os.environ.get("PORT", 10000))

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    raise ValueError("Missing TELEGRAM_TOKEN or GEMINI_API_KEY environment variables.")

# --- LOGGING ---
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- GEMINI CLIENT ---
client = genai.Client(api_key=GEMINI_API_KEY)

# --- FLASK HEALTH CHECK SERVER ---
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "✅ Bot is alive and running 24/7!"

def run_web_server():
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    flask_app.run(host="0.0.0.0", port=PORT)

# --- BOT HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hello! Powered by Gemini. Ask me anything!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    chat_id = update.effective_chat.id
    logger.info(f"Message from {chat_id}: {user_text}")

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=user_text,
            config={
                "system_instruction": "You are a helpful AI assistant."
            }
        )
        reply = response.text
        await update.message.reply_text(reply)
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        await update.message.reply_text("Sorry, I encountered an error processing your request.")

# --- MAIN ENGINE ---
def main():
    thread = threading.Thread(target=run_web_server, daemon=True)
    thread.start()
    logger.info(f"Health check server running on port {PORT}")

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🤖 Bot is running 24/7 on Render...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
          
