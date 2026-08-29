import asyncio
import logging
import os
import threading
from flask import Flask
from google import genai
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# --- CONFIGURATION ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.5-flash"
PORT = int(os.environ.get("PORT", 10000))

# --- LOGGING ---
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)

# --- FLASK APP (Keeps Render Web Service Active) ---
app_flask = Flask(__name__)


@app_flask.route("/")
def home():
    return "Rune Bot is active!"


def run_flask():
    app_flask.run(host="0.0.0.0", port=PORT)


# --- GEMINI CLIENT ---
client = genai.Client(api_key=GEMINI_API_KEY)


# --- TELEGRAM HANDLER ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_text = update.message.text
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action="typing"
    )

    try:
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.models.generate_content(
                model=GEMINI_MODEL, contents=user_text
            ),
        )

        if not response or not response.text:
            await update.message.reply_text(
                "I couldn't generate a response for this prompt due to safety filters."
            )
            return

        full_text = response.text

        chunk_size = 4000
        for i in range(0, len(full_text), chunk_size):
            await update.message.reply_text(full_text[i : i + chunk_size])

    except Exception as e:
        logging.error(f"Error during generation: {e}")
        await update.message.reply_text(
            "Sorry, I encountered an error processing your request."
        )


def main():
    if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
        raise ValueError("Missing TELEGRAM_TOKEN or GEMINI_API_KEY!")

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    tg_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    tg_app.add_handler(
        MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    )

    logging.info("Starting Telegram Bot...")
    tg_app.run_polling()


if __name__ == "__main__":
    main()
    
