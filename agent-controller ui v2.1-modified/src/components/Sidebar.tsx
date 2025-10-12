import React from 'react';import { cn } from './ui/utils';
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
  Zap,
  Mic,
  Video
} from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
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

export function Sidebar({ activeTab, onTabChange }: SidebarProps) {
  return (
    <div className="flex w-full h-full flex-col">
      <div className="flex-1 overflow-auto p-4">
        <nav className="space-y-1">
          {sidebarItems.map((item, index) => {
            const Icon = item.icon;
            return (
              React.createElement(Button, {
                key: item.id,
                variant: activeTab === item.id ? "secondary" : "ghost",
                className: cn(
                  "w-full justify-start h-10 transition-all duration-200 ease-in-out group",
                  activeTab === item.id && "bg-secondary shadow-sm scale-[1.02]",
                  activeTab !== item.id && "hover:bg-secondary/50 hover:scale-[1.02] hover:shadow-sm hover:translate-x-1"
                ),
                onClick: () => onTabChange(item.id),
                style: { animationDelay: `${index * 50}ms` }
              },
                React.createElement(Icon, { 
                  className: cn(
                    "mr-2 h-4 w-4 flex-shrink-0 transition-all duration-200",
                    activeTab === item.id && "text-primary",
                    activeTab !== item.id && "group-hover:text-primary group-hover:scale-110"
                  )
                }),
                React.createElement("span", { 
                  className: "flex-1 text-left transition-all duration-200"
                }, item.label),
                item.badge && React.createElement(Badge, {
                  variant: "default",
                  className: "ml-2 h-5 text-xs animate-pulse"
                }, item.badge)
              )
            );
          })}
        </nav>
      </div>
      
      <div className="border-t p-4 flex-shrink-0 bg-muted/20">
        <div className="space-y-1">
          {React.createElement(Button, {
            variant: activeTab === 'settings' ? "secondary" : "ghost",
            className: cn(
              "w-full justify-start h-9 transition-all duration-200 ease-in-out group",
              activeTab === 'settings' && "shadow-sm",
              activeTab !== 'settings' && "hover:bg-secondary/50 hover:translate-x-1 hover:shadow-sm"
            ),
            size: "sm",
            onClick: () => onTabChange('settings')
          },
            React.createElement(SettingsIcon, { 
              className: cn(
                "mr-2 h-4 w-4 transition-all duration-200",
                activeTab !== 'settings' && "group-hover:rotate-90 group-hover:scale-110"
              )
            }),
            "Settings"
          )}
          {React.createElement(Button, {
            variant: activeTab === 'about' ? "secondary" : "ghost",
            className: cn(
              "w-full justify-start h-9 transition-all duration-200 ease-in-out group",
              activeTab === 'about' && "shadow-sm",
              activeTab !== 'about' && "hover:bg-secondary/50 hover:translate-x-1 hover:shadow-sm"
            ),
            size: "sm",
            onClick: () => onTabChange('about')
          },
            React.createElement(HelpCircle, { 
              className: cn(
                "mr-2 h-4 w-4 transition-all duration-200",
                activeTab !== 'about' && "group-hover:scale-110"
              )
            }),
            "About"
          )}
        </div>
      </div>
    </div>
  );
}