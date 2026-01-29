"""
High-performance FastAPI WebSocket server with Redis message routing
Optimized for low-latency command/response communication
"""

import asyncio
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Set, Optional, Any
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from performance_monitor import performance_monitor, record_command_latency, record_connection_quality

# Message models
class CommandMessage(BaseModel):
    id: str
    agent_id: str
    command: str
    args: Optional[Dict[str, Any]] = None
    timestamp: float
    priority: str = "normal"  # normal, high, urgent

class ResponseMessage(BaseModel):
    id: str
    command_id: str
    agent_id: str
    status: str  # success, error, progress
    data: Optional[Dict[str, Any]] = None
    timestamp: float
    latency_ms: float

# Global state
class ConnectionManager:
    def __init__(self):
        self.agent_connections: Dict[str, WebSocket] = {}
        self.controller_connections: Set[WebSocket] = set()
        self.redis_client: Optional[redis.Redis] = None
        self.connection_start_times: Dict[str, float] = {}
        self.sent_commands: Dict[str, CommandMessage] = {}
        
    async def connect_redis(self):
        """Connect to Redis for message routing"""
        try:
            self.redis_client = redis.Redis(
                host="localhost", 
                port=6379, 
                db=0,
                decode_responses=True,
                socket_keepalive=True,
                socket_keepalive_options={}
            )
            await self.redis_client.ping()
            print("✅ Redis connected successfully")
        except Exception as e:
            print(f"⚠️ Redis connection failed: {e}")
            print("⚠️ Falling back to in-memory routing")
            self.redis_client = None
    
    async def disconnect_redis(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
    
    async def register_agent(self, agent_id: str, websocket: WebSocket):
        """Register agent WebSocket connection"""
        await websocket.accept()
        self.agent_connections[agent_id] = websocket
        self.connection_start_times[agent_id] = time.time()
        print(f"🟢 Agent {agent_id} connected")
        record_connection_quality(agent_id, 0, reconnects=0, uptime_percentage=100.0)
        
        # Notify controllers
        await self.broadcast_to_controllers({
            "type": "agent_status",
            "agent_id": agent_id,
            "status": "online",
            "timestamp": time.time()
        })
    
    async def unregister_agent(self, agent_id: str):
        """Unregister agent WebSocket connection"""
        if agent_id in self.agent_connections:
            del self.agent_connections[agent_id]
            print(f"🔴 Agent {agent_id} disconnected")
            start = self.connection_start_times.pop(agent_id, None)
            if start is not None:
                duration_ms = (time.time() - start) * 1000
                record_connection_quality(agent_id, duration_ms, disconnects=1)
            
            # Notify controllers
            await self.broadcast_to_controllers({
                "type": "agent_status",
                "agent_id": agent_id,
                "status": "offline",
                "timestamp": time.time()
            })
    
    async def register_controller(self, websocket: WebSocket):
        """Register controller WebSocket connection"""
        await websocket.accept()
        self.controller_connections.add(websocket)
        print("🟢 Controller connected")
        
        # Send current agent list
        agent_list = list(self.agent_connections.keys())
        await websocket.send_json({
            "type": "agent_list",
            "agents": agent_list,
            "timestamp": time.time()
        })
    
    async def unregister_controller(self, websocket: WebSocket):
        """Unregister controller WebSocket connection"""
        self.controller_connections.discard(websocket)
        print("🔴 Controller disconnected")
    
    async def send_command_to_agent(self, command: CommandMessage) -> bool:
        """Send command to specific agent"""
        if command.agent_id in self.agent_connections:
            try:
                websocket = self.agent_connections[command.agent_id]
                await websocket.send_json(command.dict())
                self.sent_commands[command.id] = command
                
                # Store command in Redis for tracking
                if self.redis_client:
                    await self.redis_client.setex(
                        f"command:{command.id}",
                        300,  # 5 minute TTL
                        json.dumps(command.dict())
                    )
                
                return True
            except Exception as e:
                print(f"❌ Failed to send command to agent {command.agent_id}: {e}")
                await self.unregister_agent(command.agent_id)
        return False
    
    async def send_response_to_controller(self, response: ResponseMessage) -> bool:
        """Send response to all connected controllers"""
        if not self.controller_connections:
            return False
            
        sent = False
        for websocket in list(self.controller_connections):
            try:
                await websocket.send_json(response.dict())
                sent = True
            except Exception as e:
                print(f"❌ Failed to send response to controller: {e}")
                await self.unregister_controller(websocket)
        
        return sent
    
    async def broadcast_to_controllers(self, message: dict):
        """Broadcast message to all controllers"""
        if not self.controller_connections:
            return
            
        for websocket in list(self.controller_connections):
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"❌ Failed to broadcast to controller: {e}")
                await self.unregister_controller(websocket)

# Initialize manager
manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    await manager.connect_redis()
    print("🚀 FastAPI WebSocket server starting...")
    yield
    # Shutdown
    await manager.disconnect_redis()
    print("👋 FastAPI WebSocket server shutting down...")

# Create FastAPI app
app = FastAPI(
    title="Low-Latency Control Server",
    description="High-performance WebSocket server for command/response routing",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "agents_connected": len(manager.agent_connections),
        "controllers_connected": len(manager.controller_connections),
        "redis_connected": manager.redis_client is not None
    }

# Agent WebSocket endpoint
@app.websocket("/ws/agent/{agent_id}")
async def agent_websocket(websocket: WebSocket, agent_id: str):
    """WebSocket endpoint for agents"""
    await manager.register_agent(agent_id, websocket)
    
    try:
        while True:
            # Receive response from agent
            data = await websocket.receive_json()
            
            if data.get("type") == "response":
                # Calculate latency
                command_id = data.get("command_id")
                command_timestamp = data.get("command_timestamp", time.time())
                latency_ms = (time.time() - command_timestamp) * 1000
                cmd = manager.sent_commands.get(command_id)
                cmd_type = cmd.command if cmd else "unknown"
                success = data.get("status", "success") != "error"
                record_command_latency(command_id, agent_id, cmd_type, latency_ms, success, None if success else str(data.get("data")))
                
                response = ResponseMessage(
                    id=str(uuid.uuid4()),
                    command_id=command_id,
                    agent_id=agent_id,
                    status=data.get("status", "success"),
                    data=data.get("data"),
                    timestamp=time.time(),
                    latency_ms=latency_ms
                )
                
                # Send to controllers
                await manager.send_response_to_controller(response)
                
            elif data.get("type") == "heartbeat":
                # Handle heartbeat
                await manager.broadcast_to_controllers({
                    "type": "heartbeat",
                    "agent_id": agent_id,
                    "timestamp": time.time()
                })
                
    except WebSocketDisconnect:
        await manager.unregister_agent(agent_id)
    except Exception as e:
        print(f"❌ Agent WebSocket error: {e}")
        await manager.unregister_agent(agent_id)

# Controller WebSocket endpoint
@app.websocket("/ws/controller")
async def controller_websocket(websocket: WebSocket):
    """WebSocket endpoint for controllers"""
    await manager.register_controller(websocket)
    
    try:
        while True:
            # Receive command from controller
            data = await websocket.receive_json()
            
            if data.get("type") == "command":
                command = CommandMessage(
                    id=str(uuid.uuid4()),
                    agent_id=data.get("agent_id"),
                    command=data.get("command"),
                    args=data.get("args"),
                    timestamp=time.time(),
                    priority=data.get("priority", "normal")
                )
                
                # Send to agent
                success = await manager.send_command_to_agent(command)
                
                # Send acknowledgment back to controller
                await websocket.send_json({
                    "type": "command_ack",
                    "command_id": command.id,
                    "success": success,
                    "timestamp": time.time()
                })
            elif data.get("type") == "controller_heartbeat":
                await websocket.send_json({
                    "type": "controller_heartbeat_ack",
                    "timestamp": time.time()
                })
                
    except WebSocketDisconnect:
        await manager.unregister_controller(websocket)
    except Exception as e:
        print(f"❌ Controller WebSocket error: {e}")
        await manager.unregister_controller(websocket)

# Metrics endpoint
@app.get("/metrics")
async def get_metrics():
    """Get performance metrics"""
    return {
        "agents_connected": len(manager.agent_connections),
        "controllers_connected": len(manager.controller_connections),
        "redis_connected": manager.redis_client is not None,
        "uptime": time.time(),
        "timestamp": time.time()
    }

if __name__ == "__main__":
    print("🚀 Starting FastAPI WebSocket server...")
    print("📡 Agent endpoint: ws://localhost:8000/ws/agent/{agent_id}")
    print("🎮 Controller endpoint: ws://localhost:8000/ws/controller")
    print("📊 Metrics: http://localhost:8000/metrics")
    print("🏥 Health: http://localhost:8000/health")
    
    uvicorn.run(
        "fastapi_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
