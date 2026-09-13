from flask import Flask, render_template, redirect, request, jsonify
from database import (
    get_total_deals_this_month, 
    get_most_popular_category, 
    get_deal_by_id, 
    register_click, 
    get_total_clicks_this_month, 
    get_top_clicked_deals,
    add_subscriber,
    get_connection
)
from affiliate import build_affiliate_link
import os
import string
import random
from datetime import datetime

app = Flask(__name__)

def generate_short_code(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

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

# --- LINKMONITR MICRO-SAAS ROUTES ---

@app.route('/saas')
def saas_portal():
    """Live LinkMonitr Micro-SaaS Portal for creating and tracking affiliate links"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create saas_links table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS saas_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            short_code TEXT UNIQUE NOT NULL,
            original_url TEXT NOT NULL,
            title TEXT,
            clicks INTEGER DEFAULT 0,
            created_at TIMESTAMP
        )
    """)
    conn.commit()
    
    cursor.execute("SELECT id, short_code, original_url, title, clicks, created_at FROM saas_links ORDER BY id DESC")
    rows = cursor.fetchall()
    
    total_saas_links = len(rows)
    total_saas_clicks = sum(r[4] for r in rows) if rows else 0
    est_earnings = round(total_saas_clicks * 0.12, 2) # Estimated $0.12 per click
    
    links = [
        {
            'id': r[0],
            'short_code': r[1],
            'original_url': r[2],
            'title': r[3],
            'clicks': r[4],
            'created_at': r[5]
        } for r in rows
    ]
    
    conn.close()
    
    host_domain = request.host_url.rstrip('/')
    
    return render_template(
        'saas.html',
        links=links,
        total_links=total_saas_links,
        total_clicks=total_saas_clicks,
        est_earnings=est_earnings,
        host_domain=host_domain
    )

@app.route('/saas/create', methods=['POST'])
def saas_create():
    """API & Form Endpoint to generate a tracked short-link in SaaS"""
    original_url = request.form.get('url', '').strip()
    title = request.form.get('title', '').strip() or original_url
    
    if not original_url:
        return redirect('/saas')
        
    short_code = generate_short_code()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO saas_links (short_code, original_url, title, clicks, created_at)
        VALUES (?, ?, ?, 0, ?)
    """, (short_code, original_url, title, datetime.now()))
    conn.commit()
    conn.close()
    
    return redirect('/saas')

@app.route('/s/<short_code>')
def saas_redirect(short_code):
    """SaaS Redirect Endpoint: logs click and redirects user to target URL"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, original_url, clicks FROM saas_links WHERE short_code = ?", (short_code,))
    row = cursor.fetchone()
    
    if row:
        link_id, original_url, current_clicks = row[0], row[1], row[2]
        # Increment click count
        cursor.execute("UPDATE saas_links SET clicks = clicks + 1 WHERE id = ?", (link_id,))
        conn.commit()
        conn.close()
        return redirect(original_url, code=302)
    
    conn.close()
    return redirect('/saas')

@app.route('/r/<int:deal_id>')
def redirect_deal(deal_id):
    """DealBot Click tracking endpoint"""
    deal = get_deal_by_id(deal_id)
    if deal:
        register_click(deal_id)
        affiliate_url = build_affiliate_link(deal['url'], deal['source'])
        return redirect(affiliate_url, code=302)
    else:
        return redirect("https://www.amazon.in", code=302)

@app.route('/webhook/payment', methods=['POST'])
def payment_webhook():
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
