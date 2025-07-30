"""
Security utilities and middleware for the AIM Framework.

This module provides comprehensive security features including
authentication, authorization, input validation, and security headers.
"""

import hashlib
import hmac
import secrets
import jwt
import time
from typing import Dict, Any, Optional, List, Callable
from functools import wraps
from datetime import datetime, timedelta
import logging
import re

logger = logging.getLogger(__name__)


class SecurityConfig:
    """Security configuration settings."""
    
    def __init__(self, config: Dict[str, Any]):
        self.api_key_required = config.get("api_key_required", False)
        self.jwt_secret = config.get("jwt_secret", secrets.token_urlsafe(32))
        self.jwt_expiry_hours = config.get("jwt_expiry_hours", 24)
        self.allowed_origins = config.get("allowed_origins", ["*"])
        self.rate_limit_enabled = config.get("rate_limit_enabled", True)
        self.csrf_protection = config.get("csrf_protection", True)
        self.secure_headers = config.get("secure_headers", True)
        self.max_request_size = config.get("max_request_size", 16 * 1024 * 1024)  # 16MB
        self.allowed_file_types = config.get("allowed_file_types", [
            "json", "txt", "csv", "xml", "yaml", "yml"
        ])


class InputValidator:
    """Input validation and sanitization utilities."""
    
    # Common regex patterns
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
    ALPHANUMERIC_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        return bool(InputValidator.EMAIL_PATTERN.match(email))
    
    @staticmethod
    def validate_uuid(uuid_str: str) -> bool:
        """Validate UUID format."""
        return bool(InputValidator.UUID_PATTERN.match(uuid_str.lower()))
    
    @staticmethod
    def validate_alphanumeric(text: str, min_length: int = 1, max_length: int = 255) -> bool:
        """Validate alphanumeric string with length constraints."""
        if not min_length <= len(text) <= max_length:
            return False
        return bool(InputValidator.ALPHANUMERIC_PATTERN.match(text))
    
    @staticmethod
    def sanitize_string(text: str, max_length: int = 1000) -> str:
        """Sanitize string input by removing dangerous characters."""
        if not isinstance(text, str):
            return ""
        
        # Remove null bytes and control characters
        sanitized = ''.join(char for char in text if ord(char) >= 32 or char in '\t\n\r')
        
        # Truncate to max length
        return sanitized[:max_length]
    
    @staticmethod
    def validate_json_structure(data: Dict[str, Any], required_fields: List[str]) -> tuple[bool, str]:
        """Validate JSON structure and required fields."""
        if not isinstance(data, dict):
            return False, "Data must be a JSON object"
        
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"
        
        return True, ""
    
    @staticmethod
    def validate_file_type(filename: str, allowed_types: List[str]) -> bool:
        """Validate file type based on extension."""
        if not filename or '.' not in filename:
            return False
        
        extension = filename.split('.')[-1].lower()
        return extension in allowed_types


class APIKeyManager:
    """API key management and validation."""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key.encode('utf-8')
    
    def generate_api_key(self, user_id: str, expiry_days: int = 365) -> str:
        """Generate a new API key for a user."""
        timestamp = int(time.time())
        expiry = timestamp + (expiry_days * 24 * 3600)
        
        payload = f"{user_id}:{timestamp}:{expiry}"
        signature = hmac.new(
            self.secret_key,
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return f"{payload}:{signature}"
    
    def validate_api_key(self, api_key: str) -> tuple[bool, Optional[str]]:
        """Validate an API key and return user ID if valid."""
        try:
            parts = api_key.split(':')
            if len(parts) != 4:
                return False, None
            
            user_id, timestamp, expiry, signature = parts
            payload = f"{user_id}:{timestamp}:{expiry}"
            
            # Verify signature
            expected_signature = hmac.new(
                self.secret_key,
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                return False, None
            
            # Check expiry
            if int(time.time()) > int(expiry):
                return False, None
            
            return True, user_id
            
        except (ValueError, IndexError):
            return False, None


class JWTManager:
    """JWT token management for authentication."""
    
    def __init__(self, secret_key: str, expiry_hours: int = 24):
        self.secret_key = secret_key
        self.expiry_hours = expiry_hours
    
    def generate_token(self, user_id: str, additional_claims: Optional[Dict] = None) -> str:
        """Generate a JWT token for a user."""
        payload = {
            'user_id': user_id,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=self.expiry_hours)
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def validate_token(self, token: str) -> tuple[bool, Optional[Dict]]:
        """Validate a JWT token and return payload if valid."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return True, payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            return False, None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return False, None


class SecurityMiddleware:
    """Security middleware for Flask applications."""
    
    def __init__(self, app, config: SecurityConfig):
        self.app = app
        self.config = config
        self.api_key_manager = APIKeyManager(config.jwt_secret)
        self.jwt_manager = JWTManager(config.jwt_secret, config.jwt_expiry_hours)
        
        # Apply middleware
        self._setup_security_headers()
        self._setup_request_validation()
    
    def _setup_security_headers(self):
        """Setup security headers for all responses."""
        if not self.config.secure_headers:
            return
        
        @self.app.after_request
        def add_security_headers(response):
            # Prevent clickjacking
            response.headers['X-Frame-Options'] = 'DENY'
            
            # Prevent MIME type sniffing
            response.headers['X-Content-Type-Options'] = 'nosniff'
            
            # XSS protection
            response.headers['X-XSS-Protection'] = '1; mode=block'
            
            # Strict transport security (HTTPS only)
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            
            # Content security policy
            response.headers['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; "
                "connect-src 'self'"
            )
            
            # Referrer policy
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            
            # Permissions policy
            response.headers['Permissions-Policy'] = (
                "geolocation=(), microphone=(), camera=(), "
                "payment=(), usb=(), magnetometer=(), gyroscope=()"
            )
            
            return response
    
    def _setup_request_validation(self):
        """Setup request validation middleware."""
        @self.app.before_request
        def validate_request():
            from flask import request, abort
            
            # Check request size
            if request.content_length and request.content_length > self.config.max_request_size:
                logger.warning(f"Request too large: {request.content_length} bytes")
                abort(413)  # Request Entity Too Large
            
            # Validate content type for POST/PUT requests
            if request.method in ['POST', 'PUT', 'PATCH']:
                if not request.is_json and 'multipart/form-data' not in request.content_type:
                    logger.warning(f"Invalid content type: {request.content_type}")
                    abort(400)  # Bad Request
    
    def require_api_key(self, f: Callable) -> Callable:
        """Decorator to require API key authentication."""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import request, jsonify
            
            if not self.config.api_key_required:
                return f(*args, **kwargs)
            
            api_key = request.headers.get('X-API-Key')
            if not api_key:
                return jsonify({'error': 'API key required'}), 401
            
            valid, user_id = self.api_key_manager.validate_api_key(api_key)
            if not valid:
                return jsonify({'error': 'Invalid API key'}), 401
            
            # Add user_id to request context
            request.user_id = user_id
            return f(*args, **kwargs)
        
        return decorated_function
    
    def require_jwt(self, f: Callable) -> Callable:
        """Decorator to require JWT authentication."""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import request, jsonify
            
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'error': 'JWT token required'}), 401
            
            token = auth_header.split(' ')[1]
            valid, payload = self.jwt_manager.validate_token(token)
            if not valid:
                return jsonify({'error': 'Invalid or expired token'}), 401
            
            # Add user info to request context
            request.user_id = payload['user_id']
            request.token_payload = payload
            return f(*args, **kwargs)
        
        return decorated_function
    
    def validate_input(self, schema: Dict[str, Any]) -> Callable:
        """Decorator to validate request input against a schema."""
        def decorator(f: Callable) -> Callable:
            @wraps(f)
            def decorated_function(*args, **kwargs):
                from flask import request, jsonify
                
                if not request.is_json:
                    return jsonify({'error': 'JSON data required'}), 400
                
                data = request.get_json()
                
                # Validate required fields
                required_fields = schema.get('required', [])
                valid, error_msg = InputValidator.validate_json_structure(data, required_fields)
                if not valid:
                    return jsonify({'error': error_msg}), 400
                
                # Validate field types and constraints
                for field, constraints in schema.get('fields', {}).items():
                    if field in data:
                        value = data[field]
                        
                        # Type validation
                        expected_type = constraints.get('type')
                        if expected_type and not isinstance(value, expected_type):
                            return jsonify({
                                'error': f'Field {field} must be of type {expected_type.__name__}'
                            }), 400
                        
                        # String length validation
                        if isinstance(value, str):
                            min_length = constraints.get('min_length', 0)
                            max_length = constraints.get('max_length', 10000)
                            if not min_length <= len(value) <= max_length:
                                return jsonify({
                                    'error': f'Field {field} length must be between {min_length} and {max_length}'
                                }), 400
                        
                        # Custom validation
                        validator = constraints.get('validator')
                        if validator and not validator(value):
                            return jsonify({
                                'error': f'Field {field} failed validation'
                            }), 400
                
                return f(*args, **kwargs)
            
            return decorated_function
        return decorator


class SecurityAuditor:
    """Security auditing and logging utilities."""
    
    def __init__(self):
        self.security_events: List[Dict[str, Any]] = []
    
    def log_security_event(self, event_type: str, details: Dict[str, Any], severity: str = "INFO"):
        """Log a security event."""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'type': event_type,
            'severity': severity,
            'details': details
        }
        
        self.security_events.append(event)
        
        # Log to standard logger
        log_msg = f"Security Event [{event_type}]: {details}"
        if severity == "CRITICAL":
            logger.critical(log_msg)
        elif severity == "ERROR":
            logger.error(log_msg)
        elif severity == "WARNING":
            logger.warning(log_msg)
        else:
            logger.info(log_msg)
    
    def get_security_events(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get security events from the last N hours."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        return [
            event for event in self.security_events
            if datetime.fromisoformat(event['timestamp']) >= cutoff_time
        ]
    
    def generate_security_report(self) -> Dict[str, Any]:
        """Generate a security audit report."""
        events_24h = self.get_security_events(24)
        
        # Count events by type and severity
        event_counts = {}
        severity_counts = {}
        
        for event in events_24h:
            event_type = event['type']
            severity = event['severity']
            
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            'report_generated': datetime.utcnow().isoformat(),
            'period_hours': 24,
            'total_events': len(events_24h),
            'events_by_type': event_counts,
            'events_by_severity': severity_counts,
            'recent_events': events_24h[-10:] if events_24h else []
        }


# Global security auditor instance
security_auditor = SecurityAuditor()


def setup_security(app, config: Dict[str, Any]) -> SecurityMiddleware:
    """Setup security middleware for a Flask app."""
    security_config = SecurityConfig(config)
    middleware = SecurityMiddleware(app, security_config)
    
    logger.info("Security middleware initialized")
    security_auditor.log_security_event(
        "SECURITY_SETUP",
        {"api_key_required": security_config.api_key_required,
         "jwt_enabled": True,
         "secure_headers": security_config.secure_headers},
        "INFO"
    )
    
    return middleware