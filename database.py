import sqlite3
import os
import json
from datetime import datetime, timedelta

DB_FILE = "deals.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE, timeout=30.0)
    conn.execute("PRAGMA busy_timeout = 30000;")
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA journal_mode=WAL;")
    except Exception as e:
        print(f"WAL mode init notice: {e}")
        
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS deals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT UNIQUE NOT NULL,
            original_price REAL,
            discount_price REAL,
            discount_percentage REAL,
            category TEXT,
            source TEXT,
            posted_at TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clicks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deal_id INTEGER,
            user_id INTEGER,
            clicked_at TIMESTAMP,
            FOREIGN KEY (deal_id) REFERENCES deals(id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            tier TEXT DEFAULT 'free',
            status TEXT DEFAULT 'active',
            subscribed_at TIMESTAMP,
            expires_at TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER PRIMARY KEY,
            categories_json TEXT
        )
    """)
    
    # NO-CODE BOTBUILDER SAAS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_bots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bot_name TEXT NOT NULL,
            bot_token TEXT NOT NULL,
            channel_id TEXT NOT NULL,
            source_type TEXT DEFAULT 'E-commerce Deals',
            interval_hours INTEGER DEFAULT 6,
            status TEXT DEFAULT 'active',
            last_run_at TIMESTAMP,
            created_at TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

# --- NO-CODE BOTBUILDER HELPERS ---

def create_user_bot(bot_name, bot_token, channel_id, source_type="E-commerce Deals", interval_hours=6):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_bots (bot_name, bot_token, channel_id, source_type, interval_hours, status, created_at)
        VALUES (?, ?, ?, ?, ?, 'active', ?)
    """, (bot_name, bot_token, channel_id, source_type, interval_hours, datetime.now()))
    conn.commit()
    bot_id = cursor.lastrowid
    conn.close()
    return bot_id

def get_all_user_bots():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, bot_name, bot_token, channel_id, source_type, interval_hours, status, last_run_at, created_at
        FROM user_bots ORDER BY id DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            'id': r[0],
            'bot_name': r[1],
            'bot_token': r[2],
            'channel_id': r[3],
            'source_type': r[4],
            'interval_hours': r[5],
            'status': r[6],
            'last_run_at': r[7],
            'created_at': r[8]
        } for r in rows
    ]

def toggle_user_bot_status(bot_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM user_bots WHERE id = ?", (bot_id,))
    row = cursor.fetchone()
    if row:
        new_status = 'paused' if row[0] == 'active' else 'active'
        cursor.execute("UPDATE user_bots SET status = ? WHERE id = ?", (new_status, bot_id))
        conn.commit()
    conn.close()

def delete_user_bot(bot_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_bots WHERE id = ?", (bot_id,))
    conn.commit()
    conn.close()

def update_bot_last_run(bot_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE user_bots SET last_run_at = ? WHERE id = ?", (datetime.now(), bot_id))
    conn.commit()
    conn.close()

# --- EXISTING HELPERS ---

def insert_deal(title, url, original_price, discount_price, discount_percentage, category, source):
    conn = get_connection()
    cursor = conn.cursor()
    deal_id = None
    try:
        cursor.execute("""
            INSERT INTO deals (title, url, original_price, discount_price, discount_percentage, category, source, posted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (title, url, original_price, discount_price, discount_percentage, category, source, datetime.now()))
        conn.commit()
        deal_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        cursor.execute("SELECT id FROM deals WHERE url = ?", (url,))
        row = cursor.fetchone()
        if row:
            deal_id = row[0]
    conn.close()
    return deal_id

def get_deal_by_id(deal_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, url, source, category FROM deals WHERE id = ?", (deal_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {'id': row[0], 'title': row[1], 'url': row[2], 'source': row[3], 'category': row[4]}
    return None

def register_click(deal_id, user_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO clicks (deal_id, user_id, clicked_at) VALUES (?, ?, ?)
    """, (deal_id, user_id, datetime.now()))
    conn.commit()
    conn.close()

def get_total_clicks_this_month():
    conn = get_connection()
    cursor = conn.cursor()
    current_month_prefix = datetime.now().strftime('%Y-%m')
    cursor.execute("""
        SELECT COUNT(*) FROM clicks WHERE clicked_at LIKE ?
    """, (f"{current_month_prefix}%",))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_top_clicked_deals(limit=5):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT d.title, d.category, d.source, COUNT(c.id) as click_count
        FROM deals d
        JOIN clicks c ON d.id = c.deal_id
        GROUP BY d.id
        ORDER BY click_count DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [{'title': r[0], 'category': r[1], 'source': r[2], 'clicks': r[3]} for r in rows]

def save_user_settings(user_id, categories_list):
    conn = get_connection()
    cursor = conn.cursor()
    categories_json = json.dumps(categories_list)
    cursor.execute("""
        INSERT INTO user_settings (user_id, categories_json)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET categories_json=excluded.categories_json
    """, (user_id, categories_json))
    conn.commit()
    conn.close()

def get_user_settings(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT categories_json FROM user_settings WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row and row[0]:
        return json.loads(row[0])
    return ["Electronics", "Fashion", "Home & Kitchen", "Books & Media", "Travel", "Crypto", "Coupons"]

def add_subscriber(user_id, username, days=30):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now()
    expires = now + timedelta(days=days)
    cursor.execute("""
        INSERT INTO subscribers (user_id, username, tier, status, subscribed_at, expires_at)
        VALUES (?, ?, 'premium', 'active', ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET tier='premium', status='active', expires_at=excluded.expires_at
    """, (user_id, username, now, expires))
    conn.commit()
    conn.close()

def is_premium_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT tier, expires_at FROM subscribers WHERE user_id = ? AND status = 'active'
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        expires = datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S.%f") if '.' in row[1] else datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S")
        if expires > datetime.now():
            return True
    return False

def get_total_deals_this_month():
    conn = get_connection()
    cursor = conn.cursor()
    current_month_prefix = datetime.now().strftime('%Y-%m')
    cursor.execute("""
        SELECT COUNT(*) FROM deals WHERE posted_at LIKE ?
    """, (f"{current_month_prefix}%",))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_most_popular_category():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT category, COUNT(*) as count 
        FROM deals 
        GROUP BY category 
        ORDER BY count DESC 
        LIMIT 1
    """)
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else "N/A"

if __name__ == "__main__":
    init_db()
    print("Database initialized for BotBuilder SaaS.")
