"""
SendBlue tools for manual iMessage operations.

Refactored to use the unified core client for better maintainability
and consistent error handling across the plugin.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Import schemas only (no async code)
try:
    # Try relative imports first (when used as plugin)
    from .schemas import (
        SendMessageInput, SendMessageOutput,
        ListConversationsInput, ListConversationsOutput, ConversationSummary,
        GetMessagesInput, GetMessagesOutput, MessageDetail,
        SendBlueStatsOutput
    )
except ImportError:
    # Fallback to absolute imports (when testing directly)
    from schemas import (
        SendMessageInput, SendMessageOutput,
        ListConversationsInput, ListConversationsOutput, ConversationSummary,
        GetMessagesInput, GetMessagesOutput, MessageDetail,
        SendBlueStatsOutput
    )

logger = logging.getLogger(__name__)

# Plugin statistics tracking
_plugin_stats = {
    "messages_sent": 0,
    "api_calls": 0,
    "last_activity": None,
    "gateway_active": False
}


async def sendblue_send_message(input_data: SendMessageInput) -> SendMessageOutput:
    """
    Send an iMessage to a phone number via SendBlue API.
    
    Args:
        input_data: Message details including recipient number and content
        
    Returns:
        SendMessageOutput with success status and details
    """
    try:
        # Create client each time to avoid import-time async issues
        try:
            from .core import SendBlueClient, SendBlueConfig
        except ImportError:
            from core import SendBlueClient, SendBlueConfig
        
        async with SendBlueClient() as client:
            result = await client.send_message(
                number=input_data.number,
                content=input_data.message,
                media_url=input_data.media_url
            )
            
            # Update stats
            _plugin_stats["api_calls"] += 1
            _plugin_stats["last_activity"] = datetime.now().isoformat()
            
            if result["success"]:
                _plugin_stats["messages_sent"] += 1
                return SendMessageOutput(
                    success=True,
                    message_id=None,  # SendBlue doesn't return message IDs
                    recipient=input_data.number
                )
            else:
                return SendMessageOutput(
                    success=False,
                    error=result.get("error", "Unknown error"),
                    recipient=input_data.number
                )
            
    except Exception as e:
        logger.error("Error in sendblue_send_message: %s", e, exc_info=True)
        return SendMessageOutput(
            success=False,
            error=f"Internal error: {str(e)}",
            recipient=input_data.number
        )


async def sendblue_list_conversations(input_data: ListConversationsInput) -> ListConversationsOutput:
    """
    List recent message conversations.
    
    Args:
        input_data: Parameters including limit and filters
        
    Returns:
        ListConversationsOutput with conversation summaries
    """
    try:
        # Create client each time to avoid import-time async issues
        try:
            from .core import SendBlueClient, SendBlueConfig
        except ImportError:
            from core import SendBlueClient, SendBlueConfig
        
        async with SendBlueClient() as client:
            result = await client.get_messages(limit=input_data.limit * 5)  # Get more to find unique conversations
            
            _plugin_stats["api_calls"] += 1
            _plugin_stats["last_activity"] = datetime.now().isoformat()
            
            if not result["success"]:
                return ListConversationsOutput(
                    conversations=[],
                    total_count=0
                )
            
            # Group messages by sender to create conversation summaries
            conversations_map = {}
            
            for msg in result["messages"]:
                sender = msg.get("from_number") or msg.get("fromNumber", "Unknown")
                if sender == SendBlueConfig().phone_number:
                    continue  # Skip our own messages
                
                if sender not in conversations_map:
                    conversations_map[sender] = {
                        "contact_number": sender,
                        "contact_name": None,  # SendBlue doesn't provide names
                        "last_message_text": msg.get("content", "")[:100],
                        "last_message_time": msg.get("created_at") or msg.get("createdAt", ""),
                        "unread_count": 0,  # Would need to track read state
                        "is_group_chat": False  # SendBlue primarily handles 1:1 chats
                    }
            
            conversations = [
                ConversationSummary(**conv_data) 
                for conv_data in list(conversations_map.values())[:input_data.limit]
            ]
            
            return ListConversationsOutput(
                conversations=conversations,
                total_count=len(conversations_map)
            )
        
    except Exception as e:
        logger.error("Error in sendblue_list_conversations: %s", e, exc_info=True)
        return ListConversationsOutput(
            conversations=[],
            total_count=0
        )


async def sendblue_get_messages(input_data: GetMessagesInput) -> GetMessagesOutput:
    """
    Get messages from a specific conversation.
    
    Args:
        input_data: Parameters including phone number and limit
        
    Returns:
        GetMessagesOutput with message details
    """
    try:
        # Create client each time to avoid import-time async issues
        try:
            from .core import SendBlueClient, SendBlueConfig
        except ImportError:
            from core import SendBlueClient, SendBlueConfig
        
        async with SendBlueClient() as client:
            result = await client.get_messages(
                limit=input_data.limit,
                since_time=input_data.since_timestamp
            )
            
            _plugin_stats["api_calls"] += 1
            _plugin_stats["last_activity"] = datetime.now().isoformat()
            
            if not result["success"]:
                return GetMessagesOutput(
                    messages=[],
                    conversation_with=input_data.number or "all",
                    total_count=0,
                    has_more=False
                )
            
            # Filter messages for the specific conversation (or return all if no number specified)
            config = SendBlueConfig()
            conversation_messages = []
            
            for msg in result["messages"]:
                from_number = msg.get("from_number") or msg.get("fromNumber", "")
                to_number = msg.get("to_number") or msg.get("toNumber", "")
                
                # Include messages to/from the specified number, or all messages if no number specified
                if not input_data.number or from_number == input_data.number or to_number == input_data.number:
                    conversation_messages.append(MessageDetail(
                        message_id=str(msg.get("message_handle") or msg.get("id", "")),
                        content=msg.get("content", ""),
                        timestamp=msg.get("created_at") or msg.get("createdAt"),
                        is_from_me=from_number == config.phone_number,
                        sender_number=from_number,
                        message_type=msg.get("type", "text"),
                        media_url=msg.get("media_url")
                    ))
            
            return GetMessagesOutput(
                messages=conversation_messages,
                conversation_with=input_data.number or "all",
                total_count=len(conversation_messages),
                has_more=len(result["messages"]) >= input_data.limit
            )
        
    except Exception as e:
        logger.error("Error in sendblue_get_messages: %s", e, exc_info=True)
        return GetMessagesOutput(
            messages=[],
            conversation_with=getattr(input_data, 'number', None) or "all",
            total_count=0,
            has_more=False
        )


async def sendblue_get_stats() -> SendBlueStatsOutput:
    """
    Get SendBlue usage statistics and plugin status.
    
    Returns:
        SendBlueStatsOutput with usage statistics
    """
    try:
        # Import here to avoid async/import issues
        try:
            from .core import SendBlueConfig
        except ImportError:
            from core import SendBlueConfig
        
        # Update activity status
        config = SendBlueConfig()
        _plugin_stats["gateway_active"] = config.is_valid()
        
        return SendBlueStatsOutput(
            messages_sent_today=_plugin_stats["messages_sent"],
            api_calls_today=_plugin_stats["api_calls"],
            remaining_quota=None,  # SendBlue doesn't expose quota in API
            last_activity=_plugin_stats["last_activity"]
        )
        
    except Exception as e:
        logger.error("Error in sendblue_get_stats: %s", e, exc_info=True)
        return SendBlueStatsOutput(
            messages_sent_today=0,
            api_calls_today=0,
            remaining_quota=None,
            last_activity=None
        )


def get_plugin_stats() -> Dict[str, Any]:
    """Get current plugin statistics for internal use."""
    return _plugin_stats.copy()


def update_plugin_stats(**kwargs) -> None:
    """Update plugin statistics."""
    _plugin_stats.update(kwargs)


def register(ctx):
    """Main registration function called by Hermes plugin system."""
    register_tools(ctx)


def register_tools(ctx):
    """Register SendBlue tools with the plugin context."""
    
    # Wrapper functions for sync API - handle all gateway parameters
    def send_message_handler(params=None, task_id=None, user_task=None, **kwargs):
        try:
            # Safely handle parameters to avoid slice object errors
            if params and isinstance(params, dict):
                # Filter out non-hashable values that might cause slice errors
                clean_params = {}
                for k, v in params.items():
                    if k not in ['task_id', 'user_task']:
                        # Ensure we don't pass slice objects or other non-hashable types
                        if isinstance(v, (str, int, float, bool, type(None))):
                            clean_params[k] = v
            else:
                clean_params = {}
            input_data = SendMessageInput(**clean_params)
            result = asyncio.run(sendblue_send_message(input_data))
            result_dict = result.model_dump() if hasattr(result, 'model_dump') else result.__dict__
            return json.dumps(result_dict)
        except Exception as e:
            logger.error("Error in send_message_handler: %s", e, exc_info=True)
            return json.dumps({"error": f"Handler error: {str(e)}"})
    
    def list_conversations_handler(params=None, task_id=None, user_task=None, **kwargs):
        try:
            # Safely handle parameters to avoid slice object errors
            if params and isinstance(params, dict):
                # Filter out non-hashable values that might cause slice errors
                clean_params = {}
                for k, v in params.items():
                    if k not in ['task_id', 'user_task']:
                        # Ensure we don't pass slice objects or other non-hashable types
                        if isinstance(v, (str, int, float, bool, type(None))):
                            clean_params[k] = v
            else:
                clean_params = {}
            input_data = ListConversationsInput(**clean_params)
            result = asyncio.run(sendblue_list_conversations(input_data))
            result_dict = result.model_dump() if hasattr(result, 'model_dump') else result.__dict__
            return json.dumps(result_dict)
        except Exception as e:
            logger.error("Error in list_conversations_handler: %s", e, exc_info=True)
            return json.dumps({"error": f"Handler error: {str(e)}"})
    
    def get_messages_handler(params=None, task_id=None, user_task=None, **kwargs):
        try:
            # Safely handle parameters to avoid slice object errors
            if params and isinstance(params, dict):
                # Filter out non-hashable values that might cause slice errors
                clean_params = {}
                for k, v in params.items():
                    if k not in ['task_id', 'user_task']:
                        # Ensure we don't pass slice objects or other non-hashable types
                        if isinstance(v, (str, int, float, bool, type(None))):
                            clean_params[k] = v
            else:
                clean_params = {}
            input_data = GetMessagesInput(**clean_params)
            result = asyncio.run(sendblue_get_messages(input_data))
            result_dict = result.model_dump() if hasattr(result, 'model_dump') else result.__dict__
            return json.dumps(result_dict)
        except Exception as e:
            logger.error("Error in get_messages_handler: %s", e, exc_info=True)
            return json.dumps({"error": f"Handler error: {str(e)}"})
    
    def get_stats_handler(args=None, **kwargs):
        try:
            result = asyncio.run(sendblue_get_stats())
            result_dict = result.model_dump() if hasattr(result, 'model_dump') else result.__dict__
            return json.dumps(result_dict)
        except Exception as e:
            logger.error("Error in get_stats_handler: %s", e, exc_info=True)
            return json.dumps({"error": f"Handler error: {str(e)}"})
    
    # Tool schemas
    send_message_schema = {
        "type": "object",
        "properties": {
            "number": {"type": "string", "description": "Phone number in E.164 format"},
            "message": {"type": "string", "description": "Message to send"},
            "media_url": {"type": "string", "description": "Optional media URL"}
        },
        "required": ["number", "message"]
    }
    
    list_conversations_schema = {
        "type": "object", 
        "properties": {
            "limit": {"type": "integer", "default": 10, "description": "Max conversations to return"},
            "include_group_chats": {"type": "boolean", "default": True, "description": "Include group chats"}
        }
    }
    
    get_messages_schema = {
        "type": "object",
        "properties": {
            "number": {"type": "string", "description": "Phone number in E.164 format (optional - if not provided, returns all messages)"},
            "limit": {"type": "integer", "default": 20, "description": "Max messages to return"},
            "since_timestamp": {"type": "string", "description": "Only messages after this timestamp"}
        }
    }
    
    get_stats_schema = {"type": "object", "properties": {}}
    
    # Register tools with Hermes API
    ctx.register_tool("sendblue_send_message", "hermes-sendblue", send_message_schema, send_message_handler)
    ctx.register_tool("sendblue_list_conversations", "hermes-sendblue", list_conversations_schema, list_conversations_handler)
    ctx.register_tool("sendblue_get_messages", "hermes-sendblue", get_messages_schema, get_messages_handler)
    ctx.register_tool("sendblue_get_stats", "hermes-sendblue", get_stats_schema, get_stats_handler)
    
    logger.info("Registered 4 SendBlue tools with unified core client")


# No cleanup needed with per-request client instances
async def cleanup_api_session():
    """No cleanup needed with individual client instances."""
    # With per-request clients, no shared resources to clean up
    pass