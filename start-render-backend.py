#!/usr/bin/env python3
"""
Neural Control Hub - Render Production Backend
Production-ready backend server for Render deployment
"""

import os
import sys
from pathlib import Path

# Add the current directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import the main controller
from controller import app, socketio, Config

# Production configuration
class RenderConfig(Config):
    """Render-specific configuration"""
    
    # Use Render's PORT environment variable
    PORT = int(os.environ.get('PORT', 10000))
    HOST = '0.0.0.0'
    
    # Use environment variables for security
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'change-me-in-production')
    SECRET_KEY = os.environ.get('SECRET_KEY', None)
    
    # Production settings
    SESSION_TIMEOUT = int(os.environ.get('SESSION_TIMEOUT', 3600))
    MAX_LOGIN_ATTEMPTS = int(os.environ.get('MAX_LOGIN_ATTEMPTS', 5))
    LOGIN_TIMEOUT = int(os.environ.get('LOGIN_TIMEOUT', 300))

# Update the app configuration
Config.PORT = RenderConfig.PORT
Config.HOST = RenderConfig.HOST
Config.ADMIN_PASSWORD = RenderConfig.ADMIN_PASSWORD
if RenderConfig.SECRET_KEY:
    Config.SECRET_KEY = RenderConfig.SECRET_KEY

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Neural Control Hub - Render Production Backend")
    print("=" * 60)
    print(f"🌐 Host: {Config.HOST}")
    print(f"🔌 Port: {Config.PORT}")
    print(f"🔐 Admin password: {'***' if Config.ADMIN_PASSWORD != 'change-me-in-production' else 'NOT SET - SECURITY RISK!'}")
    print(f"🔒 Session timeout: {Config.SESSION_TIMEOUT}s")
    print(f"⚠️  Max login attempts: {Config.MAX_LOGIN_ATTEMPTS}")
    print()
    print("📡 API Endpoints:")
    print("   • Authentication: /api/auth/*")
    print("   • Agents: /api/agents/*")
    print("   • System: /api/system/*")
    print("   • WebSocket: /socket.io/")
    print()
    print("🔌 CORS configured for frontend communication")
    print("🌍 Production mode: Optimized for Render")
    print("=" * 60)
    
    try:
        # Use eventlet for production with SocketIO
        socketio.run(
            app,
            host=Config.HOST,
            port=Config.PORT,
            debug=False,
            use_reloader=False,
            log_output=True
        )
    except Exception as e:
        print(f"❌ Error starting production server: {e}")
        sys.exit(1)