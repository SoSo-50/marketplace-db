import os
import logging
import telebot
from flask import request
from dotenv import load_dotenv
from app import create_app
from bot import bot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
app = create_app()

WEBHOOK_URL = os.getenv('WEBHOOK_URL')

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        return 'Access denied', 403

def set_webhook_on_startup():
    token = os.getenv('BOT_TOKEN')
    if not token or not WEBHOOK_URL:
        logger.warning("⚠️ BOT_TOKEN or WEBHOOK_URL not set. Skipping webhook setup.")
        return

    try:
        final_url = f"{WEBHOOK_URL}/webhook"
        logger.info(f"🔗 Setting webhook to: {final_url}")
        
        bot.remove_webhook()
        bot.set_webhook(url=final_url)
        logger.info("✅ Webhook set successfully.")
    except Exception as e:
        logger.error(f"❌ Failed to set webhook: {e}")

if os.getenv('RAILWAY_ENVIRONMENT'):
    set_webhook_on_startup()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)