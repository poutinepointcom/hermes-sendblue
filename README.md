# Hermes SendBlue Plugin 📱

**Production-ready iMessage integration for Hermes Agent** - enables bidirectional iMessage communication via SendBlue API with robust error handling, typing indicators, and cross-platform continuity.

[![GitHub release](https://img.shields.io/github/v/release/poutinepointcom/hermes-sendblue)](https://github.com/poutinepointcom/hermes-sendblue/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Hermes Agent](https://img.shields.io/badge/Hermes-Agent-blue.svg)](https://github.com/NousResearch/hermes-agent)

## ✨ Features

### 📱 Gateway Platform Integration
- **Real-time iMessage support** - Receive and respond to iMessages instantly
- **Typing indicators** - Shows "..." when Hermes is composing responses  
- **Message deduplication** - Prevents duplicate message processing
- **Robust error handling** - Gracefully handles API failures and network issues
- **Cross-platform continuity** - Start conversations on Telegram, continue via iMessage
- **Production-ready** - Optimized session management and performance

### 🛠️ Manual Tools (Optional)
- `sendblue_send_message` - Send individual iMessages programmatically
- `sendblue_list_conversations` - Browse recent message threads
- `sendblue_get_messages` - Retrieve conversation history  
- `sendblue_get_stats` - Monitor plugin usage and performance statistics

### 🏗️ Architecture
- **Individual Clients** - Each operation uses isolated async context managers
- **Async/Await** - Fully asynchronous for optimal performance  
- **Type Safety** - Comprehensive type hints and Pydantic schemas
- **Clean Resource Management** - Automatic connection cleanup via context managers
- **Error Recovery** - Automatic retries and graceful degradation
- **Comprehensive Testing** - 4-job CI suite prevents regressions

## 🚀 Installation

### Prerequisites

You'll need a [SendBlue](https://sendblue.co/) account with:
- API key and secret key
- Registered phone number for iMessage

### 1. Environment Configuration

Add these to your `~/.hermes/.env` file:

```bash
# Required
SENDBLUE_API_KEY=your_api_key_here
SENDBLUE_SECRET_KEY=your_secret_key_here  
SENDBLUE_PHONE_NUMBER=+1234567890

# Optional
SENDBLUE_POLL_INTERVAL=5        # Polling interval in seconds (default: 5)
SENDBLUE_DEBUG=true             # Enable debug logging (default: false)
```

### 2. Plugin Installation

⚠️ **Important:** This plugin modifies your Hermes Agent source code to integrate with the gateway. Backups are created automatically.

```bash
# Install from GitHub (recommended)
hermes plugins install https://github.com/poutinepointcom/hermes-sendblue.git

# Or clone and install locally
git clone https://github.com/poutinepointcom/hermes-sendblue.git
cd hermes-sendblue
hermes plugins install .
```

**What the installer does:**
1. **Copies `sendblue_platform.py`** → `hermes-agent/gateway/platforms/sendblue.py`
2. **Modifies `gateway/config.py`** → Adds `SENDBLUE = "sendblue"` to Platform enum  
3. **Modifies `hermes_cli/tools_config.py`** → Registers SendBlue in PLATFORMS dict
4. **Creates backups** → Saves originals to `~/.hermes/plugins/sendblue/backups/`

### 3. Gateway Integration

```bash
# Restart gateway to load the new platform
systemctl --user restart hermes-gateway

# Or using Hermes CLI
hermes gateway restart
```

### 4. Verification

```bash
# Check gateway logs for successful connection
hermes gateway logs | grep -i sendblue
# Expected output: [SendBlue] Connected and polling for messages

# Test plugin tools
hermes tools test sendblue_get_stats
```

### 5. First Message Test

Text your SendBlue phone number from your iPhone. You should receive an instant AI response! 🎉

**Note:** New contacts may require approval through the Hermes pairing system.

## 📋 Usage Examples

### Manual Tools

```python
# Send a message with error handling
result = sendblue_send_message(
    number="+1234567890", 
    message="Hello from Hermes! 🤖",
    media_url="https://example.com/image.png"  # Optional
)
print(f"Success: {result['success']}")

# List recent conversations
conversations = sendblue_list_conversations(
    limit=10,
    include_group_chats=True
)
for conv in conversations['conversations']:
    print(f"{conv['contact_number']}: {conv['last_message_text']}")

# Get conversation history  
messages = sendblue_get_messages(
    number="+1234567890",
    limit=50,
    since_timestamp="2026-04-01T00:00:00Z"  # Optional
)
print(f"Found {len(messages['messages'])} messages")

# Monitor plugin performance
stats = sendblue_get_stats()
print(f"Messages sent today: {stats['messages_sent_today']}")
print(f"API calls made: {stats['api_calls_today']}")
```

### Gateway Platform (Automatic)

Once installed, iMessage works seamlessly like any other Hermes platform:

```bash
# Set as home channel for cron results
# (text from your iPhone to your SendBlue number)
/sethome

# Cross-platform continuity
# Start conversation on Telegram → continue via iMessage automatically
```

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SENDBLUE_API_KEY` | ✅ | - | Your SendBlue API key |
| `SENDBLUE_SECRET_KEY` | ✅ | - | Your SendBlue secret key |
| `SENDBLUE_PHONE_NUMBER` | ✅ | - | Your SendBlue phone number (E.164) |
| `SENDBLUE_POLL_INTERVAL` | ❌ | `5` | Message polling interval (seconds) |
| `SENDBLUE_DEBUG` | ❌ | `false` | Enable detailed debug logging |

### Toolset Configuration

```bash
# Configure which tools are available on which platforms
hermes tools config

# Example: Disable manual tools on production, keep gateway
hermes tools disable sendblue_send_message --platform telegram
```

## 🔧 Troubleshooting

### Connection Issues

```bash
# 1. Verify configuration
python3 -c "
import os
config = {
    'API Key': bool(os.getenv('SENDBLUE_API_KEY')),
    'Secret': bool(os.getenv('SENDBLUE_SECRET_KEY')), 
    'Phone': os.getenv('SENDBLUE_PHONE_NUMBER')
}
for key, value in config.items():
    print(f'{key}: {value}')
"

# 2. Check gateway status
hermes gateway status

# 3. Test API connectivity  
hermes tools test sendblue_get_stats
```

### Performance Tuning

```bash
# Adjust polling frequency for your use case
echo "SENDBLUE_POLL_INTERVAL=10" >> ~/.hermes/.env  # Less frequent polling

# Enable debug mode for troubleshooting
echo "SENDBLUE_DEBUG=true" >> ~/.hermes/.env
hermes gateway restart
```

### Manual Reinstallation

```bash
# If integration breaks after Hermes update
cd ~/.hermes/plugins/sendblue
python3 install.py  # Reinstall gateway integration
hermes gateway restart
```

### Complete Removal

```bash
# 1. Remove gateway integration (restores original Hermes files)
cd ~/.hermes/plugins/sendblue
python3 install.py uninstall

# 2. Remove plugin completely
hermes plugins uninstall sendblue
```

**What uninstall does:**
- ✅ Restores original `gateway/config.py` from backup
- ✅ Restores original `hermes_cli/tools_config.py` from backup  
- ✅ Removes `gateway/platforms/sendblue.py`
- ✅ Your Hermes installation returns to its original state

## 📊 Monitoring & Stats

### Built-in Statistics

```python
stats = sendblue_get_stats()
print(f"""
📱 SendBlue Plugin Statistics:
- Messages sent today: {stats['messages_sent_today']}
- API calls made: {stats['api_calls_today']}  
- Last activity: {stats['last_activity']}
- Remaining quota: {stats['remaining_quota'] or 'Unknown'}
""")
```

### Gateway Logs

```bash
# Monitor real-time activity
hermes gateway logs --follow | grep -i sendblue

# Check error patterns
hermes gateway logs | grep -E "(ERROR|WARN).*[Ss]end[Bb]lue"
```

## 🏗️ Architecture Details

### Hybrid Plugin Design

This plugin uses a **hybrid approach** to integrate with Hermes gateway:

```
┌─────────────────────┐    ┌─────────────────────┐
│   Standard Plugin   │    │  Gateway Platform   │
│   (Tools & Hooks)   │◄──►│    (Auto-Install)   │
└─────────────────────┘    └─────────────────────┘
            │                         │
            ▼                         ▼
┌─────────────────────────────────────────────────┐
│        Individual SendBlue Clients              │
│  (Async Context Managers, API, Error Handling) │
└─────────────────────────────────────────────────┘
```

### Key Components

- **`core.py`** - Unified SendBlue API client with session management
- **`tools.py`** - Manual tool implementations
- **`sendblue_platform.py`** - Gateway platform adapter  
- **`schemas.py`** - Type-safe Pydantic data models
- **`install.py`** - Automated gateway integration

### Performance Features

- **Isolated Context Managers** - Clean resource management per operation
- **Async Operations** - Non-blocking I/O for optimal performance
- **Intelligent Polling** - Configurable intervals with error backoff
- **Memory Efficient** - Bounded message deduplication cache  
- **Error Recovery** - Automatic retries with exponential backoff
- **Regression Prevention** - Comprehensive CI testing on every change

## 🧪 Testing & Quality Assurance

This plugin includes comprehensive automated testing to prevent regressions:

### GitHub Actions CI
- **Fresh Install Testing** - Validates installation on clean Hermes environments
- **Idempotent Install Testing** - Ensures repeat installations don't cause corruption
- **Import Stability Testing** - Catches async hang issues before they reach users
- **Gateway Compatibility Testing** - Simulates platform loading without timeouts

### Local Testing
```bash
# Run core functionality tests
python test_core_functionality.py

# Test imports don't hang (with timeout)  
timeout 30s python -c "import core, tools, schemas; print('✅ All imports successful')"
```

### Continuous Integration
All tests run automatically on every push and pull request to the `main` branch, ensuring:
- ✅ No async import hangs that break gateway startup
- ✅ Install script works on both fresh and existing Hermes setups  
- ✅ Plugin registration functions properly
- ✅ No syntax errors or missing dependencies

## 🤝 Contributing

Built with ❤️ by [poutine.com](https://poutine.com) for the Hermes community.

### Development Setup

```bash
git clone https://github.com/poutinepointcom/hermes-sendblue.git
cd hermes-sendblue

# Install in development mode
pip install -e .

# Run tests
python -m pytest tests/

# Code quality checks
black . --check
flake8 .
mypy .
```

### Issue Reporting

Found a bug or have a feature request? Please [open an issue](https://github.com/poutinepointcom/hermes-sendblue/issues) with:

- Hermes version (`hermes version`)
- Plugin version (`hermes plugins list`)
- Error logs (with sensitive data removed)
- Steps to reproduce

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

---

**🔗 Links:**
- [SendBlue API Documentation](https://docs.sendblue.com/)
- [Hermes Agent Project](https://github.com/NousResearch/hermes-agent)  
- [Plugin Repository](https://github.com/poutinepointcom/hermes-sendblue)
- [Issues & Support](https://github.com/poutinepointcom/hermes-sendblue/issues)