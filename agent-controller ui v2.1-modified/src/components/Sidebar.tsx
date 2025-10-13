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
          {sidebarItems.map((item) => {
            const Icon = item.icon;
            return (
              React.createElement(Button, {
                key: item.id,
                variant: activeTab === item.id ? "secondary" : "ghost",
                className: cn(
                  "w-full justify-start h-10",
                  activeTab === item.id && "bg-secondary"
                ),
                onClick: () => onTabChange(item.id)
              },
                React.createElement(Icon, { className: "mr-2 h-4 w-4 flex-shrink-0" }),
                React.createElement("span", { className: "flex-1 text-left" }, item.label),
                item.badge && React.createElement(Badge, {
                  variant: "default",
                  className: "ml-2 h-5 text-xs"
                }, item.badge)
              )
            );
          })}
        </nav>
      </div>
      
      <div className="border-t p-4 flex-shrink-0">
        <div className="space-y-1">
          {React.createElement(Button, {
            variant: activeTab === 'settings' ? "secondary" : "ghost",
            className: "w-full justify-start h-9",
            size: "sm",
            onClick: () => onTabChange('settings')
          },
            React.createElement(SettingsIcon, { className: "mr-2 h-4 w-4" }),
            "Settings"
          )}
          {React.createElement(Button, {
            variant: activeTab === 'about' ? "secondary" : "ghost",
            className: "w-full justify-start h-9",
            size: "sm",
            onClick: () => onTabChange('about')
          },
            React.createElement(HelpCircle, { className: "mr-2 h-4 w-4" }),
            "About"
          )}
        </div>
      </div>
    </div>
  );
}