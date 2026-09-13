from flask import Flask, render_template
from database import get_total_deals_this_month, get_most_popular_category
import os

app = Flask(__name__)

@app.route('/')
def dashboard():
    total_deals = get_total_deals_this_month()
    popular_category = get_most_popular_category()
    
    # We assume if the Flask app is up, the bot is running (since they run together)
    bot_status = "Online" 
    
    return render_template('index.html', 
                           total_deals=total_deals, 
                           popular_category=popular_category, 
                           bot_status=bot_status)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
