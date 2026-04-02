"""SendBlue iMessage integration plugin for Hermes.

This plugin enables sending and receiving iMessages through the SendBlue API,
allowing Hermes to communicate via iMessage with external contacts.

Inspired by the openclaw-sendblue integration patterns.
"""

import logging
import os

from . import schemas, tools

logger = logging.getLogger(__name__)

# Track plugin activity
_plugin_stats = {
    "messages_sent": 0,
    "conversations_accessed": 0,
    "messages_retrieved": 0,
}


def _on_session_start(session_id: str, model: str, platform: str, **kwargs) -> None:
    """Hook: runs when a new session starts."""
    logger.info(
        "SendBlue plugin active for session %s (model: %s, platform: %s)", 
        session_id, model, platform
    )
    
    # Check if credentials are available
    api_key = os.getenv("SENDBLUE_API_KEY")
    secret_key = os.getenv("SENDBLUE_SECRET_KEY")
    
    if not api_key or not secret_key:
        logger.warning(
            "SendBlue credentials not found in environment. "
            "Set SENDBLUE_API_KEY and SENDBLUE_SECRET_KEY to enable iMessage integration."
        )


def register(ctx) -> None:
    """Wire schemas to handlers and register hooks.
    
    This function is called exactly once at startup to register
    all tools and hooks provided by this plugin.
    """
    # Register SendBlue tools
    ctx.register_tool(
        name="sendblue_send_message",
        toolset="sendblue",
        schema=schemas.SENDBLUE_SEND_MESSAGE,
        handler=tools.sendblue_send_message,
        description="Send iMessages via SendBlue API",
        emoji="📱"
    )
    
    ctx.register_tool(
        name="sendblue_list_conversations", 
        toolset="sendblue",
        schema=schemas.SENDBLUE_LIST_CONVERSATIONS,
        handler=tools.sendblue_list_conversations,
        description="List iMessage conversations",
        emoji="💬"
    )
    
    ctx.register_tool(
        name="sendblue_get_messages",
        toolset="sendblue", 
        schema=schemas.SENDBLUE_GET_MESSAGES,
        handler=tools.sendblue_get_messages,
        description="Get messages from conversation",
        emoji="📥"
    )
    
    # Register session hook
    ctx.register_hook("on_session_start", _on_session_start)
    
    logger.info("SendBlue plugin registered: 3 tools, 1 hook")


# Plugin metadata for introspection
__version__ = "1.0.0"
__author__ = "poutine.com"
__description__ = "SendBlue/iMessage integration for Hermes"