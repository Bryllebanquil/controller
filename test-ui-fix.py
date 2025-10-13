#!/usr/bin/env python3
"""
Test script to verify the UI v2.1 command execution fix
"""

import subprocess
import time
import sys
import os

def log_message(message, level="info"):
    """Simple logging function"""
    timestamp = time.strftime("%H:%M:%S")
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
    log_message("Starting UI v2.1 Command Execution Test", "info")
    log_message("=" * 50, "info")
    
    # Check if we're in the right directory
    if not os.path.exists("controller.py"):
        log_message("Error: controller.py not found. Please run from workspace root.", "error")
        sys.exit(1)
    
    if not os.path.exists("agent-controller ui v2.1"):
        log_message("Error: agent-controller ui v2.1 directory not found.", "error")
        sys.exit(1)
    
    log_message("1. Starting controller...", "info")
    try:
        controller_process = subprocess.Popen([sys.executable, "controller.py"], 
                                           stdout=subprocess.PIPE, 
                                           stderr=subprocess.PIPE)
        time.sleep(3)  # Give controller time to start
        
        if controller_process.poll() is None:
            log_message("✅ Controller started successfully", "success")
        else:
            log_message("❌ Controller failed to start", "error")
            return
    except Exception as e:
        log_message(f"❌ Error starting controller: {e}", "error")
        return
    
    log_message("2. Starting simple client...", "info")
    try:
        client_process = subprocess.Popen([sys.executable, "simple-client.py"], 
                                        stdout=subprocess.PIPE, 
                                        stderr=subprocess.PIPE)
        time.sleep(2)  # Give client time to connect
        
        if client_process.poll() is None:
            log_message("✅ Simple client started successfully", "success")
        else:
            log_message("❌ Simple client failed to start", "error")
            return
    except Exception as e:
        log_message(f"❌ Error starting simple client: {e}", "error")
        return
    
    log_message("3. Starting frontend...", "info")
    try:
        os.chdir("agent-controller ui v2.1")
        frontend_process = subprocess.Popen(["npm", "run", "dev"], 
                                          stdout=subprocess.PIPE, 
                                          stderr=subprocess.PIPE)
        time.sleep(5)  # Give frontend time to start
        
        if frontend_process.poll() is None:
            log_message("✅ Frontend started successfully", "success")
        else:
            log_message("❌ Frontend failed to start", "error")
            return
    except Exception as e:
        log_message(f"❌ Error starting frontend: {e}", "error")
        return
    
    log_message("=" * 50, "info")
    log_message("🎉 All services started successfully!", "success")
    log_message("", "info")
    log_message("Next steps:", "info")
    log_message("1. Open your browser and go to http://localhost:5173", "info")
    log_message("2. Login with the password (if required)", "info")
    log_message("3. Select the simple client agent", "info")
    log_message("4. Go to the Commands tab", "info")
    log_message("5. Type 'whoami' and press Enter", "info")
    log_message("6. Check if you see the command output in the terminal", "info")
    log_message("", "info")
    log_message("If you see the output, the fix is working! 🎉", "success")
    log_message("If not, check the browser console (F12) for debug messages", "warning")
    log_message("", "info")
    log_message("Press Ctrl+C to stop all services", "info")
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log_message("", "info")
        log_message("Stopping all services...", "info")
        
        # Stop all processes
        for process in [controller_process, client_process, frontend_process]:
            if process.poll() is None:
                process.terminate()
                process.wait()
        
        log_message("All services stopped", "info")

if __name__ == "__main__":
    main()