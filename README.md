# Hermes SendBlue Plugin

A Hermes plugin for integrating iMessage functionality via the [SendBlue API](https://sendblue.co/). This plugin enables Hermes to send and receive iMessages, making it possible to communicate with contacts through the native iOS messaging system.

**Inspired by [openclaw-sendblue](https://github.com/openclaw-sendblue)** - building on proven patterns for iMessage integration.

## Features

- **Send iMessages** - Send text messages and media to any phone number with iMessage
- **List Conversations** - View recent message threads and conversation metadata  
- **Retrieve Messages** - Get message history from specific conversations
- **Session Hooks** - Automatic credential validation and logging

## Installation

### 1. Install the Plugin

Clone this repository to your Hermes plugins directory:

```bash
cd ~/.hermes/plugins
git clone https://github.com/poutinepointcom/hermes-sendblue.git sendblue
```

Or install via pip (when published):

```bash
pip install hermes-sendblue-plugin
```

### 2. Get SendBlue API Credentials

1. Sign up for a [SendBlue account](https://sendblue.co/)
2. Get your API Key and Secret from the dashboard
3. Add them to your Hermes environment

### 3. Configure Environment

Add your SendBlue credentials to `~/.hermes/.env`:

```bash
SENDBLUE_API_KEY=your_api_key_here
SENDBLUE_SECRET_KEY=your_secret_key_here
```

### 4. Restart Hermes

```bash
hermes
```

You should see `sendblue: sendblue_send_message, sendblue_list_conversations, sendblue_get_messages` in the startup banner.

## Usage

### Send a Message

```
Send an iMessage to +1234567890 saying "Hello from Hermes!"
```

### Check Recent Conversations

```
Show me my recent iMessage conversations
```

### Get Message History

```
Get the last 10 messages from my conversation with +1234567890
```

## Tools Reference

### `sendblue_send_message`
Send an iMessage to a phone number.

**Parameters:**
- `to_phone` (required) - Phone number in E.164 format (e.g., "+1234567890")
- `message` (required) - Text content to send
- `media_url` (optional) - URL of media attachment

### `sendblue_list_conversations`
List recent iMessage conversations.

**Parameters:**
- `limit` (optional) - Number of conversations to return (1-100, default: 20)

### `sendblue_get_messages`  
Get messages from a specific conversation.

**Parameters:**
- `phone_number` (required) - Phone number in E.164 format
- `limit` (optional) - Number of messages to return (1-100, default: 20)
- `before_timestamp` (optional) - Get messages before this timestamp (ISO 8601)

## Plugin Structure

```
sendblue/
├── plugin.yaml          # Plugin manifest
├── __init__.py          # Registration and hooks
├── schemas.py           # Tool schemas for LLM
├── tools.py             # Tool implementation
├── requirements.txt     # Dependencies
├── README.md            # This file
└── after-install.md     # Post-installation guide
```

## Development

This plugin follows standard Hermes plugin conventions:

1. **Manifest** (`plugin.yaml`) - Declares tools, hooks, and requirements
2. **Schemas** (`schemas.py`) - Describes tools for the LLM
3. **Handlers** (`tools.py`) - Implements the actual functionality
4. **Registration** (`__init__.py`) - Connects everything together

### Testing

```bash
# Check plugin status
/plugins

# Test message sending (replace with real number)
Send a test message to +1234567890
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SENDBLUE_API_KEY` | Your SendBlue API Key | ✅ |
| `SENDBLUE_SECRET_KEY` | Your SendBlue Secret Key | ✅ |

### SendBlue Setup

1. Create account at [sendblue.co](https://sendblue.co/)
2. Verify your phone number for iMessage
3. Get API credentials from dashboard
4. Configure rate limits and permissions as needed

## Attribution

This plugin was inspired by and builds upon patterns established by the [openclaw-sendblue](https://github.com/openclaw-sendblue) project. We're grateful for their pioneering work in iMessage API integration.

## License

MIT License - see LICENSE file for details.

## Contributing

This is poutine.com's flagship open source contribution. Contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable  
5. Submit a pull request

## Support

- **Documentation**: See [after-install.md](after-install.md) for detailed setup
- **Issues**: Report bugs via GitHub Issues
- **Community**: Join discussions in GitHub Discussions

---

**Created by [poutine.com](https://poutine.com)** - Making AI agents more accessible and powerful.