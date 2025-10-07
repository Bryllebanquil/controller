#!/usr/bin/env python3
"""
Test Script for Simple Client
=============================

This script tests the simple client connection without running it interactively.
"""

import subprocess
import sys
import time
import os

def test_simple_client():
    """Test the simple client with a timeout"""
    print("🧪 Testing Simple Client Connection...")
    print("=" * 40)
    
    # Set environment variables for testing
    env = os.environ.copy()
    env['CONTROLLER_URL'] = 'https://agent-controller-backend.onrender.com'
    
    try:
        # Run the simple client with a timeout
        result = subprocess.run(
            [sys.executable, 'simple-client.py'],
            env=env,
            timeout=60,  # 60 second timeout
            capture_output=True,
            text=True
        )
        
        print("📋 Test Results:")
        print(f"Return Code: {result.returncode}")
        print(f"STDOUT:\n{result.stdout}")
        
        if result.stderr:
            print(f"STDERR:\n{result.stderr}")
        
        if result.returncode == 0:
            print("✅ Simple client test PASSED")
            return True
        else:
            print("❌ Simple client test FAILED")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Test timed out after 60 seconds")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == "__main__":
    success = test_simple_client()
    sys.exit(0 if success else 1)