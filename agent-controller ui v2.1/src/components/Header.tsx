import { useEffect } from 'react';
import { Shield, User, Sun, Moon, Monitor, CheckCircle, LogOut, Settings, Menu, X, BarChart3, Terminal, Files, Activity, Users, Settings as SettingsIcon, HelpCircle, Zap, Mic } from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator } from './ui/dropdown-menu';
import { NotificationCenter } from './NotificationCenter';
import { KeyboardShortcuts } from './KeyboardShortcuts';
import { useTheme } from './ThemeProvider';
import { useSocket } from './SocketProvider';
import { cn } from './ui/utils';

interface HeaderProps {
  onTabChange?: (tab: string) => void;
  onAgentSelect?: () => void;
  onAgentDeselect?: () => void;
  onMenuToggle?: () => void;
  sidebarOpen?: boolean;
  activeTab?: string;
  agentCount?: number;
  onSidebarClose?: () => void;
}

const sidebarItems = [
  { id: 'overview', label: 'Overview', icon: BarChart3 },
  { id: 'agents', label: 'Agents', icon: Users },
  { id: 'streaming', label: 'Streaming', icon: Monitor },
  { id: 'commands', label: 'Commands', icon: Terminal },
  { id: 'files', label: 'Files', icon: Files },
  { id: 'voice', label: 'Voice Control', icon: Mic, badge: 'AI' },
  { id: 'monitoring', label: 'Monitoring', icon: Activity },
  { id: 'webrtc', label: 'WebRTC Pro', icon: Zap, badge: 'NEW' },
];

export function Header({ 
  onTabChange, 
  onAgentSelect, 
  onAgentDeselect, 
  onMenuToggle, 
  sidebarOpen = false,
  activeTab = 'overview',
  agentCount = 0,
  onSidebarClose
}: HeaderProps) {
  const { theme, setTheme } = useTheme();
  const { logout } = useSocket();

  // Close sidebar on Escape key press (mobile/tablet)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && sidebarOpen && onSidebarClose) {
        onSidebarClose();
      }
    };
    
    if (sidebarOpen) {
      window.addEventListener('keydown', handleKeyDown);
      return () => window.removeEventListener('keydown', handleKeyDown);
    }
  }, [sidebarOpen, onSidebarClose]);

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const handleSettingsClick = () => {
    if (onTabChange) {
      onTabChange('settings');
    }
  };

  const handleTabChange = (tab: string) => {
    if (onTabChange) {
      onTabChange(tab);
    }
  };

  return (
    <>
      {/* Mobile/Tablet Overlay - Starts below header */}
      {sidebarOpen && (
        <div 
          className="fixed inset-x-0 top-16 bottom-0 bg-black/50 z-[60] lg:hidden"
          onClick={onSidebarClose}
        />
      )}

      <header className="sticky top-0 z-[100] w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="w-full flex h-16 items-center justify-between px-4 sm:px-6 gap-4 max-w-full">
          <div className="flex items-center space-x-2 sm:space-x-4 min-w-0 flex-1">
            {/* Mobile/Tablet Menu Button */}
            <Button
              variant="ghost"
              size="icon"
              className="lg:hidden flex-shrink-0"
              onClick={onMenuToggle}
              aria-label="Toggle menu"
              aria-expanded={sidebarOpen}
              aria-controls="main-sidebar"
            >
              <Menu className="h-5 w-5" />
              <span className="sr-only">Toggle menu</span>
            </Button>
            
            <div className="flex items-center space-x-2 min-w-0">
              <Shield className="h-6 w-6 sm:h-8 sm:w-8 text-primary flex-shrink-0" />
              <div className="min-w-0">
                <h1 className="text-sm sm:text-lg font-semibold truncate">Neural Control Hub</h1>
                <p className="text-xs text-muted-foreground hidden sm:block">Advanced Agent Management</p>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-1 sm:space-x-2 flex-shrink-0">
            
            <div className="hidden md:flex items-center space-x-2">
              <Badge variant="secondary" className="text-xs">v2.1</Badge>
            </div>
            
            <KeyboardShortcuts 
              onTabChange={onTabChange}
              onAgentSelect={onAgentSelect}
              onAgentDeselect={onAgentDeselect}
            />
            
            {/* Theme Toggle - More prominent button */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="default" className="relative px-3 py-2 h-9">
                  {theme === 'light' && <Sun className="h-4 w-4 mr-2" />}
                  {theme === 'dark' && <Moon className="h-4 w-4 mr-2" />}
                  {theme === 'system' && <Monitor className="h-4 w-4 mr-2" />}
                  <span className="hidden sm:inline">
                    {theme === 'light' && 'Light'}
                    {theme === 'dark' && 'Dark'}
                    {theme === 'system' && 'Auto'}
                  </span>
                  <span className="sr-only">Toggle theme</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="min-w-[140px]">
                <DropdownMenuItem onClick={() => setTheme('light')}>
                  <Sun className="mr-2 h-4 w-4" />
                  <span>Light</span>
                  {theme === 'light' && <CheckCircle className="ml-auto h-3 w-3" />}
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setTheme('dark')}>
                  <Moon className="mr-2 h-4 w-4" />
                  <span>Dark</span>
                  {theme === 'dark' && <CheckCircle className="ml-auto h-3 w-3" />}
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setTheme('system')}>
                  <Monitor className="mr-2 h-4 w-4" />
                  <span>System</span>
                  {theme === 'system' && <CheckCircle className="ml-auto h-3 w-3" />}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
            
            <NotificationCenter />
            
            {/* Quick Logout button for visibility */}
            <Button variant="destructive" size="sm" onClick={handleLogout} className="hidden sm:inline-flex">
              <LogOut className="mr-2 h-4 w-4" />
              Logout
            </Button>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm">
                  <User className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuItem onClick={handleSettingsClick}>
                  <Settings className="mr-2 h-4 w-4" />
                  <span>Settings</span>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout} className="text-red-600 focus:text-red-600">
                  <LogOut className="mr-2 h-4 w-4" />
                  <span>Logout</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        {/* Sidebar - Now part of Header */}
        <div 
          id="main-sidebar"
          className={cn(
            "fixed lg:static left-0 top-16 bottom-0 z-[70] w-64 border-r bg-background flex-shrink-0 transition-transform duration-300 ease-in-out lg:top-0 lg:bottom-auto lg:h-full",
            sidebarOpen ? "translate-x-0" : "-translate-x-full",
            "lg:translate-x-0" // Always visible on desktop (lg+)
          )}
        >
          <div className="flex h-full flex-col">
            {/* Mobile/Tablet Close Button */}
            <div className="lg:hidden flex items-center justify-between p-4 border-b">
              <h2 className="text-lg font-semibold">Menu</h2>
              <Button
                variant="ghost"
                size="icon"
                onClick={onSidebarClose}
              >
                <X className="h-5 w-5" />
                <span className="sr-only">Close menu</span>
              </Button>
            </div>
            
            <div className="flex-1 overflow-auto p-4">
              <nav className="space-y-1" role="navigation" aria-label="Main navigation">
                {sidebarItems.map((item) => {
                  const Icon = item.icon;
                  return (
                    <Button
                      key={item.id}
                      variant={activeTab === item.id ? "secondary" : "ghost"}
                      className={cn(
                        "w-full justify-start h-10",
                        activeTab === item.id && "bg-secondary"
                      )}
                      onClick={() => handleTabChange(item.id)}
                    >
                      <Icon className="mr-2 h-4 w-4 flex-shrink-0" />
                      <span className="flex-1 text-left">{item.label}</span>
                      {item.id === 'agents' && (
                        <Badge variant="secondary" className="ml-2 h-5 text-xs">
                          {agentCount}
                        </Badge>
                      )}
                      {item.badge && (
                        <Badge variant="default" className="ml-2 h-5 text-xs">
                          {item.badge}
                        </Badge>
                      )}
                    </Button>
                  );
                })}
              </nav>
            </div>
            
            <div className="border-t p-4 flex-shrink-0">
              <div className="space-y-1">
                <Button 
                  variant={activeTab === 'settings' ? "secondary" : "ghost"} 
                  className="w-full justify-start h-9" 
                  size="sm"
                  onClick={() => handleTabChange('settings')}
                >
                  <SettingsIcon className="mr-2 h-4 w-4" />
                  Settings
                </Button>
                <Button 
                  variant={activeTab === 'about' ? "secondary" : "ghost"} 
                  className="w-full justify-start h-9" 
                  size="sm"
                  onClick={() => handleTabChange('about')}
                >
                  <HelpCircle className="mr-2 h-4 w-4" />
                  About
                </Button>
              </div>
            </div>
          </div>
        </div>
      </header>
    </>
  );
}