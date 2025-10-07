import { Shield, User, Sun, Moon, Monitor, CheckCircle, LogOut, Settings, Menu, X, BarChart3, Terminal, Files, Activity, Users, HelpCircle, Zap, Mic } from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator } from './ui/dropdown-menu';
import { NotificationCenter } from './NotificationCenter';
import { KeyboardShortcuts } from './KeyboardShortcuts';
import { useTheme } from './ThemeProvider';
import { useSocket } from './SocketProvider';

interface HeaderProps {
  onTabChange?: (tab: string) => void;
  onAgentSelect?: () => void;
  onAgentDeselect?: () => void;
  onMenuToggle?: () => void;
  isMenuOpen?: boolean;
  activeTab?: string;
  agentCount?: number;
}

export function Header({ onTabChange, onAgentSelect, onAgentDeselect, onMenuToggle, isMenuOpen, activeTab, agentCount = 0 }: HeaderProps) {
  const { theme, setTheme } = useTheme();
  const { logout } = useSocket();

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

  // Sidebar items (merged into this component)
  const sidebarItems = [
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'agents', label: 'Agents', icon: Users },
    { id: 'streaming', label: 'Streaming', icon: Monitor },
    { id: 'commands', label: 'Commands', icon: Terminal },
    { id: 'files', label: 'Files', icon: Files },
    { id: 'voice', label: 'Voice Control', icon: Mic, badge: 'AI' },
    { id: 'monitoring', label: 'Monitoring', icon: Activity },
    { id: 'webrtc', label: 'WebRTC Pro', icon: Zap, badge: 'NEW' },
  ] as const;

  return (
    <>
      <header className="sticky top-0 z-[100] w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto flex h-16 items-center justify-between px-4 sm:px-6 gap-4">
        <div className="flex items-center space-x-2 sm:space-x-4 min-w-0 flex-1">
          {/* Mobile Menu Button */}
          <Button
            variant="ghost"
            size="icon"
            className="flex-shrink-0"
            onClick={onMenuToggle}
            aria-expanded={!!isMenuOpen}
            aria-controls="app-sidebar"
            aria-label={isMenuOpen ? 'Close menu' : 'Open menu'}
          >
            {isMenuOpen ? (
              <X className="h-5 w-5" />
            ) : (
              <Menu className="h-5 w-5" />
            )}
            <span className="sr-only">{isMenuOpen ? 'Close menu' : 'Open menu'}</span>
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
      </header>

      {/* Overlay that does not block header (starts below header) */}
      {isMenuOpen && (
        <div
          className="fixed inset-x-0 top-16 bottom-0 bg-black/50 z-[60]"
          role="button"
          aria-label="Close menu overlay"
          tabIndex={0}
          onClick={onMenuToggle}
          onKeyDown={(e) => {
            if (e.key === 'Escape' || e.key === 'Enter' || e.key === ' ') onMenuToggle?.();
          }}
        />
      )}

      {/* Integrated Sidebar (merged) */}
      <div
        id="app-sidebar"
        aria-hidden={!isMenuOpen}
        className={[
          'fixed left-0 top-16 bottom-0 z-[70] w-[260px] border-r bg-background transition-transform duration-300 ease-in-out',
          isMenuOpen ? 'translate-x-0' : '-translate-x-full xl:translate-x-0',
          'xl:sticky xl:top-16 xl:h-[calc(100vh-4rem)]'
        ].join(' ')}
      >
        <div className="flex h-full flex-col">
          <div className="xl:hidden flex items-center justify-between p-4 border-b">
            <h2 className="text-lg font-semibold">Menu</h2>
            <Button variant="ghost" size="icon" onClick={onMenuToggle}>
              <X className="h-5 w-5" />
            </Button>
          </div>

          <div className="flex-1 overflow-auto p-4">
            <nav className="space-y-1">
              {sidebarItems.map((item) => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;
                return (
                  <Button
                    key={item.id}
                    variant={isActive ? 'secondary' : 'ghost'}
                    className={[
                      'w-full justify-start h-10',
                      isActive ? 'bg-secondary' : ''
                    ].join(' ')}
                    onClick={() => {
                      onTabChange?.(item.id);
                      // close on small screens
                      if (typeof window !== 'undefined' && window.innerWidth < 1280) {
                        onMenuToggle?.();
                      }
                    }}
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
                variant={activeTab === 'settings' ? 'secondary' : 'ghost'}
                className="w-full justify-start h-9"
                size="sm"
                onClick={() => {
                  onTabChange?.('settings');
                  if (typeof window !== 'undefined' && window.innerWidth < 1280) {
                    onMenuToggle?.();
                  }
                }}
              >
                <Settings className="mr-2 h-4 w-4" />
                Settings
              </Button>
              <Button
                variant={activeTab === 'about' ? 'secondary' : 'ghost'}
                className="w-full justify-start h-9"
                size="sm"
                onClick={() => {
                  onTabChange?.('about');
                  if (typeof window !== 'undefined' && window.innerWidth < 1280) {
                    onMenuToggle?.();
                  }
                }}
              >
                <HelpCircle className="mr-2 h-4 w-4" />
                About
              </Button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}