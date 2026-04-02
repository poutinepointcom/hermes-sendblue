"""Tool handlers for SendBlue integration - the code that executes."""

import json
import logging
import os
import requests
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# SendBlue API configuration
SENDBLUE_BASE_URL = "https://api.sendblue.co/api"


def _get_sendblue_auth() -> tuple[str, str]:
    """Get SendBlue API credentials from environment."""
    api_key = os.getenv("SENDBLUE_API_KEY")
    secret_key = os.getenv("SENDBLUE_SECRET_KEY")
    
    if not api_key or not secret_key:
        raise ValueError("SENDBLUE_API_KEY and SENDBLUE_SECRET_KEY must be set")
    
    return api_key, secret_key


def _make_sendblue_request(method: str, endpoint: str, data: Optional[dict] = None) -> dict:
    """Make authenticated request to SendBlue API."""
    try:
        api_key, secret_key = _get_sendblue_auth()
        
        url = f"{SENDBLUE_BASE_URL}/{endpoint.lstrip('/')}"
        headers = {
            "sb-api-key-id": api_key,
            "sb-api-secret-key": secret_key,
            "Content-Type": "application/json",
        }
        
        response = requests.request(method, url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.warning("SendBlue API error: %d - %s", response.status_code, response.text)
            return {"error": f"API request failed: {response.status_code} {response.reason}"}
            
    except Exception as e:
        logger.exception("SendBlue request failed")
        return {"error": f"Request failed: {str(e)}"}


def sendblue_send_message(args: dict, **kwargs) -> str:
    """Send an iMessage via SendBlue API.
    
    Rules for handlers:
    1. Receive args (dict) — the parameters the LLM passed
    2. Do the work
    3. Return a JSON string — ALWAYS, even on error
    4. Accept **kwargs for forward compatibility
    """
    to_phone = args.get("to_phone", "").strip()
    message = args.get("message", "").strip()
    media_url = args.get("media_url", "").strip() or None
    
    if not to_phone or not message:
        return json.dumps({"error": "Both to_phone and message are required"})
    
    # Validate phone number format
    if not to_phone.startswith("+"):
        return json.dumps({"error": "Phone number must be in E.164 format (start with +)"})
    
    payload = {
        "number": to_phone,
        "content": message,
    }
    
    if media_url:
        payload["media_url"] = media_url
    
    result = _make_sendblue_request("POST", "/send-message", payload)
    
    if "error" in result:
        return json.dumps(result)
    
    return json.dumps({
        "success": True,
        "message": f"Message sent to {to_phone}",
        "content": message,
        "media_url": media_url,
        "timestamp": datetime.now().isoformat(),
    })


def sendblue_list_conversations(args: dict, **kwargs) -> str:
    """List recent iMessage conversations from SendBlue."""
    limit = args.get("limit", 20)
    
    if not isinstance(limit, int) or limit < 1 or limit > 100:
        limit = 20
    
    result = _make_sendblue_request("GET", f"/conversations?limit={limit}")
    
    if "error" in result:
        return json.dumps(result)
    
    # Format the response for better readability
    conversations = result.get("conversations", [])
    formatted_conversations = []
    
    for conv in conversations:
        formatted_conversations.append({
            "phone_number": conv.get("number", "Unknown"),
            "contact_name": conv.get("contact_name"),
            "last_message": conv.get("last_message", {}).get("content", ""),
            "last_message_time": conv.get("last_message", {}).get("timestamp"),
            "message_count": conv.get("message_count", 0),
            "is_group": conv.get("is_group", False),
        })
    
    return json.dumps({
        "conversations": formatted_conversations,
        "count": len(formatted_conversations),
        "limit": limit,
    })


def sendblue_get_messages(args: dict, **kwargs) -> str:
    """Get messages from a specific conversation."""
    phone_number = args.get("phone_number", "").strip()
    limit = args.get("limit", 20)
    before_timestamp = args.get("before_timestamp")
    
    if not phone_number:
        return json.dumps({"error": "phone_number is required"})
    
    if not isinstance(limit, int) or limit < 1 or limit > 100:
        limit = 20
    
    # Build query parameters
    params = f"number={phone_number}&limit={limit}"
    if before_timestamp:
        params += f"&before={before_timestamp}"
    
    result = _make_sendblue_request("GET", f"/messages?{params}")
    
    if "error" in result:
        return json.dumps(result)
    
    # Format messages for better readability
    messages = result.get("messages", [])
    formatted_messages = []
    
    for msg in messages:
        formatted_messages.append({
            "content": msg.get("content", ""),
            "from_me": msg.get("from_me", False),
            "timestamp": msg.get("timestamp"),
            "message_type": msg.get("message_type", "text"),
            "media_url": msg.get("media_url"),
            "status": msg.get("status", "unknown"),
        })
    
    return json.dumps({
        "phone_number": phone_number,
        "messages": formatted_messages,
        "count": len(formatted_messages),
        "limit": limit,
    })