"""
Advanced Network Pivoting and Lateral Movement Module
Implements sophisticated network pivoting, port forwarding, and lateral movement capabilities
"""

import socket
import threading
import select
import struct
import time
import json
import subprocess
import platform
from datetime import datetime
from collections import defaultdict
import queue


class AdvancedNetworkPivot:
    """
    Advanced network pivoting with:
    - SOCKS5 proxy server
    - Port forwarding (local and remote)
    - Dynamic port allocation
    - Multi-hop pivoting
    - Traffic tunneling
    - Connection pooling
    """
    
    def __init__(self, bind_address='127.0.0.1', bind_port=1080):
        self.bind_address = bind_address
        self.bind_port = bind_port
        self.active = False
        self.server_socket = None
        self.connections = []
        self.port_forwards = []
        self.pivot_chain = []
        self.connection_stats = defaultdict(int)
        
        # Threading
        self.server_thread = None
        self.forward_threads = []
        
        print(f"[PIVOT] Initialized on {bind_address}:{bind_port}")
    
    def start_socks_proxy(self):
        """Start SOCKS5 proxy server for pivoting"""
        if self.active:
            return {'success': False, 'error': 'Proxy already running'}
        
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.bind_address, self.bind_port))
            self.server_socket.listen(10)
            
            self.active = True
            self.server_thread = threading.Thread(target=self._socks_server_loop, daemon=True)
            self.server_thread.start()
            
            print(f"[PIVOT] SOCKS5 proxy started on {self.bind_address}:{self.bind_port}")
            return {'success': True, 'address': self.bind_address, 'port': self.bind_port}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _socks_server_loop(self):
        """Main SOCKS5 server loop"""
        while self.active:
            try:
                readable, _, _ = select.select([self.server_socket], [], [], 1)
                
                if readable:
                    client_socket, client_address = self.server_socket.accept()
                    print(f"[PIVOT] SOCKS connection from {client_address}")
                    
                    # Handle in separate thread
                    handler = threading.Thread(
                        target=self._handle_socks_client,
                        args=(client_socket, client_address),
                        daemon=True
                    )
                    handler.start()
                    self.connections.append(handler)
                    
            except Exception as e:
                if self.active:
                    print(f"[PIVOT] Server loop error: {e}")
    
    def _handle_socks_client(self, client_socket, client_address):
        """Handle SOCKS5 client connection"""
        try:
            # SOCKS5 greeting
            greeting = client_socket.recv(2)
            if not greeting or greeting[0] != 0x05:  # SOCKS version 5
                client_socket.close()
                return
            
            # No authentication required
            client_socket.sendall(b'\x05\x00')
            
            # SOCKS5 request
            request = client_socket.recv(4)
            if not request or request[0] != 0x05:
                client_socket.close()
                return
            
            cmd = request[1]
            atyp = request[3]
            
            # Only support CONNECT command
            if cmd != 0x01:
                # Command not supported
                client_socket.sendall(b'\x05\x07\x00\x01\x00\x00\x00\x00\x00\x00')
                client_socket.close()
                return
            
            # Parse destination
            if atyp == 0x01:  # IPv4
                addr_bytes = client_socket.recv(4)
                dst_addr = socket.inet_ntoa(addr_bytes)
            elif atyp == 0x03:  # Domain name
                domain_len = ord(client_socket.recv(1))
                dst_addr = client_socket.recv(domain_len).decode()
            elif atyp == 0x04:  # IPv6
                addr_bytes = client_socket.recv(16)
                dst_addr = socket.inet_ntop(socket.AF_INET6, addr_bytes)
            else:
                client_socket.sendall(b'\x05\x08\x00\x01\x00\x00\x00\x00\x00\x00')
                client_socket.close()
                return
            
            # Port
            port_bytes = client_socket.recv(2)
            dst_port = struct.unpack('>H', port_bytes)[0]
            
            print(f"[PIVOT] SOCKS request: {dst_addr}:{dst_port}")
            
            # Connect to destination
            try:
                remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                remote_socket.connect((dst_addr, dst_port))
                
                # Success response
                bind_addr = remote_socket.getsockname()
                reply = b'\x05\x00\x00\x01'
                reply += socket.inet_aton(bind_addr[0])
                reply += struct.pack('>H', bind_addr[1])
                client_socket.sendall(reply)
                
                # Relay data
                self._relay_data(client_socket, remote_socket, dst_addr, dst_port)
                
            except Exception as e:
                # Connection failed
                print(f"[PIVOT] Connection to {dst_addr}:{dst_port} failed: {e}")
                client_socket.sendall(b'\x05\x05\x00\x01\x00\x00\x00\x00\x00\x00')
                client_socket.close()
                
        except Exception as e:
            print(f"[PIVOT] Client handler error: {e}")
        finally:
            client_socket.close()
    
    def _relay_data(self, client_sock, remote_sock, dst_addr, dst_port):
        """Relay data between client and remote"""
        try:
            sockets = [client_sock, remote_sock]
            total_bytes = 0
            
            while True:
                readable, _, exceptional = select.select(sockets, [], sockets, 60)
                
                if exceptional:
                    break
                
                if not readable:
                    break
                
                for sock in readable:
                    data = sock.recv(4096)
                    
                    if not data:
                        return
                    
                    total_bytes += len(data)
                    
                    if sock is client_sock:
                        remote_sock.sendall(data)
                    else:
                        client_sock.sendall(data)
            
            # Update stats
            self.connection_stats[f"{dst_addr}:{dst_port}"] += total_bytes
            print(f"[PIVOT] Relayed {total_bytes} bytes to {dst_addr}:{dst_port}")
            
        except Exception as e:
            print(f"[PIVOT] Relay error: {e}")
        finally:
            client_sock.close()
            remote_sock.close()
    
    def add_port_forward(self, local_port, remote_host, remote_port, reverse=False):
        """
        Add port forwarding rule
        
        Args:
            local_port: Local port to listen on
            remote_host: Remote host to forward to
            remote_port: Remote port to forward to
            reverse: If True, create reverse port forward
        """
        try:
            if reverse:
                # Reverse port forward (remote -> local)
                return self._create_reverse_forward(local_port, remote_host, remote_port)
            else:
                # Local port forward (local -> remote)
                return self._create_local_forward(local_port, remote_host, remote_port)
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _create_local_forward(self, local_port, remote_host, remote_port):
        """Create local port forward"""
        try:
            # Create listening socket
            forward_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            forward_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            forward_socket.bind(('0.0.0.0', local_port))
            forward_socket.listen(5)
            
            # Start forwarding thread
            forward_thread = threading.Thread(
                target=self._local_forward_loop,
                args=(forward_socket, remote_host, remote_port),
                daemon=True
            )
            forward_thread.start()
            self.forward_threads.append(forward_thread)
            
            # Track forwarding rule
            self.port_forwards.append({
                'type': 'local',
                'local_port': local_port,
                'remote_host': remote_host,
                'remote_port': remote_port,
                'socket': forward_socket,
                'created': datetime.now().isoformat()
            })
            
            print(f"[PIVOT] Local port forward: {local_port} -> {remote_host}:{remote_port}")
            return {'success': True, 'local_port': local_port}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _local_forward_loop(self, listen_socket, remote_host, remote_port):
        """Loop for local port forwarding"""
        while self.active:
            try:
                readable, _, _ = select.select([listen_socket], [], [], 1)
                
                if readable:
                    client_socket, client_addr = listen_socket.accept()
                    print(f"[PIVOT] Forward connection from {client_addr}")
                    
                    # Connect to remote
                    remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    remote_socket.connect((remote_host, remote_port))
                    
                    # Relay in background
                    relay_thread = threading.Thread(
                        target=self._relay_data,
                        args=(client_socket, remote_socket, remote_host, remote_port),
                        daemon=True
                    )
                    relay_thread.start()
                    
            except Exception as e:
                if self.active:
                    print(f"[PIVOT] Forward loop error: {e}")
    
    def _create_reverse_forward(self, local_port, remote_host, remote_port):
        """Create reverse port forward (not implemented in basic version)"""
        return {'success': False, 'error': 'Reverse forwarding requires agent support'}
    
    def discover_network_hosts(self, network_range='192.168.1.0/24'):
        """
        Discover hosts on the network
        
        Args:
            network_range: Network range to scan (CIDR notation)
        """
        try:
            import ipaddress
            
            network = ipaddress.ip_network(network_range, strict=False)
            discovered = []
            
            print(f"[PIVOT] Scanning network: {network_range}")
            
            # Scan common ports on each host
            common_ports = [22, 80, 443, 445, 3389, 5985, 5986]
            
            def scan_host(ip):
                host_info = {'ip': str(ip), 'ports': []}
                
                for port in common_ports:
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(0.5)
                        result = sock.connect_ex((str(ip), port))
                        
                        if result == 0:
                            host_info['ports'].append(port)
                        
                        sock.close()
                    except:
                        pass
                
                if host_info['ports']:
                    discovered.append(host_info)
                    print(f"[PIVOT] Found host: {ip} - Ports: {host_info['ports']}")
            
            # Scan first 10 hosts (limited for demo)
            threads = []
            for ip in list(network.hosts())[:10]:
                t = threading.Thread(target=scan_host, args=(ip,), daemon=True)
                t.start()
                threads.append(t)
            
            # Wait for scans
            for t in threads:
                t.join(timeout=5)
            
            return {
                'success': True,
                'network': network_range,
                'hosts_found': len(discovered),
                'hosts': discovered
            }
            
        except ImportError:
            return {'success': False, 'error': 'ipaddress module not available'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_pivot_chain(self, chain_config):
        """
        Create multi-hop pivot chain
        
        Args:
            chain_config: List of pivot hops [{'host': 'x.x.x.x', 'port': 1080}, ...]
        """
        self.pivot_chain = chain_config
        
        return {
            'success': True,
            'chain_length': len(chain_config),
            'chain': chain_config
        }
    
    def get_network_info(self):
        """Get local network information"""
        try:
            info = {
                'hostname': socket.gethostname(),
                'interfaces': [],
                'routing_table': []
            }
            
            # Get IP addresses
            try:
                hostname = socket.gethostname()
                ip_list = socket.getaddrinfo(hostname, None)
                
                for ip in ip_list:
                    if ip[0] == socket.AF_INET:  # IPv4
                        info['interfaces'].append({
                            'family': 'IPv4',
                            'address': ip[4][0]
                        })
            except:
                pass
            
            # Try to get routing info (platform specific)
            if platform.system() == 'Windows':
                try:
                    result = subprocess.run(['route', 'print'], capture_output=True, text=True)
                    info['routing_table_raw'] = result.stdout[:500]  # Limit size
                except:
                    pass
            else:
                try:
                    result = subprocess.run(['ip', 'route'], capture_output=True, text=True)
                    info['routing_table_raw'] = result.stdout[:500]
                except:
                    pass
            
            return info
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_active_connections(self):
        """Get currently active pivot connections"""
        return {
            'socks_active': self.active,
            'bind_address': self.bind_address,
            'bind_port': self.bind_port,
            'active_connections': len(self.connections),
            'port_forwards': len(self.port_forwards),
            'port_forward_rules': [
                {
                    'type': pf['type'],
                    'local_port': pf['local_port'],
                    'remote_host': pf['remote_host'],
                    'remote_port': pf['remote_port'],
                    'created': pf['created']
                }
                for pf in self.port_forwards
            ],
            'traffic_stats': dict(self.connection_stats)
        }
    
    def stop_all(self):
        """Stop all pivoting services"""
        self.active = False
        
        # Close server socket
        if self.server_socket:
            self.server_socket.close()
        
        # Close port forwards
        for pf in self.port_forwards:
            try:
                pf['socket'].close()
            except:
                pass
        
        # Wait for threads
        if self.server_thread:
            self.server_thread.join(timeout=2)
        
        for thread in self.forward_threads:
            thread.join(timeout=1)
        
        print("[PIVOT] All pivoting services stopped")
        
        return {'success': True}


class LateralMovementManager:
    """Manage lateral movement across network"""
    
    def __init__(self):
        self.compromised_hosts = []
        self.movement_history = []
    
    def attempt_wmi_exec(self, target_host, username, password, command):
        """Attempt WMI execution (Windows)"""
        if platform.system() != 'Windows':
            return {'success': False, 'error': 'WMI only available on Windows'}
        
        try:
            # This would use WMI to execute remote commands
            # Simplified for demonstration
            self.movement_history.append({
                'method': 'wmi',
                'target': target_host,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'note': 'WMI execution not implemented in demo'
            })
            
            return {'success': False, 'error': 'WMI exec not implemented'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def attempt_psexec(self, target_host, username, password, command):
        """Attempt PsExec-style execution"""
        self.movement_history.append({
            'method': 'psexec',
            'target': target_host,
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'note': 'PsExec not implemented in demo'
        })
        
        return {'success': False, 'error': 'PsExec not implemented'}
    
    def attempt_ssh(self, target_host, username, password, command):
        """Attempt SSH execution"""
        try:
            import paramiko
            
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(target_host, username=username, password=password, timeout=10)
            
            stdin, stdout, stderr = ssh.exec_command(command)
            output = stdout.read().decode()
            error = stderr.read().decode()
            
            ssh.close()
            
            self.movement_history.append({
                'method': 'ssh',
                'target': target_host,
                'timestamp': datetime.now().isoformat(),
                'success': True,
                'output': output[:200]
            })
            
            self.compromised_hosts.append(target_host)
            
            return {'success': True, 'output': output, 'error': error}
            
        except ImportError:
            return {'success': False, 'error': 'paramiko not available'}
        except Exception as e:
            self.movement_history.append({
                'method': 'ssh',
                'target': target_host,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
            return {'success': False, 'error': str(e)}
    
    def get_movement_report(self):
        """Get lateral movement report"""
        return {
            'compromised_hosts': self.compromised_hosts,
            'total_attempts': len(self.movement_history),
            'successful_attempts': sum(1 for h in self.movement_history if h.get('success')),
            'history': self.movement_history[-10:]  # Last 10 attempts
        }


if __name__ == '__main__':
    # Test network pivoting
    print("Testing Advanced Network Pivoting\n")
    
    pivot = AdvancedNetworkPivot(bind_address='127.0.0.1', bind_port=1080)
    
    # Start SOCKS proxy
    result = pivot.start_socks_proxy()
    print(f"SOCKS Proxy: {result}\n")
    
    # Add port forward
    result = pivot.add_port_forward(8080, 'example.com', 80)
    print(f"Port Forward: {result}\n")
    
    # Get network info
    net_info = pivot.get_network_info()
    print(f"Network Info: {json.dumps(net_info, indent=2)}\n")
    
    # Discover hosts (limited scan)
    # result = pivot.discover_network_hosts('192.168.1.0/24')
    # print(f"Host Discovery: {result}\n")
    
    # Get active connections
    connections = pivot.get_active_connections()
    print(f"Active Connections: {json.dumps(connections, indent=2)}\n")
    
    # Test lateral movement
    lateral = LateralMovementManager()
    report = lateral.get_movement_report()
    print(f"Lateral Movement Report: {json.dumps(report, indent=2)}\n")
    
    time.sleep(2)
    
    # Cleanup
    pivot.stop_all()
