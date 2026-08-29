import os
import time
import threading
import telebot
import google.generativeai as genai
from http.server import BaseHTTPRequestHandler, HTTPServer

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    raise SystemExit("Missing TELEGRAM_TOKEN or GEMINI_API_KEY")

def keep_alive():
    port = int(os.environ.get("PORT", 10000))
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"bot ok")
        def log_message(self, *a):
            pass
    print("Web port open on", port)
    HTTPServer(("0.0.0.0", port), H).serve_forever()

threading.Thread(target=keep_alive, daemon=True).start()

genai.configure(api_key=GEMINI_API_KEY)

MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-3.7-flash",
]

bot = telebot.TeleBot(TELEGRAM_TOKEN)

def ask_gemini(text):
    last = None
    for name in MODELS:
        try:
            print("Trying Gemini:", name)
            model = genai.GenerativeModel(name)
            response = model.generate_content(text)
            if response and getattr(response, "text", None):
                print("OK Gemini:", name)
                return response.text
        except Exception as e:
            print("FAIL Gemini:", name, e)
            last = e
    raise last

@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "Bot is online. Send any message.")

@bot.message_handler(func=lambda m: True)
def chat(message):
    waiting = bot.reply_to(message, "Thinking...")
    try:
        reply = ask_gemini(message.text)
        bot.edit_message_text(reply[:4000], waiting.chat.id, waiting.message_id)
    except Exception as e:
        print("AI error:", e)
        bot.edit_message_text("AI error: " + str(e), waiting.chat.id, waiting.message_id)

if __name__ == "__main__":
    bot.remove_webhook()
    time.sleep(2)
    while True:
        try:
            print("Bot polling...")
            bot.infinity_polling(timeout=20, long_polling_timeout=20, skip_pending=True)
        except Exception as e:
            print("Polling error:", e)
            time.sleep(5)
