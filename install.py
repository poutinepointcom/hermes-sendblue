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
    
    if adapter_source.exists():
        shutil.copy2(adapter_source, adapter_dest)
        print(f"✅ Copied adapter to {adapter_dest}")
    else:
        print(f"⚠️ Adapter source not found: {adapter_source}")
    
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
    
    # 5. Add platform to gateway setup UI
    gateway_setup_file = HERMES_AGENT_PATH / "hermes_cli" / "gateway.py"
    if gateway_setup_file.exists():
        add_platform_to_gateway_setup(gateway_setup_file)
    
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
    
    # Check if already added with more specific detection
    if 'elif platform == Platform.SENDBLUE:' in content:
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
    
    # Insert before the final "return None" in _create_adapter method
    if '_create_adapter' in content:
        lines = content.split('\n')
        
        # Find the final return None in the _create_adapter method
        in_create_adapter = False
        final_return_none_line = None
        
        for i, line in enumerate(lines):
            if 'def _create_adapter(' in line:
                in_create_adapter = True
                continue
            elif in_create_adapter and line.strip().startswith('def ') and 'def _create_adapter(' not in line:
                # We've moved to the next method
                break
            elif in_create_adapter and line.strip() == 'return None':
                # This is likely the final return None
                final_return_none_line = i
        
        if final_return_none_line is not None:
            # Insert before the final return None
            indent = len(lines[final_return_none_line]) - len(lines[final_return_none_line].lstrip())
            factory_lines = factory_code.split('\n')
            indented_factory = [' ' * indent + l if l.strip() else l for l in factory_lines]
            
            # Insert with proper spacing
            lines[final_return_none_line:final_return_none_line] = [''] + indented_factory + ['']
            gateway_run_file.write_text('\n'.join(lines))
            print("✅ Added SendBlue platform factory entry")
            return
        
        print("⚠️ Could not find final return None in _create_adapter method")
    else:
        print("⚠️ Could not find _create_adapter method in gateway/run.py")


def add_platform_to_gateway_setup(gateway_setup_file: Path):
    """Add SendBlue to the gateway setup UI platform list."""
    content = gateway_setup_file.read_text()
    
    # Check if already added
    if '"sendblue"' in content and 'iMessage' in content:
        print("✅ SendBlue already in gateway setup UI")
        return
    
    # Find the _PLATFORMS array and add SendBlue entry
    sendblue_platform = dedent('''
    {
        "key": "sendblue",
        "label": "iMessage",
        "emoji": "💬",
        "token_var": "SENDBLUE_API_KEY",
        "setup_instructions": [
            "1. Sign up for SendBlue at https://sendblue.co/",
            "2. Verify your phone number — this will be used for sending iMessages",
            "3. Go to your dashboard and navigate to API Keys section",
            "4. Copy your API Key and Secret Key",
            "5. Set up your phone number in E.164 format (e.g., +1234567890)",
        ],
        "vars": [
            {"name": "SENDBLUE_API_KEY", "prompt": "API Key", "password": True,
             "help": "Your SendBlue API key from the dashboard."},
            {"name": "SENDBLUE_SECRET_KEY", "prompt": "Secret Key", "password": True,
             "help": "Your SendBlue secret key from the dashboard."},
            {"name": "SENDBLUE_PHONE_NUMBER", "prompt": "Phone number (E.164 format)", "password": False,
             "help": "Your verified phone number in E.164 format (e.g., +1234567890)."},
        ],
    },''').strip()
    
    # Find insertion point before closing bracket of _PLATFORMS
    if '_PLATFORMS = [' in content and '],\n    },\n]' in content:
        # Insert before the final closing of the array
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.strip() == ']' and i > 0:
                # Check if we're at the end of _PLATFORMS array
                context_lines = lines[max(0, i-5):i]
                if any('        ],' in l and '},' in lines[i-1] for l in context_lines):
                    # Insert SendBlue platform before the closing bracket
                    indent = len(line) - len(line.lstrip())
                    platform_lines = sendblue_platform.split('\n')
                    indented_platform = [' ' * (indent + 4) + l if l.strip() else l for l in platform_lines]
                    
                    lines[i:i] = indented_platform + ['']
                    gateway_setup_file.write_text('\n'.join(lines))
                    print("✅ Added iMessage to gateway setup UI")
                    return
        
        print("⚠️ Could not find insertion point for gateway setup UI")
    else:
        print("⚠️ Could not find _PLATFORMS array in gateway setup file")


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