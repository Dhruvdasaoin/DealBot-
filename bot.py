import os
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from scraper import get_all_deals, get_mock_deals
from database import insert_deal, init_db

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
AMAZON_AFF = os.getenv("AMAZON_AFFILIATE_ID", "default_amazon_id-21")
FLIPKART_AFF = os.getenv("FLIPKART_AFFILIATE_ID", "default_flipkart_id")

def add_affiliate_tag(url, source):
    """Appends affiliate tag based on source"""
    if 'amazon' in source.lower():
        if '?' in url:
            return f"{url}&tag={AMAZON_AFF}"
        else:
            return f"{url}?tag={AMAZON_AFF}"
    elif 'flipkart' in source.lower():
        if '?' in url:
            return f"{url}&affid={FLIPKART_AFF}"
        else:
            return f"{url}?affid={FLIPKART_AFF}"
    return url

async def format_and_send_deal(context: ContextTypes.DEFAULT_TYPE, deal):
    """Formats the deal and sends it to the channel"""
    affiliate_url = add_affiliate_tag(deal['url'], deal['source'])
    
    message = (
        f"🔥 *{deal['title']}*\n\n"
        f"💰 *Deal Price*: ₹{deal['discount_price']}\n"
        f"❌ *Original Price*: ₹{deal['original_price']}\n"
        f"📉 *Discount*: {deal['discount_percentage']}%\n"
        f"🏷️ *Category*: {deal['category']}\n\n"
        f"🛒 [Buy Now on {deal['source']}]({affiliate_url})"
    )
    
    try:
        await context.bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode='Markdown', disable_web_page_preview=False)
        return True
    except Exception as e:
        print(f"Error sending message to Telegram: {e}")
        return False

async def fetch_and_post_deals(context: ContextTypes.DEFAULT_TYPE):
    """Job to fetch deals, save to DB, and post new ones"""
    print("Running scheduled job: fetch_and_post_deals")
    
    # Try real scraping
    deals = get_all_deals()
    
    # Fallback to mock data if scraping fails entirely (for testing)
    if not deals:
        print("No real deals found (likely blocked), using mock deals for demonstration.")
        deals = get_mock_deals()
    
    # We only want to post the top 5-10 deals.
    deals_posted = 0
    max_deals_to_post = 10
    
    for deal in deals:
        if deals_posted >= max_deals_to_post:
            break
            
        # Try to insert into DB. If it's a new deal, insert_deal returns True.
        is_new = insert_deal(
            title=deal['title'],
            url=deal['url'],
            original_price=deal['original_price'],
            discount_price=deal['discount_price'],
            discount_percentage=deal['discount_percentage'],
            category=deal['category'],
            source=deal['source']
        )
        
        if is_new:
            # Add a slight delay between posts
            success = await format_and_send_deal(context, deal)
            if success:
                deals_posted += 1
                await asyncio.sleep(2) # rate limit prevention

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Basic command to check if bot is responsive."""
    await update.message.reply_text("Hello! I am DealBot. I monitor deals and post them to the channel.")

async def testpost_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command to manually trigger deal fetching/posting for testing."""
    await update.message.reply_text("Triggering deal fetch and post...")
    await fetch_and_post_deals(context)
    await update.message.reply_text("Finished posting deals.")

def create_bot_app():
    """Initializes the bot application but doesn't run it (for sharing event loops)"""
    init_db()
    
    if not TOKEN:
        print("WARNING: TELEGRAM_BOT_TOKEN not set in environment.")
        return None
        
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("testpost", testpost_command))
    
    # Schedule job every 6 hours
    job_queue = app.job_queue
    # 6 hours = 21600 seconds
    job_queue.run_repeating(fetch_and_post_deals, interval=21600, first=10) # first run after 10s
    
    return app

if __name__ == "__main__":
    # If run standalone, start polling
    bot_app = create_bot_app()
    if bot_app:
        print("Starting DealBot polling...")
        bot_app.run_polling(stop_signals=None)
    else:
        print("Failed to start DealBot.")
