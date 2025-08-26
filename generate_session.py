#!/usr/bin/env python3
"""
Generate Telethon session string for deployment
Run this locally to get session string for Render
"""

import os
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

# Your API credentials
API_ID = 22969300
API_HASH = "e78b8ed26aa341bd36690bdc13d2159a"

async def generate_session():
    """Generate USER session string for phone number checking"""
    print("🔐 Generating USER Session String for Phone Checking...")
    print("📱 IMPORTANT: Use YOUR personal phone number, NOT a bot!")
    print("⚠️  This creates a USER session to check other phone numbers")
    print("-" * 60)
    
    # Create client with string session
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    
    try:
        # Start the client (this will prompt for phone and code)
        await client.start()
        
        # Get the session string
        session_string = client.session.save()
        
        print("\n" + "="*60)
        print("🎉 SESSION STRING GENERATED SUCCESSFULLY!")
        print("="*60)
        print(f"TELETHON_SESSION={session_string}")
        print("="*60)
        print("\n📋 NEXT STEPS:")
        print("1. Copy the session string above")
        print("2. Go to Render Dashboard")
        print("3. Add environment variable:")
        print("   Key: TELETHON_SESSION")
        print(f"   Value: {session_string}")
        print("4. Redeploy your bot")
        print("\n✅ Your bot will then work with 100% accuracy!")
        
        # Test the session
        me = await client.get_me()
        print(f"\n🧪 Session test: Connected as {me.first_name} (ID: {me.id})")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Make sure you have:")
        print("- Valid phone number")
        print("- Access to SMS/calls for verification")
        print("- Stable internet connection")
    
    finally:
        await client.disconnect()

if __name__ == "__main__":
    print("🚀 Starting session generator...")
    asyncio.run(generate_session())
