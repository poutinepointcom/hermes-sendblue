#!/usr/bin/env python3
"""
End-to-end test of SendBlue iMessage integration.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from tools import sendblue_send_message, cleanup_api_session
from schemas import SendMessageInput


async def test_e2e_messaging():
    """Test sending a message via iMessage."""
    print("📱 Testing end-to-end iMessage integration...")
    
    # Get phone number from environment (the same one we use for sending)
    phone = os.getenv("SENDBLUE_PHONE_NUMBER")
    if not phone:
        print("❌ SENDBLUE_PHONE_NUMBER not set")
        return
        
    print(f"📱 Sending test message to {phone[:8]}...")
    
    try:
        input_data = SendMessageInput(
            number=phone,
            message="🧪 Testing Hermes SendBlue integration - this is a test message from the plugin!"
        )
        
        result = await sendblue_send_message(input_data)
        
        if result.success:
            print(f"✅ Message sent successfully!")
            print(f"   Message ID: {result.message_id}")
            print(f"   Recipient: {result.recipient}")
            
            print("\n💡 If you have iMessage, you should see this message now.")
            print("   Try replying to test bidirectional communication!")
        else:
            print(f"❌ Failed to send message: {result.error}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    finally:
        await cleanup_api_session()


if __name__ == "__main__":
    asyncio.run(test_e2e_messaging())