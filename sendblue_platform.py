"""
SendBlue platform adapter for Hermes Gateway.

Provides bidirectional iMessage integration via SendBlue API with improved
architecture using the unified core client.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Set
from urllib.parse import urljoin

try:
    from gateway.platforms.base import BasePlatformAdapter, MessageEvent, MessageType, SendResult
    from gateway.config import Platform
except ImportError:
    # Fallback for testing without full Hermes environment
    class BasePlatformAdapter:
        def __init__(self, config, platform): pass
    
    class MessageEvent:
        def __init__(self, **kwargs): pass
    
    class MessageType:
        TEXT = "text"
        OTHER = "other"
    
    class SendResult:
        def __init__(self, success, message_id=None):
            self.success = success
            self.message_id = message_id
    
    class Platform:
        SENDBLUE = "sendblue"

try:
    from .core import SendBlueClient, SendBlueConfig
except ImportError:
    from core import SendBlueClient, SendBlueConfig

logger = logging.getLogger(__name__)


def check_sendblue_requirements() -> bool:
    """Check if SendBlue requirements are met."""
    try:
        import aiohttp  # noqa: F401
        config = SendBlueConfig()
        return config.is_valid()
    except ImportError:
        return False


class SendBlueAdapter(BasePlatformAdapter):
    """SendBlue gateway platform adapter with unified core client."""
    
    def __init__(self, config):
        super().__init__(config, Platform.SENDBLUE)
        
        # Initialize config only - no shared client!
        self._sendblue_config = SendBlueConfig()
        
        # Polling state
        self._polling = False
        self._last_poll_time = None
        self._processed_messages: Set[str] = set()
        
        # Statistics tracking
        self._stats = {
            "messages_received": 0,
            "messages_sent": 0,
            "typing_indicators_sent": 0,
            "api_errors": 0,
            "last_activity": None
        }
    
    async def connect(self) -> bool:
        """Connect to SendBlue API and start polling."""
        try:
            # Test connection with individual client
            async with SendBlueClient() as client:
                test_result = await client.get_messages(limit=1)
                if not test_result["success"]:
                    logger.error("[%s] Failed to connect to SendBlue API: %s", "SendBlue", test_result.get("error"))
                    return False
            
            # Start message polling
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
        # No shared client to disconnect - individual clients clean up automatically
        logger.info("[%s] Disconnected", "SendBlue")
    
    async def _poll_messages(self) -> None:
        """Poll for new messages from SendBlue API."""
        while self._polling:
            try:
                await self._fetch_and_process_messages()
                await asyncio.sleep(self._sendblue_config.poll_interval)
            except Exception as e:
                logger.error("[%s] Error polling messages: %s", "SendBlue", e)
                self._stats["api_errors"] += 1
                await asyncio.sleep(10)  # Back off on error
    
    async def _fetch_and_process_messages(self) -> None:
        """Fetch messages from SendBlue API and process them."""
        try:
            # Determine time filter
            since_time = self._last_poll_time.isoformat() if self._last_poll_time else None
            
            # Use individual client for message fetching
            async with SendBlueClient() as client:
                result = await client.get_messages(limit=50, since_time=since_time)
                
                if not result["success"]:
                    logger.warning("[%s] Failed to fetch messages: %s", "SendBlue", result.get("error"))
                    self._stats["api_errors"] += 1
                    return
                
                messages = result["messages"]
            
            # Process each message
            for message in messages:
                await self._process_message(message)
            
            # Update poll time
            if messages:
                self._last_poll_time = datetime.now()
                self._stats["last_activity"] = datetime.now().isoformat()
                
        except Exception as e:
            logger.error("[%s] Error fetching messages: %s", "SendBlue", e, exc_info=True)
            self._stats["api_errors"] += 1
    
    async def _process_message(self, data: Dict[str, Any]) -> None:
        """Process a single message from the API."""
        try:
            # Extract message data with fallback field names
            message_id = (data.get("message_handle") or 
                         data.get("id") or 
                         data.get("messageId") or 
                         f"msg_{datetime.now().timestamp()}")
            from_number = data.get("from_number") or data.get("fromNumber")
            to_number = data.get("to_number") or data.get("toNumber")
            content = data.get("content", "").strip()
            message_type = data.get("type", "text").lower()
            
            # Validate required fields
            if not from_number or not message_id:
                logger.warning("[%s] Invalid message data: missing from_number or id", "SendBlue")
                return
            
            # Deduplicate messages
            if message_id in self._processed_messages:
                return
            self._processed_messages.add(message_id)
            
            # Skip our own messages
            if from_number == self._sendblue_config.phone_number:
                return
            
            # Only process messages sent TO us
            if to_number != self._sendblue_config.phone_number:
                return
            
            self._stats["messages_received"] += 1
            
            # Send typing indicator (using individual client)
            # Only send typing indicator for substantive messages (not commands)
            should_send_typing = content and not content.strip().startswith('/')
            if should_send_typing:
                async with SendBlueClient() as client:
                    typing_sent = await client.send_typing_indicator(from_number)
                    if typing_sent:
                        self._stats["typing_indicators_sent"] += 1
            
            # Process the message content
            if content:
                await self._handle_message_content(from_number, message_id, content, data)
            
            # Send read receipt  
            async with SendBlueClient() as client:
                await client.send_read_receipt(from_number)
            
        except Exception as e:
            logger.error("[%s] Error processing message: %s", "SendBlue", e, exc_info=True)
    
    async def _handle_message_content(self, from_number: str, message_id: str, 
                                    content: str, raw_data: Dict[str, Any]) -> None:
        """Handle the actual message content and send to gateway."""
        try:
            # Build source information (if gateway available)
            if hasattr(self, 'build_source'):
                source = self.build_source(
                    chat_id=from_number,
                    chat_name=from_number,  # SendBlue doesn't provide contact names
                    chat_type="dm",
                    user_id=from_number,
                    user_name=from_number,
                )
                
                # Create message event
                event = MessageEvent(
                    text=content,
                    message_type=MessageType.TEXT if raw_data.get("type") == "text" else MessageType.OTHER,
                    source=source,
                    message_id=message_id,
                    raw_message=raw_data,
                )
                
                # Send to gateway for processing (with timeout to prevent hangs)
                try:
                    await asyncio.wait_for(self.handle_message(event), timeout=30.0)
                except asyncio.TimeoutError:
                    logger.error("[%s] Gateway message handling timed out for /approve or complex message from %s", 
                               "SendBlue", from_number)
            else:
                # Fallback for testing
                logger.info("[%s] Message from %s: %s", "SendBlue", from_number, content)
                
        except Exception as e:
            logger.error("[%s] Error in message handler: %s", "SendBlue", e)
    
    async def send_message(self, recipient: str, message: str, **kwargs) -> bool:
        """Send a message via SendBlue API."""
        try:
            # Use individual client for sending
            async with SendBlueClient() as client:
                result = await client.send_message(
                    number=recipient,
                    content=message,
                    media_url=kwargs.get("media_url")
                )
                
                if result["success"]:
                    self._stats["messages_sent"] += 1
                    self._stats["last_activity"] = datetime.now().isoformat()
                    
                    if self._sendblue_config.debug:
                        logger.debug("[%s] Message sent to %s (status: %s)", 
                                   "SendBlue", recipient, result.get("status_code"))
                    return True
                else:
                    logger.error("[%s] Failed to send message to %s: %s", 
                               "SendBlue", recipient, result.get("error"))
                    self._stats["api_errors"] += 1
                    return False
                
        except Exception as e:
            logger.error("[%s] Error sending message to %s: %s", "SendBlue", recipient, e)
            self._stats["api_errors"] += 1
            return False
    
    async def send_typing(self, chat_id: str, metadata=None) -> None:
        """Send typing indicator (interface method for gateway framework)."""
        try:
            # Use individual client for typing indicator
            async with SendBlueClient() as client:
                success = await client.send_typing_indicator(chat_id)
                if success:
                    self._stats["typing_indicators_sent"] += 1
        except Exception as e:
            logger.debug("[%s] Typing indicator error for %s: %s", "SendBlue", chat_id, e)
    
    # Abstract method implementations
    async def send(self, chat_id: str, content: str, reply_to=None, metadata=None) -> SendResult:
        """Send a message via SendBlue (BasePlatformAdapter interface)."""
        success = await self.send_message(chat_id, content)
        return SendResult(success=success, message_id=None)
    
    async def get_chat_info(self, chat_id: str):
        """Get chat info for a phone number."""
        return {
            "name": chat_id,
            "type": "dm",
            "platform": "sendblue"
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get adapter statistics."""
        return {
            **self._stats,
            "polling_active": self._polling,
            "processed_message_count": len(self._processed_messages),
            "config_valid": self._sendblue_config.is_valid(),
            "poll_interval": self._sendblue_config.poll_interval
        }