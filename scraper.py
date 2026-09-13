import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import time
import random

categories = ["Electronics", "Fashion", "Home & Kitchen"]

def get_headers():
    ua = UserAgent()
    return {
        'User-Agent': ua.random,
        'Accept-Language': 'en-US, en;q=0.5'
    }

def scrape_amazon_deals(category):
    # This is a stub for Amazon scraping. 
    # Real scraping of Amazon without APIs often requires Selenium/Proxies due to captchas.
    # We will attempt a basic request to Amazon's "Today's Deals" page or category page.
    deals = []
    
    # Example URL (highly likely to be blocked or require JS, but we try as requested)
    url = f"https://www.amazon.in/s?k={category.replace(' ', '+')}+deals"
    
    try:
        response = requests.get(url, headers=get_headers(), timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            # Amazon search results container (varies often)
            items = soup.find_all('div', {'data-component-type': 's-search-result'})
            
            for item in items[:5]: # limit to 5 per scrape attempt
                try:
                    title_elem = item.find('span', class_='a-text-normal')
                    if not title_elem: continue
                    title = title_elem.text.strip()
                    
                    price_elem = item.find('span', class_='a-price-whole')
                    if not price_elem: continue
                    discount_price = float(price_elem.text.replace(',', '').strip())
                    
                    # Original price (sometimes not present)
                    orig_elem = item.find('span', class_='a-text-price')
                    if orig_elem:
                        original_price_str = orig_elem.find('span', class_='a-offscreen')
                        if original_price_str:
                            original_price = float(original_price_str.text.replace('₹', '').replace(',', '').strip())
                        else:
                            original_price = discount_price
                    else:
                        original_price = discount_price
                    
                    link_elem = item.find('a', class_='a-link-normal')
                    if not link_elem: continue
                    product_url = "https://www.amazon.in" + link_elem['href']
                    
                    if original_price > discount_price:
                        discount_percentage = ((original_price - discount_price) / original_price) * 100
                    else:
                        discount_percentage = 0.0
                        
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
                except Exception as e:
                    print(f"Error parsing Amazon item: {e}")
                    continue
    except Exception as e:
        print(f"Failed to scrape Amazon {category}: {e}")
    
    return deals

def scrape_flipkart_deals(category):
    # Stub for Flipkart scraping.
    deals = []
    url = f"https://www.flipkart.com/search?q={category.replace(' ', '+')}+offers"
    
    try:
        response = requests.get(url, headers=get_headers(), timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            # Flipkart search results (various classes, this is a generic attempt)
            # Flipkart often uses '_1AtVbE' or similar classes for containers
            items = soup.find_all('div', class_='_1AtVbE')
            
            for item in items[:5]:
                try:
                    title_elem = item.find('a', class_='IRpwTa') or item.find('div', class_='_4rR01T')
                    if not title_elem: continue
                    title = title_elem.text.strip()
                    
                    link_elem = item.find('a', class_='_1fQZEK') or item.find('a', class_='IRpwTa')
                    if not link_elem: continue
                    product_url = "https://www.flipkart.com" + link_elem['href']
                    
                    price_elem = item.find('div', class_='_30jeq3')
                    if not price_elem: continue
                    discount_price = float(price_elem.text.replace('₹', '').replace(',', '').strip())
                    
                    orig_elem = item.find('div', class_='_3I9_wc')
                    if orig_elem:
                        original_price = float(orig_elem.text.replace('₹', '').replace(',', '').strip())
                    else:
                        original_price = discount_price
                    
                    if original_price > discount_price:
                        discount_percentage = ((original_price - discount_price) / original_price) * 100
                    else:
                        discount_percentage = 0.0
                        
                    if discount_percentage > 30:
                        deals.append({
                            'title': title,
                            'url': product_url,
                            'original_price': original_price,
                            'discount_price': discount_price,
                            'discount_percentage': round(discount_percentage, 2),
                            'category': category,
                            'source': 'Flipkart'
                        })
                except Exception as e:
                    print(f"Error parsing Flipkart item: {e}")
                    continue
    except Exception as e:
        print(f"Failed to scrape Flipkart {category}: {e}")
        
    return deals

def get_all_deals():
    """Scrapes deals and returns top deals with >30% discount"""
    all_deals = []
    for category in categories:
        # Add random delay to avoid rate limiting
        time.sleep(random.uniform(1.0, 3.0))
        
        amazon_deals = scrape_amazon_deals(category)
        all_deals.extend(amazon_deals)
        
        time.sleep(random.uniform(1.0, 3.0))
        
        flipkart_deals = scrape_flipkart_deals(category)
        all_deals.extend(flipkart_deals)
        
    # Sort by discount percentage descending
    all_deals.sort(key=lambda x: x['discount_percentage'], reverse=True)
    return all_deals

def get_mock_deals():
    """Fallback if scraping fails completely (for testing/dashboard)"""
    return [
        {
            'title': 'Test Product: Wireless Earbuds',
            'url': 'https://www.amazon.in/dp/B08XYZ123?tag=test-21',
            'original_price': 4999.0,
            'discount_price': 1999.0,
            'discount_percentage': 60.0,
            'category': 'Electronics',
            'source': 'Amazon'
        },
        {
            'title': 'Test Product: Running Shoes',
            'url': 'https://www.flipkart.com/test-shoes/p/itme?affid=test',
            'original_price': 3999.0,
            'discount_price': 1499.0,
            'discount_percentage': 62.5,
            'category': 'Fashion',
            'source': 'Flipkart'
        },
        {
            'title': 'Test Product: Non-Stick Cookware',
            'url': 'https://www.amazon.in/dp/B07ABC123?tag=test-21',
            'original_price': 2999.0,
            'discount_price': 1599.0,
            'discount_percentage': 46.6,
            'category': 'Home & Kitchen',
            'source': 'Amazon'
        }
    ]

if __name__ == "__main__":
    print("Testing Scraper...")
    deals = get_all_deals()
    print(f"Found {len(deals)} real deals.")
    for d in deals:
        print(d)
