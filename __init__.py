"""
SendBlue Hybrid Plugin for Hermes.

This plugin provides both:
1. Tools for manual SendBlue operations (send_message, list_conversations, etc.)
2. Gateway platform adapter for bidirectional iMessage integration

The gateway integration is automatically installed when the plugin is loaded,
creating a seamless iMessage experience without manual core modifications.
"""

import logging
import os

from . import hooks, schemas, tools

logger = logging.getLogger(__name__)

# Track plugin activity
_plugin_stats = {
    "messages_sent": 0,
    "conversations_accessed": 0,
    "messages_retrieved": 0,
    "gateway_active": False
}


def register(ctx):
    """Register plugin tools and hooks with Hermes."""
    # Register all tools
    tools.register_tools(ctx)
    
    # Register hooks for lifecycle management
    hooks.register_hooks(ctx)
    
    logger.info("SendBlue hybrid plugin registered - tools + gateway platform")


def on_session_start(session_id: str, model: str, platform: str, **kwargs):
    """Hook: runs when a new session starts."""
    if platform == "sendblue":
        _plugin_stats["gateway_active"] = True
        
    logger.info(
        "SendBlue plugin active for session %s (model: %s, platform: %s)", 
        session_id, model, platform
    )


def get_plugin_stats() -> dict:
    """Return plugin usage statistics."""
    return _plugin_stats.copy()


def is_configured() -> bool:
    """Check if SendBlue is properly configured."""
    required_vars = ["SENDBLUE_API_KEY", "SENDBLUE_SECRET_KEY", "SENDBLUE_PHONE_NUMBER"]
    return all(os.getenv(var) for var in required_vars)


# Plugin metadata
__version__ = "2.0.0"
__author__ = "poutine.com"
__description__ = "SendBlue/iMessage hybrid integration - tools + gateway platform"