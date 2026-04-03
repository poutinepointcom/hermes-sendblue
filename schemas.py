"""
Pydantic schemas for SendBlue tool inputs and outputs.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, validator
import re


class SendMessageInput(BaseModel):
    """Input schema for sending iMessages via SendBlue."""
    
    number: str = Field(
        description="Recipient phone number in E.164 format (e.g., +1234567890)",
        example="+1234567890"
    )
    message: str = Field(
        description="Message content to send",
        max_length=1000
    )
    media_url: Optional[str] = Field(
        None,
        description="Optional URL of media to attach (image, video, audio)"
    )
    
    @validator('number')
    def validate_phone_number(cls, v):
        # Basic E.164 validation
        if not re.match(r'^\+[1-9]\d{1,14}$', v):
            raise ValueError('Phone number must be in E.164 format (e.g., +1234567890)')
        return v


class SendMessageOutput(BaseModel):
    """Output schema for send message results."""
    
    success: bool = Field(description="Whether the message was sent successfully")
    message_id: Optional[str] = Field(None, description="Unique identifier for the sent message")
    error: Optional[str] = Field(None, description="Error message if sending failed")
    recipient: str = Field(description="Phone number the message was sent to")


class ListConversationsInput(BaseModel):
    """Input schema for listing conversations."""
    
    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of conversations to return"
    )
    include_group_chats: bool = Field(
        default=True,
        description="Whether to include group conversations"
    )


class ConversationSummary(BaseModel):
    """Summary of a conversation."""
    
    contact_number: str = Field(description="Phone number of the contact")
    contact_name: Optional[str] = Field(None, description="Display name if available")
    last_message_text: str = Field(description="Preview of the most recent message")
    last_message_time: str = Field(description="Timestamp of the last message")
    unread_count: int = Field(default=0, description="Number of unread messages")
    is_group_chat: bool = Field(default=False, description="Whether this is a group conversation")


class ListConversationsOutput(BaseModel):
    """Output schema for conversation list."""
    
    conversations: List[ConversationSummary] = Field(description="List of conversation summaries")
    total_count: int = Field(description="Total number of conversations available")


class GetMessagesInput(BaseModel):
    """Input schema for retrieving messages from a conversation."""
    
    number: Optional[str] = Field(
        None,
        description="Phone number to get messages from (E.164 format). If not provided, returns all messages",
        example="+123****7890"
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of messages to return"
    )
    since_timestamp: Optional[str] = Field(
        None,
        description="Only return messages after this timestamp (ISO format)"
    )
    
    @validator('number')
    def validate_phone_number(cls, v):
        if v and not re.match(r'^\\+[1-9]\\d{1,14}$', v):
            raise ValueError('Phone number must be in E.164 format (e.g., +123****7890)')
        return v


class MessageDetail(BaseModel):
    """Details of a single message."""
    
    message_id: str = Field(description="Unique identifier for the message")
    content: str = Field(description="Message text content")
    timestamp: Optional[str] = Field(None, description="When the message was sent/received")
    is_from_me: bool = Field(description="Whether this message was sent by us")
    sender_number: str = Field(description="Phone number of the sender")
    message_type: str = Field(default="text", description="Type of message (text, image, etc.)")
    media_url: Optional[str] = Field(None, description="URL of attached media if any")


class GetMessagesOutput(BaseModel):
    """Output schema for message retrieval."""
    
    messages: List[MessageDetail] = Field(description="List of messages in the conversation")
    conversation_with: str = Field(description="Phone number of the conversation partner")
    total_count: int = Field(description="Total number of messages in conversation")
    has_more: bool = Field(default=False, description="Whether there are more messages available")


class SendBlueStatsOutput(BaseModel):
    """Output schema for SendBlue usage statistics."""
    
    messages_sent_today: int = Field(description="Number of messages sent today")
    api_calls_today: int = Field(description="Number of API calls made today")
    remaining_quota: Optional[int] = Field(None, description="Remaining API quota if available")
    last_activity: Optional[str] = Field(None, description="Timestamp of last SendBlue activity")