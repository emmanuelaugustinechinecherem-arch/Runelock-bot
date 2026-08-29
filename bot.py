import asyncio
import os
import google.generativeai as genai
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# Initialize Gemini API
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-3.6-flash")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    # 1. Send "typing..." status to Telegram so the user knows it's working
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action="typing"
    )

    try:
        # 2. Run model generation in a background thread to prevent blocking/timeouts
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None, lambda: model.generate_content(user_text)
        )

        # 3. Handle empty/blocked safety filter responses
        if not response or not response.text:
            await update.message.reply_text(
                "I couldn't generate a response for this prompt due to safety filters."
            )
            return

        full_text = response.text

        # 4. Split long responses into chunks under Telegram's 4096-character limit
        chunk_size = 4000
        for i in range(0, len(full_text), chunk_size):
            await update.message.reply_text(full_text[i : i + chunk_size])

    except Exception as e:
        print(f"Error during generation: {e}")
        await update.message.reply_text(
            "Sorry, I encountered an error processing your request."
        )


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()

    app.add_handler(
        MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    )

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
    
