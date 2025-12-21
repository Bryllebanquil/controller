#!/usr/bin/env python3
"""
Debug Command Flow Script
========================

This script helps debug the command execution flow by:
1. Starting a debug client
2. Providing detailed logging
3. Testing command execution manually

Usage:
    python3 debug-command-flow.py [--url CONTROLLER_URL]
"""

import os
import sys
import time
import json
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
        "debug": "\033[95m",
        "reset": "\033[0m"
    }
    
    color = colors.get(level, colors["info"])
    reset = colors["reset"]
    print(f"{color}[{timestamp}] {level.upper()}: {message}{reset}")

def test_command_execution():
    """Test command execution locally"""
    log_message("🧪 Testing command execution locally...", "info")
    
    test_commands = [
        "echo 'Hello World'",
        "dir" if platform.system() == "Windows" else "ls",
        "whoami",
        "pwd"
    ]
    
    for cmd in test_commands:
        log_message(f"🔧 Testing command: {cmd}", "debug")
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["powershell.exe", "-NoProfile", "-Command", cmd],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                result = subprocess.run(
                    ["bash", "-c", cmd],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            
            output = result.stdout + result.stderr
            log_message(f"✅ Command '{cmd}' executed successfully", "success")
            log_message(f"📄 Output: {output[:100]}{'...' if len(output) > 100 else ''}", "debug")
            
        except Exception as e:
            log_message(f"❌ Command '{cmd}' failed: {e}", "error")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Debug Command Flow Script')
    parser.add_argument('--url', default='https://agent-controller-backend.onrender.com',
                       help='Controller URL')
    
    args = parser.parse_args()
    
    print("🐛 Debug Command Flow Script")
    print("=" * 50)
    print(f"Controller URL: {args.url}")
    print("=" * 50)
    
    # Test 1: Local command execution
    test_command_execution()
    
    # Test 2: Start debug client
    log_message("🚀 Starting debug client...", "info")
    log_message("📋 Instructions:", "info")
    log_message("1. Open browser to your controller URL", "info")
    log_message("2. Login and go to Agents tab", "info")
    log_message("3. Select the debug client agent", "info")
    log_message("4. Go to Commands tab and execute a command", "info")
    log_message("5. Check browser console (F12) for debug logs", "info")
    log_message("6. Check this terminal for client-side logs", "info")
    
    try:
        # Start the debug client
        cmd = [sys.executable, "debug-simple-client.py", "--url", args.url]
        log_message(f"🔧 Running: {' '.join(cmd)}", "debug")
        
        process = subprocess.Popen(cmd)
        process.wait()
        
    except KeyboardInterrupt:
        log_message("🛑 Debug interrupted by user", "warning")
    except Exception as e:
        log_message(f"❌ Debug failed: {e}", "error")

if __name__ == "__main__":
    main()