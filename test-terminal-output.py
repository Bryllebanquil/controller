#!/usr/bin/env python3
"""
Terminal Output Test Script
==========================

This script helps test the terminal-like command execution functionality.

Usage:
    python3 test-terminal-output.py [--url CONTROLLER_URL]
"""

import os
import sys
import time
import subprocess
import platform
import argparse
from datetime import datetime

def log_message(message, level="info"):
    """Simple logging function"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    colors = {
        "info": "\033[94m",
        "success": "\033[92m",
        "warning": "\033[93m",
        "error": "\033[91m",
        "reset": "\033[0m"
    }
    
    color = colors.get(level, colors["info"])
    reset = colors["reset"]
    print(f"{color}[{timestamp}] {level.upper()}: {message}{reset}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Terminal Output Test Script')
    parser.add_argument('--url', default='https://agent-controller-backend.onrender.com',
                       help='Controller URL')
    
    args = parser.parse_args()
    
    print("🖥️  Terminal Output Test Script")
    print("=" * 50)
    print(f"Controller URL: {args.url}")
    print("=" * 50)
    
    log_message("🚀 Starting simple client for terminal testing...", "info")
    log_message("📋 Test Instructions:", "info")
    log_message("1. Open browser to your controller dashboard", "info")
    log_message("2. Login and go to Agents tab", "info")
    log_message("3. Select the simple client agent", "info")
    log_message("4. Go to Commands tab", "info")
    log_message("5. Try these terminal commands:", "info")
    
    print("\n🧪 Test Commands:")
    print("=" * 30)
    
    if platform.system() == "Windows":
        test_commands = [
            "whoami",
            "echo Hello World",
            "dir",
            "Get-Date",
            "Get-Process | Select-Object -First 3",
            "echo 'Terminal test successful'"
        ]
    else:
        test_commands = [
            "whoami",
            "echo Hello World",
            "ls",
            "date",
            "ps aux | head -3",
            "echo 'Terminal test successful'"
        ]
    
    for i, cmd in enumerate(test_commands, 1):
        print(f"{i}. {cmd}")
    
    print("\n📋 Expected Terminal Output:")
    print("=" * 30)
    print("$ whoami")
    print("your-username")
    print("")
    print("$ echo Hello World")
    print("Hello World")
    print("")
    print("$ dir  # or ls on Linux/Mac")
    print("Directory listing...")
    print("")
    
    log_message("🔧 Starting simple client...", "info")
    
    try:
        # Start the simple client
        cmd = [sys.executable, "simple-client.py", "--url", args.url]
        log_message(f"🔧 Running: {' '.join(cmd)}", "debug")
        
        process = subprocess.Popen(cmd)
        
        log_message("✅ Simple client started successfully!", "success")
        log_message("📱 Now test the commands in your dashboard", "info")
        log_message("🛑 Press Ctrl+C to stop the client", "info")
        
        process.wait()
        
    except KeyboardInterrupt:
        log_message("🛑 Test interrupted by user", "warning")
    except Exception as e:
        log_message(f"❌ Test failed: {e}", "error")

if __name__ == "__main__":
    main()