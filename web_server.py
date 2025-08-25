#!/usr/bin/env python3
"""
Web server for keeping the bot alive on Render
"""

import os
import asyncio
import threading
from flask import Flask, jsonify
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

def run_flask():
    """Run Flask server"""
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)

def run_bot_thread():
    """Run bot in separate thread"""
    asyncio.run(run_bot())

if __name__ == '__main__':
    # Start bot in background thread
    bot_thread = threading.Thread(target=run_bot_thread, daemon=True)
    bot_thread.start()
    
    # Start Flask server in main thread
    run_flask()
