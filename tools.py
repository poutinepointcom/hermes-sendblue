"""
SendBlue tools for manual iMessage operations.

These tools work alongside the gateway platform adapter to provide
both manual control and automated messaging capabilities.
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin

import aiohttp

try:
    from .schemas import (
        SendMessageInput, SendMessageOutput,
        ListConversationsInput, ListConversationsOutput, ConversationSummary,
        GetMessagesInput, GetMessagesOutput, MessageDetail,
        SendBlueStatsOutput
    )
except ImportError:
    # Fallback for direct execution
    from schemas import (
        SendMessageInput, SendMessageOutput,
        ListConversationsInput, ListConversationsOutput, ConversationSummary,
        GetMessagesInput, GetMessagesOutput, MessageDetail,
        SendBlueStatsOutput
    )

logger = logging.getLogger(__name__)

# Global session for API calls
_api_session = None


def _get_sendblue_config() -> Dict[str, str]:
    """Get SendBlue configuration from environment."""
    return {
        "api_key": os.getenv("SENDBLUE_API_KEY", ""),
        "secret_key": os.getenv("SENDBLUE_SECRET_KEY", ""),
        "phone_number": os.getenv("SENDBLUE_PHONE_NUMBER", ""),
        "api_base": "https://api.sendblue.com/api/"
    }


async def _get_api_session() -> aiohttp.ClientSession:
    """Get or create the API session with proper headers."""
    global _api_session
    
    if _api_session is None or _api_session.closed:
        config = _get_sendblue_config()
        
        if not all([config["api_key"], config["secret_key"]]):
            raise ValueError(
                "SendBlue credentials not found. Set SENDBLUE_API_KEY and SENDBLUE_SECRET_KEY"
            )
        
        _api_session = aiohttp.ClientSession(
            headers={
                "sb-api-key-id": config["api_key"],
                "sb-api-secret-key": config["secret_key"],
                "Content-Type": "application/json"
            },
            timeout=aiohttp.ClientTimeout(total=30)
        )
    
    return _api_session


async def sendblue_send_message(input_data: SendMessageInput) -> SendMessageOutput:
    """
    Send an iMessage to a phone number via SendBlue API.
    
    Args:
        input_data: Message details including recipient number and content
        
    Returns:
        SendMessageOutput with success status and message ID
    """
    try:
        session = await _get_api_session()
        config = _get_sendblue_config()
        
        url = urljoin(config["api_base"], "send-message")
        payload = {
            "number": input_data.number,
            "from_number": config["phone_number"],
            "content": input_data.message
        }
        
        # Add media if provided
        if input_data.media_url:
            payload["media_url"] = input_data.media_url
            # If there's media, content becomes the caption
            if not input_data.message.strip():
                payload["content"] = "📎"  # Emoji for media without caption
        
        async with session.post(url, json=payload) as resp:
            if resp.status == 200:
                response_data = await resp.json()
                message_id = response_data.get("id") or response_data.get("messageId")
                
                logger.info("Successfully sent message to %s", input_data.number)
                return SendMessageOutput(
                    success=True,
                    message_id=message_id,
                    recipient=input_data.number
                )
            else:
                error_text = await resp.text()
                logger.error("Failed to send message: %d - %s", resp.status, error_text)
                return SendMessageOutput(
                    success=False,
                    error=f"API error {resp.status}: {error_text}",
                    recipient=input_data.number
                )
                
    except Exception as e:
        logger.error("Error sending SendBlue message: %s", e, exc_info=True)
        return SendMessageOutput(
            success=False,
            error=f"Request failed: {str(e)}",
            recipient=input_data.number
        )


async def sendblue_list_conversations(input_data: ListConversationsInput) -> ListConversationsOutput:
    """
    List recent iMessage conversations via SendBlue API.
    
    Args:
        input_data: Query parameters including limit and filters
        
    Returns:
        ListConversationsOutput with conversation summaries
    """
    try:
        session = await _get_api_session()
        config = _get_sendblue_config()
        
        url = urljoin(config["api_base"], "v2/messages")
        params = {
            "limit": min(input_data.limit * 3, 150),  # Get more to deduplicate
            "order_by": "createdAt",
            "order_direction": "desc"
        }
        
        async with session.get(url, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                messages = data.get("data", []) if isinstance(data, dict) else []
                
                # Group messages by conversation partner
                conversations = {}
                our_number = config["phone_number"]
                
                for msg in messages:
                    from_num = msg.get("from_number") or msg.get("fromNumber")
                    to_num = msg.get("to_number") or msg.get("toNumber") 
                    content = msg.get("content", "").strip()
                    timestamp = msg.get("created_at") or msg.get("createdAt")
                    
                    if not from_num or not content:
                        continue
                        
                    # Determine conversation partner
                    if from_num == our_number:
                        # We sent this message
                        partner = to_num
                    else:
                        # We received this message  
                        partner = from_num
                        
                    if not partner or partner == our_number:
                        continue
                        
                    # Skip group chats if not requested
                    is_group = len(partner.split(",")) > 1 or "+" not in partner
                    if is_group and not input_data.include_group_chats:
                        continue
                    
                    # Track most recent message per conversation
                    if partner not in conversations:
                        conversations[partner] = {
                            "contact_number": partner,
                            "last_message_text": content[:100],  # Preview
                            "last_message_time": timestamp or "",
                            "is_group_chat": is_group,
                            "messages_count": 1
                        }
                    else:
                        # Update if this message is newer (handle None timestamps)
                        current_time = conversations[partner]["last_message_time"] or ""
                        new_time = timestamp or ""
                        if new_time > current_time:
                            conversations[partner]["last_message_text"] = content[:100]
                            conversations[partner]["last_message_time"] = new_time
                        conversations[partner]["messages_count"] += 1
                
                # Convert to list and sort by recency
                conversation_list = []
                for conv_data in conversations.values():
                    conversation_list.append(ConversationSummary(
                        contact_number=conv_data["contact_number"],
                        contact_name=None,  # SendBlue doesn't provide contact names
                        last_message_text=conv_data["last_message_text"],
                        last_message_time=conv_data["last_message_time"],
                        unread_count=0,  # Would need additional API to determine
                        is_group_chat=conv_data["is_group_chat"]
                    ))
                
                # Sort by last message time (newest first) and limit
                conversation_list.sort(
                    key=lambda x: x.last_message_time, 
                    reverse=True
                )
                conversation_list = conversation_list[:input_data.limit]
                
                logger.info("Retrieved %d conversations", len(conversation_list))
                return ListConversationsOutput(
                    conversations=conversation_list,
                    total_count=len(conversations)
                )
                
            else:
                error_text = await resp.text()
                logger.error("Failed to list conversations: %d - %s", resp.status, error_text)
                return ListConversationsOutput(
                    conversations=[],
                    total_count=0
                )
                
    except Exception as e:
        logger.error("Error listing conversations: %s", e, exc_info=True)
        return ListConversationsOutput(
            conversations=[],
            total_count=0
        )


async def sendblue_get_messages(input_data: GetMessagesInput) -> GetMessagesOutput:
    """
    Get messages from a specific conversation via SendBlue API.
    
    Args:
        input_data: Query parameters including contact number and limit
        
    Returns:
        GetMessagesOutput with message details
    """
    try:
        session = await _get_api_session()
        config = _get_sendblue_config()
        
        url = urljoin(config["api_base"], "v2/messages")
        params = {
            "limit": min(input_data.limit, 100),
            "order_by": "createdAt",
            "order_direction": "desc"
        }
        
        # Add timestamp filter if provided
        if input_data.since_timestamp:
            params["created_at_gte"] = input_data.since_timestamp
            
        async with session.get(url, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                all_messages = data.get("data", []) if isinstance(data, dict) else []
                
                # Filter messages for this specific conversation
                our_number = config["phone_number"]
                target_number = input_data.number
                conversation_messages = []
                
                for msg in all_messages:
                    from_num = msg.get("from_number") or msg.get("fromNumber")
                    to_num = msg.get("to_number") or msg.get("toNumber")
                    content = msg.get("content", "").strip()
                    
                    if not content or not from_num:
                        continue
                    
                    # Check if this message is part of the conversation
                    is_relevant = (
                        (from_num == target_number and to_num == our_number) or  # They sent to us
                        (from_num == our_number and to_num == target_number)     # We sent to them
                    )
                    
                    if is_relevant:
                        message_id = msg.get("message_handle") or msg.get("id") or msg.get("messageId")
                        timestamp = msg.get("created_at") or msg.get("createdAt")
                        message_type = msg.get("type", "text").lower()
                        media_url = msg.get("media_url") or msg.get("mediaUrl")
                        
                        conversation_messages.append(MessageDetail(
                            message_id=str(message_id) if message_id else "",
                            content=content,
                            timestamp=timestamp or "",
                            is_from_me=(from_num == our_number),
                            sender_number=from_num,
                            message_type=message_type,
                            media_url=media_url
                        ))
                
                # Sort chronologically (oldest first for conversation view)
                conversation_messages.sort(key=lambda x: x.timestamp)
                
                # Limit results
                if len(conversation_messages) > input_data.limit:
                    conversation_messages = conversation_messages[-input_data.limit:]
                    has_more = True
                else:
                    has_more = False
                    
                logger.info("Retrieved %d messages from conversation with %s", 
                          len(conversation_messages), input_data.number)
                          
                return GetMessagesOutput(
                    messages=conversation_messages,
                    conversation_with=input_data.number,
                    total_count=len(conversation_messages),
                    has_more=has_more
                )
                
            else:
                error_text = await resp.text()
                logger.error("Failed to get messages: %d - %s", resp.status, error_text)
                return GetMessagesOutput(
                    messages=[],
                    conversation_with=input_data.number,
                    total_count=0,
                    has_more=False
                )
                
    except Exception as e:
        logger.error("Error getting messages: %s", e, exc_info=True)
        return GetMessagesOutput(
            messages=[],
            conversation_with=input_data.number,
            total_count=0,
            has_more=False
        )


async def sendblue_get_stats() -> SendBlueStatsOutput:
    """
    Get SendBlue usage statistics and plugin status.
    
    Returns:
        SendBlueStatsOutput with usage statistics
    """
    # This would require a dedicated stats endpoint from SendBlue
    # For now, return basic plugin activity
    try:
        from . import get_plugin_stats
        stats = get_plugin_stats()
    except ImportError:
        # Fallback if not in plugin context
        stats = {"messages_sent": 0, "gateway_active": False}
    
    return SendBlueStatsOutput(
        messages_sent_today=stats.get("messages_sent", 0),
        api_calls_today=0,  # Would need API tracking
        remaining_quota=None,  # SendBlue doesn't expose this
        last_activity=datetime.now().isoformat() if stats.get("gateway_active") else None
    )


def register_tools(ctx):
    """Register SendBlue tools with the plugin context."""
    
    # Wrapper functions for sync API - handle all gateway parameters
    def send_message_handler(params=None, task_id=None, user_task=None, **kwargs):
        # Remove gateway parameters from params if present
        if params:
            clean_params = {k: v for k, v in params.items() if k not in ['task_id', 'user_task']}
        else:
            clean_params = {}
        input_data = SendMessageInput(**clean_params)
        result = asyncio.run(sendblue_send_message(input_data))
        return result.model_dump() if hasattr(result, 'model_dump') else result.__dict__
    
    def list_conversations_handler(params=None, task_id=None, user_task=None, **kwargs):
        # Remove gateway parameters from params if present
        if params:
            clean_params = {k: v for k, v in params.items() if k not in ['task_id', 'user_task']}
        else:
            clean_params = {}
        input_data = ListConversationsInput(**clean_params)
        result = asyncio.run(sendblue_list_conversations(input_data))
        return result.model_dump() if hasattr(result, 'model_dump') else result.__dict__
    
    def get_messages_handler(params=None, task_id=None, user_task=None, **kwargs):
        # Remove gateway parameters from params if present
        if params:
            clean_params = {k: v for k, v in params.items() if k not in ['task_id', 'user_task']}
        else:
            clean_params = {}
        input_data = GetMessagesInput(**clean_params)
        result = asyncio.run(sendblue_get_messages(input_data))
        return result.model_dump() if hasattr(result, 'model_dump') else result.__dict__
    
    def get_stats_handler(params=None, task_id=None, user_task=None, **kwargs):
        # get_stats doesn't need any parameters
        result = asyncio.run(sendblue_get_stats())
        # Convert pydantic object to dict for gateway
        return result.model_dump() if hasattr(result, 'model_dump') else result.__dict__
    
    # SendMessage tool schema
    send_message_schema = {
        "type": "object",
        "properties": {
            "number": {"type": "string", "description": "Phone number in E.164 format"},
            "message": {"type": "string", "description": "Message to send"},
            "media_url": {"type": "string", "description": "Optional media URL"}
        },
        "required": ["number", "message"]
    }
    
    # ListConversations tool schema  
    list_conversations_schema = {
        "type": "object", 
        "properties": {
            "limit": {"type": "integer", "default": 10, "description": "Max conversations to return"}
        }
    }
    
    # GetMessages tool schema
    get_messages_schema = {
        "type": "object",
        "properties": {
            "number": {"type": "string", "description": "Phone number in E.164 format"},
            "limit": {"type": "integer", "default": 20, "description": "Max messages to return"}
        },
        "required": ["number"]
    }
    
    # GetStats tool schema (no params)
    get_stats_schema = {"type": "object", "properties": {}}
    
    # Register tools with Hermes API (name, toolset, schema, handler)
    ctx.register_tool("sendblue_send_message", "hermes-sendblue", send_message_schema, send_message_handler)
    ctx.register_tool("sendblue_list_conversations", "hermes-sendblue", list_conversations_schema, list_conversations_handler)
    ctx.register_tool("sendblue_get_messages", "hermes-sendblue", get_messages_schema, get_messages_handler)
    ctx.register_tool("sendblue_get_stats", "hermes-sendblue", get_stats_schema, get_stats_handler)
    
    logger.info("Registered 4 SendBlue tools")


# Cleanup function for session management
async def cleanup_api_session():
    """Close the API session when plugin is unloaded."""
    global _api_session
    if _api_session and not _api_session.closed:
        await _api_session.close()
        _api_session = None