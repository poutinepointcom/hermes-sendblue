"""
SendBlue API core client for shared functionality.

Provides a unified, DRY implementation for both gateway platform 
and manual tools to avoid code duplication.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
import os
from urllib.parse import urljoin

import aiohttp

logger = logging.getLogger(__name__)


class SendBlueConfig:
    """SendBlue API configuration management."""
    
    def __init__(self):
        self.api_key = os.getenv("SENDBLUE_API_KEY", "")
        self.secret_key = os.getenv("SENDBLUE_SECRET_KEY", "")
        self.phone_number = os.getenv("SENDBLUE_PHONE_NUMBER", "")
        self.api_base = "https://api.sendblue.com/api/"
        self.timeout = 30
        self.poll_interval = int(os.getenv("SENDBLUE_POLL_INTERVAL", "5"))
        self.debug = os.getenv("SENDBLUE_DEBUG", "").lower() == "true"
    
    def is_valid(self) -> bool:
        """Check if all required configuration is present."""
        return bool(self.api_key and self.secret_key and self.phone_number)
    
    def get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for SendBlue API requests."""
        return {
            "sb-api-key-id": self.api_key,
            "sb-api-secret-key": self.secret_key,
            "Content-Type": "application/json"
        }


class SendBlueClient:
    """
    Unified SendBlue API client for both gateway and tools.
    
    Provides session management, error handling, and common API operations.
    """
    
    def __init__(self, config: Optional[SendBlueConfig] = None):
        self.config = config or SendBlueConfig()
        self._session: Optional[aiohttp.ClientSession] = None
        # Removed session lock to fix deadlock
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
    
    async def connect(self) -> bool:
        """Initialize the HTTP session and validate credentials."""
        if not self.config.is_valid():
            logger.error("SendBlue configuration is incomplete")
            return False
        
        # async with self._session_lock: # REMOVED TO FIX DEADLOCK
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers=self.config.get_headers(),
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            )
            
            # Test connection
            if not await self._test_connection():
                await self._session.close()
                self._session = None
                return False
        
        return True
    
    async def disconnect(self) -> None:
        """Clean up the HTTP session."""
        # async with self._session_lock: # REMOVED TO FIX DEADLOCK
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
    
    async def _test_connection(self) -> bool:
        """Test API connection with a minimal request."""
        try:
            url = urljoin(self.config.api_base, "v2/messages")
            params = {"limit": 1, "order_by": "createdAt", "order_direction": "desc"}
            
            async with self._session.get(url, params=params) as resp:
                if resp.status == 200:
                    if self.config.debug:
                        logger.debug("SendBlue API connection test successful")
                    return True
                else:
                    logger.error("SendBlue API test failed: %d", resp.status)
                    return False
        except Exception as e:
            logger.error("SendBlue API connection test failed: %s", e)
            return False
    
    async def send_message(self, number: str, content: str, media_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Send an iMessage via SendBlue API.
        
        Args:
            number: Recipient phone number in E.164 format
            content: Message text content
            media_url: Optional media URL to attach
            
        Returns:
            Dict with success status and details
        """
        if not self._session:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        try:
            url = urljoin(self.config.api_base, "send-message")
            payload = {
                "number": number,
                "from_number": self.config.phone_number,
                "content": content
            }
            
            if media_url:
                payload["media_url"] = media_url
            
            async with self._session.post(url, json=payload) as resp:
                if resp.status in [200, 201, 202]:  # 202 = queued/accepted
                    return {
                        "success": True,
                        "status_code": resp.status,
                        "message": "Message sent successfully"
                    }
                else:
                    error_text = await resp.text()
                    return {
                        "success": False,
                        "status_code": resp.status,
                        "error": f"API error: {error_text}"
                    }
        except Exception as e:
            logger.error("Error sending message to %s: %s", number, e)
            return {
                "success": False,
                "error": f"Request failed: {str(e)}"
            }
    
    async def get_messages(self, limit: int = 50, since_time: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch messages from SendBlue API.
        
        Args:
            limit: Maximum number of messages to return
            since_time: ISO timestamp to fetch messages after
            
        Returns:
            Dict with messages and metadata
        """
        if not self._session:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        try:
            url = urljoin(self.config.api_base, "v2/messages")
            params = {
                "limit": limit,
                "is_outbound": "false",
                "order_by": "createdAt",
                "order_direction": "desc"
            }
            
            if since_time:
                params["created_at_gte"] = since_time
            
            async with self._session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "success": True,
                        "messages": data.get("data", []) if isinstance(data, dict) else [],
                        "total_count": len(data.get("data", [])) if isinstance(data, dict) else 0
                    }
                else:
                    error_text = await resp.text()
                    return {
                        "success": False,
                        "error": f"API error {resp.status}: {error_text}"
                    }
        except Exception as e:
            logger.error("Error fetching messages: %s", e)
            return {
                "success": False,
                "error": f"Request failed: {str(e)}"
            }
    
    async def send_typing_indicator(self, number: str) -> bool:
        """
        Send typing indicator to a phone number.
        
        Args:
            number: Recipient phone number in E.164 format
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self._session:
            return False
        
        try:
            url = urljoin(self.config.api_base, "send-typing-indicator")
            payload = {
                "number": number,
                "from_number": self.config.phone_number
            }
            
            async with self._session.post(url, json=payload) as resp:
                success = resp.status in [200, 201]
                if not success and self.config.debug:
                    logger.debug("Typing indicator failed for %s: %d (normal for some numbers)", number, resp.status)
                return success
        except Exception as e:
            if self.config.debug:
                logger.debug("Typing indicator error for %s: %s", number, e)
            return False
    
    async def send_read_receipt(self, number: str) -> bool:
        """
        Send read receipt to a phone number.
        
        Args:
            number: Sender phone number in E.164 format
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self._session:
            return False
        
        try:
            url = urljoin(self.config.api_base, "read-receipt")
            payload = {"number": number}
            
            async with self._session.post(url, json=payload) as resp:
                success = resp.status in [200, 201]
                if not success and self.config.debug:
                    logger.debug("Read receipt failed for %s: %d (normal for some numbers)", number, resp.status)
                return success
        except Exception as e:
            if self.config.debug:
                logger.debug("Read receipt error for %s: %s", number, e)
            return False


# No global shared client - create fresh instances to avoid import-time async issues