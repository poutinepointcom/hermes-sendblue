# SendBlue Plugin - Post-Installation Setup

Thank you for installing the Hermes SendBlue plugin! This guide will help you complete the setup and get your iMessage integration working.

## Quick Setup Checklist

- [ ] Obtain SendBlue API credentials
- [ ] Configure environment variables
- [ ] Verify plugin activation
- [ ] Test message sending
- [ ] Configure optional settings

## Step 1: Get SendBlue Credentials

### Sign up for SendBlue

1. Visit [sendblue.co](https://sendblue.co/) and create an account
2. Verify your phone number - this will be used for sending iMessages
3. Navigate to your dashboard to access API credentials

### Get API Keys

From your SendBlue dashboard:
1. Go to **API Keys** section
2. Copy your **API Key** 
3. Copy your **Secret Key**
4. Note any rate limits or usage quotas

> **Important**: Keep these credentials secure. Never commit them to version control.

## Step 2: Configure Environment

Add your credentials to Hermes environment file:

```bash
# Edit your environment file
nano ~/.hermes/.env
```

Add these lines:

```bash
# SendBlue API Configuration
SENDBLUE_API_KEY=your_api_key_here
SENDBLUE_SECRET_KEY=your_secret_key_here
```

### Alternative: System Environment

You can also set these as system environment variables:

```bash
export SENDBLUE_API_KEY="your_api_key_here"
export SENDBLUE_SECRET_KEY="your_secret_key_here"
```

## Step 3: Verify Installation

Restart Hermes to load the plugin:

```bash
hermes
```

Check that the plugin loaded successfully:

```
/plugins
```

You should see:
```
Plugins (1):
  ✓ sendblue v1.0.0 (3 tools, 1 hooks)
```

Look for SendBlue tools in the startup banner:
```
Available tools: [..., sendblue_send_message, sendblue_list_conversations, sendblue_get_messages, ...]
```

## Step 4: Test the Integration

### Send a Test Message

Try sending a message to yourself or a test contact:

```
Send an iMessage to +1234567890 saying "Testing Hermes SendBlue integration!"
```

Replace `+1234567890` with a real phone number that has iMessage enabled.

### Check Conversations

```
Show me my recent iMessage conversations
```

### Retrieve Messages

```
Get my last 5 messages with +1234567890
```

## Step 5: Troubleshooting

### Plugin Not Loading

If the plugin doesn't appear in `/plugins`:

1. Check that the plugin is in the correct directory:
   ```bash
   ls ~/.hermes/plugins/sendblue/
   # Should show: plugin.yaml, __init__.py, schemas.py, tools.py, etc.
   ```

2. Check Hermes logs for errors:
   ```bash
   tail -f ~/.hermes/logs/hermes.log
   ```

3. Verify plugin.yaml syntax:
   ```bash
   python -c "import yaml; print(yaml.safe_load(open('~/.hermes/plugins/sendblue/plugin.yaml')))"
   ```

### API Authentication Issues

If you see "credentials not found" or "authentication failed":

1. Verify environment variables are set:
   ```bash
   echo $SENDBLUE_API_KEY
   echo $SENDBLUE_SECRET_KEY
   ```

2. Check that credentials are in the correct file:
   ```bash
   grep SENDBLUE ~/.hermes/.env
   ```

3. Restart Hermes after adding credentials

### Message Sending Failures

Common issues and solutions:

| Error | Cause | Solution |
|-------|-------|----------|
| "Phone number must be in E.164 format" | Invalid number format | Use +1234567890 format |
| "API request failed: 401" | Invalid credentials | Check API key and secret |
| "API request failed: 429" | Rate limit exceeded | Wait and try again later |
| "Recipient not reachable" | Phone doesn't have iMessage | Verify recipient has iMessage |

## Step 6: Optional Configuration

### Rate Limiting

SendBlue has API rate limits. You can monitor usage:

```
What's my SendBlue usage today?
```

### Phone Number Validation

The plugin validates phone numbers must be in E.164 format:
- ✅ `+1234567890`
- ✅ `+447123456789` 
- ❌ `(123) 456-7890`
- ❌ `123-456-7890`

### Media Attachments

To send images or other media:

```
Send an iMessage to +1234567890 with the image at https://example.com/image.jpg and say "Check this out!"
```

## Advanced Usage

### Batch Operations

Send multiple messages:
```
Send "Hello!" to these contacts: +1111111111, +2222222222, +3333333333
```

### Conversation Management

Get conversation summaries:
```
Summarize my last 10 conversations
```

Check for new messages:
```
Check if I have any new messages since yesterday
```

## Getting Help

### Documentation
- Plugin README: [README.md](README.md)
- Hermes Plugin Guide: [Build a Plugin](https://hermes.dev/docs/guides/build-a-hermes-plugin)

### Support Channels
- GitHub Issues: Report bugs and feature requests
- GitHub Discussions: Community help and questions
- poutine.com: Commercial support options

### Log Files

Useful log locations:
- Hermes main log: `~/.hermes/logs/hermes.log`
- Plugin debug logs: Search for "sendblue" in logs
- SendBlue API logs: Look for HTTP request/response details

## Next Steps

🎉 **Congratulations!** Your SendBlue plugin is now configured.

Consider these next steps:

1. **Explore automation**: Set up message templates or auto-responses
2. **Monitor usage**: Track API quota and message volume
3. **Security review**: Ensure credentials are properly secured
4. **Backup contacts**: Export important conversation data
5. **Customize behavior**: Adjust plugin settings for your workflow

---

**Need help?** Open an issue at [github.com/poutinepointcom/hermes-sendblue](https://github.com/poutinepointcom/hermes-sendblue) or visit [poutine.com](https://poutine.com) for support options.