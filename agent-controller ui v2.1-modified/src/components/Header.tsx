import React from 'react';
import { Shield, User, Sun, Moon, Monitor, CheckCircle, LogOut, Settings, Menu, Bell } from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator } from './ui/dropdown-menu';
import { NotificationCenter } from './NotificationCenter';
import { KeyboardShortcuts } from './KeyboardShortcuts';
import { useTheme } from './ThemeProvider';
import { useSocket } from './SocketProvider';

interface HeaderProps {
  onMenuClick?: () => void;
  isMobile?: boolean;
  sidebarOpen?: boolean;
}

export function Header({ onMenuClick, isMobile = false, sidebarOpen = false }: HeaderProps) {
  const { theme, setTheme } = useTheme();
  const { logout } = useSocket();

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-16 items-center justify-between px-4 sm:px-6 gap-4">
        {/* Left side - Logo and Mobile Menu */}
        <div className="flex items-center space-x-2 sm:space-x-4 min-w-0 flex-1">
          {/* Mobile Menu Button */}
          {isMobile && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onMenuClick}
              className="p-2"
            >
              <Menu className="h-5 w-5" />
            </Button>
          )}
          
          <div className="flex items-center space-x-2 min-w-0">
            <Shield className="h-6 w-6 sm:h-8 sm:w-8 text-primary flex-shrink-0" />
            <div className="min-w-0">
              <h1 className="text-sm sm:text-lg font-semibold truncate">Neural Control Hub</h1>
              <p className="text-xs text-muted-foreground hidden sm:block">Advanced Agent Management</p>
            </div>
          </div>
        </div>

        {/* Right side - Actions */}
        <div className="flex items-center space-x-1 sm:space-x-2 flex-shrink-0">
          {/* Version Badge - Hidden on mobile */}
          <div className="hidden md:flex items-center space-x-2">
            <Badge variant="secondary" className="text-xs">v2.1</Badge>
          </div>
          
          {/* Theme Toggle */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" className="relative px-2 sm:px-3 py-2 h-9">
                {theme === 'light' && <Sun className="h-4 w-4" />}
                {theme === 'dark' && <Moon className="h-4 w-4" />}
                {theme === 'system' && <Monitor className="h-4 w-4" />}
                <span className="hidden sm:inline ml-2">
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
          
          {/* Notifications */}
          <NotificationCenter />
          
          {/* User Menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="p-2">
                <User className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuItem>
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