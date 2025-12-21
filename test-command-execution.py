#!/usr/bin/env python3
"""
Command Execution Test Script
============================

This script helps test the command execution functionality by:
1. Starting the controller (if not running)
2. Starting a simple client
3. Providing instructions for testing

Usage:
    python3 test-command-execution.py [--controller-url URL] [--interactive]

Features:
    - Automatic controller startup check
    - Simple client startup
    - Interactive testing mode
    - Command execution verification
"""

import os
import sys
import time
import subprocess
import requests
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

def check_controller_running(url):
    """Check if controller is running"""
    try:
        response = requests.get(f"{url}/", timeout=5)
        return response.status_code in [200, 302]
    except:
        return False

def start_controller():
    """Start the controller if not running"""
    log_message("Checking if controller is running...", "info")
    
    if check_controller_running("http://localhost:8080"):
        log_message("✅ Controller is already running", "success")
        return True
    
    log_message("Controller not running, attempting to start...", "warning")
    
    try:
        # Try to start controller
        log_message("Starting controller.py...", "info")
        process = subprocess.Popen([
            sys.executable, "controller.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a bit for startup
        time.sleep(3)
        
        if check_controller_running("http://localhost:8080"):
            log_message("✅ Controller started successfully", "success")
            return True
        else:
            log_message("❌ Controller failed to start", "error")
            return False
            
    except Exception as e:
        log_message(f"❌ Failed to start controller: {e}", "error")
        return False

def start_simple_client(controller_url, interactive=False):
    """Start the simple client"""
    log_message("Starting simple client...", "info")
    
    try:
        cmd = [sys.executable, "simple-client.py", "--url", controller_url]
        if interactive:
            cmd.append("--interactive")
        
        log_message(f"Running: {' '.join(cmd)}", "info")
        
        # Start the client
        process = subprocess.Popen(cmd)
        
        log_message("✅ Simple client started", "success")
        return process
        
    except Exception as e:
        log_message(f"❌ Failed to start simple client: {e}", "error")
        return None

def print_testing_instructions():
    """Print instructions for testing command execution"""
    print("\n" + "="*70)
    print("🧪 COMMAND EXECUTION TESTING INSTRUCTIONS")
    print("="*70)
    print("1. Open your web browser and go to: http://localhost:8080")
    print("2. Login with your admin password")
    print("3. Navigate to the 'Agents' tab")
    print("4. You should see a 'Simple-Client' agent in the list")
    print("5. Select the agent by clicking on it")
    print("6. Go to the 'Commands' tab")
    print("7. Try executing these test commands:")
    print("   - Windows: 'dir' or 'Get-Date'")
    print("   - Linux/Mac: 'ls' or 'date'")
    print("   - Universal: 'echo Hello World'")
    print("8. Check the command output panel for results")
    print("\n📋 Expected behavior:")
    print("   ✅ Command should appear in the output panel")
    print("   ✅ Command result should be displayed")
    print("   ✅ Status should show [SUCCESS] or [ERROR]")
    print("\n🔧 Troubleshooting:")
    print("   - If no agent appears: Check simple-client.py is running")
    print("   - If commands don't work: Check browser console for errors")
    print("   - If connection fails: Check controller.py is running")
    print("="*70)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Command Execution Test Script')
    parser.add_argument('--controller-url', default='http://localhost:8080',
                       help='Controller URL (default: http://localhost:8080)')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Start simple client in interactive mode')
    parser.add_argument('--skip-controller', action='store_true',
                       help='Skip controller startup check')
    
    args = parser.parse_args()
    
    print("🧪 Command Execution Test Script")
    print("=" * 50)
    print(f"Controller URL: {args.controller_url}")
    print(f"Interactive Mode: {'✅ Enabled' if args.interactive else '❌ Disabled'}")
    print("=" * 50)
    
    # Step 1: Check/Start controller
    if not args.skip_controller:
        if not start_controller():
            log_message("❌ Cannot proceed without controller", "error")
            return False
    
    # Step 2: Start simple client
    client_process = start_simple_client(args.controller_url, args.interactive)
    if not client_process:
        log_message("❌ Cannot proceed without simple client", "error")
        return False
    
    # Step 3: Print testing instructions
    print_testing_instructions()
    
    # Step 4: Wait for user input
    try:
        if args.interactive:
            log_message("Simple client is running in interactive mode", "info")
            log_message("Press Ctrl+C to stop", "info")
            client_process.wait()
        else:
            log_message("Simple client is running in background", "info")
            log_message("Press Enter to stop the test...", "info")
            input()
            
    except KeyboardInterrupt:
        log_message("🛑 Test interrupted by user", "warning")
    
    # Cleanup
    if client_process.poll() is None:
        log_message("Stopping simple client...", "info")
        client_process.terminate()
        client_process.wait()
    
    log_message("✅ Test completed", "success")
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        log_message("🛑 Test interrupted by user", "warning")
        sys.exit(1)
    except Exception as e:
        log_message(f"❌ Unexpected error: {e}", "error")
        sys.exit(1)