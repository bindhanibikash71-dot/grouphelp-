import os
import time
from flask import Flask, request, abort
import telebot

from config import init_env # Dummy if loading automatically via dotenv in production
from database import init_db
from bot_core import bot, setup_webhook
from admin_api import admin

app = Flask(__name__)
app.secret_key = os.urandom(24) # Random Secure Session string
app.register_blueprint(admin)   # Web interface connected to root

# Configure Webhooks exclusively via secure endpoint
@app.route('/webhook', methods=['POST'])
def webhook_bridge():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        abort(403)

if __name__ == '__main__':
    print("[INIT] Synchronizing databases...")
    init_db()
    
    app_url = os.getenv("APP_URL")
    print(f"[NET] Bridging Neural hook to Telegram Data Core -> {app_url}...")
    setup_webhook(app_url)
    
    # Listen Port matching Render
    port = int(os.environ.get('PORT', 10000))
    print(f"[ACTIVE] Gunicorn API interface open on {port}. Serving UI/Admin Dashboard...")
    
    # We use Waitress/Gunicorn mostly in prod, but simple run handles webhook correctly locally
    app.run(host='0.0.0.0', port=port, debug=False)
