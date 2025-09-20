"""
Security utilities and middleware for the voice chat backend
"""
import re
import html
from typing import Optional
from fastapi import Request, HTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging

logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

class SecurityValidator:
    """Security validation utilities"""
    
    # Patterns for potentially malicious content
    SUSPICIOUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript:',                # JavaScript URLs
        r'on\w+\s*=',                 # Event handlers
        r'<iframe[^>]*>.*?</iframe>',  # Iframes
        r'eval\s*\(',                 # eval() calls
        r'document\.',                # DOM manipulation
        r'window\.',                  # Window object access
    ]
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r'(\bUNION\b|\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\bDROP\b)',
        r'(\bOR\b|\bAND\b)\s+\d+\s*=\s*\d+',
        r'[\'";]\s*(\bOR\b|\bAND\b)',
        r'--\s*$',
        r'/\*.*?\*/',
    ]
    
    @classmethod
    def sanitize_text_input(cls, text: str) -> str:
        """Sanitize text input to prevent XSS and injection attacks"""
        if not text:
            return text
            
        # HTML escape
        sanitized = html.escape(text)
        
        # Remove potentially dangerous patterns
        for pattern in cls.SUSPICIOUS_PATTERNS:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        # Limit length to prevent DoS
        if len(sanitized) > 10000:  # 10KB limit
            raise HTTPException(
                status_code=400,
                detail="Input too long. Maximum 10,000 characters allowed."
            )
        
        return sanitized.strip()
    
    @classmethod
    def validate_message_content(cls, message: str) -> str:
        """Validate and sanitize chat message content"""
        if not message or not message.strip():
            raise HTTPException(
                status_code=400,
                detail="Message cannot be empty"
            )
        
        # Check for SQL injection patterns
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, message, re.IGNORECASE):
                logger.warning(f"Potential SQL injection attempt detected: {pattern}")
                raise HTTPException(
                    status_code=400,
                    detail="Invalid message content detected"
                )
        
        # Sanitize the message
        sanitized = cls.sanitize_text_input(message)
        
        # Additional length check for chat messages
        if len(sanitized) > 4000:
            raise HTTPException(
                status_code=400,
                detail="Message too long. Maximum 4,000 characters allowed."
            )
        
        return sanitized
    
    @classmethod
    def validate_file_upload(cls, file_content: bytes, filename: str) -> None:
        """Validate uploaded file for security"""
        # Check file size (25MB limit)
        max_size = 25 * 1024 * 1024  # 25MB
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size is {max_size // (1024*1024)}MB."
            )
        
        # Check filename for path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            raise HTTPException(
                status_code=400,
                detail="Invalid filename"
            )
        
        # Check for executable file extensions
        dangerous_extensions = ['.exe', '.bat', '.cmd', '.sh', '.ps1', '.scr', '.com']
        file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
        if f'.{file_ext}' in dangerous_extensions:
            raise HTTPException(
                status_code=400,
                detail="File type not allowed"
            )
        
        # Basic magic number check for audio files
        if not cls._is_audio_file(file_content):
            logger.warning(f"Non-audio file uploaded: {filename}")
            # Don't reject, as some audio files might not have standard headers
    
    @staticmethod
    def _is_audio_file(content: bytes) -> bool:
        """Check if file content appears to be audio"""
        if len(content) < 12:
            return False
        
        # Check for common audio file signatures
        audio_signatures = [
            b'RIFF',      # WAV
            b'ID3',       # MP3
            b'\xff\xfb',  # MP3
            b'\xff\xf3',  # MP3
            b'\xff\xf2',  # MP3
            b'OggS',      # OGG
            b'fLaC',      # FLAC
        ]
        
        for signature in audio_signatures:
            if content.startswith(signature):
                return True
        
        return True  # Allow by default for now

class SecurityHeaders:
    """Security headers middleware"""
    
    @staticmethod
    def add_security_headers(response):
        """Add security headers to response"""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "connect-src 'self' https: wss:; "
            "font-src 'self'; "
            "object-src 'none'; "
            "media-src 'self'; "
            "frame-src 'none';"
        )
        return response

def get_client_ip(request: Request) -> str:
    """Get client IP address, considering proxy headers"""
    # Check for forwarded headers (when behind a proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct connection
    return request.client.host if request.client else "unknown"

def log_security_event(request: Request, event_type: str, details: str):
    """Log security-related events"""
    client_ip = get_client_ip(request)
    user_agent = request.headers.get("User-Agent", "Unknown")
    
    logger.warning(
        f"Security Event - Type: {event_type}, "
        f"IP: {client_ip}, "
        f"User-Agent: {user_agent}, "
        f"Details: {details}"
    )

# Rate limiting configurations
RATE_LIMITS = {
    "transcribe": "10/minute",  # 10 transcriptions per minute
    "chat": "30/minute",        # 30 chat messages per minute
    "health": "60/minute",      # 60 health checks per minute
}

def create_rate_limiter(endpoint: str):
    """Create rate limiter for specific endpoint"""
    limit = RATE_LIMITS.get(endpoint, "100/minute")
    return limiter.limit(limit)
