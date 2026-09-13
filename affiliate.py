import os
from dotenv import load_dotenv

load_dotenv()

AMAZON_AFF = os.getenv("AMAZON_AFFILIATE_ID", "").strip()
FLIPKART_AFF = os.getenv("FLIPKART_AFFILIATE_ID", "").strip()
IMPACT_AFF = os.getenv("IMPACT_AFFILIATE_ID", "").strip()
SHAREASALE_AFF = os.getenv("SHAREASALE_AFFILIATE_ID", "").strip()

def build_affiliate_link(url, source):
    """Appends affiliate tag directly to product URL and returns clean direct link"""
    if not url:
        return "https://www.amazon.in"
        
    source_lower = source.lower()
    
    # Strip any test parameters or trailing newlines/spaces
    clean_url = str(url).strip().split('&test_ts=')[0].split('?test_ts=')[0]
    
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
