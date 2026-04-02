"""
Hermes SendBlue Plugin - Production-ready iMessage integration.

This plugin provides comprehensive iMessage support for Hermes Agent via
the SendBlue API, including real-time messaging, typing indicators, and
cross-platform continuity.
"""

__version__ = "1.0.0"
__author__ = "poutine.com"
__license__ = "MIT"

from . import schemas, tools, core

# Plugin metadata
PLUGIN_NAME = "sendblue"
PLUGIN_VERSION = __version__
PLUGIN_DESCRIPTION = "Production-ready iMessage integration for Hermes Agent via SendBlue API"

# Export main components
__all__ = [
    "schemas",
    "tools", 
    "core",
    "PLUGIN_NAME",
    "PLUGIN_VERSION", 
    "PLUGIN_DESCRIPTION"
]