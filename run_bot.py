#!/usr/bin/env python3
"""
Simple script to run the Telegram Number Checker Bot
"""

import asyncio
import sys
import os
import threading
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def start_web_server():
    """Start simple web server for Render health check"""
    try:
        from flask import Flask
        
        app = Flask(__name__)
        
        @app.route('/')
        def health():
            return {"status": "Bot is running!", "timestamp": str(datetime.now())}
        
        @app.route('/health')
        def health_check():
            return {"status": "healthy"}
        
        port = int(os.getenv('PORT', 10000))
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        print(f"Web server error: {e}")

if __name__ == '__main__':
    print("🤖 Starting Telegram Number Checker Bot...")
    print("📝 Make sure you have set your API_ID and API_HASH in telegram_checker_bot.py")
    print("⏳ Press Ctrl+C to stop the bot")
    print("-" * 50)
    
    # Start web server for Render if PORT is set
    if os.getenv('PORT'):
        print(f"🌐 Starting web server on port {os.getenv('PORT')}")
        web_thread = threading.Thread(target=start_web_server, daemon=True)
        web_thread.start()
    
    # Start bot
    try:
        from telegram_checker_bot import main
        print("🤖 Starting bot...")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
