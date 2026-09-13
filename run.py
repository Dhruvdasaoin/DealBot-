import threading
import asyncio
import socket
import os
from app import app
from bot import create_bot_app

def is_bot_leader():
    """Ensures only ONE Gunicorn worker process starts the bot thread using a socket lock."""
    try:
        lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Bind to a local port to serve as a process lock
        lock_socket.bind(('127.0.0.1', 14728))
        return lock_socket
    except OSError:
        return None

def run_bot():
    """Runs the telegram bot in a new event loop inside a thread."""
    bot_app = create_bot_app()
    if bot_app:
        print("Starting Telegram Bot (Leader)...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        # Pass stop_signals=None so it doesn't fail in a background thread
        bot_app.run_polling(stop_signals=None)
    else:
        print("Bot failed to start. Is TELEGRAM_BOT_TOKEN set?")

# Only start the bot if this process wins the socket lock
bot_lock = is_bot_leader()
if bot_lock:
    print("Acquired bot lock. Starting Telegram Bot thread...")
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
else:
    print("Bot lock already acquired by another worker. Skipping bot thread in this process.")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
