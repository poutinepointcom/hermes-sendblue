#!/usr/bin/env python3
"""
Quick test script for SendBlue plugin functionality.
"""

import asyncio
import os
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from tools import sendblue_send_message, sendblue_list_conversations, sendblue_get_stats, cleanup_api_session
from schemas import SendMessageInput, ListConversationsInput


async def test_plugin():
    """Test basic plugin functionality."""
    print("🧪 Testing SendBlue Plugin...")
    
    # Test 1: Check configuration
    print("\n1. Configuration check:")
    config_vars = ["SENDBLUE_API_KEY", "SENDBLUE_SECRET_KEY", "SENDBLUE_PHONE_NUMBER"]
    for var in config_vars:
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var}: {'*' * min(len(value), 8)}...{value[-4:] if len(value) > 4 else ''}")
        else:
            print(f"   ❌ {var}: Not set")
    
    # Test 2: List conversations (safe API call)
    print("\n2. Testing list conversations:")
    try:
        input_data = ListConversationsInput(limit=3)
        result = await sendblue_list_conversations(input_data)
        print(f"   ✅ Got {len(result.conversations)} conversations")
        for conv in result.conversations[:2]:  # Show first 2
            print(f"      📱 {conv.contact_number}: {conv.last_message_text[:50]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Get plugin stats
    print("\n3. Testing plugin stats:")
    try:
        stats = await sendblue_get_stats()
        print(f"   ✅ Messages sent today: {stats.messages_sent_today}")
        print(f"   ✅ Last activity: {stats.last_activity}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n🎉 Plugin test completed!")
    
    # Clean up API session
    await cleanup_api_session()


if __name__ == "__main__":
    asyncio.run(test_plugin())