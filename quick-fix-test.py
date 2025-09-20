#!/usr/bin/env python3
"""
Quick Fix Test Script
====================

This script helps identify and fix the command result issue.

Usage:
    python3 quick-fix-test.py
"""

import os
import sys
import time
import json
import subprocess
import platform
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
    print("🔧 Quick Fix Test Script")
    print("=" * 40)
    
    log_message("🔍 Diagnosing command result issue...", "info")
    
    # Test 1: Check if simple client is working
    log_message("📋 Test 1: Starting simple client...", "info")
    log_message("📋 Instructions:", "info")
    log_message("1. Open browser to https://agent-controller-backend.onrender.com", "info")
    log_message("2. Login and go to Agents tab", "info")
    log_message("3. Select the simple client agent", "info")
    log_message("4. Go to Commands tab", "info")
    log_message("5. Type 'whoami' and press Enter", "info")
    log_message("6. Check browser console (F12) for these messages:", "info")
    log_message("   - 🔍 sendCommand called:", "info")
    log_message("   - 🔍 Emitting execute_command:", "info")
    log_message("   - 🔍 Command result received:", "info")
    log_message("   - 🔍 Adding command output:", "info")
    log_message("7. If you don't see 'Command result received', the issue is in the controller", "info")
    log_message("8. If you see 'Command result received' but no output, the issue is in the UI", "info")
    
    print("\n" + "=" * 40)
    log_message("🚀 Starting simple client...", "info")
    
    try:
        # Start the simple client
        cmd = [sys.executable, "simple-client.py", "--url", "https://agent-controller-backend.onrender.com"]
        log_message(f"🔧 Running: {' '.join(cmd)}", "debug")
        
        process = subprocess.Popen(cmd)
        
        log_message("✅ Simple client started!", "success")
        log_message("📱 Now test the commands in your dashboard", "info")
        log_message("🛑 Press Ctrl+C to stop", "info")
        
        process.wait()
        
    except KeyboardInterrupt:
        log_message("🛑 Test interrupted by user", "warning")
    except Exception as e:
        log_message(f"❌ Test failed: {e}", "error")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log_message("🛑 Test interrupted by user", "warning")
    except Exception as e:
        log_message(f"❌ Unexpected error: {e}", "error")