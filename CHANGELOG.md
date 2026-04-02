# Changelog

All notable changes to the Hermes SendBlue Plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-04-02

### Added
- 🎉 **Initial Release** - Production-ready iMessage integration for Hermes Agent
- **Gateway Platform Integration** - Full bidirectional iMessage communication
- **Typing Indicators** - Shows "..." when Hermes is composing responses
- **Message Deduplication** - Prevents duplicate message processing
- **Cross-Platform Continuity** - Seamless conversation flow between platforms
- **Robust Error Handling** - Graceful API failure and network issue handling
- **Manual Tools** - Optional programmatic iMessage operations
  - `sendblue_send_message` - Send individual iMessages
  - `sendblue_list_conversations` - Browse recent message threads
  - `sendblue_get_messages` - Retrieve conversation history
  - `sendblue_get_stats` - Monitor plugin usage and status
- **Production Features**
  - Automatic API session management
  - Proper credential validation
  - Comprehensive logging
  - Clean uninstall support

### Technical Details
- Based on OpenClaw SendBlue implementation research
- Uses SendBlue API v2 endpoints
- Implements proper gateway platform interface
- Handles 202 (queued) status codes correctly
- Includes proper `send_typing()` interface method
- DRY code principles with helper functions
- Comprehensive error handling and logging
- Type annotations for better code maintainability

### Requirements
- SendBlue API account with API key, secret key, and phone number
- Hermes Agent v2+ (gateway platform support)
- Python packages: `aiohttp`, `pydantic`

### Supported Platforms
- iMessage (via SendBlue API)
- Cross-platform continuity with Telegram, Email, etc.