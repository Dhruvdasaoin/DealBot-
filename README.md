# DealBot

A Telegram bot that scrapes e-commerce sites (Amazon India, Flipkart) for deals and posts them to a Telegram channel every 6 hours, alongside a Flask-based web dashboard.

## Setup Instructions

1. **Clone the repository** (or navigate to this directory).
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure Environment**:
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Get a Telegram Bot Token from [BotFather](https://t.me/botfather).
   - Create a Telegram Channel, add the bot as an administrator.
   - Fill in `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHANNEL_ID`, and your affiliate IDs in `.env`.

## Running Locally

To run both the Telegram bot (scheduler) and the Flask dashboard:

```bash
python run.py
```

The dashboard will be available at `http://localhost:5000`.

## Deployment to Render / Railway (Free Tier)

1. Push your code to a GitHub repository.
2. Link the repository to your Render or Railway account.
3. Configure the environment variables (from `.env`) in the deployment settings.
4. Set the Start Command to:
   ```bash
   gunicorn -b 0.0.0.0:$PORT run:app
   ```
   *(Note: This uses `gunicorn` for the web server, which will also start the bot scheduler in a background thread).*
5. **Keep Awake**: Free tiers usually sleep after 15 minutes of inactivity. To ensure the bot scrapes every 6 hours, you can use a free service like [cron-job.org](https://cron-job.org/) to ping your web service URL every 10 minutes.
