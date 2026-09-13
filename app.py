from flask import Flask, render_template, redirect, request, jsonify
from database import (
    get_total_deals_this_month, 
    get_most_popular_category, 
    get_deal_by_id, 
    register_click, 
    get_total_clicks_this_month, 
    get_top_clicked_deals,
    add_subscriber
)
from affiliate import build_affiliate_link
import os

app = Flask(__name__)

@app.route('/')
def dashboard():
    total_deals = get_total_deals_this_month()
    total_clicks = get_total_clicks_this_month()
    popular_category = get_most_popular_category()
    top_deals = get_top_clicked_deals(limit=5)
    
    return render_template(
        'index.html', 
        total_deals=total_deals, 
        total_clicks=total_clicks,
        popular_category=popular_category, 
        top_deals=top_deals,
        bot_status="Online"
    )

@app.route('/r/<int:deal_id>')
def redirect_deal(deal_id):
    """Click tracking endpoint: logs click in SQLite and redirects to affiliate product URL"""
    deal = get_deal_by_id(deal_id)
    if deal:
        # Register the click
        register_click(deal_id)
        # Build affiliate link
        affiliate_url = build_affiliate_link(deal['url'], deal['source'])
        return redirect(affiliate_url, code=302)
    else:
        # Fallback if deal ID not found
        return redirect("https://www.amazon.in", code=302)

@app.route('/webhook/payment', methods=['POST'])
def payment_webhook():
    """Webhook endpoint for payment gateways (Stripe / Razorpay) to activate premium subscriptions"""
    data = request.json or {}
    user_id = data.get('user_id')
    username = data.get('username', 'Subscriber')
    
    if user_id:
        add_subscriber(user_id=user_id, username=username, days=30)
        return jsonify({"status": "success", "message": f"Activated 30-day premium for user {user_id}"}), 200
    
    return jsonify({"status": "error", "message": "Missing user_id"}), 400

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
