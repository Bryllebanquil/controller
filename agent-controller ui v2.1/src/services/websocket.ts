/**
 * WebSocket Service for Neural Control Hub Frontend
 * Handles real-time communication with the backend via Socket.IO
 */

import { io, Socket } from 'socket.io-client';

// WebSocket Configuration
// Prefer runtime-injected overrides from backend, then same-origin, then env, finally localhost
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const runtimeSocketUrl = (globalThis as any)?.__SOCKET_URL__ as string | undefined;
const WEBSOCKET_URL =
  runtimeSocketUrl ||
  (typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.host}` : '') ||
  (import.meta as any)?.env?.VITE_WS_URL ||
  'http://localhost:8080';

// Event Types
export interface WebSocketEvents {
  // Connection events
  connect: () => void;
  disconnect: () => void;
  
  // Agent events
  agent_list_update: (agents: any) => void;
  agent_performance_update: (data: { agent_id: string; performance: any }) => void;
  
  // Command events
  command_result: (data: {
    agent_id: string;
    execution_id: string;
    command: string;
    output: string;
    success: boolean;
    execution_time: number;
    timestamp: string;
  }) => void;
  
  // Stream events
  stream_status_update: (data: {
    agent_id: string;
    stream_type: string;
    status: 'started' | 'stopped' | 'error';
    quality: string;
    timestamp: string;
  }) => void;
  
  // File operation events
  file_operation_result: (data: {
    agent_id: string;
    operation: 'download' | 'upload' | 'delete';
    file_path: string;
    success: boolean;
    error_message?: string;
    file_size?: number;
    timestamp: string;
  }) => void;
  
  // System events
  system_alert: (data: {
    agent_id: string;
    type: 'warning' | 'error' | 'critical';
    message: string;
    details: string;
    timestamp: string;
  }) => void;
  
  // Activity events
  activity_update: (data: {
    id: string;
    type: 'connection' | 'command' | 'stream' | 'file' | 'security' | 'system';
    action: string;
    details: string;
    agent_id: string;
    agent_name: string;
    timestamp: string;
    status: 'success' | 'warning' | 'error' | 'info';
  }) => void;
}

// WebSocket Client Class
class WebSocketClient {
  private socket: Socket | null = null;
  private url: string;
  private eventListeners: Map<string, Set<Function>> = new Map();
  private isConnected: boolean = false;

  constructor(url: string = WEBSOCKET_URL) {
    this.url = url;
  }

  // Connection Management
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.socket?.connected) {
        resolve();
        return;
      }

      this.socket = io(this.url, {
        withCredentials: true,
        transports: ['websocket', 'polling'],
        timeout: 5000,
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 1000,
      });

      // Connection event handlers
      this.socket.on('connect', () => {
        console.log('✅ WebSocket connected');
        this.isConnected = true;
        
        // Join operators room for receiving updates
        this.socket?.emit('operator_connect');
        
        this.emit('connect');
        resolve();
      });

      this.socket.on('disconnect', (reason) => {
        console.log('❌ WebSocket disconnected:', reason);
        this.isConnected = false;
        this.emit('disconnect');
      });

      this.socket.on('connect_error', (error) => {
        console.error('❌ WebSocket connection error:', error);
        reject(error);
      });

      // Set up event forwarding
      this.setupEventForwarding();

      // Connection timeout
      setTimeout(() => {
        if (!this.isConnected) {
          reject(new Error('WebSocket connection timeout'));
        }
      }, 10000);
    });
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.isConnected = false;
    }
  }

  // Event Management
  on<K extends keyof WebSocketEvents>(event: K, callback: WebSocketEvents[K]): void {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, new Set());
    }
    this.eventListeners.get(event)!.add(callback);
  }

  off<K extends keyof WebSocketEvents>(event: K, callback: WebSocketEvents[K]): void {
    const listeners = this.eventListeners.get(event);
    if (listeners) {
      listeners.delete(callback);
    }
  }

  private emit(event: string, ...args: any[]): void {
    const listeners = this.eventListeners.get(event);
    if (listeners) {
      listeners.forEach(callback => {
        try {
          callback(...args);
        } catch (error) {
          console.error(`Error in WebSocket event handler for ${event}:`, error);
        }
      });
    }
  }

  // Setup event forwarding from Socket.IO to our event system
  private setupEventForwarding(): void {
    if (!this.socket) return;

    // Agent events
    this.socket.on('agent_list_update', (data) => this.emit('agent_list_update', data));
    this.socket.on('agent_performance_update', (data) => this.emit('agent_performance_update', data));

    // Command events
    this.socket.on('command_result', (data) => this.emit('command_result', data));

    // Stream events
    this.socket.on('stream_status_update', (data) => this.emit('stream_status_update', data));

    // File operation events
    this.socket.on('file_operation_result', (data) => this.emit('file_operation_result', data));

    // System events
    this.socket.on('system_alert', (data) => this.emit('system_alert', data));

    // Activity events
    this.socket.on('activity_update', (data) => this.emit('activity_update', data));
  }

  // Outgoing Events (to server)
  sendHeartbeat(agentId: string, performance?: any): void {
    if (this.socket?.connected) {
      this.socket.emit('heartbeat', {
        agent_id: agentId,
        performance,
      });
    }
  }

  executeCommand(agentId: string, command: string): void {
    if (this.socket?.connected) {
      this.socket.emit('execute_command', {
        agent_id: agentId,
        command,
      });
    }
  }

  // Connection Status
  get connected(): boolean {
    return this.isConnected && this.socket?.connected === true;
  }

  // Reconnection
  reconnect(): void {
    if (this.socket) {
      this.socket.connect();
    } else {
      this.connect().catch(console.error);
    }
  }
}

// Export singleton instance
export const wsClient = new WebSocketClient();
export default wsClient;
