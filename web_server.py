#!/usr/bin/env python3
"""
Web server for keeping the bot alive on Render
"""

import os
import asyncio
import threading
from flask import Flask, jsonify, request
from telegram_checker_bot import run_bot

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "alive",
        "message": "Telegram Number Checker Bot is running!",
        "version": "2.0",
        "features": [
            "Multi-language support",
            "Admin approval system",
            "Global phone number checking",
            "24/7 deployment ready"
        ]
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "uptime": "running",
        "bot": "active"
    })

@app.route('/start')
def start_bot():
    return jsonify({
        "message": "Bot is already running!",
        "status": "active"
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook endpoint for Telegram"""
    try:
        # Get the update from Telegram
        update_data = request.get_json()
        
        if update_data:
            # Import here to avoid circular imports
            from telegram import Update
            from telegram_checker_bot import application
            
            # Create Update object
            update = Update.de_json(update_data, application.bot)
            
            # Process the update asynchronously
            if application and update:
                # Run the update processing in the event loop
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(application.process_update(update))
                finally:
                    loop.close()
        
        return 'OK', 200
    except Exception as e:
        print(f"Webhook error: {e}")
        return 'Error', 500

def run_flask():
    """Run Flask server"""
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)

def run_bot_thread():
    """Run bot in separate thread"""
    try:
        # Import here to avoid circular imports
        from telegram_checker_bot import main
        asyncio.run(main())
    except Exception as e:
        print(f"Error starting bot: {e}")

if __name__ == '__main__':
    # Start bot in background thread
    bot_thread = threading.Thread(target=run_bot_thread, daemon=True)
    bot_thread.start()
    
    # Start Flask server in main thread
    run_flask()
