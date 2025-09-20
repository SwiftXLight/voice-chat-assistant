import pytest
import os
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import tempfile

# Set test environment variables
os.environ["OPENAI_API_KEY"] = "test-key-12345"

@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    from main import app
    return TestClient(app)

@pytest.fixture
def mock_openai():
    """Mock OpenAI client for testing"""
    with patch('main.openai') as mock:
        # Mock transcription response - return string directly
        mock.audio.transcriptions.create.return_value = "Hello, this is a test transcription"
        
        # Mock chat completion response
        mock_choice = Mock()
        mock_choice.message.content = "Hello! This is a test response from the AI assistant."
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock.chat.completions.create.return_value = mock_response
        
        yield mock

@pytest.fixture
def sample_audio_file():
    """Create a temporary audio file for testing"""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        # Write some dummy audio data
        f.write(b"RIFF" + b"\x00" * 40)  # Minimal WAV header
        f.flush()
        yield f.name
    
    # Clean up
    try:
        os.unlink(f.name)
    except FileNotFoundError:
        pass

@pytest.fixture
def large_audio_file():
    """Create a large audio file for testing file size limits"""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        # Write 30MB of data (exceeds 25MB limit)
        f.write(b"RIFF" + b"\x00" * (30 * 1024 * 1024))
        f.flush()
        yield f.name
    
    # Clean up
    try:
        os.unlink(f.name)
    except FileNotFoundError:
        pass
