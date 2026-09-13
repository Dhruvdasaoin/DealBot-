import sqlite3
import os
from datetime import datetime

DB_FILE = "deals.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
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
    conn.commit()
    conn.close()

def insert_deal(title, url, original_price, discount_price, discount_percentage, category, source):
    """Inserts a deal if it hasn't been posted before (based on URL). Returns True if inserted, False if exists."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO deals (title, url, original_price, discount_price, discount_percentage, category, source, posted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (title, url, original_price, discount_price, discount_percentage, category, source, datetime.now()))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False # URL already exists
    conn.close()
    return success

def get_total_deals_this_month():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Get current year and month in YYYY-MM format
    current_month_prefix = datetime.now().strftime('%Y-%m')
    
    cursor.execute("""
        SELECT COUNT(*) FROM deals WHERE posted_at LIKE ?
    """, (f"{current_month_prefix}%",))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_most_popular_category():
    conn = sqlite3.connect(DB_FILE)
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
    print("Database initialized.")
