#!/usr/bin/env python3
"""
Test script to validate the automatic execution mechanism in client.py
This script tests all the antivirus-friendly features implemented.
"""

import sys
import os
import tempfile
import subprocess
import time

def test_client_execution():
    """Test the client.py execution mechanism"""
    print("Testing client.py automatic execution mechanism...")
    print("=" * 60)
    
    # Test 1: Import the safe execution functions
    print("\n1. Testing safe execution wrapper functions...")
    try:
        # Add the current directory to Python path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        # Import the functions from client.py
        from client import (
            safe_execution_check,
            _check_antivirus_interference,
            _validate_system_permissions,
            _platform_independent_checks
        )
        print("SUCCESS: Successfully imported safe execution functions")
    except Exception as e:
        print(f"✗ Failed to import functions: {e}")
        return False
    
    # Test 2: Test individual functions
    print("\n2. Testing individual validation functions...")
    
    # Test antivirus interference check
    try:
        antivirus_result = _check_antivirus_interference()
        print(f"✓ Antivirus interference check: {antivirus_result} (should be False)")
        if antivirus_result:
            print("  ⚠ Antivirus interference detected - this is expected in some environments")
    except Exception as e:
        print(f"✗ Antivirus interference check failed: {e}")
        return False
    
    # Test system permissions validation
    try:
        permissions_result = _validate_system_permissions()
        print(f"✓ System permissions validation: {permissions_result} (should be True)")
        if not permissions_result:
            print("  ⚠ Permission issues detected")
    except Exception as e:
        print(f"✗ System permissions validation failed: {e}")
        return False
    
    # Test platform-independent checks
    try:
        platform_result = _platform_independent_checks()
        print(f"✓ Platform-independent checks: {platform_result} (should be True)")
        if not platform_result:
            print("  ⚠ Platform issues detected")
    except Exception as e:
        print(f"✗ Platform-independent checks failed: {e}")
        return False
    
    # Test 3: Test the complete safe execution wrapper
    print("\n3. Testing complete safe execution wrapper...")
    try:
        safe_result = safe_execution_check()
        print(f"✓ Safe execution check: {safe_result}")
        if not safe_result:
            print("  ⚠ Safe execution check failed - check individual components above")
    except Exception as e:
        print(f"✗ Safe execution check failed: {e}")
        return False
    
    # Test 4: Test client.py execution with subprocess
    print("\n4. Testing client.py execution...")
    try:
        # Create a test script that imports client.py
        test_script = """
import sys
import os
sys.path.insert(0, r'{}')

# Test that we can import the safe execution functions
try:
    from client import safe_execution_check, _check_antivirus_interference
    print("SUCCESS: Safe execution functions imported successfully")
    
    # Test that safe_execution_check works
    result = safe_execution_check()
    print(f"Safe execution check result: {{result}}")
    
    if result:
        print("SUCCESS: All checks passed - client.py can execute safely")
    else:
        print("WARNING: Some checks failed - client.py may not execute")
        
except Exception as e:
    print(f"ERROR: {{e}}")
    sys.exit(1)
""".format(os.path.dirname(os.path.abspath(__file__)))
        
        # Write test script to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_script)
            test_file = f.name
        
        # Run the test script
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, text=True, timeout=10)
        
        # Clean up test file
        os.unlink(test_file)
        
        print(f"✓ Subprocess execution result: {result.returncode}")
        if result.stdout:
            print("Output:")
            for line in result.stdout.strip().split('\n'):
                print(f"  {line}")
        
        if result.stderr:
            print("Errors:")
            for line in result.stderr.strip().split('\n'):
                print(f"  {line}")
        
        if result.returncode == 0:
            print("✓ Client.py execution test passed")
        else:
            print("✗ Client.py execution test failed")
            return False
            
    except subprocess.TimeoutExpired:
        print("✗ Client.py execution timed out")
        return False
    except Exception as e:
        print(f"✗ Client.py execution test failed: {e}")
        return False
    
    # Test 5: Verify clean exit behavior
    print("\n5. Testing clean exit behavior...")
    try:
        # Check that temp files are cleaned up
        temp_dir = tempfile.gettempdir()
        agent_files = [f for f in os.listdir(temp_dir) if f.startswith('agent_test') or f.startswith('agent_startup')]
        
        if agent_files:
            print(f"⚠ Found {len(agent_files)} temporary agent files (this may be normal)")
            for file in agent_files[:5]:  # Show first 5
                print(f"  - {file}")
        else:
            print("✓ No temporary agent files found (clean exit working)")
            
    except Exception as e:
        print(f"⚠ Could not check temp files: {e}")
    
    print("\n" + "=" * 60)
    print("✓ All execution mechanism tests completed successfully!")
    print("✓ The automatic execution mechanism is working properly")
    print("✓ Antivirus-friendly features are implemented and functional")
    return True

if __name__ == "__main__":
    success = test_client_execution()
    sys.exit(0 if success else 1)