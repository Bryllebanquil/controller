
import React, { useState, useEffect } from 'react';
import { useSocket } from './SocketProvider';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { MobileNavigation } from './MobileNavigation';
import { ActivityFeed } from './ActivityFeed';
import { QuickActions } from './QuickActions';
import { AgentCard } from './AgentCard';
import { CommandPanel } from './CommandPanel';
import { StreamViewer } from './StreamViewer';
import { FileManager } from './FileManager';
import { SystemMonitor } from './SystemMonitor';
import { VoiceControl } from './VoiceControl';
import { WebRTCMonitoring } from './WebRTCMonitoring';
import { ProcessManager } from './ProcessManager';
import { SearchAndFilter } from './SearchAndFilter';
import { NotificationCenter } from './NotificationCenter';
import { Settings } from './Settings';
import { About } from './About';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { 
  Activity, 
  Users, 
  Monitor, 
  Terminal, 
  Files, 
  Mic, 
  Video, 
  Settings as SettingsIcon,
  Info,
  Search,
  Filter,
  Bell,
  Menu,
  X
} from 'lucide-react';
import { cn } from './ui/utils';

type TabType = 'overview' | 'agents' | 'streaming' | 'commands' | 'files' | 'voice' | 'video' | 'monitoring' | 'settings' | 'about';

export function Dashboard() {
  const { 
    authenticated, 
    agents, 
    selectedAgent, 
    setSelectedAgent, 
    connected,
    commandOutput 
  } = useSocket();
  
  console.log("Dashboard: authenticated =", authenticated);
  console.log("Dashboard: connected =", connected);
  console.log("Dashboard: agents =", agents);
  
  const [activeTab, setActiveTab] = useState('overview' as TabType);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState('all' as 'all' | 'online' | 'offline');

  // Authentication check removed - always authenticated

  // Check for mobile viewport
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Filter agents based on search and status
  const filteredAgents = agents.filter(agent => {
    const matchesSearch = agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         agent.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         agent.platform.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = filterStatus === 'all' || agent.status === filterStatus;
    return matchesSearch && matchesStatus;
  });

  // Get online agents count
  const onlineAgents = agents.filter(agent => agent.status === 'online').length;
  const totalAgents = agents.length;

  // Handle tab change
  const handleTabChange = (tab: string) => {
    setActiveTab(tab as TabType);
    // Close mobile sidebar when switching tabs
    if (isMobile) {
      setSidebarOpen(false);
    }
  };

  // Handle agent selection
  const handleAgentSelect = (agentId: string) => {
    setSelectedAgent(agentId);
    // Close mobile sidebar when selecting agent
    if (isMobile) {
      setSidebarOpen(false);
    }
  };

  // Authentication check removed - always authenticated

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <Header 
        onMenuClick={() => setSidebarOpen(!sidebarOpen)}
        isMobile={isMobile}
        sidebarOpen={sidebarOpen}
      />

      {/* Mobile Navigation Overlay */}
      {isMobile && sidebarOpen && (
        <div className="fixed inset-0 z-50 bg-black/50" onClick={() => setSidebarOpen(false)}>
          <div className="fixed left-0 top-0 h-full w-80 bg-background border-r shadow-lg">
            <div className="flex items-center justify-between p-4 border-b">
              <h2 className="text-lg font-semibold">Navigation</h2>
              {React.createElement(Button, {
                variant: "ghost",
                size: "sm",
                onClick: () => setSidebarOpen(false)
              }, React.createElement(X, { className: "h-4 w-4" }))}
            </div>
            <MobileNavigation 
              activeTab={activeTab}
              onTabChange={handleTabChange}
              onClose={() => setSidebarOpen(false)}
            />
          </div>
        </div>
      )}

      {/* Desktop Sidebar */}
      {!isMobile && (
        <div className="fixed left-0 top-16 h-[calc(100vh-4rem)] w-64 bg-background border-r">
          <Sidebar 
            activeTab={activeTab}
            onTabChange={handleTabChange}
          />
        </div>
      )}

      {/* Main Content */}
      <div className={cn(
        "pt-16 transition-all duration-300",
        !isMobile && "ml-64"
      )}>
        <div className="p-4 md:p-6">
          {/* Mobile Tab Navigation */}
          {isMobile && (
            <div className="mb-4">
              <Tabs value={activeTab} onValueChange={(value) => handleTabChange(value as TabType)}>
                <TabsList className="grid w-full grid-cols-3 lg:grid-cols-6">
                  <TabsTrigger value="overview" className="text-xs">
                    <Activity className="h-3 w-3 mr-1" />
                    <span className="hidden sm:inline">Overview</span>
                  </TabsTrigger>
                  <TabsTrigger value="agents" className="text-xs">
                    <Users className="h-3 w-3 mr-1" />
                    <span className="hidden sm:inline">Agents</span>
                  </TabsTrigger>
                  <TabsTrigger value="streaming" className="text-xs">
                    <Monitor className="h-3 w-3 mr-1" />
                    <span className="hidden sm:inline">Stream</span>
                  </TabsTrigger>
                  <TabsTrigger value="commands" className="text-xs">
                    <Terminal className="h-3 w-3 mr-1" />
                    <span className="hidden sm:inline">Cmd</span>
                  </TabsTrigger>
                  <TabsTrigger value="files" className="text-xs">
                    <Files className="h-3 w-3 mr-1" />
                    <span className="hidden sm:inline">Files</span>
                  </TabsTrigger>
                  <TabsTrigger value="monitoring" className="text-xs">
                    <Activity className="h-3 w-3 mr-1" />
                    <span className="hidden sm:inline">Monitor</span>
                  </TabsTrigger>
                </TabsList>
              </Tabs>
            </div>
          )}

          {/* Desktop Tab Navigation */}
          {!isMobile && (
            <div className="mb-6">
              <Tabs value={activeTab} onValueChange={(value) => handleTabChange(value as TabType)}>
                <TabsList className="grid w-full grid-cols-6 lg:grid-cols-9">
                  <TabsTrigger value="overview">Overview</TabsTrigger>
                  <TabsTrigger value="agents">Agents</TabsTrigger>
                  <TabsTrigger value="streaming">Streaming</TabsTrigger>
                  <TabsTrigger value="commands">Commands</TabsTrigger>
                  <TabsTrigger value="files">Files</TabsTrigger>
                  <TabsTrigger value="voice">Voice</TabsTrigger>
                  <TabsTrigger value="video">Video RTC</TabsTrigger>
                  <TabsTrigger value="monitoring">Monitoring</TabsTrigger>
                  <TabsTrigger value="settings">Settings</TabsTrigger>
                </TabsList>
              </Tabs>
            </div>
          )}

          {/* Tab Content */}
          <Tabs value={activeTab} onValueChange={(value) => handleTabChange(value as TabType)}>
            {/* Overview Tab */}
            <TabsContent value="overview" className="space-y-6">
              {/* System Overview Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Connected Agents</CardTitle>
                    <Users className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{onlineAgents}</div>
                    <p className="text-xs text-muted-foreground">
                      {totalAgents} total agents
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">System Status</CardTitle>
                    <Activity className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      <Badge variant={connected ? "default" : "destructive"}>
                        {connected ? "Online" : "Offline"}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Controller connection
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Active Streams</CardTitle>
                    <Monitor className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">0</div>
                    <p className="text-xs text-muted-foreground">
                      Currently streaming
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Commands Executed</CardTitle>
                    <Terminal className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{commandOutput.length}</div>
                    <p className="text-xs text-muted-foreground">
                      Total commands
                    </p>
                  </CardContent>
                </Card>
              </div>

              {/* Quick Actions */}
              <Card>
                <CardHeader>
                  <CardTitle>Quick Actions</CardTitle>
                  <CardDescription>
                    Perform bulk operations on all connected agents
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <QuickActions 
                    agentCount={totalAgents}
                    selectedAgent={selectedAgent}
                  />
                </CardContent>
              </Card>

              {/* Activity Feed */}
              <Card>
                <CardHeader>
                  <CardTitle>Activity Feed</CardTitle>
                  <CardDescription>
                    Real-time system events and agent activities
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ActivityFeed />
                </CardContent>
              </Card>
            </TabsContent>

            {/* Agents Tab */}
            <TabsContent value="agents" className="space-y-6">
              <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
                <div className="flex-1 min-w-0">
                  <SearchAndFilter
                    searchTerm={searchQuery}
                    onSearchChange={setSearchQuery}
                    onFiltersChange={(filters) => {
                      // Handle filter changes
                      console.log('Filters changed:', filters);
                    }}
                    onSortChange={(sortBy, sortOrder) => {
                      // Handle sort changes
                      console.log('Sort changed:', sortBy, sortOrder);
                    }}
                    availableFilters={{
                      platforms: ['Windows', 'Linux', 'macOS'],
                      capabilities: ['screen', 'camera', 'audio', 'files', 'commands']
                    }}
                    resultCount={filteredAgents.length}
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {filteredAgents.map((agent) => {
                  return React.createElement(AgentCard, {
                    key: agent.id,
                    agent: agent,
                    isSelected: selectedAgent === agent.id,
                    onSelect: () => handleAgentSelect(agent.id)
                  });
                })}
              </div>

              {filteredAgents.length === 0 && (
                <Card>
                  <CardContent className="flex flex-col items-center justify-center py-12">
                    <Users className="h-12 w-12 text-muted-foreground mb-4" />
                    <h3 className="text-lg font-semibold mb-2">No agents found</h3>
                    <p className="text-muted-foreground text-center">
                      {searchQuery || filterStatus !== 'all' 
                        ? 'Try adjusting your search or filter criteria'
                        : 'No agents are currently connected to the system'
                      }
                    </p>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            {/* Streaming Tab */}
            <TabsContent value="streaming" className="space-y-6">
              {selectedAgent ? (
                <StreamViewer 
                  agentId={selectedAgent}
                  type="screen"
                  title="Screen Stream"
                />
              ) : (
                <Card>
                  <CardContent className="flex flex-col items-center justify-center py-12">
                    <Monitor className="h-12 w-12 text-muted-foreground mb-4" />
                    <h3 className="text-lg font-semibold mb-2">No agent selected</h3>
                    <p className="text-muted-foreground text-center">
                      Select an agent from the Agents tab to start streaming
                    </p>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            {/* Commands Tab */}
            <TabsContent value="commands" className="space-y-6">
              {selectedAgent ? (
                <CommandPanel agentId={selectedAgent} />
              ) : (
                <Card>
                  <CardContent className="flex flex-col items-center justify-center py-12">
                    <Terminal className="h-12 w-12 text-muted-foreground mb-4" />
                    <h3 className="text-lg font-semibold mb-2">No agent selected</h3>
                    <p className="text-muted-foreground text-center">
                      Select an agent from the Agents tab to execute commands
                    </p>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            {/* Files Tab */}
            <TabsContent value="files" className="space-y-6">
              {selectedAgent ? (
                <FileManager agentId={selectedAgent} />
              ) : (
                <Card>
                  <CardContent className="flex flex-col items-center justify-center py-12">
                    <Files className="h-12 w-12 text-muted-foreground mb-4" />
                    <h3 className="text-lg font-semibold mb-2">No agent selected</h3>
                    <p className="text-muted-foreground text-center">
                      Select an agent from the Agents tab to manage files
                    </p>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            {/* Voice Tab */}
            <TabsContent value="voice" className="space-y-6">
              {selectedAgent ? (
                <VoiceControl 
                  agentId={selectedAgent}
                  isConnected={true}
                />
              ) : (
                <Card>
                  <CardContent className="flex flex-col items-center justify-center py-12">
                    <Mic className="h-12 w-12 text-muted-foreground mb-4" />
                    <h3 className="text-lg font-semibold mb-2">No agent selected</h3>
                    <p className="text-muted-foreground text-center">
                      Select an agent from the Agents tab to control voice
                    </p>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            {/* Video RTC Tab */}
            <TabsContent value="video" className="space-y-6">
              {selectedAgent ? (
                <WebRTCMonitoring selectedAgent={selectedAgent} />
              ) : (
                <Card>
                  <CardContent className="flex flex-col items-center justify-center py-12">
                    <Video className="h-12 w-12 text-muted-foreground mb-4" />
                    <h3 className="text-lg font-semibold mb-2">No agent selected</h3>
                    <p className="text-muted-foreground text-center">
                      Select an agent from the Agents tab to monitor WebRTC
                    </p>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            {/* Monitoring Tab */}
            <TabsContent value="monitoring" className="space-y-6">
              {selectedAgent ? (
                <SystemMonitor agentId={selectedAgent} />
              ) : (
                <Card>
                  <CardContent className="flex flex-col items-center justify-center py-12">
                    <Activity className="h-12 w-12 text-muted-foreground mb-4" />
                    <h3 className="text-lg font-semibold mb-2">No agent selected</h3>
                    <p className="text-muted-foreground text-center">
                      Select an agent from the Agents tab to monitor system performance
                    </p>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            {/* Settings Tab */}
            <TabsContent value="settings" className="space-y-6">
              <Settings />
            </TabsContent>

            {/* About Tab */}
            <TabsContent value="about" className="space-y-6">
              <About />
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
