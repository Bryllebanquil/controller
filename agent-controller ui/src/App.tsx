import { useState, useEffect } from 'react';
import { AgentCard } from './components/AgentCard';
import { StreamViewer } from './components/StreamViewer';
import { CommandPanel } from './components/CommandPanel';
import { SystemMonitor } from './components/SystemMonitor';
import { FileManager } from './components/FileManager';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { SearchAndFilter } from './components/SearchAndFilter';
import { ActivityFeed } from './components/ActivityFeed';
import { QuickActions } from './components/QuickActions';
import { Settings } from './components/Settings';
import { About } from './components/About';
import { Login } from './components/Login';
import { ThemeProvider } from './components/ThemeProvider';
import { SocketProvider, useSocket } from './components/SocketProvider-new';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Badge } from './components/ui/badge';
import { Button } from './components/ui/button';
import { Shield, Monitor, Terminal, Files, Activity, Settings as SettingsIcon, Users, Wifi, Loader2 } from 'lucide-react';

// Mock data for demonstration
const mockAgents = [
  {
    id: 'agent-001',
    name: 'Windows-Desktop-01',
    status: 'online',
    platform: 'Windows 11',
    ip: '192.168.1.100',
    lastSeen: new Date(),
    capabilities: ['screen', 'audio', 'camera', 'files', 'commands'],
    performance: { cpu: 45, memory: 62, network: 12 }
  },
  {
    id: 'agent-002',
    name: 'Linux-Server-01',
    status: 'online',
    platform: 'Ubuntu 22.04',
    ip: '192.168.1.101',
    lastSeen: new Date(),
    capabilities: ['screen', 'files', 'commands'],
    performance: { cpu: 23, memory: 78, network: 8 }
  },
  {
    id: 'agent-003',
    name: 'MacBook-Pro-01',
    status: 'offline',
    platform: 'macOS Sonoma',
    ip: '192.168.1.102',
    lastSeen: new Date(Date.now() - 300000),
    capabilities: ['screen', 'audio', 'camera', 'files'],
    performance: { cpu: 0, memory: 0, network: 0 }
  }
];

function AppContent() {
  const { 
    authenticated, 
    connected,
    agents, 
    selectedAgent, 
    setSelectedAgent,
    systemStats,
    activities
  } = useSocket();
  
  const [activeTab, setActiveTab] = useState('overview');
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({ status: [], platform: [], capabilities: [] });
  const [sortBy, setSortBy] = useState('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  // Show login screen if not authenticated
  if (!authenticated) {
    return <Login />;
  }

  // Show loading screen while connecting
  if (!connected) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center space-y-4">
          <Loader2 className="h-8 w-8 animate-spin mx-auto" />
          <p className="text-muted-foreground">Connecting to Neural Control Hub...</p>
        </div>
      </div>
    );
  }

  const onlineAgents = agents.filter(agent => agent.status === 'online');
  
  // Advanced filtering and sorting
  const filteredAgents = agents.filter(agent => {
    // Text search
    const matchesSearch = searchTerm === '' || 
      agent.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      agent.platform.toLowerCase().includes(searchTerm.toLowerCase()) ||
      agent.ip.includes(searchTerm);
    
    // Status filter
    const matchesStatus = filters.status.length === 0 || filters.status.includes(agent.status);
    
    // Platform filter
    const matchesPlatform = filters.platform.length === 0 || 
      filters.platform.some(platform => agent.platform.includes(platform));
    
    // Capabilities filter
    const matchesCapabilities = filters.capabilities.length === 0 ||
      filters.capabilities.every(capability => agent.capabilities.includes(capability));
    
    return matchesSearch && matchesStatus && matchesPlatform && matchesCapabilities;
  }).sort((a, b) => {
    let aValue, bValue;
    
    switch (sortBy) {
      case 'status':
        aValue = a.status;
        bValue = b.status;
        break;
      case 'platform':
        aValue = a.platform;
        bValue = b.platform;
        break;
      case 'lastSeen':
        aValue = a.lastSeen.getTime();
        bValue = b.lastSeen.getTime();
        break;
      case 'performance':
        aValue = a.performance.cpu + a.performance.memory;
        bValue = b.performance.cpu + b.performance.memory;
        break;
      default:
        aValue = a.name;
        bValue = b.name;
    }
    
    if (sortOrder === 'asc') {
      return aValue > bValue ? 1 : -1;
    } else {
      return aValue < bValue ? 1 : -1;
    }
  });

  const availableFilters = {
    platforms: [...new Set(agents.map(agent => agent.platform.split(' ')[0]))],
    capabilities: [...new Set(agents.flatMap(agent => agent.capabilities))]
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
      <Header 
        onTabChange={setActiveTab}
        onAgentSelect={handleAgentSelect}
        onAgentDeselect={handleAgentDeselect}
      />
      
      <div className="flex min-h-[calc(100vh-4rem)]">
        <Sidebar 
          activeTab={activeTab} 
          onTabChange={setActiveTab}
          agentCount={onlineAgents.length}
        />
        
        <main className="flex-1 overflow-auto">
          <div className="p-6 space-y-6">
            {/* Overview Stats - only show for overview tab */}
            {activeTab === 'overview' && !['settings', 'about'].includes(activeTab) && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Total Agents</CardTitle>
                    <Users className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{systemStats?.agents.total || agents.length}</div>
                    <p className="text-xs text-muted-foreground">
                      {systemStats?.agents.online || onlineAgents.length} online
                    </p>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Active Streams</CardTitle>
                    <Monitor className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{systemStats?.streams.active || 0}</div>
                    <p className="text-xs text-muted-foreground">
                      Screen + Audio
                    </p>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Commands Executed</CardTitle>
                    <Terminal className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{systemStats?.commands.executed_today || 0}</div>
                    <p className="text-xs text-muted-foreground">
                      {systemStats?.commands.successful || 0} successful
                    </p>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Network Status</CardTitle>
                    <Wifi className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{systemStats?.network.status || 'Unknown'}</div>
                    <p className="text-xs text-muted-foreground">
                      {systemStats?.network.latency || 0}ms latency
                    </p>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Advanced Search and Filter - only for main tabs */}
            {!['settings', 'about'].includes(activeTab) && (
              <SearchAndFilter
                searchTerm={searchTerm}
                onSearchChange={setSearchTerm}
                onFiltersChange={setFilters}
                onSortChange={(sortBy, sortOrder) => {
                  setSortBy(sortBy);
                  setSortOrder(sortOrder);
                }}
                availableFilters={availableFilters}
                resultCount={filteredAgents.length}
              />
            )}

            {/* Only show search and tabs for main content, not settings/about */}
            {!['settings', 'about'].includes(activeTab) && (
              <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
                <TabsList className="grid w-full grid-cols-6">
                  <TabsTrigger value="overview">Overview</TabsTrigger>
                  <TabsTrigger value="agents">Agents</TabsTrigger>
                  <TabsTrigger value="streaming">Streaming</TabsTrigger>
                  <TabsTrigger value="commands">Commands</TabsTrigger>
                  <TabsTrigger value="files">Files</TabsTrigger>
                  <TabsTrigger value="monitoring">Monitoring</TabsTrigger>
                </TabsList>

              <TabsContent value="overview" className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>System Overview</CardTitle>
                    <CardDescription>
                      Real-time status of all connected agents and system performance
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                      <div className="lg:col-span-2">
                        <ActivityFeed />
                      </div>
                      <div className="space-y-4">
                        <SystemMonitor />
                        <QuickActions 
                          agentCount={onlineAgents.length}
                          selectedAgent={selectedAgent}
                        />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="agents" className="space-y-6">
                <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                  {filteredAgents.map(agent => (
                    <AgentCard
                      key={agent.id}
                      agent={agent}
                      isSelected={selectedAgent === agent.id}
                      onSelect={() => setSelectedAgent(agent.id)}
                    />
                  ))}
                </div>
              </TabsContent>

              <TabsContent value="streaming" className="space-y-6">
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

              <TabsContent value="commands" className="space-y-6">
                <CommandPanel agentId={selectedAgent} />
              </TabsContent>

              <TabsContent value="files" className="space-y-6">
                <FileManager agentId={selectedAgent} />
              </TabsContent>

              <TabsContent value="monitoring" className="space-y-6">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <SystemMonitor />
                  <Card>
                    <CardHeader>
                      <CardTitle>Network Performance</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div className="flex justify-between items-center">
                          <span className="text-sm">Latency</span>
                          <Badge variant="secondary">12ms</Badge>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm">Throughput</span>
                          <Badge variant="secondary">2.4 MB/s</Badge>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm">Packet Loss</span>
                          <Badge variant="secondary">0.1%</Badge>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>
            </Tabs>
            )}

            {/* Settings Page */}
            {activeTab === 'settings' && <Settings />}
            
            {/* About Page */}
            {activeTab === 'about' && <About />}
          </div>
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider defaultTheme="system" storageKey="neural-control-hub-theme">
      <SocketProvider>
        <AppContent />
      </SocketProvider>
    </ThemeProvider>
  );
}