"""Tool schemas for SendBlue integration - what the LLM sees."""

SENDBLUE_SEND_MESSAGE = {
    "name": "sendblue_send_message",
    "description": (
        "Send an iMessage using SendBlue API. Use this to send messages to any "
        "phone number via iMessage. The recipient must have iMessage enabled. "
        "Supports text messages and attachments."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "to_phone": {
                "type": "string",
                "description": "Recipient phone number in E.164 format (e.g., '+1234567890')",
            },
            "message": {
                "type": "string",
                "description": "Text message content to send",
            },
            "media_url": {
                "type": "string",
                "description": "Optional URL of media attachment to send (image, video, etc.)",
            },
        },
        "required": ["to_phone", "message"],
    },
}

SENDBLUE_LIST_CONVERSATIONS = {
    "name": "sendblue_list_conversations",
    "description": (
        "List recent iMessage conversations from SendBlue. Shows conversations "
        "with message counts and last message timestamps. Use to see who you've "
        "been messaging with recently."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "Maximum number of conversations to return (default: 20, max: 100)",
                "minimum": 1,
                "maximum": 100,
            },
        },
        "required": [],
    },
}

SENDBLUE_GET_MESSAGES = {
    "name": "sendblue_get_messages",
    "description": (
        "Get messages from a specific iMessage conversation. Use this to read "
        "message history with a contact. Returns messages in chronological order."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "phone_number": {
                "type": "string",
                "description": "Phone number to get messages for in E.164 format (e.g., '+1234567890')",
            },
            "limit": {
                "type": "integer", 
                "description": "Maximum number of messages to return (default: 20, max: 100)",
                "minimum": 1,
                "maximum": 100,
            },
            "before_timestamp": {
                "type": "string",
                "description": "Optional timestamp to get messages before (ISO 8601 format)",
            },
        },
        "required": ["phone_number"],
    },
}