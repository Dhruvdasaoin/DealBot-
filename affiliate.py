import os
from dotenv import load_dotenv

load_dotenv()

AMAZON_AFF = os.getenv("AMAZON_AFFILIATE_ID", "default_amazon_id-21")
FLIPKART_AFF = os.getenv("FLIPKART_AFFILIATE_ID", "default_flipkart_id")
IMPACT_AFF = os.getenv("IMPACT_AFFILIATE_ID", "default_impact_id")
SHAREASALE_AFF = os.getenv("SHAREASALE_AFFILIATE_ID", "default_shareasale_id")
BASE_URL = os.getenv("BASE_URL", "")

def build_affiliate_link(url, source):
    """Appends affiliate tag based on source ecommerce or network"""
    source_lower = source.lower()
    
    if 'amazon' in source_lower:
        connector = '&' if '?' in url else '?'
        return f"{url}{connector}tag={AMAZON_AFF}"
    elif 'flipkart' in source_lower:
        connector = '&' if '?' in url else '?'
        return f"{url}{connector}affid={FLIPKART_AFF}"
    elif 'impact' in source_lower:
        connector = '&' if '?' in url else '?'
        return f"{url}{connector}irclickid={IMPACT_AFF}"
    elif 'shareasale' in source_lower:
        connector = '&' if '?' in url else '?'
        return f"{url}{connector}u={SHAREASALE_AFF}"
    
    return url

def get_tracking_url(deal_id, base_domain=None):
    """Generates short redirect URL for click tracking"""
    domain = base_domain or BASE_URL or "http://localhost:5000"
    domain = domain.rstrip('/')
    return f"{domain}/r/{deal_id}"
