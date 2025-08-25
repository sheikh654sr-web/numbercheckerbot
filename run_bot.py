#!/usr/bin/env python3
"""
Simple script to run the Telegram Number Checker Bot
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from telegram_checker_bot import main

if __name__ == '__main__':
    print("🤖 Starting Telegram Number Checker Bot...")
    print("📝 Make sure you have set your API_ID and API_HASH in telegram_checker_bot.py")
    print("⏳ Press Ctrl+C to stop the bot")
    print("-" * 50)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
