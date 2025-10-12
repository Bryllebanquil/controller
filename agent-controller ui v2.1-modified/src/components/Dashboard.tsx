
import React, { useState, useEffect } from 'react';
import { useSocket } from './SocketProvider';
import { Login } from './Login';
import { ErrorBoundary } from './ErrorBoundary';
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
  X,
  Wifi
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
  const [networkActivity, setNetworkActivity] = useState("0.0");

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

  // Check for mobile viewport (account for zoom levels)
  useEffect(() => {
    const checkMobile = () => {
      // Use 1024px breakpoint to better handle zoom levels
      const isMobileView = window.innerWidth < 1024;
      setIsMobile(isMobileView);
      
      // Close sidebar if switching to mobile
      if (isMobileView) {
        setSidebarOpen(false);
      }
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

  return (
    <div className="min-h-screen bg-background">
      <ErrorBoundary>
        {/* Header */}
        <Header 
          onMenuClick={() => setSidebarOpen(!sidebarOpen)}
          isMobile={isMobile}
          sidebarOpen={sidebarOpen}
        />

      {/* Mobile Navigation Overlay */}
      {isMobile && sidebarOpen && (
        <div className="fixed inset-0 z-50 bg-black/50 animate-in fade-in duration-200" onClick={() => setSidebarOpen(false)}>
          <div className="fixed left-0 top-0 h-full w-80 bg-background border-r shadow-lg animate-in slide-in-from-left duration-300 z-50" onClick={(e) => e.stopPropagation()}>
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
        <ErrorBoundary>
          <div className="fixed left-0 top-16 h-[calc(100vh-4rem)] w-64 bg-background border-r shadow-sm transition-all duration-300 hover:shadow-md z-30">
            <Sidebar 
              activeTab={activeTab}
              onTabChange={handleTabChange}
            />
          </div>
        </ErrorBoundary>
      )}

      {/* Main Content */}
      <div className={cn(
        "pt-16 transition-all duration-300 ease-in-out min-h-screen relative z-0",
        !isMobile && "ml-64",
        isMobile && "ml-0"
      )}>
        <div className="p-3 sm:p-4 md:p-6 lg:p-8 w-full max-w-[2000px] mx-auto">
          {/* Mobile Tab Navigation - Scrollable */}
          {isMobile && (
            <div className="mb-4 -mx-3 sm:-mx-4 px-3 sm:px-4 overflow-x-auto scrollbar-hide">
              <div className="flex space-x-2 pb-2 min-w-max animate-in fade-in slide-in-from-top-2 duration-500">
                {[
                  { id: 'overview', label: 'Overview', icon: Activity },
                  { id: 'agents', label: 'Agents', icon: Users },
                  { id: 'streaming', label: 'Streaming', icon: Monitor },
                  { id: 'commands', label: 'Commands', icon: Terminal },
                  { id: 'files', label: 'Files', icon: Files },
                  { id: 'voice', label: 'Voice', icon: Mic },
                  { id: 'video', label: 'Video RTC', icon: Video },
                  { id: 'monitoring', label: 'Monitoring', icon: Activity },
                  { id: 'settings', label: 'Settings', icon: SettingsIcon },
                  { id: 'about', label: 'About', icon: Info },
                ].map((item) => {
                  const Icon = item.icon;
                  return (
                    React.createElement(Button, {
                      key: item.id,
                      variant: activeTab === item.id ? "default" : "outline",
                      size: "sm",
                      className: cn(
                        "flex-shrink-0 h-9 transition-all duration-200 ease-in-out",
                        activeTab === item.id && "shadow-md scale-105",
                        activeTab !== item.id && "hover:scale-105 hover:shadow-sm hover:border-primary/50"
                      ),
                      onClick: () => handleTabChange(item.id)
                    },
                      React.createElement(Icon, { className: "h-4 w-4 mr-2 transition-transform duration-200" }),
                      item.label
                    )
                  );
                })}
              </div>
            </div>
          )}

          {/* Page Header with Current Tab */}
          <div className="mb-4 sm:mb-6 flex items-center justify-between animate-in fade-in slide-in-from-top-4 duration-500">
            <div className="flex items-center space-x-2 sm:space-x-3">
              <div className={cn(
                "rounded-lg bg-primary/10 flex items-center justify-center transition-all duration-300 hover:bg-primary/20 hover:scale-110",
                isMobile ? "w-8 h-8" : "w-10 h-10 sm:w-12 sm:h-12"
              )}>
                {React.createElement(
                  activeTab === 'overview' ? Activity :
                  activeTab === 'agents' ? Users :
                  activeTab === 'streaming' ? Monitor :
                  activeTab === 'commands' ? Terminal :
                  activeTab === 'files' ? Files :
                  activeTab === 'voice' ? Mic :
                  activeTab === 'video' ? Video :
                  activeTab === 'monitoring' ? Activity :
                  activeTab === 'settings' ? SettingsIcon :
                  Info,
                  { className: isMobile ? "h-4 w-4 text-primary" : "h-5 w-5 text-primary" }
                )}
              </div>
              <div className="min-w-0">
                <h2 className={cn(
                  "font-bold capitalize transition-all duration-300",
                  isMobile ? "text-base sm:text-lg" : "text-xl sm:text-2xl lg:text-3xl"
                )}>
                  {activeTab === 'video' ? 'Video RTC' : activeTab}
                </h2>
                {!isMobile && (
                  <p className="text-sm text-muted-foreground">
                    {activeTab === 'overview' && 'System overview and agent status'}
                    {activeTab === 'agents' && 'Manage connected agents'}
                    {activeTab === 'streaming' && 'View agent streams'}
                    {activeTab === 'commands' && 'Execute commands on agents'}
                    {activeTab === 'files' && 'Browse and transfer files'}
                    {activeTab === 'voice' && 'Voice control interface'}
                    {activeTab === 'video' && 'Video RTC streaming'}
                    {activeTab === 'monitoring' && 'System monitoring and metrics'}
                    {activeTab === 'settings' && 'Application settings'}
                    {activeTab === 'about' && 'About Neural Control Hub'}
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Tab Content */}
          <div className="space-y-4 sm:space-y-6">
            {/* Overview Tab */}
            {activeTab === 'overview' && (
            <div className="space-y-4 sm:space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
              {/* System Overview Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
                <Card className="transition-all duration-300 hover:shadow-lg hover:scale-[1.02] hover:-translate-y-1 cursor-default">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Connected Agents</CardTitle>
                    <Users className="h-4 w-4 text-muted-foreground transition-transform duration-200 hover:scale-125" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{onlineAgents}</div>
                    <p className="text-xs text-muted-foreground">
                      {totalAgents} total agents
                    </p>
                  </CardContent>
                </Card>

                <Card className="transition-all duration-300 hover:shadow-lg hover:scale-[1.02] hover:-translate-y-1 cursor-default">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">System Status</CardTitle>
                    <Activity className="h-4 w-4 text-muted-foreground transition-transform duration-200 hover:scale-125" />
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

                <Card className="transition-all duration-300 hover:shadow-lg hover:scale-[1.02] hover:-translate-y-1 cursor-default">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Commands Executed</CardTitle>
                    <Terminal className="h-4 w-4 text-muted-foreground transition-transform duration-200 hover:scale-125" />
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
            </div>
            )}

            {/* Agents Tab */}
            {activeTab === 'agents' && (
            <div className="space-y-6">
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

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-3 sm:gap-4">
                {filteredAgents.map((agent, index) => {
                  return React.createElement(AgentCard, {
                    key: agent.id,
                    agent: agent,
                    isSelected: selectedAgent === agent.id,
                    onSelect: () => handleAgentSelect(agent.id),
                    style: { animationDelay: `${index * 50}ms` }
                  });
                })}
              </div>

              {filteredAgents.length === 0 && (
                <Card className="animate-in fade-in zoom-in-95 duration-500">
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
            </div>
            )}

            {/* Streaming Tab */}
            {activeTab === 'streaming' && (
            <div className="space-y-6">
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
            </div>
            )}

            {/* Commands Tab - with Process Manager nested tabs */}
            {activeTab === 'commands' && (
            <div className="space-y-6">
              {selectedAgent ? (
                <Tabs defaultValue="terminal" className="space-y-4">
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="terminal">Terminal</TabsTrigger>
                    <TabsTrigger value="processes">Process Manager</TabsTrigger>
                  </TabsList>
                  <TabsContent value="terminal">
                    <CommandPanel agentId={selectedAgent} />
                  </TabsContent>
                  <TabsContent value="processes">
                    <ProcessManager 
                      agentId={selectedAgent} 
                      isConnected={onlineAgents > 0}
                    />
                  </TabsContent>
                </Tabs>
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
            </div>
            )}

            {/* Files Tab */}
            {activeTab === 'files' && (
            <div className="space-y-6">
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
            </div>
            )}

            {/* Voice Tab */}
            {activeTab === 'voice' && (
            <div className="space-y-6">
              {selectedAgent ? (
                <VoiceControl 
                  agentId={selectedAgent}
                  isConnected={onlineAgents > 0}
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
            </div>
            )}

            {/* Video RTC Tab */}
            {activeTab === 'video' && (
            <div className="space-y-6">
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
            </div>
            )}

            {/* Monitoring Tab - Enhanced with Network Performance */}
            {activeTab === 'monitoring' && (
            <div className="space-y-6">
              {selectedAgent ? (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <SystemMonitor agentId={selectedAgent} />
                  <Card>
                    <CardHeader>
                      <CardTitle>Network Performance</CardTitle>
                      <CardDescription>Real-time network metrics and activity</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div className="flex justify-between items-center">
                          <span className="text-sm">Latency</span>
                          <Badge variant="secondary">12ms</Badge>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm">Throughput</span>
                          <Badge variant="secondary">{networkActivity} MB/s</Badge>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm">Packet Loss</span>
                          <Badge variant="secondary">0.1%</Badge>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm">Connection Status</span>
                          <Badge variant="default">
                            <Wifi className="h-3 w-3 mr-1" />
                            Stable
                          </Badge>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
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
            </div>
            )}

            {/* Settings Tab */}
            {activeTab === 'settings' && (
              <div className="space-y-6">
                <Settings />
              </div>
            )}

            {/* About Tab */}
            {activeTab === 'about' && (
              <div className="space-y-6">
                <About />
              </div>
            )}
          </div>
        </div>
      </div>
      </ErrorBoundary>
    </div>
  );
}
