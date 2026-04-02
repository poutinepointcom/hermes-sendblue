"""
Self-installation script for SendBlue Gateway Platform Integration.

This script automatically integrates SendBlue as a gateway platform
without requiring manual core source modifications.
"""

import os
import shutil
from pathlib import Path
from textwrap import dedent

HERMES_HOME = Path(os.getenv("HERMES_HOME", Path.home() / ".hermes"))
HERMES_AGENT_PATH = HERMES_HOME / "hermes-agent"


def install_gateway_platform():
    """Install SendBlue as a gateway platform."""
    print("🔧 Installing SendBlue gateway platform integration...")
    
    # 1. Copy adapter to gateway platforms directory
    platforms_dir = HERMES_AGENT_PATH / "gateway" / "platforms"
    platforms_dir.mkdir(parents=True, exist_ok=True)
    
    adapter_source = Path(__file__).parent / "sendblue_adapter.py"
    adapter_dest = platforms_dir / "sendblue.py"
    
    shutil.copy2(adapter_source, adapter_dest)
    print(f"✅ Copied adapter to {adapter_dest}")
    
    # 2. Add platform to config enum
    config_file = HERMES_AGENT_PATH / "gateway" / "config.py"
    if config_file.exists():
        add_platform_to_config(config_file)
    
    # 3. Add platform to tools config
    tools_config_file = HERMES_AGENT_PATH / "hermes_cli" / "tools_config.py"
    if tools_config_file.exists():
        add_platform_to_tools_config(tools_config_file)
    
    # 4. Add platform factory entry
    gateway_run_file = HERMES_AGENT_PATH / "gateway" / "run.py"
    if gateway_run_file.exists():
        add_platform_factory_entry(gateway_run_file)
    
    print("🎉 SendBlue gateway platform installed successfully!")


def add_platform_to_config(config_file: Path):
    """Add SENDBLUE to Platform enum in config.py."""
    content = config_file.read_text()
    
    # Check if already added
    if 'SENDBLUE = "sendblue"' in content:
        print("✅ Platform already in config.py")
        return
    
    # Find the Platform class and add SENDBLUE
    if 'class Platform(str, Enum):' in content:
        # Add after the last platform entry
        lines = content.split('\n')
        inserted = False
        for i, line in enumerate(lines):
            if 'MATTERMOST = "mattermost"' in line:
                lines.insert(i + 1, '    SENDBLUE = "sendblue"')
                inserted = True
                break
        
        if inserted:
            config_file.write_text('\n'.join(lines))
            print("✅ Added SENDBLUE to Platform enum")
        else:
            print("⚠️ Could not find insertion point in config.py")
    else:
        print("⚠️ Could not find Platform class in config.py")


def add_platform_to_tools_config(tools_config_file: Path):
    """Add sendblue to PLATFORMS dict in tools_config.py."""
    content = tools_config_file.read_text()
    
    # Check if already added
    if '"sendblue"' in content and 'SendBlue' in content:
        print("✅ Platform already in tools_config.py")
        return
    
    # Find PLATFORMS dict and add sendblue entry
    if 'PLATFORMS = {' in content:
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if '"mattermost":' in line and 'Mattermost' in line:
                # Add after mattermost line
                new_line = '    "sendblue": {"label": "📱 SendBlue (iMessage)", "default_toolset": "hermes-sendblue"},'
                lines.insert(i + 1, new_line)
                tools_config_file.write_text('\n'.join(lines))
                print("✅ Added sendblue to PLATFORMS dict")
                return
        
        print("⚠️ Could not find insertion point in tools_config.py")
    else:
        print("⚠️ Could not find PLATFORMS dict in tools_config.py")


def add_platform_factory_entry(gateway_run_file: Path):
    """Add SendBlue factory entry to gateway/run.py."""
    content = gateway_run_file.read_text()
    
    # Check if already added
    if 'Platform.SENDBLUE:' in content:
        print("✅ Platform factory entry already exists")
        return
    
    # Find the factory method and add SendBlue case
    factory_code = dedent('''
        elif platform == Platform.SENDBLUE:
            from gateway.platforms.sendblue import SendBlueAdapter, check_sendblue_requirements
            if not check_sendblue_requirements():
                logger.warning("SendBlue: aiohttp not installed or SENDBLUE_API_KEY/SECRET/PHONE_NUMBER not set")
                return None
            return SendBlueAdapter(config)
    ''').strip()
    
    # Insert before "return None" in _create_adapter method
    if 'return None' in content and '_create_adapter' in content:
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'return None' in line and i > 0:
                # Check if we're in the _create_adapter method context
                context_lines = lines[max(0, i-20):i]
                if any('_create_adapter' in l for l in context_lines):
                    # Insert our factory code before the return None
                    indent = len(line) - len(line.lstrip())
                    factory_lines = factory_code.split('\n')
                    indented_factory = [' ' * indent + l if l.strip() else l for l in factory_lines]
                    
                    # Insert with proper spacing
                    lines[i:i] = [''] + indented_factory + ['']
                    gateway_run_file.write_text('\n'.join(lines))
                    print("✅ Added SendBlue platform factory entry")
                    return
        
        print("⚠️ Could not find insertion point for platform factory")
    else:
        print("⚠️ Could not find _create_adapter method in gateway/run.py")


def backup_core_files():
    """Create backup of core files before modification."""
    backup_dir = Path(__file__).parent / "backups"
    backup_dir.mkdir(exist_ok=True)
    
    files_to_backup = [
        HERMES_AGENT_PATH / "gateway" / "config.py",
        HERMES_AGENT_PATH / "hermes_cli" / "tools_config.py", 
        HERMES_AGENT_PATH / "gateway" / "run.py"
    ]
    
    for file_path in files_to_backup:
        if file_path.exists():
            backup_path = backup_dir / f"{file_path.name}.backup"
            shutil.copy2(file_path, backup_path)
            print(f"📦 Backed up {file_path.name}")


def uninstall_gateway_platform():
    """Remove SendBlue gateway platform integration."""
    print("🧹 Uninstalling SendBlue gateway platform...")
    
    # Remove adapter file
    adapter_file = HERMES_AGENT_PATH / "gateway" / "platforms" / "sendblue.py"
    if adapter_file.exists():
        adapter_file.unlink()
        print("✅ Removed adapter file")
    
    # TODO: Remove from config files (restore from backup)
    backup_dir = Path(__file__).parent / "backups"
    if backup_dir.exists():
        print("💡 Restore core files from backups/ directory if needed")
    
    print("🎉 SendBlue gateway platform uninstalled!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "uninstall":
        uninstall_gateway_platform()
    else:
        backup_core_files()
        install_gateway_platform()