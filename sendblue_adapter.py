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
from typing import Dict, Any, List, Set
from urllib.parse import urljoin

import aiohttp

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


class SendBlueAdapter:
    """SendBlue gateway platform adapter."""
    
    def __init__(self, config):
        self.name = "Sendblue"
        self.platform = "sendblue"
        
        # API configuration - corrected URL construction
        self._api_base = "https://api.sendblue.com/api/"
        self._api_key = config.api_key
        self._secret_key = config.extra.get("secret_key")
        self._phone_number = config.extra.get("phone_number")
        
        # Session and state
        self._session = None
        self._polling = False
        self._last_poll_time = None
        self._processed_messages: Set[str] = set()
        
        # Event handlers
        self.on_message = None
        self.gateway_runner = None
        
    async def connect(self) -> bool:
        """Connect to SendBlue API and start polling."""
        try:
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
            
            logger.info("[%s] Connected and polling for messages", self.name)
            return True
            
        except Exception as e:
            logger.error("[%s] Failed to connect: %s", self.name, e)
            return False
    
    async def disconnect(self) -> None:
        """Disconnect and cleanup."""
        self._polling = False
        if self._session:
            await self._session.close()
            self._session = None
        logger.info("[%s] Disconnected", self.name)
    
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
                    logger.debug("[%s] API connection test successful", self.name)
                    return True
                else:
                    logger.error("[%s] API test failed: %d", self.name, resp.status)
                    return False
                    
        except Exception as e:
            logger.error("[%s] API connection test failed: %s", self.name, e)
            return False
    
    async def _poll_messages(self) -> None:
        """Poll for new messages."""
        while self._polling:
            try:
                await self._fetch_messages()
                await asyncio.sleep(5)  # Poll every 5 seconds
            except Exception as e:
                logger.error("[%s] Error polling messages: %s", self.name, e)
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
                    logger.warning("[%s] Failed to fetch messages: %d", self.name, resp.status)
                    
        except Exception as e:
            logger.error("[%s] Error fetching messages: %s", self.name, e, exc_info=True)
            
    async def _process_message(self, data: Dict[str, Any]) -> None:
        """Process a single message from the API."""
        try:
            # Extract message data - fixed field mapping
            message_id = data.get("message_handle") or data.get("id") or data.get("messageId")
            from_number = data.get("from_number") or data.get("fromNumber")
            to_number = data.get("to_number") or data.get("toNumber")
            content = data.get("content", "").strip()
            message_type = data.get("type", "text").lower()
            
            # Basic validation
            if not from_number or not message_id:
                logger.warning("[%s] Invalid message data: missing from_number or id", self.name)
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
            if self.on_message and content:
                try:
                    await self.on_message(
                        platform=self.platform,
                        user_id=from_number,
                        display_name=from_number,
                        message=content,
                        message_type=message_type,
                        raw_data=data
                    )
                except Exception as e:
                    logger.error("[%s] Error in message handler: %s", self.name, e)
                    
            # Mark message as read
            await self._mark_read(from_number)
            
        except Exception as e:
            logger.error("[%s] Error processing message: %s", self.name, e, exc_info=True)
    
    async def send_message(self, recipient: str, message: str, **kwargs) -> bool:
        """Send a message via SendBlue."""
        try:
            url = urljoin(self._api_base, "send-message")
            payload = {
                "number": recipient,
                "content": message
            }
            
            # Handle media if provided
            media_url = kwargs.get("media_url")
            if media_url:
                payload["media_url"] = media_url
                payload["content"] = kwargs.get("caption", "")
            
            async with self._session.post(url, json=payload) as resp:
                if resp.status == 200:
                    logger.debug("[%s] Message sent to %s", self.name, recipient)
                    return True
                else:
                    logger.error("[%s] Failed to send message: %d", self.name, resp.status)
                    return False
                    
        except Exception as e:
            logger.error("[%s] Error sending message: %s", self.name, e)
            return False
    
    async def _send_typing_indicator(self, number: str) -> None:
        """Send typing indicator."""
        try:
            url = urljoin(self._api_base, "send-typing-indicator")
            payload = {"number": number}
            
            async with self._session.post(url, json=payload) as resp:
                if resp.status != 200:
                    logger.warning("[%s] Typing indicator failed for %s: %d", 
                                 self.name, number, resp.status)
        except Exception as e:
            logger.debug("[%s] Typing indicator error: %s", self.name, e)
    
    async def _mark_read(self, number: str) -> None:
        """Mark message as read."""
        try:
            url = urljoin(self._api_base, "mark-read")
            payload = {"number": number}
            
            async with self._session.post(url, json=payload) as resp:
                if resp.status != 200:
                    logger.warning("[%s] Mark read failed for %s: %d", 
                                 self.name, number, resp.status)
        except Exception as e:
            logger.debug("[%s] Mark read error: %s", self.name, e)