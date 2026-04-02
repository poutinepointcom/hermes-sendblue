# Hermes SendBlue Plugin 📱

**Production-ready iMessage integration for Hermes Agent** - enables bidirectional iMessage communication via SendBlue API with both manual tools and full gateway platform integration.

## Features 🎯

### 📱 Gateway Platform Integration
- **Real-time iMessage support** - Receive and respond to iMessages instantly
- **Typing indicators** - Shows "..." when Hermes is composing responses
- **Message deduplication** - Prevents duplicate message processing
- **Robust error handling** - Gracefully handles API failures and network issues
- **Cross-platform continuity** - Start conversations on Telegram, continue via iMessage

### 🛠️ Manual Tools (Optional)
- `sendblue_send_message` - Send individual iMessages programmatically
- `sendblue_list_conversations` - Browse recent message threads
- `sendblue_get_messages` - Retrieve conversation history
- `sendblue_get_stats` - Monitor plugin usage and status

## Installation 🚀

### 1. Prerequisites

You'll need a [SendBlue](https://sendblue.co/) account with:
- API key and secret key
- Registered phone number for iMessage

### 2. Environment Variables

Add these to your `~/.hermes/.env` file:

```bash
SENDBLUE_API_KEY=your_api_key_here
SENDBLUE_SECRET_KEY=your_secret_key_here  
SENDBLUE_PHONE_NUMBER=+1234567890
```

### 3. Install Plugin

```bash
# Install from GitHub
hermes plugins install https://github.com/poutinepointcom/hermes-sendblue.git

# Or clone and install locally
git clone https://github.com/poutinepointcom/hermes-sendblue.git
cd hermes-sendblue
hermes plugins install .
```

### 4. Restart Gateway

```bash
systemctl --user restart hermes-gateway
# OR
hermes gateway restart
```

### 5. Verify Installation

Check gateway logs to confirm SendBlue is connected:

```bash
hermes gateway logs | grep -i sendblue
# You should see: [SendBlue] Connected and polling for messages
```

### 6. Test iMessage Integration

Text your SendBlue phone number from your phone. You should get an instant AI response via iMessage! 🎉

**Note:** The first message from a new number may require approval through the Hermes pairing system.

## Usage Examples 📋

### Manual Tools (from any platform)

```python
# Send a message
sendblue_send_message(number="+1234567890", message="Hello from Hermes!")

# List recent conversations  
sendblue_list_conversations(limit=10)

# Get messages from a conversation
sendblue_get_messages(number="+1234567890", limit=20)
```

### Gateway Platform (automatic)

Once installed, iMessage works like any other Hermes platform:
- Text your SendBlue number → Hermes responds via iMessage
- Set as home channel: text `/sethome` to get cron results via iMessage
- Cross-platform continuity: start conversation on Telegram, continue via iMessage

## Configuration ⚙️

### Optional Settings

```bash
# Polling interval (default: 5 seconds)
SENDBLUE_POLL_INTERVAL=5

# Enable debug logging  
SENDBLUE_DEBUG=true

# Auto-approve all users (CAUTION!)
SENDBLUE_ALLOW_ALL_USERS=false
```

### Platform-specific Toolsets

The plugin creates a `hermes-sendblue` toolset. Customize tools per platform:

```bash
hermes tools config  # Configure which tools are enabled where
```

## Troubleshooting 🔧

### Gateway Not Connecting

```bash
# Check requirements
python3 -c "
import os
print('API Key:', bool(os.getenv('SENDBLUE_API_KEY')))  
print('Secret:', bool(os.getenv('SENDBLUE_SECRET_KEY')))
print('Phone:', os.getenv('SENDBLUE_PHONE_NUMBER'))
"

# Check gateway logs
hermes gateway logs | grep -i sendblue
```

### Manual Reinstallation

If integration breaks after a Hermes update:

```bash
cd ~/.hermes/plugins/sendblue
python3 install.py  # Reinstall gateway integration
hermes gateway restart
```

### Complete Uninstall

```bash
cd ~/.hermes/plugins/sendblue  
python3 install.py uninstall  # Remove gateway integration
hermes plugins uninstall sendblue  # Remove plugin
```

## Architecture 🏗️

This plugin uses a **hybrid approach** to work around Hermes' lack of official gateway platform plugins:

1. **Standard Plugin** - Registers tools and hooks normally
2. **Self-Installation** - Automatically patches core files during installation
3. **Update Survival** - Hooks detect Hermes updates and reinstall integration
4. **Clean Uninstall** - Restores core files from backups when removed

## API Reference 📚

### Tools

#### `sendblue_send_message`
Send an iMessage to a phone number.

**Parameters:**
- `number` (str): Recipient phone number (E.164 format)
- `message` (str): Message content  
- `media_url` (str, optional): URL of media to attach

**Returns:** `{"success": bool, "message_id": str}`

#### `sendblue_list_conversations`  
List recent message conversations.

**Parameters:**
- `limit` (int): Max conversations to return (default: 10)

**Returns:** `{"conversations": [...]}`

#### `sendblue_get_messages`
Get messages from a specific conversation.

**Parameters:**
- `number` (str): Phone number to get messages from
- `limit` (int): Max messages to return (default: 20)

**Returns:** `{"messages": [...]}`

## Contributing 🤝

Built with ❤️ by [poutine.com](https://poutine.com) for the Hermes community.

Issues and PRs welcome at: https://github.com/poutinepointcom/hermes-sendblue

## License 📄

MIT License - see [LICENSE](LICENSE) file.