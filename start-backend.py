#!/usr/bin/env python3
"""
Neural Control Hub - Backend Server
Standalone backend server for the agent controller system
"""

import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the main controller
from controller import app, socketio, Config

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Neural Control Hub - Backend Server")
    print("=" * 60)
    print(f"🔐 Admin password: {'*' * len(Config.ADMIN_PASSWORD)} (hidden for security)")
    print(f"🌐 Backend server: http://{Config.HOST}:{Config.PORT}")
    print(f"🔒 Session timeout: {Config.SESSION_TIMEOUT} seconds")
    print(f"⚠️  Max login attempts: {Config.MAX_LOGIN_ATTEMPTS}")
    print(f"🔧 WebRTC support: {'Enabled' if 'WEBRTC_AVAILABLE' in globals() else 'Disabled'}")
    print()
    print("📡 API Endpoints Available:")
    print("   • Authentication: /api/auth/*")
    print("   • Agents: /api/agents/*")
    print("   • System: /api/system/*")
    print("   • Activity: /api/activity")
    print("   • Settings: /api/settings")
    print()
    print("🔌 WebSocket Events: Real-time communication enabled")
    print("🌍 CORS: Configured for frontend communication")
    print()
    print("Frontend should connect to:")
    print(f"   • HTTP API: http://{Config.HOST}:{Config.PORT}/api/")
    print(f"   • WebSocket: ws://{Config.HOST}:{Config.PORT}/socket.io/")
    print("=" * 60)
    
    try:
        # Run the server
        socketio.run(
            app, 
            host=Config.HOST, 
            port=Config.PORT, 
            debug=False,
            use_reloader=False,
            log_output=True
        )
    except KeyboardInterrupt:
        print("\n🛑 Backend server stopped by user")
    except Exception as e:
        print(f"❌ Error starting backend server: {e}")
        sys.exit(1)