import os
from dotenv import load_dotenv

load_dotenv()

AMAZON_AFF = os.getenv("AMAZON_AFFILIATE_ID", "")
FLIPKART_AFF = os.getenv("FLIPKART_AFFILIATE_ID", "")
IMPACT_AFF = os.getenv("IMPACT_AFFILIATE_ID", "")
SHAREASALE_AFF = os.getenv("SHAREASALE_AFFILIATE_ID", "")
BASE_URL = os.getenv("BASE_URL", "")

def build_affiliate_link(url, source):
    """Appends affiliate tag based on source ecommerce or network if tag exists"""
    source_lower = source.lower()
    
    # Strip any test parameters
    clean_url = url.split('&test_ts=')[0].split('?test_ts=')[0]
    
    if 'amazon' in source_lower and AMAZON_AFF and not AMAZON_AFF.startswith('default_'):
        connector = '&' if '?' in clean_url else '?'
        return f"{clean_url}{connector}tag={AMAZON_AFF}"
    elif 'flipkart' in source_lower and FLIPKART_AFF and not FLIPKART_AFF.startswith('default_'):
        connector = '&' if '?' in clean_url else '?'
        return f"{clean_url}{connector}affid={FLIPKART_AFF}"
    elif 'impact' in source_lower and IMPACT_AFF and not IMPACT_AFF.startswith('default_'):
        connector = '&' if '?' in clean_url else '?'
        return f"{clean_url}{connector}irclickid={IMPACT_AFF}"
    elif 'shareasale' in source_lower and SHAREASALE_AFF and not SHAREASALE_AFF.startswith('default_'):
        connector = '&' if '?' in clean_url else '?'
        return f"{clean_url}{connector}u={SHAREASALE_AFF}"
    
    return clean_url

def get_tracking_url(deal_id, base_domain=None):
    """Generates short redirect URL using live Render domain"""
    domain = base_domain or os.getenv("RENDER_EXTERNAL_URL") or BASE_URL or "https://dealbot-kb4o.onrender.com"
    domain = domain.rstrip('/')
    return f"{domain}/r/{deal_id}"
