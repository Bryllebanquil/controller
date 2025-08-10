#!/usr/bin/env python3
"""
Simple startup script for main.py
Provides easy access to different running modes and configurations
"""

import sys
import os
import subprocess
import argparse

def check_dependencies():
    """Check if required dependencies are installed."""
    required_modules = ['aiortc', 'cv2', 'mss', 'pyaudio', 'numpy', 'PIL', 'socketio']
    missing_modules = []
    
    for module in required_modules:
        try:
            if module == 'cv2':
                import cv2
            elif module == 'PIL':
                from PIL import Image
            elif module == 'socketio':
                import socketio
            else:
                __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print("❌ Missing dependencies:")
        for module in missing_modules:
            print(f"   - {module}")
        print("\nInstall with: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies are installed")
    return True

def run_main(mode='agent', host='0.0.0.0', port=8080, no_ssl=False, debug=False):
    """Run main.py with specified parameters."""
    
    # Build command
    cmd = [sys.executable, 'main.py']
    
    if mode != 'agent':
        cmd.extend(['--mode', mode])
    
    if mode in ['controller', 'both']:
        cmd.extend(['--host', host, '--port', str(port)])
        if no_ssl:
            cmd.append('--no-ssl')
    
    if debug:
        cmd.append('--debug')
    
    print(f"🚀 Starting main.py with command: {' '.join(cmd)}")
    print(f"📋 Mode: {mode}")
    if mode in ['controller', 'both']:
        protocol = 'http' if no_ssl else 'https'
        print(f"🌐 Controller will be available at: {protocol}://{host}:{port}")
    
    print("\n" + "="*50)
    
    try:
        # Run main.py
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error running main.py: {e}")
        return False
    except FileNotFoundError:
        print("❌ Error: main.py not found in current directory")
        return False
    
    return True

def show_help():
    """Show help information."""
    help_text = """
🎯 Main.py Startup Script

USAGE:
    python start.py [options]

OPTIONS:
    --mode {agent,controller,both}    Run mode (default: agent)
    --host HOST                       Controller host (default: 0.0.0.0)
    --port PORT                       Controller port (default: 8080)
    --no-ssl                         Disable SSL for controller
    --debug                          Enable debug mode
    --check                          Check dependencies only
    --help                           Show this help

EXAMPLES:
    # Run as agent (default)
    python start.py
    
    # Run as controller
    python start.py --mode controller
    
    # Run controller on specific port without SSL
    python start.py --mode controller --port 9000 --no-ssl
    
    # Run both agent and controller
    python start.py --mode both
    
    # Check dependencies only
    python start.py --check

MODES:
    agent      - Remote control agent (connects to Socket.IO server)
    controller - Web-based controller (starts HTTP/HTTPS server)
    both       - Runs both agent and controller simultaneously

TROUBLESHOOTING:
    - Ensure all dependencies are installed: pip install -r requirements.txt
    - Run as administrator on Windows for full functionality
    - Check firewall settings for network access
    - Verify Python 3.8+ is installed
    """
    print(help_text)

def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Startup script for main.py',
        add_help=False
    )
    
    parser.add_argument('--mode', choices=['agent', 'controller', 'both'], 
                       default='agent', help='Run mode')
    parser.add_argument('--host', default='0.0.0.0', help='Controller host')
    parser.add_argument('--port', type=int, default=8080, help='Controller port')
    parser.add_argument('--no-ssl', action='store_true', help='Disable SSL')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--check', action='store_true', help='Check dependencies only')
    parser.add_argument('--help', action='store_true', help='Show help')
    
    args = parser.parse_args()
    
    if args.help:
        show_help()
        return
    
    print("🚀 Main.py Startup Script")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        if args.check:
            return
        print("\n⚠️  Some dependencies are missing. Continuing anyway...")
    
    if args.check:
        return
    
    # Run main.py
    success = run_main(
        mode=args.mode,
        host=args.host,
        port=args.port,
        no_ssl=args.no_ssl,
        debug=args.debug
    )
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()