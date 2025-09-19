import { Shield, User, Sun, Moon, Monitor, CheckCircle, LogOut, Settings } from 'lucide-react';
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
}

export function Header({ onTabChange, onAgentSelect, onAgentDeselect }: HeaderProps) {
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

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between px-4 sm:px-6 gap-4">
        <div className="flex items-center space-x-2 sm:space-x-4 min-w-0 flex-1">
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
  );
}