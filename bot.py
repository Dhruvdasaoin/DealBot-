import os
import asyncio
import time
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
    """Formats the deal and sends it to the channel. Returns (success_bool, error_str)"""
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
        print(f"Successfully sent deal to {CHANNEL_ID}: {deal['title']}")
        return True, None
    except Exception as e:
        err_msg = str(e)
        print(f"Error sending message to Telegram channel ({CHANNEL_ID}): {err_msg}")
        return False, err_msg

async def fetch_and_post_deals(context: ContextTypes.DEFAULT_TYPE, force_post=False):
    """Job to fetch deals, save to DB, and post new ones. Returns summary tuple."""
    print(f"Running job: fetch_and_post_deals (force={force_post})")
    
    deals = await asyncio.to_thread(get_all_deals)
    
    if not deals:
        print("No real deals found, using mock deals.")
        deals = get_mock_deals()
        if force_post:
            ts = int(time.time())
            for d in deals:
                d['url'] = f"{d['url']}&test_ts={ts}"
    
    deals_posted = 0
    max_deals_to_post = 10
    errors = []
    
    for deal in deals:
        if deals_posted >= max_deals_to_post:
            break
            
        is_new = insert_deal(
            title=deal['title'],
            url=deal['url'],
            original_price=deal['original_price'],
            discount_price=deal['discount_price'],
            discount_percentage=deal['discount_percentage'],
            category=deal['category'],
            source=deal['source']
        )
        
        if is_new or force_post:
            success, err = await format_and_send_deal(context, deal)
            if success:
                deals_posted += 1
                await asyncio.sleep(1)
            else:
                errors.append(err)
                break # stop on error to report
    
    return deals_posted, errors

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Basic command to check if bot is responsive."""
    await update.message.reply_text("Hello! I am DealBot. I monitor deals and post them to the channel.")

async def testpost_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command to manually trigger deal fetching/posting for testing."""
    target_channel = CHANNEL_ID or "NOT SET"
    await update.message.reply_text(f"Triggering deal fetch... Attempting to post to channel: {target_channel}")
    
    posted_count, errors = await fetch_and_post_deals(context, force_post=True)
    
    if posted_count > 0:
        await update.message.reply_text(f"✅ Success! Posted {posted_count} deals to {target_channel}.")
    elif errors:
        await update.message.reply_text(f"❌ Failed to post to channel `{target_channel}`.\n\nError from Telegram: {errors[0]}\n\nPlease check:\n1. Is your channel username correct in Render environment variables?\n2. Is the bot added as an Administrator to that channel?")
    else:
        await update.message.reply_text(f"Finished processing deals. No new deals to post to {target_channel}.")

def create_bot_app():
    """Initializes the bot application"""
    init_db()
    
    if not TOKEN:
        print("WARNING: TELEGRAM_BOT_TOKEN not set in environment.")
        return None
        
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("testpost", testpost_command))
    
    job_queue = app.job_queue
    job_queue.run_repeating(fetch_and_post_deals, interval=21600, first=30)
    
    return app

if __name__ == "__main__":
    bot_app = create_bot_app()
    if bot_app:
        print("Starting DealBot polling...")
        bot_app.run_polling(stop_signals=None)
    else:
        print("Failed to start DealBot.")
