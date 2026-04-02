#!/usr/bin/env python3
"""
Live API test to verify SendBlue integration is working.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from tools import sendblue_list_conversations, sendblue_get_messages, cleanup_api_session
from schemas import ListConversationsInput, GetMessagesInput


async def test_live_api():
    """Test live SendBlue API integration."""
    print("🔴 LIVE API TEST - SendBlue Integration")
    print("=" * 50)
    
    try:
        # Test 1: List recent conversations
        print("\n📋 1. Listing recent conversations...")
        conversations = await sendblue_list_conversations(ListConversationsInput(limit=5))
        
        print(f"   Found {len(conversations.conversations)} conversations:")
        for i, conv in enumerate(conversations.conversations[:3], 1):
            print(f"   {i}. {conv.contact_number}")
            print(f"      Last: {conv.last_message_text[:60]}...")
            print(f"      Time: {conv.last_message_time}")
        
        if conversations.conversations:
            # Test 2: Get messages from first conversation
            print(f"\n💬 2. Getting messages from {conversations.conversations[0].contact_number}...")
            messages_input = GetMessagesInput(
                number=conversations.conversations[0].contact_number,
                limit=3
            )
            messages = await sendblue_get_messages(messages_input)
            
            print(f"   Retrieved {len(messages.messages)} recent messages:")
            for msg in messages.messages[-2:]:  # Last 2 messages
                direction = "➡️ Sent" if msg.is_from_me else "⬅️ Received" 
                print(f"   {direction}: {msg.content[:50]}...")
                print(f"   Time: {msg.timestamp}")
        
        print(f"\n✅ SendBlue API integration is working!")
        print("   - API authentication: ✅")
        print("   - Message retrieval: ✅")
        print("   - Conversation listing: ✅")
        print("\n💡 Ready for bidirectional iMessage gateway!")
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await cleanup_api_session()


if __name__ == "__main__":
    asyncio.run(test_live_api())