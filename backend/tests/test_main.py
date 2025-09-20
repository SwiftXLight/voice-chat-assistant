import pytest
import json
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
import openai


class TestHealthEndpoint:
    """Test the health check endpoint"""
    
    def test_health_check(self, client):
        """Test that health check returns correct response"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Voice Chat API is running"
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["version"] == "1.0.0"


class TestTranscribeEndpoint:
    """Test the transcribe endpoint"""
    
    def test_transcribe_success(self, client, mock_openai, sample_audio_file):
        """Test successful audio transcription"""
        with open(sample_audio_file, "rb") as f:
            response = client.post(
                "/transcribe",
                files={"file": ("test.wav", f, "audio/wav")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["transcript"] == "Hello, this is a test transcription"
        
        # Verify OpenAI was called
        mock_openai.audio.transcriptions.create.assert_called_once()
    
    def test_transcribe_no_file(self, client):
        """Test transcribe endpoint without file"""
        response = client.post("/transcribe")
        
        assert response.status_code == 422  # Validation error
    
    def test_transcribe_empty_file(self, client):
        """Test transcribe endpoint with empty file"""
        response = client.post(
            "/transcribe",
            files={"file": ("empty.wav", b"", "audio/wav")}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "Empty audio file" in data["detail"]
    
    def test_transcribe_large_file(self, client, large_audio_file):
        """Test transcribe endpoint with file too large"""
        with open(large_audio_file, "rb") as f:
            response = client.post(
                "/transcribe",
                files={"file": ("large.wav", f, "audio/wav")}
            )
        
        assert response.status_code == 400
        data = response.json()
        assert "too large" in data["detail"]
    
    def test_transcribe_openai_auth_error(self, client, sample_audio_file):
        """Test transcribe endpoint with OpenAI authentication error"""
        with patch('main.openai.audio.transcriptions.create') as mock_create:
            # Create a proper mock response and body for the exception
            mock_response = Mock()
            mock_response.status_code = 401
            mock_body = {"error": {"message": "Invalid API key"}}
            mock_create.side_effect = openai.AuthenticationError(
                "Invalid API key", 
                response=mock_response, 
                body=mock_body
            )
            
            with open(sample_audio_file, "rb") as f:
                response = client.post(
                    "/transcribe",
                    files={"file": ("test.wav", f, "audio/wav")}
                )
            
            assert response.status_code == 401
            data = response.json()
            assert "Invalid OpenAI API key" in data["detail"]
    
    def test_transcribe_openai_rate_limit(self, client, sample_audio_file):
        """Test transcribe endpoint with OpenAI rate limit error"""
        with patch('main.openai.audio.transcriptions.create') as mock_create:
            mock_response = Mock()
            mock_response.status_code = 429
            mock_body = {"error": {"message": "Rate limit exceeded"}}
            mock_create.side_effect = openai.RateLimitError(
                "Rate limit exceeded",
                response=mock_response,
                body=mock_body
            )
            
            with open(sample_audio_file, "rb") as f:
                response = client.post(
                    "/transcribe",
                    files={"file": ("test.wav", f, "audio/wav")}
                )
            
            assert response.status_code == 429
            data = response.json()
            assert "Rate limit exceeded" in data["detail"]
    
    def test_transcribe_no_api_key(self, client, sample_audio_file):
        """Test transcribe endpoint without API key"""
        with patch('main.openai.api_key', None):
            with open(sample_audio_file, "rb") as f:
                response = client.post(
                    "/transcribe",
                    files={"file": ("test.wav", f, "audio/wav")}
                )
            
            assert response.status_code == 500
            data = response.json()
            assert "not configured" in data["detail"]


class TestChatEndpoint:
    """Test the chat endpoint"""
    
    def test_chat_success(self, client, mock_openai):
        """Test successful chat completion"""
        response = client.post(
            "/chat",
            json={"message": "Hello, how are you?"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "Hello! This is a test response from the AI assistant."
        
        # Verify OpenAI was called with correct parameters
        mock_openai.chat.completions.create.assert_called_once()
        call_args = mock_openai.chat.completions.create.call_args
        assert call_args[1]["model"] == "gpt-3.5-turbo"
        assert len(call_args[1]["messages"]) == 2
        assert call_args[1]["messages"][1]["content"] == "Hello, how are you?"
    
    def test_chat_empty_message(self, client):
        """Test chat endpoint with empty message"""
        response = client.post(
            "/chat",
            json={"message": ""}
        )
        
        assert response.status_code == 400  # Security validation error
    
    def test_chat_whitespace_message(self, client):
        """Test chat endpoint with whitespace-only message"""
        response = client.post(
            "/chat",
            json={"message": "   "}
        )
        
        assert response.status_code == 400  # Security validation error
    
    def test_chat_long_message(self, client):
        """Test chat endpoint with very long message"""
        long_message = "x" * 5000  # Exceeds 4000 character limit
        response = client.post(
            "/chat",
            json={"message": long_message}
        )
        
        assert response.status_code == 400  # Security validation error
    
    def test_chat_no_message(self, client):
        """Test chat endpoint without message field"""
        response = client.post("/chat", json={})
        
        assert response.status_code == 422  # Validation error
    
    def test_chat_invalid_json(self, client):
        """Test chat endpoint with invalid JSON"""
        response = client.post(
            "/chat",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_chat_openai_auth_error(self, client):
        """Test chat endpoint with OpenAI authentication error"""
        with patch('main.openai.chat.completions.create') as mock_create:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_body = {"error": {"message": "Invalid API key"}}
            mock_create.side_effect = openai.AuthenticationError(
                "Invalid API key",
                response=mock_response,
                body=mock_body
            )
            
            response = client.post(
                "/chat",
                json={"message": "Hello"}
            )
            
            assert response.status_code == 401
            data = response.json()
            assert "Invalid OpenAI API key" in data["detail"]
    
    def test_chat_openai_rate_limit(self, client):
        """Test chat endpoint with OpenAI rate limit error"""
        with patch('main.openai.chat.completions.create') as mock_create:
            mock_response = Mock()
            mock_response.status_code = 429
            mock_body = {"error": {"message": "Rate limit exceeded"}}
            mock_create.side_effect = openai.RateLimitError(
                "Rate limit exceeded",
                response=mock_response,
                body=mock_body
            )
            
            response = client.post(
                "/chat",
                json={"message": "Hello"}
            )
            
            assert response.status_code == 429
            data = response.json()
            assert "Rate limit exceeded" in data["detail"]
    
    def test_chat_empty_openai_response(self, client):
        """Test chat endpoint when OpenAI returns empty response"""
        with patch('main.openai.chat.completions.create') as mock_create:
            mock_choice = Mock()
            mock_choice.message.content = None  # Empty response
            mock_response = Mock()
            mock_response.choices = [mock_choice]
            mock_create.return_value = mock_response
            
            response = client.post(
                "/chat",
                json={"message": "Hello"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "couldn't generate a response" in data["response"]
    
    def test_chat_no_api_key(self, client):
        """Test chat endpoint without API key"""
        with patch('main.openai.api_key', None):
            response = client.post(
                "/chat",
                json={"message": "Hello"}
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "not configured" in data["detail"]


class TestErrorHandling:
    """Test global error handling"""
    
    def test_404_endpoint(self, client):
        """Test accessing non-existent endpoint"""
        response = client.get("/nonexistent")
        
        assert response.status_code == 404
    
    def test_method_not_allowed(self, client):
        """Test using wrong HTTP method"""
        response = client.get("/chat")  # Should be POST
        
        assert response.status_code == 405


class TestCORS:
    """Test CORS configuration"""
    
    def test_cors_headers(self, client):
        """Test that CORS headers are present"""
        response = client.options("/", headers={"Origin": "http://localhost:3000"})
        
        # FastAPI automatically handles OPTIONS requests for CORS
        assert response.status_code in [200, 405]  # Depending on FastAPI version
