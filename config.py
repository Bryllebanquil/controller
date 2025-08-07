# Configuration file for Neural Control Hub
import os

# Admin Authentication
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')  # Change this in production

# Flask Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', None)  # Will be auto-generated if not set

# Server Configuration
HOST = os.environ.get('HOST', '0.0.0.0')
PORT = int(os.environ.get('PORT', 8080))

# Security Settings
SESSION_TIMEOUT = 3600  # 1 hour in seconds
MAX_LOGIN_ATTEMPTS = 5
LOGIN_TIMEOUT = 300  # 5 minutes lockout after max attempts