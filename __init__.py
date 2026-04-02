"""
Hermes SendBlue Plugin - Production-ready iMessage integration.

This plugin provides comprehensive iMessage support for Hermes Agent via
the SendBlue API, including real-time messaging, typing indicators, and
cross-platform continuity.
"""

__version__ = "1.0.0"
__author__ = "poutine.com"
__license__ = "MIT"

# Plugin metadata
PLUGIN_NAME = "sendblue"
PLUGIN_VERSION = __version__
PLUGIN_DESCRIPTION = "Production-ready iMessage integration for Hermes Agent via SendBlue API"

# Main plugin registration function
def register(ctx):
    """Main plugin registration function called by Hermes."""
    # Import modules only when needed
    from . import tools, hooks
    
    # Register tools and hooks
    tools.register(ctx)
    hooks.register_hooks(ctx)

# Export main components
__all__ = [
    "schemas",
    "tools", 
    "core",
    "PLUGIN_NAME",
    "PLUGIN_VERSION", 
    "PLUGIN_DESCRIPTION"
]