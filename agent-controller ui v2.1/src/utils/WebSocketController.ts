/**
 * High-performance WebSocket controller for React frontend
 * Optimized for low-latency command/response communication
 */

import { useState, useEffect, useRef, useCallback } from 'react';

// Message types
interface CommandMessage {
  id: string;
  agent_id: string;
  command: string;
  args?: Record<string, any>;
  timestamp: number;
  priority?: 'normal' | 'high' | 'urgent';
}

interface ResponseMessage {
  id: string;
  command_id: string;
  agent_id: string;
  status: 'success' | 'error' | 'progress';
  data?: Record<string, any>;
  timestamp: number;
  latency_ms: number;
}

interface AgentStatus {
  agent_id: string;
  status: 'online' | 'offline';
  last_seen: number;
}

interface ConnectionStats {
  connected: boolean;
  commands_sent: number;
  responses_received: number;
  average_latency: number;
  last_latency: number;
  uptime: number;
}

export class WebSocketController {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnect_delay = 1000;
  private max_reconnect_delay = 30000;
  private heartbeat_interval: any = null;
  private heartbeat_ms = 25000;
  private message_handlers = new Map<string, (data: any) => void>();
  private pending_commands = new Map<string, {
    resolve: (response: ResponseMessage) => void;
    reject: (error: Error) => void;
    timestamp: number;
  }>();
  
  // Connection state
  private connected = false;
  private connection_start = 0;
  private agents: string[] = [];
  private stats: ConnectionStats = {
    connected: false,
    commands_sent: 0,
    responses_received: 0,
    average_latency: 0,
    last_latency: 0,
    uptime: 0
  };

  constructor(url: string) {
    this.url = url;
    this.setupMessageHandlers();
  }

  private setupMessageHandlers() {
    // Agent status updates
    this.on('agent_status', (data) => {
      console.log(`Agent ${data.agent_id} is ${data.status}`);
    });

    // Command acknowledgments
    this.on('command_ack', (data) => {
      console.log(`Command ${data.command_id} acknowledged: ${data.success}`);
    });

    // Heartbeat responses
    this.on('heartbeat', (data) => {
      console.log(`Agent ${data.agent_id} heartbeat`);
    });

    // Agent list updates
    this.on('agent_list', (data) => {
      console.log(`Available agents: ${data.agents.join(', ')}`);
      this.agents = data.agents || [];
    });
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        console.log(`Connecting to WebSocket server at ${this.url}...`);
        
        this.ws = new WebSocket(this.url);
        
        this.ws.onopen = () => {
          console.log('✅ Connected to WebSocket server');
          this.connected = true;
          this.connection_start = Date.now();
          this.reconnect_delay = 1000;
          this.stats.connected = true;
          this.startHeartbeat();
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
          } catch (error) {
            console.error('Failed to parse message:', error);
          }
        };

        this.ws.onclose = () => {
          console.log('🔴 WebSocket connection closed');
          this.connected = false;
          this.stats.connected = false;
          this.stopHeartbeat();
          this.attemptReconnect();
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.connected = false;
          this.stats.connected = false;
          this.stopHeartbeat();
          reject(error);
        };

      } catch (error) {
        reject(error);
      }
    });
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.connected = false;
    this.stats.connected = false;
    this.stopHeartbeat();
  }

  private attemptReconnect(): void {
    if (this.connected) return;

    console.log(`Reconnecting in ${this.reconnect_delay}ms...`);
    
    setTimeout(() => {
      this.connect().catch((error) => {
        console.error('Reconnection failed:', error);
        this.reconnect_delay = Math.min(this.reconnect_delay * 2, this.max_reconnect_delay);
        this.attemptReconnect();
      });
    }, this.reconnect_delay);
  }

  private handleMessage(data: any): void {
    const messageType = data.type;
    
    // Handle responses to pending commands
    if (messageType === 'response') {
      const response = data as ResponseMessage;
      const pending = this.pending_commands.get(response.command_id);
      
      if (pending) {
        this.pending_commands.delete(response.command_id);
        pending.resolve(response);
        
        // Update stats
        this.stats.responses_received++;
        this.stats.last_latency = response.latency_ms;
        this.updateAverageLatency(response.latency_ms);
      }
    }

    // Call registered message handlers
    const handler = this.message_handlers.get(messageType);
    if (handler) {
      handler(data);
    }
  }

  private startHeartbeat(): void {
    if (this.heartbeat_interval) return;
    this.heartbeat_interval = setInterval(() => {
      if (this.connected && this.ws) {
        try {
          this.ws.send(JSON.stringify({
            type: 'controller_heartbeat',
            timestamp: Date.now()
          }));
        } catch {}
      }
    }, this.heartbeat_ms);
  }

  private stopHeartbeat(): void {
    if (this.heartbeat_interval) {
      clearInterval(this.heartbeat_interval);
      this.heartbeat_interval = null;
    }
  }

  private updateAverageLatency(latency: number): void {
    const alpha = 0.1; // Smoothing factor
    this.stats.average_latency = this.stats.average_latency * (1 - alpha) + latency * alpha;
  }

  // Public API
  on(messageType: string, handler: (data: any) => void): void {
    this.message_handlers.set(messageType, handler);
  }

  off(messageType: string): void {
    this.message_handlers.delete(messageType);
  }

  async sendCommand(agentId: string, command: string, args?: Record<string, any>, priority: 'normal' | 'high' | 'urgent' = 'normal'): Promise<ResponseMessage> {
    if (!this.connected || !this.ws) {
      throw new Error('WebSocket not connected');
    }

    const ws = this.ws;

    const commandId = `cmd_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    const message: CommandMessage = {
      id: commandId,
      agent_id: agentId,
      command,
      args,
      timestamp: Date.now(),
      priority
    };

    return new Promise((resolve, reject) => {
      // Set up timeout
      const timeout = setTimeout(() => {
        this.pending_commands.delete(commandId);
        reject(new Error(`Command timeout: ${commandId}`));
      }, 30000); // 30 second timeout

      // Store pending command
      this.pending_commands.set(commandId, {
        resolve: (response) => {
          clearTimeout(timeout);
          resolve(response);
        },
        reject: (error) => {
          clearTimeout(timeout);
          reject(error);
        },
        timestamp: Date.now()
      });

      // Send command
      ws.send(JSON.stringify({
        type: 'command',
        ...message
      }));

      this.stats.commands_sent++;
      console.log(`Command sent: ${command} to ${agentId} (ID: ${commandId})`);
    });
  }

  getStats(): ConnectionStats {
    return {
      ...this.stats,
      uptime: this.connected ? Date.now() - this.connection_start : 0
    };
  }

  getConnectedAgents(): string[] {
    // This would be populated by agent_list messages
    return this.agents;
  }
}

// React Hook for WebSocket controller
export function useWebSocketController(serverUrl?: string) {
  // Resolve default URL when not provided
  const resolvedUrl = (() => {
    if (serverUrl) return serverUrl;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const runtimeUrl = (globalThis as any)?.__CONTROLLER_WS_URL__ as string | undefined;
    if (runtimeUrl) return runtimeUrl;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const envUrl = (import.meta as any)?.env?.VITE_CONTROLLER_WS_URL as string | undefined;
    if (envUrl) return envUrl;
    if (typeof window !== 'undefined') {
      const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
      return `${proto}://${window.location.host}/ws/controller`;
    }
    return 'ws://localhost:8000/ws/controller';
  })();

  const [controller] = useState(() => new WebSocketController(resolvedUrl));
  const [connected, setConnected] = useState(false);
  const [stats, setStats] = useState<ConnectionStats>({
    connected: false,
    commands_sent: 0,
    responses_received: 0,
    average_latency: 0,
    last_latency: 0,
    uptime: 0
  });
  const [agents, setAgents] = useState<AgentStatus[]>([]);

  useEffect(() => {
    // Set up message handlers
    controller.on('agent_list', (data) => {
      const agentList = data.agents.map((id: string) => ({
        agent_id: id,
        status: 'online' as const,
        last_seen: Date.now()
      }));
      setAgents(agentList);
    });

    controller.on('agent_status', (data) => {
      setAgents(prev => {
        const existing = prev.find(a => a.agent_id === data.agent_id);
        if (existing) {
          return prev.map(a => 
            a.agent_id === data.agent_id 
              ? { ...a, status: data.status, last_seen: data.timestamp }
              : a
          );
        } else {
          return [...prev, {
            agent_id: data.agent_id,
            status: data.status,
            last_seen: data.timestamp
          }];
        }
      });
    });

    // Connect to server
    controller.connect().then(() => {
      setConnected(true);
    }).catch((error) => {
      console.error('Failed to connect:', error);
    });

    // Update stats periodically
    const statsInterval = setInterval(() => {
      setStats(controller.getStats());
    }, 1000);

    return () => {
      clearInterval(statsInterval);
      controller.disconnect();
    };
  }, [controller, serverUrl]);

  const sendCommand = useCallback(async (agentId: string, command: string, args?: Record<string, any>) => {
    try {
      return await controller.sendCommand(agentId, command, args);
    } catch (error) {
      console.error('Command failed:', error);
      throw error;
    }
  }, [controller]);

  return {
    controller,
    connected,
    stats,
    agents,
    sendCommand
  };
}

export default WebSocketController;
