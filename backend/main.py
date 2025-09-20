from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator
import openai
import os
from dotenv import load_dotenv
import tempfile
import logging
import time
from typing import Optional
import traceback
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from security import (
    SecurityValidator, 
    SecurityHeaders, 
    create_rate_limiter, 
    get_client_ip, 
    log_security_event
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
# Try to load from parent directory first (for Docker), then current directory (for local dev)
load_dotenv("../.env")  # Docker: load from root
load_dotenv(".env")     # Local: load from backend dir if exists
load_dotenv()           # Fallback: load from current directory

app = FastAPI(title="Voice Chat API", version="1.0.0")

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Frontend production/manual setup
        "http://localhost:5173",  # Vite dev server default
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    return SecurityHeaders.add_security_headers(response)

# Initialize OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")

# Simple in-memory conversation store (use Redis/DB for production)
conversation_store = {}

# Validate API key is loaded
if not openai.api_key:
    logger.warning("OPENAI_API_KEY not found in environment variables!")
    logger.warning("Make sure to set it in .env file or environment")

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    request_id = id(request)
    logger.error(f"[{request_id}] Unhandled exception: {str(exc)}")
    logger.error(f"[{request_id}] Traceback: {traceback.format_exc()}")
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            detail="An unexpected error occurred. Please try again.",
            error_type="INTERNAL_ERROR",
            timestamp=time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
            request_id=str(request_id)
        ).model_dump()
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler with better error responses"""
    request_id = id(request)
    logger.warning(f"[{request_id}] HTTP {exc.status_code}: {exc.detail}")
    
    # Map status codes to error types
    error_type_map = {
        400: "VALIDATION_ERROR",
        401: "AUTHENTICATION_ERROR", 
        403: "AUTHORIZATION_ERROR",
        404: "NOT_FOUND_ERROR",
        429: "RATE_LIMIT_ERROR",
        500: "INTERNAL_ERROR",
        502: "SERVICE_ERROR"
    }
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            detail=exc.detail,
            error_type=error_type_map.get(exc.status_code, "UNKNOWN_ERROR"),
            timestamp=time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
            request_id=str(request_id)
        ).model_dump()
    )

# Request/Response Models
class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None  # Optional conversation tracking
    
    @field_validator('message')
    def validate_message(cls, v):
        return SecurityValidator.validate_message_content(v)

class ChatResponse(BaseModel):
    response: str

class TranscribeResponse(BaseModel):
    transcript: str

class ErrorResponse(BaseModel):
    detail: str
    error_type: str
    timestamp: str
    request_id: Optional[str] = None

class HealthResponse(BaseModel):
    message: str
    status: str
    timestamp: str
    version: str = "1.0.0"

@app.get("/", response_model=HealthResponse)
@create_rate_limiter("health")
async def root(request: Request):
    """Health check endpoint"""
    response = HealthResponse(
        message="Voice Chat API is running",
        status="healthy",
        timestamp=time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
    )
    return response

@app.post("/transcribe", response_model=TranscribeResponse)
@create_rate_limiter("transcribe")
async def transcribe_audio(request: Request, file: UploadFile = File(...)):
    """
    Transcribe audio file using OpenAI Whisper
    """
    request_id = id(request)
    logger.info(f"[{request_id}] Transcription request received")
    
    # Validate API key
    if not openai.api_key:
        logger.error(f"[{request_id}] OpenAI API key not configured")
        raise HTTPException(
            status_code=500, 
            detail="OpenAI API key not configured"
        )
    
    # Validate file
    if not file.filename:
        logger.error(f"[{request_id}] No file provided")
        log_security_event(request, "INVALID_FILE_UPLOAD", "No filename provided")
        raise HTTPException(
            status_code=400,
            detail="No audio file provided"
        )
    
    # Check file type
    allowed_types = ['audio/wav', 'audio/mp3', 'audio/mp4', 'audio/mpeg', 'audio/mpga', 'audio/m4a', 'audio/webm']
    if file.content_type and file.content_type not in allowed_types:
        logger.warning(f"[{request_id}] Unsupported file type: {file.content_type}")
        # Don't reject, as content_type might be incorrect
    
    temp_file_path = None
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            content = await file.read()
            
            # Security validation
            SecurityValidator.validate_file_upload(content, file.filename)
            
            if len(content) == 0:
                log_security_event(request, "EMPTY_FILE_UPLOAD", f"Empty file: {file.filename}")
                raise HTTPException(
                    status_code=400,
                    detail="Empty audio file provided"
                )
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        logger.info(f"[{request_id}] Saved audio file: {len(content)} bytes")
        
        # Transcribe using OpenAI Whisper
        with open(temp_file_path, "rb") as audio_file:
            transcript = openai.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
        
        logger.info(f"[{request_id}] Transcription successful: {len(transcript)} characters")
        
        return TranscribeResponse(transcript=transcript)
    
    except HTTPException:
        raise
    except openai.AuthenticationError as e:
        logger.error(f"[{request_id}] OpenAI authentication error: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Invalid OpenAI API key"
        )
    except openai.RateLimitError as e:
        logger.error(f"[{request_id}] OpenAI rate limit error: {str(e)}")
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later."
        )
    except openai.APIError as e:
        logger.error(f"[{request_id}] OpenAI API error: {str(e)}")
        raise HTTPException(
            status_code=502,
            detail="OpenAI service error. Please try again."
        )
    except Exception as e:
        logger.error(f"[{request_id}] Transcription failed: {str(e)}")
        logger.error(f"[{request_id}] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, 
            detail="Transcription failed. Please try again."
        )
    finally:
        # Clean up temp file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.info(f"[{request_id}] Cleaned up temp file")
            except Exception as e:
                logger.warning(f"[{request_id}] Failed to clean up temp file: {str(e)}")

@app.post("/chat", response_model=ChatResponse)
@create_rate_limiter("chat")
async def chat_with_gpt(request: Request, message: ChatMessage):
    """
    Get response from ChatGPT
    """
    request_id = id(request)
    logger.info(f"[{request_id}] Chat request received: {len(message.message)} characters")
    
    # Validate API key
    if not openai.api_key:
        logger.error(f"[{request_id}] OpenAI API key not configured")
        raise HTTPException(
            status_code=500, 
            detail="OpenAI API key not configured"
        )
    
    try:
        # Voice chat optimized system prompt
        system_prompt = """You are a helpful and friendly voice assistant. You're having a natural conversation through voice messages, so:

- Respond in English by default, unless the user specifically asks you to respond in another language
- If a user explicitly requests a response in a specific language (e.g., "answer in Spanish", "respond in Ukrainian", "tell me in French"), then use that language
- Do not automatically switch languages based on context, location, or assumptions about the user's preferences
- Keep responses conversational and concise (1-3 sentences usually)
- Use a warm, friendly tone like you're talking to a friend
- Avoid long lists or complex formatting since this is voice-to-voice
- If asked about technical topics, explain simply and clearly
- Feel free to ask follow-up questions to keep the conversation flowing
- Remember this is a voice chat, so respond as if you're speaking, not writing

Be helpful, engaging, and natural in your responses. Default to English unless explicitly asked otherwise."""

        # Build conversation history
        conversation_id = message.conversation_id or "default"
        
        # Get or create conversation history (keep last 10 messages for context)
        if conversation_id not in conversation_store:
            conversation_store[conversation_id] = []
        
        conversation_history = conversation_store[conversation_id]
        
        # Build messages with history
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add recent conversation history (last 8 messages to stay within token limits)
        for hist_msg in conversation_history[-8:]:
            messages.append(hist_msg)
        
        # Add current user message
        messages.append({"role": "user", "content": message.message})

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=250,  # Shorter responses for voice chat
            temperature=0.8,  # Slightly more creative for natural conversation
            timeout=30  # 30 second timeout
        )
        
        response_text = response.choices[0].message.content
        if not response_text:
            logger.warning(f"[{request_id}] Empty response from OpenAI")
            response_text = "I apologize, but I couldn't generate a response. Please try again."
        
        # Save conversation history
        conversation_history.append({"role": "user", "content": message.message})
        conversation_history.append({"role": "assistant", "content": response_text})
        
        # Keep conversation history manageable (max 20 messages = 10 exchanges)
        if len(conversation_history) > 20:
            conversation_history = conversation_history[-20:]
            conversation_store[conversation_id] = conversation_history
        
        logger.info(f"[{request_id}] Chat response successful: {len(response_text)} characters")
        
        return ChatResponse(response=response_text)
    
    except openai.AuthenticationError as e:
        logger.error(f"[{request_id}] OpenAI authentication error: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Invalid OpenAI API key"
        )
    except openai.RateLimitError as e:
        logger.error(f"[{request_id}] OpenAI rate limit error: {str(e)}")
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later."
        )
    except openai.APIError as e:
        logger.error(f"[{request_id}] OpenAI API error: {str(e)}")
        raise HTTPException(
            status_code=502,
            detail="OpenAI service error. Please try again."
        )
    except Exception as e:
        logger.error(f"[{request_id}] Chat failed: {str(e)}")
        logger.error(f"[{request_id}] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, 
            detail="Chat failed. Please try again."
        )

@app.post("/chat/clear")
async def clear_conversation(request: Request, conversation_id: str = "default"):
    """Clear conversation history for a given conversation ID"""
    request_id = id(request)
    logger.info(f"[{request_id}] Clearing conversation history for: {conversation_id}")
    
    if conversation_id in conversation_store:
        del conversation_store[conversation_id]
        logger.info(f"[{request_id}] Conversation history cleared")
    
    return {"message": "Conversation history cleared", "conversation_id": conversation_id}

# Serve static files (frontend) in production
if os.path.exists("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")

def main():
    """Main entry point for the application."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
