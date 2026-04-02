# Changelog

All notable changes to the Hermes SendBlue Plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-04-02

### 🚨 Critical iMessage Approval System Fix

### Fixed

#### Approval System Deadlocks
- **Complete agent unresponsiveness** - Fixed deadlock when processing dangerous command approvals via iMessage
- **Approval response blocking** - Dangerous commands no longer cause the agent to become permanently stuck  
- **Message handler deadlock** - Approval commands now processed independently to prevent pipeline blocking
- **Command recognition improvements** - Natural approval responses ("approve", "deny") automatically prefixed with "/"

#### Root Cause Resolution
- **Concurrent message processing conflict** - Original dangerous command blocked `_message_handler()` waiting for approval
- **Approval response processing failure** - `/approve` responses couldn't be processed due to blocked message pipeline  
- **Architecture redesign** - Approval responses now bypass normal message flow via separate async tasks
- **Session state isolation** - Prevents approval processing from corrupting main message handling

### Added
- **Independent approval command detection** - Preprocessing layer identifies approval responses before normal routing
- **Async approval resolution** - Non-blocking approval processing via dedicated `resolve_gateway_approval()` calls
- **User feedback on approval** - Immediate confirmation when approval responses are processed
- **Command preprocessing** - Automatic conversion of natural approval language to proper command format

---

## [1.1.0] - 2026-04-02

### 🔧 Critical Fixes & Testing Infrastructure

This release resolves major stability issues and adds comprehensive testing infrastructure.

### Fixed

#### Gateway Stability
- **Async import hangs** - Eliminated shared client singleton that caused import timeouts
- **Plugin registration failures** - Added proper `register(ctx)` function with lazy imports  
- **Gateway platform loading errors** - Fixed corrupted configuration lines
- **Install script path issues** - Corrected `sendblue_adapter.py` → `sendblue_platform.py` source path

#### Architecture Improvements  
- **Individual client instances** - Each operation uses `async with SendBlueClient()` context managers
- **No shared state** - Eliminates race conditions and import-time async calls
- **Simplified error handling** - Context managers ensure proper cleanup
- **Install script idempotency** - Safe to run multiple times without corruption

### Added

#### Comprehensive CI Testing
- **Fresh install testing** - Validates clean Hermes environment installation
- **Idempotent install testing** - Ensures repeat installs don't break existing setups
- **Import validation** - Catches async hang issues automatically  
- **Gateway compatibility testing** - Simulates platform loading without hanging
- **Automated regression prevention** - Runs on every push/PR to main branch

#### Development Infrastructure
- **GitHub Actions CI** - 4 comprehensive test jobs covering all failure modes
- **Local testing suite** - `test_core_functionality.py` for quick validation
- **Branch standardization** - Migrated to `main` branch from `master`

### Changed

#### Architecture Refactor
- **From:** Shared client singleton with connection pooling
- **To:** Individual async context manager instances per operation
- **Benefit:** Eliminates import-time async calls and race conditions

#### Plugin Registration
- **From:** Direct imports during plugin load
- **To:** Lazy imports in `register(ctx)` function
- **Benefit:** Plugin loads without hanging, proper error handling

### Technical Details

#### Async Pattern Change
```python
# OLD (caused hangs):
client = get_shared_client()
await client.connect()

# NEW (stable):  
async with SendBlueClient() as client:
    result = await client.send_message(...)
```

#### CI Coverage
- ✅ Import stability (no async timeouts)
- ✅ Fresh Hermes installation scenario
- ✅ Already-modified Hermes installation scenario  
- ✅ Gateway platform loading compatibility
- ✅ Install script syntax and path validation

### Migration Notes

No user action required - all changes are backward compatible. The plugin will work exactly the same but with improved stability and reliability.

---

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