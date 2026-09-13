import threading
import asyncio
from app import app
from bot import create_bot_app
import os

def run_bot():
    """Runs the telegram bot in a new event loop inside a thread."""
    bot_app = create_bot_app()
    if bot_app:
        print("Starting Telegram Bot...")
        # create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Start polling (this is blocking, so it stays in this thread)
        bot_app.run_polling()
    else:
        print("Bot failed to start. Is TELEGRAM_BOT_TOKEN set?")

# Start the bot thread when this module is loaded
# This ensures it runs whether started via `python run.py` or `gunicorn run:app`
bot_thread = threading.Thread(target=run_bot, daemon=True)
bot_thread.start()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
