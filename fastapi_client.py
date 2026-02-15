"""
High-performance client with persistent WebSocket connections
Optimized for low-latency command/response communication
"""

import asyncio
import json
import time
import uuid
import websockets
import threading
import queue
from typing import Dict, Optional, Any, Callable
from datetime import datetime
import logging
from performance_monitor import record_command_latency, record_connection_quality, performance_monitor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FastAPIClient:
    """High-performance WebSocket client for FastAPI server"""
    
    def __init__(self, server_url: str, agent_id: str):
        self.server_url = server_url
        self.agent_id = agent_id
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.connected = False
        self.reconnect_delay = 1
        self.max_reconnect_delay = 60
        
        # Message queues
        self.command_queue = queue.Queue()
        self.response_queue = queue.Queue()
        
        # Command handlers
        self.command_handlers: Dict[str, Callable] = {}
        
        # Connection thread
        self.connection_thread = None
        self.running = False
        
        # Performance tracking
        self.message_stats = {
            'commands_received': 0,
            'responses_sent': 0,
            'connection_time': 0,
            'last_latency': 0
        }
    
    def register_command_handler(self, command: str, handler: Callable):
        """Register a handler for specific commands"""
        self.command_handlers[command] = handler
        logger.info(f"Registered handler for command: {command}")
    
    async def connect(self):
        """Connect to WebSocket server with auto-reconnect"""
        while self.running:
            try:
                ws_url = f"{self.server_url}/ws/agent/{self.agent_id}"
                logger.info(f"Connecting to {ws_url}...")
                
                async with websockets.connect(ws_url) as websocket:
                    self.websocket = websocket
                    self.connected = True
                    self.reconnect_delay = 1
                    self.message_stats['connection_time'] = time.time()
                    record_connection_quality(self.agent_id, 0, reconnects=0, uptime_percentage=100.0)
                    
                    logger.info(f"✅ Connected to server as agent {self.agent_id}")
                    
                    # Start heartbeat
                    heartbeat_task = asyncio.create_task(self.heartbeat_loop())
                    
                    # Handle incoming messages
                    await self.handle_messages()
                    
                    # Cleanup
                    heartbeat_task.cancel()
                    
            except websockets.exceptions.ConnectionClosed:
                logger.warning("Connection closed, attempting reconnect...")
            except Exception as e:
                logger.error(f"Connection error: {e}")
            
            self.connected = False
            if self.message_stats['connection_time'] > 0:
                duration_ms = (time.time() - self.message_stats['connection_time']) * 1000
                record_connection_quality(self.agent_id, duration_ms, disconnects=1)
            
            # Exponential backoff
            if self.running:
                logger.info(f"Reconnecting in {self.reconnect_delay} seconds...")
                await asyncio.sleep(self.reconnect_delay)
                self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)
    
    async def handle_messages(self):
        """Handle incoming WebSocket messages"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    message_type = data.get('type')
                    
                    if message_type == 'command':
                        await self.handle_command(data)
                    else:
                        logger.warning(f"Unknown message type: {message_type}")
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed")
    
    async def handle_command(self, command_data: Dict[str, Any]):
        """Handle incoming command"""
        start_time = time.time()
        
        command_id = command_data.get('id')
        command = command_data.get('command')
        args = command_data.get('args', {})
        
        logger.info(f"Received command: {command} (ID: {command_id})")
        self.message_stats['commands_received'] += 1
        
        try:
            # Execute command
            if command in self.command_handlers:
                result = await self.execute_command_async(command, args)
                status = "success"
            else:
                result = {"error": f"Unknown command: {command}"}
                status = "error"
            
            # Send response
            response = {
                "type": "response",
                "id": str(uuid.uuid4()),
                "command_id": command_id,
                "agent_id": self.agent_id,
                "status": status,
                "data": result,
                "command_timestamp": command_data.get('timestamp', start_time),
                "timestamp": time.time()
            }
            
            await self.send_response(response)
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            self.message_stats['last_latency'] = latency_ms
            record_command_latency(command_id, self.agent_id, command, latency_ms, True)
            logger.info(f"Command {command_id} completed in {latency_ms:.2f}ms")
            
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            
            error_response = {
                "type": "response",
                "id": str(uuid.uuid4()),
                "command_id": command_id,
                "agent_id": self.agent_id,
                "status": "error",
                "data": {"error": str(e)},
                "command_timestamp": command_data.get('timestamp', start_time),
                "timestamp": time.time()
            }
            
            await self.send_response(error_response)
            record_command_latency(command_id, self.agent_id, command, (time.time() - start_time) * 1000, False, str(e))
    
    async def execute_command_async(self, command: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute command asynchronously"""
        handler = self.command_handlers.get(command)
        if handler:
            # Check if handler is async
            if asyncio.iscoroutinefunction(handler):
                return await handler(args)
            else:
                # Run sync handler in thread pool
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, handler, args)
        
        return {"error": f"No handler for command: {command}"}
    
    async def send_response(self, response: Dict[str, Any]):
        """Send response to server"""
        if self.connected and self.websocket:
            try:
                await self.websocket.send(json.dumps(response))
                self.message_stats['responses_sent'] += 1
                logger.debug(f"Response sent: {response.get('command_id')}")
            except Exception as e:
                logger.error(f"Failed to send response: {e}")
    
    async def heartbeat_loop(self):
        """Send periodic heartbeat to server"""
        while self.connected:
            try:
                heartbeat = {
                    "type": "heartbeat",
                    "agent_id": self.agent_id,
                    "timestamp": time.time()
                }
                
                await self.websocket.send(json.dumps(heartbeat))
                logger.debug("Heartbeat sent")
                
                await asyncio.sleep(30)  # 30-second heartbeat
                
            except Exception as e:
                logger.error(f"Heartbeat failed: {e}")
                break
    
    def start(self):
        """Start the client in a separate thread"""
        if self.running:
            return
        
        self.running = True
        self.connection_thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self.connection_thread.start()
        logger.info("FastAPI client started")
    
    def stop(self):
        """Stop the client"""
        self.running = False
        if self.connection_thread:
            self.connection_thread.join(timeout=5)
        logger.info("FastAPI client stopped")
    
    def _run_async_loop(self):
        """Run the async event loop"""
        asyncio.run(self.connect())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            **self.message_stats,
            'connected': self.connected,
            'uptime': time.time() - self.message_stats['connection_time'] if self.message_stats['connection_time'] > 0 else 0
        }

# Example command handlers
async def handle_ping(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle ping command"""
    return {
        "message": "pong",
        "timestamp": time.time(),
        "args": args
    }

async def handle_info(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle info command"""
    return {
        "agent_id": "example_agent",
        "version": "1.0.0",
        "platform": "windows",
        "timestamp": time.time()
    }

# Usage example
if __name__ == "__main__":
    # Create client
    client = FastAPIClient("ws://localhost:8000", "example_agent")
    
    # Register command handlers
    client.register_command_handler("ping", handle_ping)
    client.register_command_handler("info", handle_info)
    
    # Start client
    client.start()
    
    try:
        # Keep running
        while True:
            time.sleep(1)
            stats = client.get_stats()
            print(f"Stats: {stats}")
            
    except KeyboardInterrupt:
        print("Stopping client...")
        client.stop()
