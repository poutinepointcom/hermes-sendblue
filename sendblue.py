"""
SendBlue platform adapter for Hermes Gateway.

Provides bidirectional iMessage integration via SendBlue API:
- Polling messages via /v2/messages endpoint 
- Sending responses via API
- Typing indicators and read receipts
- Media handling (images, audio, videos)
- User authorization and pairing
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Set, Optional
from urllib.parse import urljoin

import aiohttp

from gateway.platforms.base import BasePlatformAdapter, MessageEvent, MessageType, SendResult
from gateway.config import Platform

logger = logging.getLogger(__name__)


def check_sendblue_requirements() -> bool:
    """Check if SendBlue requirements are met."""
    try:
        import aiohttp  # noqa: F401
        return all([
            os.getenv("SENDBLUE_API_KEY"),
            os.getenv("SENDBLUE_SECRET_KEY"), 
            os.getenv("SENDBLUE_PHONE_NUMBER")
        ])
    except ImportError:
        return False


class SendBlueAdapter(BasePlatformAdapter):
    """SendBlue gateway platform adapter."""
    
    def __init__(self, config):
        super().__init__(config, Platform.SENDBLUE)
        
        # API configuration
        self._api_base = "https://api.sendblue.com/api/"
        self._api_key = config.extra.get("api_key") or os.getenv("SENDBLUE_API_KEY")
        self._secret_key = config.extra.get("secret_key") or os.getenv("SENDBLUE_SECRET_KEY")
        self._phone_number = config.extra.get("phone_number") or os.getenv("SENDBLUE_PHONE_NUMBER")
        
        # Session and state
        self._session: Optional[aiohttp.ClientSession] = None
        self._polling = False
        self._last_poll_time: Optional[datetime] = None
        self._processed_messages: Set[str] = set()
        
    async def connect(self) -> bool:
        """Connect to SendBlue API and start polling."""
        try:
            # Validate required credentials
            if not self._api_key or not self._secret_key or not self._phone_number:
                logger.error("[%s] Missing required credentials: api_key=%s secret_key=%s phone_number=%s", 
                           "SendBlue", bool(self._api_key), bool(self._secret_key), bool(self._phone_number))
                return False
                
            self._session = aiohttp.ClientSession(
                headers={
                    "sb-api-key-id": self._api_key,
                    "sb-api-secret-key": self._secret_key,
                    "Content-Type": "application/json"
                },
                timeout=aiohttp.ClientTimeout(total=30)
            )
            
            # Test API connection
            if not await self._test_api_connection():
                return False
                
            # Start polling for messages
            self._polling = True
            asyncio.create_task(self._poll_messages())
            
            logger.info("[%s] Connected and polling for messages", "SendBlue")
            return True
            
        except Exception as e:
            logger.error("[%s] Failed to connect: %s", "SendBlue", e)
            return False
    
    async def disconnect(self) -> None:
        """Disconnect and cleanup."""
        self._polling = False
        if self._session:
            await self._session.close()
            self._session = None
        logger.info("[%s] Disconnected", "SendBlue")
    
    async def _test_api_connection(self) -> bool:
        """Test API connection with minimal request."""
        try:
            url = urljoin(self._api_base, "v2/messages")
            params = {
                "limit": 1,
                "is_outbound": "false",
                "order_by": "createdAt", 
                "order_direction": "desc"
            }
            
            async with self._session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    logger.debug("[%s] API connection test successful", "SendBlue")
                    return True
                else:
                    logger.error("[%s] API test failed: %d", "SendBlue", resp.status)
                    return False
                    
        except Exception as e:
            logger.error("[%s] API connection test failed: %s", "SendBlue", e)
            return False
    
    async def _poll_messages(self) -> None:
        """Poll for new messages."""
        while self._polling:
            try:
                await self._fetch_messages()
                await asyncio.sleep(5)  # Poll every 5 seconds
            except Exception as e:
                logger.error("[%s] Error polling messages: %s", "SendBlue", e)
                await asyncio.sleep(10)  # Back off on error
                
    async def _fetch_messages(self) -> None:
        """Fetch messages from SendBlue API."""
        try:
            url = urljoin(self._api_base, "v2/messages")
            params = {
                "limit": 50,
                "is_outbound": "false",  # Only get inbound messages
                "order_by": "createdAt",
                "order_direction": "desc"
            }
            
            # Add timestamp filter if we have a last poll time
            if self._last_poll_time:
                params["created_at_gte"] = self._last_poll_time.isoformat()
                
            async with self._session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    messages = data.get("data", []) if isinstance(data, dict) else []
                    
                    for message in messages:
                        await self._process_message(message)
                        
                    # Update last poll time
                    if messages:
                        self._last_poll_time = datetime.now()
                        
                else:
                    logger.warning("[%s] Failed to fetch messages: %d", "SendBlue", resp.status)
                    
        except Exception as e:
            logger.error("[%s] Error fetching messages: %s", "SendBlue", e, exc_info=True)
            
    async def _process_message(self, data: Dict[str, Any]) -> None:
        """Process a single message from the API."""
        try:
            # Extract message data
            message_id = data.get("message_handle") or data.get("id") or data.get("messageId")
            from_number = data.get("from_number") or data.get("fromNumber")
            to_number = data.get("to_number") or data.get("toNumber")
            content = data.get("content", "").strip()
            message_type = data.get("type", "text").lower()
            
            # Basic validation
            if not from_number or not message_id:
                logger.warning("[%s] Invalid message data: missing from_number or id", "SendBlue")
                return
            
            # Deduplicate messages
            if message_id in self._processed_messages:
                return
            self._processed_messages.add(message_id)
            
            # Ignore messages from our own number
            if from_number == self._phone_number:
                return
            
            # Ignore messages we sent (to_number is our number means we sent it)
            if to_number == self._phone_number and from_number != self._phone_number:
                # This is an incoming message TO us - process it
                pass
            else:
                return
                
            # Send typing indicator
            await self._send_typing_indicator(from_number)
            
            # Process the message
            if content:
                try:
                    # Build source for the message
                    source = self.build_source(
                        chat_id=from_number,
                        chat_name=from_number,
                        chat_type="dm",
                        user_id=from_number,
                        user_name=from_number,
                    )
                    
                    # Create message event
                    event = MessageEvent(
                        text=content,
                        message_type=MessageType.TEXT if message_type == "text" else MessageType.OTHER,
                        source=source,
                        message_id=message_id,
                        raw_message=data,
                    )
                    
                    await self.handle_message(event)
                except Exception as e:
                    logger.error("[%s] Error in message handler: %s", "SendBlue", e)
                    
            # Mark message as read
            await self._mark_read(from_number)
            
        except Exception as e:
            logger.error("[%s] Error processing message: %s", "SendBlue", e, exc_info=True)
    
    async def send_message(self, recipient: str, message: str, **kwargs) -> bool:
        """Send a message via SendBlue."""
        try:
            url = urljoin(self._api_base, "send-message")
            payload = {
                "number": recipient,
                "from_number": self._phone_number,
                "content": message
            }
            
            # Handle media if provided
            media_url = kwargs.get("media_url")
            if media_url:
                payload["media_url"] = media_url
                payload["content"] = kwargs.get("caption", "")
            
            async with self._session.post(url, json=payload) as resp:
                if resp.status in [200, 201, 202]:  # 202 = accepted/queued, this is success
                    logger.debug("[%s] Message sent to %s (status: %d)", "SendBlue", recipient, resp.status)
                    return True
                else:
                    error_text = await resp.text()
                    logger.error("[%s] Failed to send message: %d - %s", "SendBlue", resp.status, error_text)
                    return False
                    
        except Exception as e:
            logger.error("[%s] Error sending message: %s", "SendBlue", e)
            return False
    
    async def _send_typing_indicator(self, number: str) -> None:
        """Send typing indicator."""
        try:
            url = urljoin(self._api_base, "send-typing-indicator")
            payload = {
                "number": number,
                "from_number": self._phone_number
            }
            
            async with self._session.post(url, json=payload) as resp:
                if resp.status not in [200, 201]:
                    logger.debug("[%s] Typing indicator failed for %s: %d (normal - not all numbers support it)", 
                                 "SendBlue", number, resp.status)
        except Exception as e:
            logger.debug("[%s] Typing indicator error: %s", "SendBlue", e)
    
    async def _mark_read(self, number: str) -> None:
        """Mark message as read."""
        try:
            url = urljoin(self._api_base, "read-receipt") 
            payload = {"number": number}
            
            async with self._session.post(url, json=payload) as resp:
                if resp.status not in [200, 201]:
                    logger.debug("[%s] Mark read failed for %s: %d (normal - not all numbers support it)", 
                                 "SendBlue", number, resp.status)
        except Exception as e:
            logger.debug("[%s] Mark read error: %s", "SendBlue", e)
    
    # Abstract method implementations
    async def send(self, chat_id: str, content: str, reply_to=None, metadata=None) -> SendResult:
        """Send a message via SendBlue (BasePlatformAdapter interface)."""
        success = await self.send_message(chat_id, content)
        return SendResult(success=success, message_id=None)
    
    async def get_chat_info(self, chat_id: str) -> Dict[str, Any]:
        """Get chat info for a phone number."""
        return {
            "name": chat_id,
            "type": "dm"
        }
    
    async def send_typing(self, chat_id: str, metadata=None) -> None:
        """Send typing indicator (interface method for gateway framework)."""
        await self._send_typing_indicator(chat_id)