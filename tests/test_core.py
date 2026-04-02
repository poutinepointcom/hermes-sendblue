"""
Test suite for SendBlue core client functionality.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
import os

from ..core import SendBlueConfig, SendBlueClient


class TestSendBlueConfig:
    """Test SendBlue configuration management."""
    
    def test_config_initialization(self):
        """Test configuration initialization with environment variables."""
        with patch.dict(os.environ, {
            'SENDBLUE_API_KEY': 'test_key',
            'SENDBLUE_SECRET_KEY': 'test_secret', 
            'SENDBLUE_PHONE_NUMBER': '+1234567890'
        }):
            config = SendBlueConfig()
            assert config.api_key == 'test_key'
            assert config.secret_key == 'test_secret'
            assert config.phone_number == '+1234567890'
            assert config.is_valid()
    
    def test_config_invalid(self):
        """Test invalid configuration detection."""
        with patch.dict(os.environ, {}, clear=True):
            config = SendBlueConfig()
            assert not config.is_valid()
    
    def test_config_headers(self):
        """Test HTTP headers generation."""
        config = SendBlueConfig()
        config.api_key = 'test_key'
        config.secret_key = 'test_secret'
        
        headers = config.get_headers()
        assert headers['sb-api-key-id'] == 'test_key'
        assert headers['sb-api-secret-key'] == 'test_secret'
        assert headers['Content-Type'] == 'application/json'


class TestSendBlueClient:
    """Test SendBlue API client functionality."""
    
    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        config = SendBlueConfig()
        config.api_key = 'test_key'
        config.secret_key = 'test_secret'
        config.phone_number = '+1234567890'
        return config
    
    @pytest.fixture
    def client(self, config):
        """Create a test client."""
        return SendBlueClient(config)
    
    @pytest.mark.asyncio
    async def test_client_context_manager(self, client):
        """Test client as async context manager."""
        with patch.object(client, 'connect', return_value=True) as mock_connect:
            with patch.object(client, 'disconnect') as mock_disconnect:
                async with client:
                    pass
                mock_connect.assert_called_once()
                mock_disconnect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_message_success(self, client):
        """Test successful message sending."""
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_session.post.return_value.__aenter__.return_value = mock_response
        client._session = mock_session
        
        result = await client.send_message('+1234567890', 'Test message')
        
        assert result['success'] is True
        assert result['status_code'] == 200
        mock_session.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_message_failure(self, client):
        """Test message sending failure."""
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.text.return_value = 'Bad Request'
        mock_session.post.return_value.__aenter__.return_value = mock_response
        client._session = mock_session
        
        result = await client.send_message('+1234567890', 'Test message')
        
        assert result['success'] is False
        assert result['status_code'] == 400
        assert 'Bad Request' in result['error']
    
    @pytest.mark.asyncio
    async def test_send_message_not_connected(self, client):
        """Test message sending when client not connected."""
        with pytest.raises(RuntimeError, match="Client not connected"):
            await client.send_message('+1234567890', 'Test message')
    
    @pytest.mark.asyncio
    async def test_get_messages_success(self, client):
        """Test successful message retrieval."""
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {'data': [{'id': '1', 'content': 'Test'}]}
        mock_session.get.return_value.__aenter__.return_value = mock_response
        client._session = mock_session
        
        result = await client.get_messages(limit=10)
        
        assert result['success'] is True
        assert len(result['messages']) == 1
        assert result['messages'][0]['content'] == 'Test'
    
    @pytest.mark.asyncio
    async def test_typing_indicator(self, client):
        """Test typing indicator sending."""
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_session.post.return_value.__aenter__.return_value = mock_response
        client._session = mock_session
        
        result = await client.send_typing_indicator('+1234567890')
        
        assert result is True
        mock_session.post.assert_called_once()
    
    @pytest.mark.asyncio 
    async def test_typing_indicator_failure(self, client):
        """Test typing indicator failure (normal for some numbers)."""
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_session.post.return_value.__aenter__.return_value = mock_response
        client._session = mock_session
        
        result = await client.send_typing_indicator('+1234567890')
        
        assert result is False


if __name__ == '__main__':
    pytest.main([__file__])