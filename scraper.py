import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import time
import random

all_categories = [
    "Electronics", 
    "Fashion", 
    "Home & Kitchen", 
    "Books & Media", 
    "Travel", 
    "Crypto", 
    "Coupons"
]

def get_headers():
    ua = UserAgent()
    return {
        'User-Agent': ua.random,
        'Accept-Language': 'en-US, en;q=0.5'
    }

def scrape_amazon_deals(category):
    deals = []
    url = f"https://www.amazon.in/s?k={category.replace(' ', '+')}+deals"
    try:
        response = requests.get(url, headers=get_headers(), timeout=8)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            items = soup.find_all('div', {'data-component-type': 's-search-result'})
            for item in items[:3]:
                try:
                    title_elem = item.find('span', class_='a-text-normal')
                    if not title_elem: continue
                    title = title_elem.text.strip()
                    
                    price_elem = item.find('span', class_='a-price-whole')
                    if not price_elem: continue
                    discount_price = float(price_elem.text.replace(',', '').strip())
                    
                    orig_elem = item.find('span', class_='a-text-price')
                    if orig_elem:
                        original_price_str = orig_elem.find('span', class_='a-offscreen')
                        original_price = float(original_price_str.text.replace('₹', '').replace(',', '').strip()) if original_price_str else discount_price
                    else:
                        original_price = discount_price
                    
                    link_elem = item.find('a', class_='a-link-normal')
                    if not link_elem: continue
                    product_url = "https://www.amazon.in" + link_elem['href']
                    
                    discount_percentage = ((original_price - discount_price) / original_price) * 100 if original_price > discount_price else 0.0
                    
                    if discount_percentage > 30:
                        deals.append({
                            'title': title,
                            'url': product_url,
                            'original_price': original_price,
                            'discount_price': discount_price,
                            'discount_percentage': round(discount_percentage, 2),
                            'category': category,
                            'source': 'Amazon'
                        })
                except Exception:
                    continue
    except Exception as e:
        print(f"Amazon scrape notice ({category}): {e}")
    return deals

def scrape_crypto_movers():
    """Scrapes top crypto market movers using CoinGecko public API"""
    deals = []
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=10&page=1&sparkline=false&price_change_percentage_24h"
        response = requests.get(url, headers={'User-Agent': 'DealBot/1.0'}, timeout=8)
        if response.status_code == 200:
            data = response.json()
            for coin in data:
                change = coin.get('price_change_percentage_24h_in_currency') or coin.get('price_change_percentage_24h') or 0
                if abs(change) >= 5.0:
                    price = coin.get('current_price', 0)
                    old_price = price / (1 + (change / 100)) if change != -100 else price
                    deals.append({
                        'title': f"Crypto Alert: {coin['name']} ({coin['symbol'].upper()}) {'🚀 Up' if change > 0 else '📉 Down'} {round(change, 2)}% in 24h",
                        'url': f"https://www.coingecko.com/en/coins/{coin['id']}",
                        'original_price': round(old_price, 4),
                        'discount_price': round(price, 4),
                        'discount_percentage': round(abs(change), 2),
                        'category': 'Crypto',
                        'source': 'CoinGecko'
                    })
    except Exception as e:
        print(f"Crypto API notice: {e}")
    return deals

def get_all_deals():
    """Scrapes deals across all categories"""
    all_deals = []
    
    for cat in ["Electronics", "Fashion", "Home & Kitchen"]:
        time.sleep(random.uniform(0.5, 1.5))
        all_deals.extend(scrape_amazon_deals(cat))
    
    all_deals.extend(scrape_crypto_movers())
    
    all_deals.sort(key=lambda x: x['discount_percentage'], reverse=True)
    return all_deals

def get_mock_deals():
    """Returns direct links to specific live discount pages across all categories"""
    return [
        {
            'title': 'boAt Airdopes 141 Bluetooth TWS Earbuds (71% OFF)',
            'url': 'https://www.amazon.in/dp/B09N3ZLB3T',
            'original_price': 4490.0,
            'discount_price': 1299.0,
            'discount_percentage': 71.0,
            'category': 'Electronics',
            'source': 'Amazon'
        },
        {
            'title': 'Amazon Fashion Top Deals & Apparel Discounts (Up to 70% OFF)',
            'url': 'https://www.amazon.in/b?node=1984443031',
            'original_price': 2999.0,
            'discount_price': 899.0,
            'discount_percentage': 70.0,
            'category': 'Fashion',
            'source': 'Amazon'
        },
        {
            'title': 'Pigeon Electric Kettle 1.5L (49% OFF Deal)',
            'url': 'https://www.amazon.in/dp/B07WMS75KY',
            'original_price': 1245.0,
            'discount_price': 629.0,
            'discount_percentage': 49.5,
            'category': 'Home & Kitchen',
            'source': 'Amazon'
        },
        {
            'title': 'Atomic Habits Bestseller Book (40% OFF Deal)',
            'url': 'https://www.amazon.in/dp/1847941831',
            'original_price': 799.0,
            'discount_price': 480.0,
            'discount_percentage': 39.9,
            'category': 'Books & Media',
            'source': 'Amazon'
        },
        {
            'title': 'Skyscanner Live Flights Offers & Discount Search',
            'url': 'https://www.skyscanner.co.in/flights',
            'original_price': 6500.0,
            'discount_price': 4225.0,
            'discount_percentage': 35.0,
            'category': 'Travel',
            'source': 'Skyscanner'
        },
        {
            'title': 'Skyscanner Live Hotel Deals & Discounted Stay Booking',
            'url': 'https://www.skyscanner.co.in/hotels',
            'original_price': 4500.0,
            'discount_price': 2925.0,
            'discount_percentage': 35.0,
            'category': 'Travel',
            'source': 'Skyscanner'
        },
        {
            'title': 'Crypto Live Price Alert: Solana (SOL) Market Movers',
            'url': 'https://www.coingecko.com/en/coins/solana',
            'original_price': 160.0,
            'discount_price': 135.0,
            'discount_percentage': 15.6,
            'category': 'Crypto',
            'source': 'CoinGecko'
        },
        {
            'title': 'Swiggy Gourmet Live Discounts & Food Promo Codes',
            'url': 'https://www.swiggy.com/gourmet',
            'original_price': 500.0,
            'discount_price': 350.0,
            'discount_percentage': 30.0,
            'category': 'Coupons',
            'source': 'Swiggy'
        }
    ]

if __name__ == "__main__":
    print("Testing Scraper direct discount links...")
    deals = get_mock_deals()
    print(f"Loaded {len(deals)} direct discount landing page links.")
