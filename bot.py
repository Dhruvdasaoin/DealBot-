import os
import asyncio
import time
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from scraper import get_all_deals, get_mock_deals, all_categories
from database import (
    insert_deal, 
    init_db, 
    save_user_settings, 
    get_user_settings, 
    add_subscriber, 
    is_premium_user
)
from affiliate import get_tracking_url

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
PREMIUM_CHANNEL_ID = os.getenv("PREMIUM_CHANNEL_ID", CHANNEL_ID)
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "https://dealbot-kb4o.onrender.com")

async def format_and_send_deal(context: ContextTypes.DEFAULT_TYPE, deal, target_channel_id=None):
    """Formats the deal and sends it to the channel with tracked click redirect links."""
    channel_id = target_channel_id or CHANNEL_ID
    
    # Use live tracking URL /r/<deal_id>
    if deal.get('id'):
        buy_url = get_tracking_url(deal['id'], RENDER_EXTERNAL_URL)
    else:
        buy_url = deal['url']
        
    message = (
        f"🔥 *{deal['title']}*\n\n"
        f"💰 *Deal Price*: ₹{deal['discount_price']}\n"
        f"❌ *Original Price*: ₹{deal['original_price']}\n"
        f"📉 *Discount*: {deal['discount_percentage']}%\n"
        f"🏷️ *Category*: {deal['category']}\n\n"
        f"🛒 [Buy Now on {deal['source']}]({buy_url})"
    )
    
    try:
        await context.bot.send_message(chat_id=channel_id, text=message, parse_mode='Markdown', disable_web_page_preview=False)
        print(f"Successfully sent deal to {channel_id}: {deal['title']}")
        return True, None
    except Exception as e:
        err_msg = str(e)
        print(f"Error sending message to Telegram channel ({channel_id}): {err_msg}")
        return False, err_msg

async def fetch_and_post_deals(context: ContextTypes.DEFAULT_TYPE, force_post=False):
    """Job to fetch deals across all categories, save to DB, and post with tracking links."""
    print(f"Running job: fetch_and_post_deals (force={force_post})")
    
    deals = await asyncio.to_thread(get_all_deals)
    
    if not deals:
        print("No real deals found, using mock deals across categories.")
        deals = get_mock_deals()
        if force_post:
            ts = int(time.time())
            for d in deals:
                sep = '&' if '?' in d['url'] else '?'
                d['url'] = f"{d['url']}{sep}test_ts={ts}"
    
    deals_posted = 0
    max_deals_to_post = 10
    errors = []
    
    for deal in deals:
        if deals_posted >= max_deals_to_post:
            break
            
        deal_id = insert_deal(
            title=deal['title'],
            url=deal['url'],
            original_price=deal['original_price'],
            discount_price=deal['discount_price'],
            discount_percentage=deal['discount_percentage'],
            category=deal['category'],
            source=deal['source']
        )
        deal['id'] = deal_id
        
        if deal_id or force_post:
            success, err = await format_and_send_deal(context, deal)
            if success:
                deals_posted += 1
                await asyncio.sleep(1)
            else:
                errors.append(err)
                break
    
    return deals_posted, errors

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Basic command greeting and menu."""
    msg = (
        "🤖 *Welcome to DealBot!*\n\n"
        "I monitor e-commerce sites, travel, crypto, and coupon deals 24/7.\n\n"
        "Available Commands:\n"
        "⚙️ `/settings` - Select category preferences\n"
        "⭐ `/subscribe` - Join Premium for real-time alerts & early access\n"
        "⚡ `/testpost` - Trigger an instant deal scan"
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Interactive category preference menu with toggle buttons."""
    user_id = update.effective_user.id
    user_cats = get_user_settings(user_id)
    
    keyboard = []
    for cat in all_categories:
        is_selected = cat in user_cats
        icon = "✅" if is_selected else "❌"
        button_text = f"{icon} {cat}"
        callback_data = f"toggle_{cat}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("⚙️ *Category Preferences*\nTap a category below to toggle alerts:", reply_markup=reply_markup, parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles inline keyboard button toggles for settings."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user_cats = get_user_settings(user_id)
    
    data = query.data
    if data.startswith("toggle_"):
        cat = data.replace("toggle_", "")
        if cat in user_cats:
            user_cats.remove(cat)
        else:
            user_cats.append(cat)
            
        save_user_settings(user_id, user_cats)
        
        keyboard = []
        for c in all_categories:
            is_selected = c in user_cats
            icon = "✅" if is_selected else "❌"
            button_text = f"{icon} {c}"
            callback_data = f"toggle_{c}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_reply_markup(reply_markup=reply_markup)

async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays Premium Subscription benefits and payment link."""
    user_id = update.effective_user.id
    is_prem = is_premium_user(user_id)
    
    status_str = "🌟 *Status: PREMIUM ACTIVE*" if is_prem else "🆓 *Status: FREE TIER*"
    
    msg = (
        f"{status_str}\n\n"
        "⭐ *Upgrade to DealBot Premium ($2/month)* ⭐\n\n"
        "Benefits:\n"
        "⚡ Real-time instant deal alerts\n"
        "🕒 15-minute early access before public channel\n"
        "🎯 Filter alerts by specific price ranges & brands\n"
        "🔒 Exclusive access to Private Deals Channel\n\n"
        "To activate, click below or run `/subscribetest` to try for free!"
    )
    
    checkout_url = f"{RENDER_EXTERNAL_URL}/subscribe_pay?user_id={user_id}"
    keyboard = [[InlineKeyboardButton("💳 Subscribe via Stripe / Razorpay ($2/mo)", url=checkout_url)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode='Markdown')

async def subscribetest_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test command to instantly grant 30-day Premium tier for testing."""
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    
    add_subscriber(user_id=user_id, username=username, days=30)
    await update.message.reply_text(f"🎉 *Success!* Granted 30-day Premium Tier access to {username}!\n\nYou will now receive instant deal alerts.", parse_mode='Markdown')

async def testpost_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command to manually trigger deal fetching/posting for testing."""
    target_channel = CHANNEL_ID or "NOT SET"
    await update.message.reply_text(f"Triggering deal fetch across 7 categories... Attempting to post to channel: {target_channel}")
    
    posted_count, errors = await fetch_and_post_deals(context, force_post=True)
    
    if posted_count > 0:
        await update.message.reply_text(f"✅ Success! Posted {posted_count} deals with click-tracking links to {target_channel}.")
    elif errors:
        await update.message.reply_text(f"❌ Failed to post to channel `{target_channel}`.\n\nError from Telegram: {errors[0]}\n\nPlease verify:\n1. Is your channel username correct in Render environment variables?\n2. Is the bot added as an Administrator in that channel?")
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
    app.add_handler(CommandHandler("settings", settings_command))
    app.add_handler(CommandHandler("subscribe", subscribe_command))
    app.add_handler(CommandHandler("subscribetest", subscribetest_command))
    app.add_handler(CommandHandler("testpost", testpost_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    
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
