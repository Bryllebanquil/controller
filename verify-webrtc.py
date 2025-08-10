#!/usr/bin/env python3
"""
WebRTC Verification Script
Tests if all dependencies are working for smooth, low-latency streaming
"""

import sys
import time
import subprocess
import platform

def print_header(title):
    print("=" * 60)
    print(f" {title}")
    print("=" * 60)

def print_status(message, status="INFO"):
    colors = {
        "INFO": "\033[94m",    # Blue
        "SUCCESS": "\033[92m", # Green
        "WARNING": "\033[93m", # Yellow
        "ERROR": "\033[91m",   # Red
        "RESET": "\033[0m"     # Reset
    }
    print(f"{colors.get(status, colors['INFO'])}{status}:{colors['RESET']} {message}")

def test_python_version():
    """Test Python version compatibility"""
    print_header("Python Version Check")
    
    version = sys.version_info
    print(f"Python Version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 8:
        print_status("Python version is compatible with WebRTC", "SUCCESS")
        return True
    else:
        print_status("Python version may have compatibility issues", "WARNING")
        return False

def test_imports():
    """Test critical module imports"""
    print_header("Module Import Tests")
    
    modules = {
        "aiortc": "WebRTC core library",
        "cv2": "OpenCV for video processing",
        "mss": "Fast screen capture",
        "pyaudio": "Audio capture and processing",
        "numpy": "Fast array operations",
        "PIL": "Image processing",
        "socketio": "Real-time communication"
    }
    
    results = {}
    
    for module, description in modules.items():
        try:
            if module == "PIL":
                import PIL
                print_status(f"{description}: OK", "SUCCESS")
                results[module] = True
            elif module == "socketio":
                import socketio
                print_status(f"{description}: OK", "SUCCESS")
                results[module] = True
            else:
                __import__(module)
                print_status(f"{description}: OK", "SUCCESS")
                results[module] = True
        except ImportError as e:
            print_status(f"{description}: FAILED - {e}", "ERROR")
            results[module] = False
        except Exception as e:
            print_status(f"{description}: ERROR - {e}", "ERROR")
            results[module] = False
    
    return results

def test_system_info():
    """Display system information"""
    print_header("System Information")
    
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Architecture: {platform.machine()}")
    print(f"Processor: {platform.processor()}")
    
    try:
        import psutil
        memory = psutil.virtual_memory()
        print(f"Memory: {memory.total // (1024**3)} GB total, {memory.available // (1024**3)} GB available")
        
        cpu_count = psutil.cpu_count()
        print(f"CPU Cores: {cpu_count}")
        
        if memory.total >= 4 * 1024**3:  # 4GB
            print_status("Memory: Sufficient for WebRTC", "SUCCESS")
        else:
            print_status("Memory: May be insufficient for smooth streaming", "WARNING")
            
        if cpu_count >= 2:
            print_status("CPU: Sufficient cores for WebRTC", "SUCCESS")
        else:
            print_status("CPU: Limited cores may affect performance", "WARNING")
            
    except ImportError:
        print_status("psutil not available - cannot check system resources", "WARNING")

def test_webrtc_config():
    """Test WebRTC configuration"""
    print_header("WebRTC Configuration Test")
    
    try:
        # Try to import main.py configuration
        import main
        
        if hasattr(main, 'AIORTC_AVAILABLE'):
            if main.AIORTC_AVAILABLE:
                print_status("WebRTC (aiortc) is available", "SUCCESS")
            else:
                print_status("WebRTC (aiortc) is NOT available", "ERROR")
                return False
        else:
            print_status("AIORTC_AVAILABLE not found in main.py", "ERROR")
            return False
            
        if hasattr(main, 'WEBRTC_CONFIG'):
            config = main.WEBRTC_CONFIG
            if config.get('enabled', False):
                print_status("WebRTC is enabled in configuration", "SUCCESS")
                
                # Check quality levels
                if 'quality_levels' in config:
                    print_status("Quality levels configured", "SUCCESS")
                    
                # Check performance tuning
                if 'performance_tuning' in config:
                    perf = config['performance_tuning']
                    if perf.get('ultra_low_latency', False):
                        print_status("Ultra-low latency mode enabled", "SUCCESS")
                    else:
                        print_status("Ultra-low latency mode disabled", "WARNING")
                        
                    if perf.get('hardware_acceleration', False):
                        print_status("Hardware acceleration enabled", "SUCCESS")
                    else:
                        print_status("Hardware acceleration disabled", "WARNING")
                else:
                    print_status("Performance tuning not configured", "WARNING")
            else:
                print_status("WebRTC is disabled in configuration", "ERROR")
                return False
        else:
            print_status("WEBRTC_CONFIG not found in main.py", "ERROR")
            return False
            
        return True
        
    except Exception as e:
        print_status(f"Error testing WebRTC configuration: {e}", "ERROR")
        return False

def test_performance():
    """Test basic performance metrics"""
    print_header("Performance Tests")
    
    try:
        import time
        import numpy as np
        
        # Test array operations (important for video processing)
        start_time = time.time()
        test_array = np.random.rand(1920, 1080, 3).astype(np.uint8)
        array_time = time.time() - start_time
        
        if array_time < 0.1:
            print_status(f"Array operations: Fast ({array_time:.3f}s)", "SUCCESS")
        else:
            print_status(f"Array operations: Slow ({array_time:.3f}s)", "WARNING")
            
        # Test screen capture speed
        try:
            import mss
            with mss.mss() as sct:
                start_time = time.time()
                screenshot = sct.grab(sct.monitors[1])
                capture_time = time.time() - start_time
                
                if capture_time < 0.05:
                    print_status(f"Screen capture: Fast ({capture_time:.3f}s)", "SUCCESS")
                else:
                    print_status(f"Screen capture: Slow ({capture_time:.3f}s)", "WARNING")
                    
        except Exception as e:
            print_status(f"Screen capture test failed: {e}", "WARNING")
            
    except Exception as e:
        print_status(f"Performance tests failed: {e}", "WARNING")

def generate_report(import_results, webrtc_ok):
    """Generate final report"""
    print_header("Final Report")
    
    critical_modules = ['aiortc', 'cv2', 'mss', 'pyaudio']
    critical_ok = all(import_results.get(module, False) for module in critical_modules)
    
    if critical_ok and webrtc_ok:
        print_status("🎉 EXCELLENT: All critical components are ready!", "SUCCESS")
        print_status("Expected performance: <1 second latency, 30 FPS streaming", "SUCCESS")
        print_status("You can now run: python main.py", "SUCCESS")
    elif webrtc_ok:
        print_status("⚠️  GOOD: WebRTC is configured but some modules are missing", "WARNING")
        print_status("Streaming may work but with reduced functionality", "WARNING")
    else:
        print_status("❌ CRITICAL: WebRTC is not properly configured", "ERROR")
        print_status("Streaming will NOT work - fix issues above", "ERROR")
    
    print("\nNext steps:")
    if not critical_ok:
        print("1. Install missing modules: pip install -r requirements-webrtc-optimized.txt")
        print("2. Run setup script: .\\setup-webrtc-optimized.bat")
    if not webrtc_ok:
        print("3. Check main.py configuration")
    if critical_ok and webrtc_ok:
        print("1. Test streaming: python main.py")
        print("2. Monitor performance in controller dashboard")

def main():
    """Main verification function"""
    print_header("WebRTC Verification Script")
    print("This script tests if your system is ready for smooth, low-latency WebRTC streaming")
    print()
    
    # Run all tests
    python_ok = test_python_version()
    print()
    
    import_results = test_imports()
    print()
    
    test_system_info()
    print()
    
    webrtc_ok = test_webrtc_config()
    print()
    
    test_performance()
    print()
    
    generate_report(import_results, webrtc_ok)
    print()
    
    print_header("Verification Complete")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nVerification interrupted by user")
    except Exception as e:
        print(f"\n\nUnexpected error during verification: {e}")
        import traceback
        traceback.print_exc()