from flask import Flask, render_template, redirect, request, jsonify
from database import (
    get_total_deals_this_month, 
    get_most_popular_category, 
    get_deal_by_id, 
    register_click, 
    get_total_clicks_this_month, 
    get_top_clicked_deals,
    add_subscriber,
    get_connection,
    create_user_bot,
    get_all_user_bots,
    toggle_user_bot_status,
    delete_user_bot
)
from affiliate import build_affiliate_link
from botbuilder_engine import run_single_user_bot
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
    est_earnings = round(total_saas_clicks * 0.12, 2)
    
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
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, original_url, clicks FROM saas_links WHERE short_code = ?", (short_code,))
    row = cursor.fetchone()
    
    if row:
        link_id, original_url, current_clicks = row[0], row[1], row[2]
        cursor.execute("UPDATE saas_links SET clicks = clicks + 1 WHERE id = ?", (link_id,))
        conn.commit()
        conn.close()
        return redirect(original_url, code=302)
    
    conn.close()
    return redirect('/saas')

# --- BOTBUILDER NO-CODE SAAS ROUTES ---

@app.route('/botbuilder')
def botbuilder_portal():
    """BotBuilder No-Code SaaS Web Portal"""
    bots = get_all_user_bots()
    total_bots = len(bots)
    active_bots = sum(1 for b in bots if b['status'] == 'active')
    total_mrr = active_bots * 19 # $19/mo per active bot
    
    return render_template(
        'botbuilder.html',
        bots=bots,
        total_bots=total_bots,
        active_bots=active_bots,
        total_mrr=total_mrr
    )

@app.route('/botbuilder/create', methods=['POST'])
def botbuilder_create():
    bot_name = request.form.get('bot_name', '').strip()
    bot_token = request.form.get('bot_token', '').strip()
    channel_id = request.form.get('channel_id', '').strip()
    source_type = request.form.get('source_type', 'E-commerce Deals').strip()
    interval_hours = int(request.form.get('interval_hours', 6))
    
    if bot_name and bot_token and channel_id:
        create_user_bot(bot_name, bot_token, channel_id, source_type, interval_hours)
        
    return redirect('/botbuilder')

@app.route('/botbuilder/toggle/<int:bot_id>')
def botbuilder_toggle(bot_id):
    toggle_user_bot_status(bot_id)
    return redirect('/botbuilder')

@app.route('/botbuilder/delete/<int:bot_id>')
def botbuilder_delete(bot_id):
    delete_user_bot(bot_id)
    return redirect('/botbuilder')

@app.route('/botbuilder/test/<int:bot_id>')
def botbuilder_test(bot_id):
    bots = get_all_user_bots()
    target_bot = next((b for b in bots if b['id'] == bot_id), None)
    if target_bot:
        try:
            run_single_user_bot(target_bot)
        except Exception as e:
            print(f"Manual test run error for bot {bot_id}: {e}")
    return redirect('/botbuilder')

# --- EXISTING ROUTES ---

@app.route('/r/<int:deal_id>')
def redirect_deal(deal_id):
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
