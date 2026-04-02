"""
Plugin hooks for SendBlue integration survival and lifecycle management.
"""

import logging
from pathlib import Path

from . import install

logger = logging.getLogger(__name__)


def on_session_start(session_id: str, model: str, platform: str, **kwargs):
    """Hook called when a session starts."""
    if platform == "sendblue":
        logger.info("SendBlue session started - session_id: %s, model: %s", session_id, model)


def on_plugin_install(**kwargs):
    """Hook called when plugin is installed."""
    logger.info("Installing SendBlue gateway platform integration...")
    try:
        install.install_gateway_platform()
        return {"success": True, "message": "SendBlue gateway platform installed"}
    except Exception as e:
        logger.error("Failed to install SendBlue gateway platform: %s", e)
        return {"success": False, "error": str(e)}


def on_hermes_update(version: str = None, **kwargs):
    """Hook called when Hermes is updated - re-install integration."""
    logger.info("Hermes updated to %s - checking SendBlue integration...", version)
    
    # Check if our integration is still intact
    hermes_home = Path(kwargs.get("hermes_home", Path.home() / ".hermes"))
    adapter_file = hermes_home / "hermes-agent" / "gateway" / "platforms" / "sendblue.py"
    
    if not adapter_file.exists():
        logger.info("SendBlue integration missing after update - reinstalling...")
        try:
            install.install_gateway_platform()
            return {"success": True, "message": "SendBlue integration restored after update"}
        except Exception as e:
            logger.error("Failed to restore SendBlue after update: %s", e)
            return {"success": False, "error": str(e)}
    else:
        logger.info("SendBlue integration intact after update")
        return {"success": True, "message": "SendBlue integration verified"}


def register_hooks(ctx):
    """Register all hooks with the plugin context."""
    ctx.register_hook("on_session_start", on_session_start)