import React from 'react';
import { cn } from './ui/utils';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { 
  BarChart3, 
  Monitor, 
  Terminal, 
  Files, 
  Activity, 
  Users,
  Settings as SettingsIcon,
  HelpCircle,
  Mic,
  Video
} from 'lucide-react';

interface MobileNavigationProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
  onClose?: () => void;
}

const sidebarItems = [
  { id: 'overview', label: 'Overview', icon: BarChart3 },
  { id: 'agents', label: 'Agents', icon: Users },
  { id: 'streaming', label: 'Streaming', icon: Monitor },
  { id: 'commands', label: 'Commands', icon: Terminal },
  { id: 'files', label: 'Files', icon: Files },
  { id: 'voice', label: 'Voice Control', icon: Mic, badge: 'AI' },
  { id: 'video', label: 'Video RTC', icon: Video, badge: 'NEW' },
  { id: 'monitoring', label: 'Monitoring', icon: Activity },
];

export function MobileNavigation({ activeTab, onTabChange, onClose }: MobileNavigationProps) {
  const handleTabChange = (tab: string) => {
    onTabChange(tab);
    if (onClose) {
      onClose();
    }
  };

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="p-4 border-b">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center">
            <BarChart3 className="h-4 w-4 text-primary" />
          </div>
          <div>
            <h2 className="text-lg font-semibold">Neural Control Hub</h2>
            <p className="text-xs text-muted-foreground">v2.1</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex-1 overflow-auto p-4">
        <nav className="space-y-1">
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
      
      {/* Footer */}
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
  );
}
