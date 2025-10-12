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
      <div className="p-4 border-b bg-gradient-to-r from-primary/5 to-transparent">
        <div className="flex items-center space-x-2 animate-in fade-in slide-in-from-left duration-300">
          <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center transition-all duration-300 hover:bg-primary/20 hover:scale-110">
            <BarChart3 className="h-4 w-4 text-primary transition-transform duration-200 hover:rotate-12" />
          </div>
          <div>
            <h2 className="text-lg font-semibold transition-colors duration-200 hover:text-primary">Neural Control Hub</h2>
            <p className="text-xs text-muted-foreground">v2.1</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex-1 overflow-auto p-4 scrollbar-hide">
        <nav className="space-y-1">
          {sidebarItems.map((item, index) => {
            const Icon = item.icon;
            return (
              <Button
                key={item.id}
                variant={activeTab === item.id ? "secondary" : "ghost"}
                className={cn(
                  "w-full justify-start h-10 transition-all duration-200 ease-in-out group",
                  "animate-in fade-in slide-in-from-left",
                  activeTab === item.id && "bg-secondary shadow-sm scale-[1.02]",
                  activeTab !== item.id && "hover:bg-secondary/50 hover:scale-[1.02] hover:translate-x-1 hover:shadow-sm"
                )}
                onClick={() => handleTabChange(item.id)}
                style={{ animationDelay: `${index * 50}ms`, animationDuration: '300ms' }}
              >
                <Icon className={cn(
                  "mr-2 h-4 w-4 flex-shrink-0 transition-all duration-200",
                  activeTab === item.id && "text-primary",
                  activeTab !== item.id && "group-hover:text-primary group-hover:scale-110"
                )} />
                <span className="flex-1 text-left">{item.label}</span>
                {item.badge && (
                  <Badge variant="default" className="ml-2 h-5 text-xs animate-pulse">
                    {item.badge}
                  </Badge>
                )}
              </Button>
            );
          })}
        </nav>
      </div>
      
      {/* Footer */}
      <div className="border-t p-4 flex-shrink-0 bg-muted/20">
        <div className="space-y-1">
          <Button 
            variant={activeTab === 'settings' ? "secondary" : "ghost"} 
            className={cn(
              "w-full justify-start h-9 transition-all duration-200 ease-in-out group",
              activeTab === 'settings' && "shadow-sm",
              activeTab !== 'settings' && "hover:bg-secondary/50 hover:translate-x-1 hover:shadow-sm"
            )}
            size="sm"
            onClick={() => handleTabChange('settings')}
          >
            <SettingsIcon className={cn(
              "mr-2 h-4 w-4 transition-all duration-200",
              activeTab !== 'settings' && "group-hover:rotate-90 group-hover:scale-110"
            )} />
            Settings
          </Button>
          <Button 
            variant={activeTab === 'about' ? "secondary" : "ghost"} 
            className={cn(
              "w-full justify-start h-9 transition-all duration-200 ease-in-out group",
              activeTab === 'about' && "shadow-sm",
              activeTab !== 'about' && "hover:bg-secondary/50 hover:translate-x-1 hover:shadow-sm"
            )}
            size="sm"
            onClick={() => handleTabChange('about')}
          >
            <HelpCircle className={cn(
              "mr-2 h-4 w-4 transition-all duration-200",
              activeTab !== 'about' && "group-hover:scale-110"
            )} />
            About
          </Button>
        </div>
      </div>
    </div>
  );
}
