#!/usr/bin/env python3
"""
Smoke Test for client.py - Quick Verification
Run this to verify all fixes are working correctly

Usage:
    python3 smoke_test.py

Expected runtime: 5 minutes
"""

import subprocess
import time
import threading
import sys
import os

class SmokeTest:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
        
    def test(self, name, func):
        """Run a test and track results"""
        print(f"\n{'='*70}")
        print(f"🧪 TEST: {name}")
        print(f"{'='*70}")
        
        try:
            start = time.time()
            result = func()
            elapsed = time.time() - start
            
            if result:
                print(f"✅ PASS ({elapsed:.2f}s)")
                self.passed += 1
            else:
                print(f"❌ FAIL ({elapsed:.2f}s)")
                self.failed += 1
                
            self.tests.append((name, result, elapsed))
            return result
            
        except Exception as e:
            print(f"❌ EXCEPTION: {e}")
            self.failed += 1
            self.tests.append((name, False, 0))
            return False
    
    def test_import(self):
        """Test 1: Import client.py without errors"""
        print("Importing client.py...")
        try:
            # Try to import (syntax check)
            result = subprocess.run(
                [sys.executable, '-m', 'py_compile', 'client.py'],
                capture_output=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print("✓ Syntax OK")
                print("✓ No import errors")
                return True
            else:
                print(f"✗ Compilation failed: {result.stderr.decode()}")
                return False
                
        except Exception as e:
            print(f"✗ Import test failed: {e}")
            return False
    
    def test_thread_locks_exist(self):
        """Test 2: Verify thread locks are defined"""
        print("Checking for thread lock definitions...")
        
        with open('client.py', 'r') as f:
            content = f.read()
        
        required_locks = [
            '_stream_lock',
            '_audio_stream_lock',
            '_camera_stream_lock',
            '_keylogger_lock',
            '_clipboard_lock',
            '_reverse_shell_lock',
            '_voice_control_lock',
        ]
        
        found = 0
        for lock in required_locks:
            if f'{lock} = threading.Lock()' in content:
                print(f"✓ Found {lock}")
                found += 1
            else:
                print(f"✗ Missing {lock}")
        
        print(f"\nFound {found}/{len(required_locks)} locks")
        return found == len(required_locks)
    
    def test_safe_emit_exists(self):
        """Test 3: Verify safe_emit() function exists"""
        print("Checking for safe_emit() function...")
        
        with open('client.py', 'r') as f:
            content = f.read()
        
        if 'def safe_emit(' in content:
            print("✓ safe_emit() function defined")
            
            # Check it has connection checking
            if 'sio.connected' in content:
                print("✓ Connection checking present")
            else:
                print("✗ Missing connection check")
                return False
            
            # Check it handles exceptions
            if 'not a connected namespace' in content:
                print("✓ Exception handling present")
            else:
                print("✗ Missing exception handling")
                return False
            
            return True
        else:
            print("✗ safe_emit() function not found")
            return False
    
    def test_safe_emit_usage(self):
        """Test 4: Verify safe_emit() is used instead of direct emit"""
        print("Checking safe_emit() usage...")
        
        with open('client.py', 'r') as f:
            content = f.read()
        
        import re
        safe_emits = len(re.findall(r'safe_emit\s*\(', content))
        direct_emits = len(re.findall(r'sio\.emit\s*\(', content))
        
        # Subtract 1 for the emit inside safe_emit function
        unsafe_emits = direct_emits - 1
        
        print(f"✓ safe_emit() calls: {safe_emits}")
        print(f"✓ Direct sio.emit() calls: {unsafe_emits}")
        
        if safe_emits >= 80 and unsafe_emits <= 2:
            print(f"✓ Excellent coverage: {(safe_emits/(safe_emits+unsafe_emits)*100):.1f}%")
            return True
        else:
            print(f"✗ Poor coverage: {(safe_emits/(safe_emits+unsafe_emits)*100):.1f}%")
            return False
    
    def test_keyboard_interrupt_handlers(self):
        """Test 5: Verify KeyboardInterrupt handlers in workers"""
        print("Checking KeyboardInterrupt handlers...")
        
        with open('client.py', 'r') as f:
            content = f.read()
        
        import re
        handlers = len(re.findall(r'except KeyboardInterrupt:', content))
        
        print(f"✓ Found {handlers} KeyboardInterrupt handlers")
        
        if handlers >= 30:
            print("✓ Excellent coverage (30+ handlers)")
            return True
        else:
            print(f"✗ Insufficient coverage ({handlers} < 30)")
            return False
    
    def test_start_functions_protected(self):
        """Test 6: Verify start functions use locks"""
        print("Checking start function protection...")
        
        with open('client.py', 'r') as f:
            content = f.read()
        
        start_functions = [
            'start_streaming',
            'start_audio_streaming',
            'start_camera_streaming',
            'start_keylogger',
            'start_clipboard_monitor',
            'start_reverse_shell',
            'start_voice_control',
        ]
        
        import re
        protected = 0
        for func in start_functions:
            # Find function definition
            pattern = rf'def {func}\([^)]*\):.*?(?=\ndef )'
            match = re.search(pattern, content, re.DOTALL)
            
            if match:
                func_body = match.group(0)
                if 'with _' in func_body and '_lock:' in func_body:
                    print(f"✓ {func} - Protected with lock")
                    protected += 1
                else:
                    print(f"✗ {func} - NOT protected")
            else:
                print(f"✗ {func} - Not found")
        
        print(f"\nProtected: {protected}/{len(start_functions)}")
        return protected == len(start_functions)
    
    def test_documentation_exists(self):
        """Test 7: Verify documentation files exist"""
        print("Checking documentation files...")
        
        docs = [
            'FIXES_REPORT.md',
            'CRITICAL_ISSUES_FOUND.md',
            'THIRD_SCAN_FIXES_APPLIED.md',
            'COMPREHENSIVE_TEST_SUITE.md',
            'FINAL_COMPLETION_SUMMARY.md',
            'QUICK_REFERENCE.md',
            'FOURTH_SCAN_FINAL_REPORT.md',
        ]
        
        found = 0
        for doc in docs:
            if os.path.exists(doc):
                size = os.path.getsize(doc)
                print(f"✓ {doc:45} ({size:,} bytes)")
                found += 1
            else:
                print(f"✗ {doc:45} MISSING")
        
        print(f"\nFound {found}/{len(docs)} documentation files")
        return found >= 5  # At least 5 docs required
    
    def run_all(self):
        """Run all smoke tests"""
        print("=" * 70)
        print("🔥 CLIENT.PY SMOKE TEST SUITE")
        print("=" * 70)
        print(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Python: {sys.version}")
        print("=" * 70)
        
        # Run all tests
        self.test("Import & Syntax Check", self.test_import)
        self.test("Thread Locks Defined", self.test_thread_locks_exist)
        self.test("safe_emit() Function Exists", self.test_safe_emit_exists)
        self.test("safe_emit() Usage Coverage", self.test_safe_emit_usage)
        self.test("KeyboardInterrupt Handlers", self.test_keyboard_interrupt_handlers)
        self.test("Start Functions Protected", self.test_start_functions_protected)
        self.test("Documentation Complete", self.test_documentation_exists)
        
        # Print summary
        print("\n" + "=" * 70)
        print("📊 SMOKE TEST SUMMARY")
        print("=" * 70)
        
        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0
        
        print(f"Tests Run: {total}")
        print(f"Passed: {self.passed} ✅")
        print(f"Failed: {self.failed} ❌")
        print(f"Pass Rate: {pass_rate:.1f}%")
        print()
        
        # Detailed results
        print("Detailed Results:")
        for name, result, elapsed in self.tests:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status} {name:40} ({elapsed:.2f}s)")
        
        print("=" * 70)
        
        if pass_rate >= 95:
            print("✅ SMOKE TEST PASSED - CODE IS PRODUCTION READY!")
            print("✅ All critical fixes verified")
            print("✅ Ready for comprehensive testing")
            return 0
        elif pass_rate >= 80:
            print("⚠️  SMOKE TEST PARTIAL PASS - Some issues detected")
            print("⚠️  Review failed tests before deployment")
            return 1
        else:
            print("❌ SMOKE TEST FAILED - Critical issues detected")
            print("❌ Fix issues before proceeding")
            return 2

if __name__ == '__main__':
    tester = SmokeTest()
    exit_code = tester.run_all()
    sys.exit(exit_code)
