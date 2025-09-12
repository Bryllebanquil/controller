#!/usr/bin/env python3
"""
Render Deployment Startup Script for Neural Control Hub
Handles environment variables and security configuration for production deployment
"""

import os
import sys
from controller import app, socketio, Config

def main():
    """Main startup function for Render deployment"""
    
    # Print deployment information
    print("🚀 Neural Control Hub - Render Deployment")
    print("=" * 50)
    
    # Security configuration
    admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
    secret_key = os.environ.get('SECRET_KEY')
    session_timeout = os.environ.get('SESSION_TIMEOUT', '3600')
    max_login_attempts = os.environ.get('MAX_LOGIN_ATTEMPTS', '5')
    login_timeout = os.environ.get('LOGIN_TIMEOUT', '300')
    hash_iterations = os.environ.get('HASH_ITERATIONS', '100000')
    salt_length = os.environ.get('SALT_LENGTH', '32')
    
    # Display configuration (without exposing sensitive data)
    print(f"✅ Admin password: {'*' * len(admin_password)} ({len(admin_password)} chars)")
    print(f"✅ Secret key: {'Set' if secret_key else 'Auto-generated'}")
    print(f"✅ Session timeout: {session_timeout} seconds")
    print(f"✅ Max login attempts: {max_login_attempts}")
    print(f"✅ Login lockout timeout: {login_timeout} seconds")
    print(f"✅ Hash iterations: {int(hash_iterations):,}")
    print(f"✅ Salt length: {salt_length} bytes")
    print(f"✅ Password security: PBKDF2-SHA256")
    
    # Security warnings
    if admin_password == 'admin123':
        print("⚠️  WARNING: Using default password. Change ADMIN_PASSWORD in Render dashboard!")
    
    if not secret_key:
        print("⚠️  WARNING: No SECRET_KEY set. Using auto-generated key.")
    
    # Get port from Render
    port = int(os.environ.get('PORT', 8080))
    host = '0.0.0.0'
    
    print(f"🌐 Server will be available at: http://0.0.0.0:{port}")
    print("🔒 All endpoints are protected with authentication")
    print("=" * 50)
    
    # Start the application
    try:
        socketio.run(app, host=host, port=port, debug=False)
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()