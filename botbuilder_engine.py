import asyncio
import time
import requests
from database import get_all_user_bots, update_bot_last_run
from scraper import get_mock_deals

def run_single_user_bot(bot):
    """Executes a single user-created bot configuration synchronously"""
    bot_id = bot['id']
    bot_name = bot['bot_name']
    bot_token = bot['bot_token']
    channel_id = bot['channel_id']
    source_type = bot['source_type']
    
    print(f"[BotBuilder Engine] Executing bot: {bot_name} (ID: {bot_id}) -> Channel: {channel_id}")
    
    # Select deals based on source type
    deals = get_mock_deals()
    if source_type != 'E-commerce Deals':
        deals = [d for d in deals if d['category'].lower() in source_type.lower() or source_type.lower() in d['category'].lower()] or deals
        
    posted = 0
    for d in deals[:3]: # post up to 3 deals per run
        msg = (
            f"🤖 *[{bot_name}] Alert*\n\n"
            f"🔥 *{d['title']}*\n"
            f"💰 *Price*: ₹{d['discount_price']} (Original: ₹{d['original_price']})\n"
            f"📉 *Discount*: {d['discount_percentage']}%\n\n"
            f"🛒 [View Deal on {d['source']}]({d['url']})"
        )
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': channel_id,
            'text': msg,
            'parse_mode': 'Markdown',
            'disable_web_page_preview': False
        }
        
        try:
            res = requests.post(url, json=payload, timeout=10)
            if res.status_code == 200:
                posted += 1
            else:
                print(f"[BotBuilder Engine] Error sending message for {bot_name}: {res.text}")
        except Exception as e:
            print(f"[BotBuilder Engine] Request failed for {bot_name}: {e}")
            
    update_bot_last_run(bot_id)
    print(f"[BotBuilder Engine] Finished running {bot_name}. Posted {posted} messages.")

def run_all_active_user_bots():
    """Fetches all active user bots from database and executes them"""
    bots = get_all_user_bots()
    active_bots = [b for b in bots if b['status'] == 'active']
    print(f"[BotBuilder Engine] Found {len(active_bots)} active user bots to run.")
    
    for bot in active_bots:
        try:
            run_single_user_bot(bot)
        except Exception as e:
            print(f"[BotBuilder Engine] Failed to execute bot {bot['bot_name']}: {e}")

if __name__ == "__main__":
    print("Testing BotBuilder Dynamic Orchestrator...")
    run_all_active_user_bots()
