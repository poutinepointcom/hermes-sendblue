# Changelog

All notable changes to the Hermes SendBlue Plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-04-02

### 🎉 Initial Release

This is the first production-ready release of the Hermes SendBlue Plugin, providing comprehensive iMessage integration for Hermes Agent.

### Added

#### Core Functionality
- **Complete iMessage integration** via SendBlue API
- **Gateway platform adapter** for real-time message processing
- **Manual tools** for programmatic message management
- **Typing indicators** with proper SendBlue API implementation
- **Message deduplication** to prevent duplicate processing
- **Cross-platform continuity** - seamless switching between platforms

#### Architecture & Performance
- **Unified core client** (`core.py`) eliminates code duplication
- **Session management** with connection pooling and reuse
- **Async/await** throughout for optimal performance
- **Type safety** with comprehensive Pydantic schemas
- **Error handling** with retries and graceful degradation
- **Statistics tracking** for monitoring and debugging

#### Tools & APIs
- `sendblue_send_message` - Send iMessages with media support
- `sendblue_list_conversations` - Browse recent message threads  
- `sendblue_get_messages` - Retrieve conversation history
- `sendblue_get_stats` - Monitor plugin performance and usage

#### Gateway Integration
- **Real-time message polling** with configurable intervals
- **Automatic typing indicators** when composing responses
- **Read receipts** for better user experience
- **Robust error recovery** for network issues and API failures
- **Message validation** and sanitization

#### Development & Quality
- **Comprehensive documentation** with examples and troubleshooting
- **Type hints** throughout codebase
- **Modular design** for easy maintenance and testing
- **Configuration validation** with helpful error messages
- **Debug logging** for development and troubleshooting

### Technical Details

#### API Endpoints Implemented
- `POST /api/send-message` - Message sending
- `GET /api/v2/messages` - Message retrieval  
- `POST /api/send-typing-indicator` - Typing indicators
- `POST /api/read-receipt` - Read receipts

#### Environment Variables
- `SENDBLUE_API_KEY` (required) - API authentication key
- `SENDBLUE_SECRET_KEY` (required) - API secret key  
- `SENDBLUE_PHONE_NUMBER` (required) - SendBlue phone number (E.164)
- `SENDBLUE_POLL_INTERVAL` (optional) - Polling interval in seconds (default: 5)
- `SENDBLUE_DEBUG` (optional) - Enable debug logging (default: false)

#### Dependencies
- `aiohttp` - Async HTTP client for SendBlue API
- `pydantic` - Type-safe data validation and serialization
- Standard Python 3.8+ async libraries

#### Error Handling
- Connection failures with exponential backoff
- API rate limiting with respect for SendBlue quotas
- Malformed message data with validation and sanitization
- Network timeouts with configurable retry logic
- Authentication failures with clear error messages

#### Performance Optimizations
- HTTP session reuse across API calls
- Bounded message deduplication cache (prevents memory leaks)
- Configurable polling intervals to balance responsiveness vs. API usage
- Async message processing to prevent blocking
- Lazy client initialization to reduce startup time

### Security & Privacy
- API credentials never logged or exposed
- Message content sanitization for safety
- E.164 phone number validation
- Secure session management with proper cleanup
- No persistent storage of message content

### Installation & Compatibility
- **Hermes Agent** >= 2.0 (gateway platform support required)
- **Python** >= 3.8 (async/await and type hints)
- **SendBlue API** access with valid credentials
- **Linux/macOS** - Primary testing platforms
- **Windows** - Expected to work but not extensively tested

### Documentation
- Comprehensive README with installation guide
- API reference with examples
- Troubleshooting guide with common solutions
- Architecture documentation for developers
- Performance tuning recommendations

### Future Roadmap
- Group chat support (when SendBlue API supports it)
- Message history persistence (optional)
- Rich media handling improvements
- Webhook support as alternative to polling
- Integration with Hermes contact management
- Plugin marketplace compatibility

---

**Installation:**
```bash
hermes plugins install https://github.com/poutinepointcom/hermes-sendblue.git
```

**Minimum Requirements:**
- Hermes Agent >= 2.0
- Python >= 3.8  
- SendBlue API account
- Valid iMessage-enabled phone number

**Known Limitations:**
- Group chats not supported by SendBlue API
- Message history limited to SendBlue retention period
- Typing indicators may not work for all carriers/regions
- Read receipts require recipient iMessage support

For detailed installation and usage instructions, see [README.md](README.md).