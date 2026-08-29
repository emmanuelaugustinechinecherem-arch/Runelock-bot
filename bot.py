import os
import telebot
import google.generativeai as genai

# Fetch environment variables configured on Render
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN") or os.environ.get("BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Initialize Telegram Bot
bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "👋 **RUNELOCK Bot is online!** Send me any question or prompt to chat.")

@bot.message_handler(func=lambda message: True)
def chat_with_gemini(message):
    # Send typing action indicator in Telegram
    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        response = model.generate_content(message.text)
        
        # Check if Gemini returned valid text content
        if response and hasattr(response, 'text') and response.text:
            text = response.text
            # Telegram character limit is 4096 characters per message
            if len(text) > 4000:
                for i in range(0, len(text), 4000):
                    bot.reply_to(message, text[i:i+4000])
            else:
                bot.reply_to(message, text)
        else:
            bot.reply_to(message, "⚠️ Gemini blocked or returned an empty response for that prompt. Try rephrasing.")
            
    except Exception as e:
        print(f"Error handling request: {e}")
        bot.reply_to(message, "❌ An error occurred while contacting Gemini. Please try again.")

if __name__ == "__main__":
    print("RUNELOCK Bot is polling for messages...")
    bot.infinity_polling()
